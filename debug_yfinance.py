import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

symbol = "AMPX"
print(f"Fetching {symbol} from Yahoo Finance...")

try:
    # Fetch 5-minute data for the last 5 days to ensure we get today's data if available
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5d", interval="5m")
    
    if df.empty:
        print("❌ Empty response from Yahoo Finance")
    else:
        print(f"✅ Got {len(df)} candles")
        
        # Ensure timezone is NY
        if df.index.tz is None:
            df.index = df.index.tz_localize('America/New_York')
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
