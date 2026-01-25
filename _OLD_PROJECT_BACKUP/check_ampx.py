import pandas as pd
import numpy as np

# Load the data
file_path = 'morning_scan_20251224_212928.csv'
df = pd.read_csv(file_path, names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'symbol'])

# Filter for AMPX
ampx_df = df[df['symbol'] == 'AMPX'].copy()

# Convert columns to numeric
cols = ['open', 'high', 'low', 'close', 'volume']
for col in cols:
    ampx_df[col] = pd.to_numeric(ampx_df[col], errors='coerce')

ampx_df['datetime'] = pd.to_datetime(ampx_df['datetime'])
ampx_df.set_index('datetime', inplace=True)
ampx_df.sort_index(inplace=True)

print(f"Loaded {len(ampx_df)} candles for AMPX")

def debug_golden_grinder(df):
    # Bypass length check for debugging
    # if len(df) < 50: 
    #     print("❌ Not enough data (<50)")
    #     return False
    
    # 1. Calculate EMAs
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

    current = df.iloc[-1]
    price = current['close']
    print(f"Current Price: {price}")
    
    if price < 5 or price > 200:
        print(f"❌ Price {price} out of range (5-200)")
        # return False # Continue for debugging
    
    # 3. Candle Size Check
    last_5 = df.tail(5).copy()
    print("\nChecking last 5 candles:")
    failed = False
    for i in range(len(last_5)):
        c = last_5.iloc[i]
        open_p = c['open']
        close_p = c['close']
        high_p = c['high']
        
        body_pct = (abs(close_p - open_p) / open_p) * 100
        is_red = close_p < open_p
        
        print(f"  Candle {i}: Open={open_p}, Close={close_p}, Body%={body_pct:.2f}%, Red={is_red}")

        if body_pct > 1.2:
            print(f"    ❌ Candle {i} too big ({body_pct:.2f}%)")
            failed = True

        if is_red and body_pct > 0.4:
            print(f"    ❌ Red candle {i} too big ({body_pct:.2f}%)")
            failed = True
            
        upper_wick = high_p - max(open_p, close_p)
        wick_pct = (upper_wick / open_p * 100)
        if body_pct > 0.1 and wick_pct > 0.8:
            print(f"    ❌ Ugly upper wick in candle {i} ({wick_pct:.2f}%)")
            failed = True

    # 4. EMA9 Distance
    dist = (current['close'] - current['ema9']) / current['ema9'] * 100
    print(f"\nDistance from EMA9: {dist:.2f}%")
    if dist > 0.8:
        print(f"❌ Too far from EMA9 ({dist:.2f}%)")
        failed = True

    if failed:
        print("❌ FAILED Golden Grinder")
    else:
        print("✅ PASSED Golden Grinder")
    return not failed

debug_golden_grinder(ampx_df)
