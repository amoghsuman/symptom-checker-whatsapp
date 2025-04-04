from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from infermedica_client import parse_symptoms
import uuid

app = Flask(__name__)

# Temporary in-memory store: phone_number -> state
user_sessions = {}

@app.route("/whatsapp", methods=['POST'])
def symptom_checker():
    incoming_msg = request.form.get('Body').strip()
    phone = request.form.get('From')

    session = user_sessions.get(phone, {"step": 0})

    resp = MessagingResponse()
    msg = resp.message()

    # Step 0: Ask gender
    if session["step"] == 0:
        msg.body("Hi! Let's check your symptoms.\nWhat is your gender? (male/female)")
        session["step"] = 1

    # Step 1: Capture gender
    elif session["step"] == 1:
        if incoming_msg.lower() in ['male', 'female']:
            session["gender"] = incoming_msg.lower()
            msg.body("Got it. What's your age?")
            session["step"] = 2
        else:
            msg.body("Please reply with either 'male' or 'female'.")

    # Step 2: Capture age
    elif session["step"] == 2:
        if incoming_msg.isdigit():
            session["age"] = int(incoming_msg)
            msg.body("Thanks! Now tell me what symptoms you’re experiencing?")
            session["step"] = 3
        else:
            msg.body("Please reply with a valid age in numbers.")

    # Step 3: Capture symptoms and analyze
    elif session["step"] == 3:
        symptoms_text = incoming_msg
        result = parse_symptoms(symptoms_text, sex=session["gender"], age=session["age"])

        mentions = result.get("mentions", [])
        if mentions:
            msg.body("From your symptoms, I understood:\n" + "\n".join(f"- {m['name']}" for m in mentions))
        else:
            msg.body("Hmm, I couldn't identify any known symptoms. Could you describe it differently?")

        # Reset session
        session = {"step": 0}

    user_sessions[phone] = session
    return str(resp)

if __name__ == "__main__":
    app.run()
