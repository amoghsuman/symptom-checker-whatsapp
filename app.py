from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from infermedica_client import parse_symptom_text, run_diagnosis

app = Flask(__name__)
user_sessions = {}

@app.route("/whatsapp", methods=['POST'])
def symptom_checker():
    incoming_msg = request.form.get('Body').strip().lower()
    phone = request.form.get('From')
    resp = MessagingResponse()
    msg = resp.message()

    # Debug logs (optional - shows in Render logs)
    print(f"[{phone}] Message: {incoming_msg}")

    # Handle restart/reset logic before anything else
    if incoming_msg in ["restart", "*start", "start", "hi", "hello"]:
    session = {
        "step": "awaiting_gender"
    }
    msg.body("Welcome to the Symptom Checker Bot.\nWhat is your gender? (male/female)")
    user_sessions[phone] = session
    return str(resp)

    # Load session only after restart check
    session = user_sessions.get(phone, {"step": "awaiting_gender"})

    print(f"[{phone}] Current step: {session.get('step')}")

    # Step 1: Gender
    if session["step"] == "awaiting_gender":
        if incoming_msg in ["male", "female"]:
            session["gender"] = incoming_msg
            session["step"] = "awaiting_age"
            msg.body("Got it. What is your age?")
        else:
            msg.body("Welcome! Please tell me your gender (male/female).")

    # Step 2: Age
    elif session["step"] == "awaiting_age":
        if incoming_msg.isdigit():
            session["age"] = int(incoming_msg)
            session["step"] = "awaiting_symptom"
            msg.body("Thanks. What's the main symptom you're experiencing?")
        else:
            msg.body("Please reply with a valid age (e.g., 30).")

    # Step 3: Initial symptom
    elif session["step"] == "awaiting_symptom":
        result = parse_symptom_text(incoming_msg, session["gender"], session["age"])
        mentions = result.get("mentions", [])
        if mentions:
            session["evidence"] = [{
                "id": mentions[0]['id'],
                "choice_id": "present"
            }]
            diagnosis = run_diagnosis(session["evidence"], session["gender"], session["age"])
            session["question"] = diagnosis.get("question")
            session["conditions"] = diagnosis.get("conditions")
            session["question_count"] = 0
            session["step"] = "asking_question"

            if session["question"] and session["question"]["type"] == "single":
                msg.body(f"{session['question']['text']} (yes/no/don't know)")
            else:
                msg.body(format_conditions(session["conditions"]))
                session = {"step": "awaiting_gender"}
        else:
            msg.body("I couldn't recognize that symptom. Please try another one.")

    # Step 4: Follow-up question flow
    elif session["step"] == "asking_question":
        answer_map = {
            "yes": "present",
            "no": "absent",
            "don't know": "unknown",
            "dont know": "unknown"
        }

        if session["question"]["type"] != "single":
            # Skip multi-choice or open-ended question
            for item in session["question"]["items"]:
                session["evidence"].append({
                    "id": item["id"],
                    "choice_id": "unknown"
                })
        elif incoming_msg in answer_map:
            selected_choice = answer_map[incoming_msg]
            session["evidence"].append({
                "id": session["question"]["items"][0]["id"],
                "choice_id": selected_choice
            })
        else:
            msg.body("Please reply with 'yes', 'no', or 'don't know'.")
            user_sessions[phone] = session
            return str(resp)

        # Run next diagnosis step
        diagnosis = run_diagnosis(session["evidence"], session["gender"], session["age"])
        session["question"] = diagnosis.get("question")
        session["conditions"] = diagnosis.get("conditions")
        session["question_count"] += 1

        # Stop after 25 questions or when no more questions left
        if not session["question"] or session["question_count"] >= 25:
            msg.body(format_conditions(session["conditions"]))
            session = {"step": "awaiting_gender"}
        elif session["question"]["type"] == "single":
            msg.body(f"{session['question']['text']} (yes/no/don't know)")
        else:
            # Skip and auto-answer unknown for non-yes/no questions
            for item in session["question"]["items"]:
                session["evidence"].append({
                    "id": item["id"],
                    "choice_id": "unknown"
                })
            diagnosis = run_diagnosis(session["evidence"], session["gender"], session["age"])
            session["question"] = diagnosis.get("question")
            session["conditions"] = diagnosis.get("conditions")
            if not session["question"] or session["question_count"] >= 25:
                msg.body(format_conditions(session["conditions"]))
                session = {"step": "awaiting_gender"}
            else:
                msg.body(f"{session['question']['text']} (yes/no/don't know)")

    user_sessions[phone] = session
    return str(resp)

def format_conditions(conditions):
    if not conditions:
        return "Sorry, I couldn't determine your condition. Please consult a doctor."
    reply = "🧠 Based on your answers, you might have:\n\n"
    for cond in conditions[:3]:  # Top 3 results
        name = cond['name']
        prob = round(cond['probability'] * 100, 1)
        reply += f"- {name} ({prob}%)\n"
    return reply
