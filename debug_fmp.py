import requests
import pandas as pd
import os
from dotenv import load_dotenv
import pytz
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")
symbol = "AMPX"

# Try v4 endpoint?
url = f"https://financialmodelingprep.com/api/v4/historical-chart/5min/{symbol}?apikey={API_KEY}"
print(f"Fetching {url}...")

try:
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        print(f"Status: {res.status_code}")
        print(res.text)
    else:
        data = res.json()
        if not data:
            print("❌ Empty response from FMP")
        else:
            print(f"✅ Got {len(data)} candles")
            print(data[:1])
        
except Exception as e:
    print(f"Error: {e}")
