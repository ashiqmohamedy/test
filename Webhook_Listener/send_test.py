import requests
import json
import base64
import urllib3

# This line suppresses the annoying SSL warnings in your console
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIG
TOPIC = "wh_receiver_8824"
URL = f"https://ntfy.sh/{TOPIC}"


def send_webhook(username=None, password=None):
    data_payload = {
        "event": "user_login",
        "status": "success",
        "user_id": 12345
    }

    headers_to_send = {
        "Content-Type": "application/json"
    }

    if username and password:
        auth_str = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers_to_send["Authorization"] = f"Basic {encoded_auth}"

    wrapped_package = {
        "headers": headers_to_send,
        "payload": data_payload
    }

    # --- THE FIX IS HERE: verify=False ---
    response = requests.post(
        URL,
        data=json.dumps(wrapped_package),
        verify=False
    )

    if response.status_code == 200:
        print(f"✅ Sent successfully to {TOPIC}")
    else:
        print(f"❌ Failed with status: {response.status_code}")


print("Sending Authenticated Webhook...")
send_webhook("admin", "secret123")