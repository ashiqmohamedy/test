import requests
import urllib3

# This hides the "InsecureRequestWarning" message in your terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://kvdb.io/ashiq-test-webhook-2026/history"
payload = {"status": "Success!", "user": "ashiq"}

try:
    # Added verify=False to skip the SSL check
    response = requests.post(url, json=payload, verify=False)
    print(f"Status Code: {response.status_code}")
    print("Check your Streamlit UI!")
except Exception as e:
    print(f"An error occurred: {e}")