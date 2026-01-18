import pandas as pd
import requests
import os
import time
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")

SYMBOLS = ['VIVK', 'NCL', 'MWG', 'SOBR', 'XTKG', 'SIDU', 'WOK', 'IRBT', 'ELOG', 'LAZR', 'APLT', 'INDP', 'SGD', 'ATPC', 'FMFC', 'SDM', 'IVP', 'ECDA', 'DRMA', 'STEC', 'KAVL', 'CTXR', 'RPTX', 'RR', 'ECX', 'RVPH', 'SRXH', 'OCG', 'PCLA', 'SOC', 'VMAR', 'GPUS', 'WLDS', 'RDW', 'TSE', 'TNMG', 'RZLV', 'ZYXI', 'RZLT', 'TMC', 'AIRE', 'SLS', 'TE', 'PFSA', 'TRIB', 'UAMY', 'LAES', 'LAC', 'IBRX', 'VUZI', 'EUDA', 'MIST', 'NVTS', 'HXHX', 'BDN', 'SPCE', 'QSI', 'POET', 'UWMC', 'AIV', 'HIHO', 'SBET', 'DRCT', 'CRML', 'RCAT', 'ABAT', 'ASBP', 'NFE', 'KALA', 'SATL', 'NUAI', 'YCBD', 'GOSS', 'BLNK', 'CANF', 'LNKS', 'LFMD', 'ORIS', 'AIRI', 'CRGY', 'CYPH', 'OTLK', 'IXHL', 'AMPX', 'RVYL', 'BEAT', 'SLDP', 'PGEN', 'LION', 'PLG', 'INVZ', 'ASPI', 'FFAI', 'TMQ', 'HUMA', 'ENVX', 'GOVX', 'TNYA', 'BFLY', 'SG']

# Target Range: 2025-10-01 to 2025-11-05
START_DATE = int(datetime(2025, 10, 1).timestamp())
END_DATE = int(datetime(2025, 11, 5).timestamp())

all_data = []

print(f"🚀 Fetching data for {len(SYMBOLS)} stocks from 2025-10-01 to 2025-11-05...")

for i, symbol in enumerate(SYMBOLS):
    try:
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': START_DATE,
            'to': END_DATE,
            'period': '5m',
            'fmt': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                # EODHD returns: timestamp, open, high, low, close, volume
                # We need to convert timestamp to datetime
                df['date'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert('America/New_York')
                df['symbol'] = symbol
                
                # Keep only relevant columns
                df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
                all_data.append(df)
                print(f"✅ {symbol}: {len(df)} candles")
            else:
                print(f"⚠️ {symbol}: No data")
        else:
            print(f"❌ {symbol}: Error {response.status_code}")
            
    except Exception as e:
        print(f"❌ {symbol}: Exception {e}")
        
    # Avoid rate limits
    time.sleep(0.2)

if all_data:
    new_df = pd.concat(all_data)
    
    # Load existing data
    existing_df = pd.read_csv('extended_candles_40days.csv')
    existing_df['date'] = pd.to_datetime(existing_df['date'])
    
    # Make existing data timezone-aware (assuming it's NY time)
    if existing_df['date'].dt.tz is None:
        existing_df['date'] = existing_df['date'].dt.tz_localize('America/New_York')
    else:
        existing_df['date'] = existing_df['date'].dt.tz_convert('America/New_York')
    
    # Combine
    combined_df = pd.concat([new_df, existing_df])
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['symbol', 'date']).sort_values(['symbol', 'date'])
    
    # Save
    output_file = 'extended_candles_60days.csv'
    combined_df.to_csv(output_file, index=False)
    print(f"\n💾 Saved {len(combined_df)} rows to {output_file}")
else:
    print("\n❌ No data fetched.")
