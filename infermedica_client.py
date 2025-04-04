import requests

APP_ID = 'YOUR_APP_ID'   # Replace later
APP_KEY = 'YOUR_APP_KEY' # Replace later

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
