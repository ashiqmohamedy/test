import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://ntfy.sh/ashiq_webhook_test_2026_xyz"
auth = HTTPBasicAuth('my_username', 'my_password')

# We bundle headers into the message so ntfy carries them to our UI
payload = {
    "headers": {"Authorization": "Basic bXlfdXNlcm5hbWU6bXlfcGFzc3dvcmQ="},  # Simulated header
    "payload": {"event": "secure_data", "id": 101}
}

requests.post(url, data=json.dumps(payload), verify=False)