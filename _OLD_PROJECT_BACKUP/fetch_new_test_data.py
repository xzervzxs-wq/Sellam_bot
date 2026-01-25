import requests
import pandas as pd
import time
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")
OLD_DATA_FILE = 'reference_candles_15days_20251225.csv'

if not API_KEY:
    print("❌ API KEY not found")
    exit()

def get_existing_symbols():
    if os.path.exists(OLD_DATA_FILE):
        try:
            df = pd.read_csv(OLD_DATA_FILE)
            return set(df['symbol'].unique())
        except:
            return set()
    return set()

def get_new_stocks_list(existing_symbols):
    print("📦 Fetching fresh stock list from FMP...")
    # We fetch more to ensure we have enough new ones
    url = (f"https://financialmodelingprep.com/stable/company-screener"
           f"?priceMoreThan=0.02&priceLowerThan=10&volumeMoreThan=100000"
           f"&isEtf=false&exchange=nasdaq,nyse,amex&isActivelyTrading=true&limit=500&apikey={API_KEY}")
    
    try:
        results = requests.get(url, timeout=20).json()
        if not results: return []
        
        # Sort by volume
        results.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        final_list = []
        for item in results:
            if len(final_list) >= 100: break
            
            sym = item.get('symbol')
            if not sym or len(sym) > 5: continue
            
            # Skip if already tested
            if sym in existing_symbols: continue
            
            final_list.append(sym)
            print(f"📌 {len(final_list)}/100: {sym} (New)")
                
        return final_list
    except Exception as e:
        print(f"❌ Error fetching list: {e}")
        return []

def fetch_candles(symbol):
    # Fetch 20 days of 5-min candles
    from_timestamp = int(time.time()) - (25 * 24 * 60 * 60) # 25 days buffer
    
    url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        if not data: return None
        
        df = pd.DataFrame(data)
        
        # Normalize columns
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
    existing = get_existing_symbols()
    print(f"ℹ️ Found {len(existing)} existing symbols to exclude.")
    
    stocks = get_new_stocks_list(existing)
    if not stocks:
        print("❌ No new stocks found")
        return
        
    print(f"\n📥 Fetching 20-day candles for {len(stocks)} NEW stocks...")
    
    all_data = []
    for i, sym in enumerate(stocks):
        print(f"⏳ {i+1}/{len(stocks)} Fetching {sym}...", end="\r")
        df = fetch_candles(sym)
        if df is not None and not df.empty:
            all_data.append(df)
        time.sleep(0.5) # Rate limit
        
    if all_data:
        final_df = pd.concat(all_data)
        filename = f"new_test_candles_20days_{datetime.now().strftime('%Y%m%d')}.csv"
        final_df.to_csv(filename, index=False)
        print(f"\n✅ Saved {len(final_df)} rows to {filename}")
    else:
        print("\n❌ No data collected")

if __name__ == "__main__":
    main()
