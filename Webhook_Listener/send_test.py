import requests
import json
import base64

# CONFIG
TOPIC = "wh_receiver_8824"
URL = f"https://ntfy.sh/{TOPIC}"


def send_webhook(username=None, password=None):
    # 1. Prepare the data
    data_payload = {
        "event": "user_login",
        "status": "success",
        "user_id": 12345
    }

    # 2. Prepare "Tunneled" headers
    headers_to_send = {
        "Content-Type": "application/json"
    }

    if username and password:
        # Create Basic Auth string manually
        auth_str = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers_to_send["Authorization"] = f"Basic {encoded_auth}"

    # 3. Wrap everything in one JSON for ntfy to carry
    wrapped_package = {
        "headers": headers_to_send,
        "payload": data_payload
    }

    # 4. POST to ntfy (WITHOUT real Auth headers, so ntfy doesn't block it)
    response = requests.post(
        URL,
        data=json.dumps(wrapped_package),
        headers={"Title": "Webhook Inbound"}  # Optional ntfy header
    )

    if response.status_code == 200:
        print(f"✅ Sent successfully to {TOPIC}")
    else:
        print(f"❌ Failed with status: {response.status_code}")


# Test Authenticated
print("Sending Authenticated Webhook...")
send_webhook("admin", "secret123")

# Test Unauthenticated
print("Sending Unauthenticated Webhook...")
send_webhook()