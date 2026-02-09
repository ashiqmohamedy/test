import requests
import json
import base64

# Use the same credentials as the UI
user, pw = "admin", "secret123"
valid_auth = f"Basic {base64.b64encode(f'{user}:{pw}'.encode()).decode()}"
wrong_auth = f"Basic {base64.b64encode(b'hacker:1234').decode()}"

URL = "https://ntfy.sh/ashiq_webhook_test_2026_xyz"


def send_test(auth_value):
    payload = {
        "headers": {"Authorization": auth_value},
        "payload": {"event": "login_attempt", "ip": "192.168.1.1"}
    }
    requests.post(URL, data=json.dumps(payload), verify=False)


# 1. Send Valid
send_test(valid_auth)
# 2. Send Invalid
send_test(wrong_auth)
# 3. Send No Auth
requests.post(URL, data=json.dumps({"payload": {"test": "no auth"}}), verify=False)

print("Check your UI for Green, Red, and Gray boxes!")