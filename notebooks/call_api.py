import requests
from urllib.parse import quote

SAVE_PATH = "../src/data-pipline/all_SP500_cap_financials.csv"

url = "http://127.0.0.1:8000/pull_large_cap_dataset"
params = {
    "save_path": SAVE_PATH,
    "max_workers": 10
}

try:
    response = requests.get(url, params=params)
    print("Status code:", response.status_code)
    print("Response text:", response.text)
except Exception as e:
    print(f"[ERROR] Could not call API: {e}")
