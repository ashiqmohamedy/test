import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# We will use a unique name in the URL to act as your "ID"
# Change 'ashiq-unique-123' to something random if you want it private
URL = "https://jsonbin.org/ashiq-unique-123/webhooks"

new_payload = {
    "status": "Success",
    "message": "Testing from local machine",
    "user": "ashiq"
}

try:
    # 1. Get existing history
    response = requests.get(URL, verify=False)
    history = response.json() if response.status_code == 200 else []

    # 2. Add new data
    if not isinstance(history, list): history = []
    history.append(new_payload)

    # 3. Push back
    # Note: jsonbin.org might require a dummy 'Authorization' header
    # for public bins sometimes, but let's try the direct way first.
    res = requests.post(URL, json=history, verify=False)

    print(f"Status Code: {res.status_code}")
    print("Check your Streamlit UI!")
except Exception as e:
    print(f"Error: {e}")