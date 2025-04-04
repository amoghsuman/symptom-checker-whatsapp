import os
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("INFERMEDICA_APP_ID")
APP_KEY = os.getenv("INFERMEDICA_APP_KEY")

API_URL = "https://api.infermedica.com/v3"

headers = {
    "App-Id": APP_ID,
    "App-Key": APP_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def parse_symptom_text(text, sex, age):
    url = f"{API_URL}/parse"
    payload = {
        "text": text,
        "age": {"value": age},
        "sex": sex
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def run_diagnosis(evidence, sex, age):
    url = f"{API_URL}/diagnosis"
    payload = {
        "sex": sex,
        "age": {"value": age},
        "evidence": evidence
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
