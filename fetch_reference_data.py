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

if not API_KEY:
    print("❌ API KEY not found")
    exit()

def get_stocks_list():
    print("📦 Fetching stock list from FMP...")
    url = (f"https://financialmodelingprep.com/stable/company-screener"
           f"?priceMoreThan=0.02&priceLowerThan=10&volumeMoreThan=150000"
           f"&isEtf=false&exchange=nasdaq,nyse,amex&isActivelyTrading=true&limit=2000&apikey={API_KEY}")
    
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
            
            # Basic float check (optional, but good to keep consistent)
            try:
                f_url = f"https://financialmodelingprep.com/stable/shares-float?symbol={sym}&apikey={API_KEY}"
                f_data = requests.get(f_url, timeout=1).json()
                if f_data and isinstance(f_data, list):
                    float_shares = f_data[0].get('floatShares', 0)
                    if 0 < float_shares <= 200_000_000:
                        final_list.append(sym)
                        print(f"📌 {len(final_list)}/100: {sym}")
            except:
                pass
                
        return final_list
    except Exception as e:
        print(f"❌ Error fetching list: {e}")
        return []

def fetch_candles(symbol):
    # Fetch 15 days of 5-minute candles
    # EODHD allows fetching by timestamp
    # 15 days * 24 hours * 60 mins * 60 secs
    from_timestamp = int(time.time()) - (20 * 24 * 60 * 60) # 20 days to be safe for weekends
    
    url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Failed to fetch {symbol}: {resp.status_code}")
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
    stocks = get_stocks_list()
    if not stocks:
        print("❌ No stocks found")
        return
        
    print(f"\n📥 Fetching candles for {len(stocks)} stocks...")
    
    all_data = []
    for i, sym in enumerate(stocks):
        print(f"⏳ {i+1}/{len(stocks)} Fetching {sym}...", end="\r")
        df = fetch_candles(sym)
        if df is not None and not df.empty:
            all_data.append(df)
        time.sleep(0.5) # Rate limit
        
    if all_data:
        final_df = pd.concat(all_data)
        filename = f"reference_candles_15days_{datetime.now().strftime('%Y%m%d')}.csv"
        final_df.to_csv(filename, index=False)
        print(f"\n✅ Saved {len(final_df)} rows to {filename}")
    else:
        print("\n❌ No data collected")

if __name__ == "__main__":
    main()
