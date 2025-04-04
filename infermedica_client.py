import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

APP_ID = os.getenv('INFERMEDICA_APP_ID')
APP_KEY = os.getenv('INFERMEDICA_APP_KEY')

headers = {
    'App-Id': APP_ID,
    'App-Key': APP_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

API_URL = "https://api.infermedica.com/v3"

def parse_symptoms(text, sex="male", age=30):
    url = f"{API_URL}/parse"
    data = {
        "text": text,
        "age": {"value": age},
        "sex": sex
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
