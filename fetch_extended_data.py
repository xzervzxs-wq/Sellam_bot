import pandas as pd
import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")
INPUT_FILE = 'reference_candles_15days_20251225.csv'
OUTPUT_FILE = 'extended_candles_40days.csv'

def fetch_extended_history(symbol):
    # Fetch 40 days of data
    # 40 days * 24h * 60m * 60s
    from_timestamp = int(time.time()) - (50 * 24 * 60 * 60) # 50 days buffer to ensure 40 trading days
    
    url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return None
        data = resp.json()
        if not data: return None
        
        df = pd.DataFrame(data)
        df.columns = df.columns.str.lower()
        
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        elif 'datetime' in df.columns:
            df['date'] = pd.to_datetime(df['datetime'])
        else:
            return None
            
        df['symbol'] = symbol
        return df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"⚠️ Error {symbol}: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print("❌ Input file not found.")
        return

    print("📖 Reading original stock list...")
    df_orig = pd.read_csv(INPUT_FILE)
    symbols = df_orig['symbol'].unique()
    
    print(f"📋 Found {len(symbols)} stocks. Fetching 40 days of history for each...")
    
    all_data = []
    for i, sym in enumerate(symbols):
        print(f"⏳ {i+1}/{len(symbols)} Fetching {sym}...", end="\r")
        df = fetch_extended_history(sym)
        if df is not None and not df.empty:
            all_data.append(df)
        time.sleep(0.5)
        
    if all_data:
        final_df = pd.concat(all_data)
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Saved {len(final_df)} rows to {OUTPUT_FILE}")
    else:
        print("\n❌ Failed to fetch data.")

if __name__ == "__main__":
    main()
