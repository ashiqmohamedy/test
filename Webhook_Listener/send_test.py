import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Use a very unique topic name so others don't see your data
TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}"

new_payload = {
    "status": "Success",
    "message": "Hello from Local Python",
    "user": "ashiq"
}

try:
    # We send the JSON as the "Body" of the request
    # ntfy.sh is great because it accepts simple POST requests
    res = requests.post(URL,
                        data=json.dumps(new_payload),
                        headers={"Title": "New Webhook Received"},
                        verify=False)

    print(f"Status Code: {res.status_code}")  # Looking for 200
    print(f"Go to https://ntfy.sh/{TOPIC} to see it in the browser!")
except Exception as e:
    print(f"Error: {e}")