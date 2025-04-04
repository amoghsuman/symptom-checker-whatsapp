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

    session = user_sessions.get(phone, {"step": "awaiting_gender"})

    if session["step"] == "awaiting_gender":
        if incoming_msg in ["male", "female"]:
            session["gender"] = incoming_msg
            session["step"] = "awaiting_age"
            msg.body("Got it. What is your age?")
        else:
            msg.body("Welcome! Please tell me your gender (male/female).")

    elif session["step"] == "awaiting_age":
        if incoming_msg.isdigit():
            session["age"] = int(incoming_msg)
            session["step"] = "awaiting_symptom"
            msg.body("Thanks. What's the main symptom you're experiencing?")
        else:
            msg.body("Please reply with a valid age (number).")

    elif session["step"] == "awaiting_symptom":
        # Parse symptom to get symptom ID
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
            if session["question"]:
                session["step"] = "asking_question"
                msg.body(f"{session['question']['text']} (yes/no/don't know)")
            else:
                msg.body(format_conditions(diagnosis["conditions"]))
                session = {"step": "awaiting_gender"}  # Reset session
        else:
            msg.body("I couldn't recognize that symptom. Can you rephrase it?")

    elif session["step"] == "asking_question":
        answer_map = {
            "yes": "present",
            "no": "absent",
            "don't know": "unknown",
            "dont know": "unknown"
        }
        if incoming_msg in answer_map:
            selected_choice = answer_map[incoming_msg]
            question_item = {
                "id": session["question"]["items"][0]["id"],
                "choice_id": selected_choice
            }
            session["evidence"].append(question_item)

            # Get next question or final conditions
            diagnosis = run_diagnosis(session["evidence"], session["gender"], session["age"])
            session["question"] = diagnosis.get("question")
            session["conditions"] = diagnosis.get("conditions")

            if session["question"]:
                msg.body(f"{session['question']['text']} (yes/no/don't know)")
            else:
                msg.body(format_conditions(diagnosis["conditions"]))
                session = {"step": "awaiting_gender"}  # Reset session
        else:
            msg.body("Please reply with 'yes', 'no', or 'don't know'.")

    user_sessions[phone] = session
    return str(resp)

def format_conditions(conditions):
    reply = "🧠 Based on your answers, you might have:\n\n"
    for cond in conditions[:3]:  # Top 3 conditions
        name = cond['name']
        prob = round(cond['probability'] * 100, 1)
        reply += f"- {name} ({prob}%)\n"
    return reply
