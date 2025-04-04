from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from infermedica_client import parse_symptoms

app = Flask(__name__)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.form.get('Body')
    user_sex = "male"
    user_age = 30
    
    response_data = parse_symptoms(incoming_msg, sex=user_sex, age=user_age)
    
    conditions = [mention['name'] for mention in response_data.get("mentions", [])]
    
    reply = "From your message, I understood these symptoms:\n"
    for condition in conditions:
        reply += f"- {condition}\n"
    
    if not conditions:
        reply = "Sorry, I couldn't recognize any symptoms. Please describe your issue in more detail."
    
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run()
