import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
import pytz
from datetime import datetime

load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")
symbol = "AMPX"

# Get timestamp for 3 days ago
from_timestamp = int(time.time()) - (3 * 24 * 60 * 60)

url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
print(f"Fetching {url}...")

try:
    resp = requests.get(url, timeout=10)
    data = resp.json()
    
    if not data:
        print("❌ Empty response from EODHD")
    else:
        print(f"✅ Got {len(data)} candles")
        df = pd.DataFrame(data)
        
        # Handle columns
        df_cols = df.columns.str.lower()
        if 'timestamp' in df_cols:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        elif 'datetime' in df_cols:
            df['date'] = pd.to_datetime(df['datetime'])
        else:
            df['date'] = pd.to_datetime(df.iloc[:, 0])
            
        # Set index and timezone
        df.set_index('date', inplace=True)
        if df.index.tz is None: 
            df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df.index = df.index.tz_convert('America/New_York')
            
        print(df.tail())
        print(f"Last candle date: {df.index[-1]}")
        
        ny_tz = pytz.timezone('America/New_York')
        today = datetime.now(ny_tz).date()
        print(f"Today in NY: {today}")
        
        if df.index[-1].date() == today:
            print("✅ Data is from TODAY!")
        else:
            print("❌ Data is OLD (Yesterday or before)")

except Exception as e:
    print(f"Error: {e}")
