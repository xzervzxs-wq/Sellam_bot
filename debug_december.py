import pandas as pd

DATA_FILE = 'extended_candles_60days.csv'
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])
df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')

dec_data = df_all[df_all['date'].dt.month == 12]
print(f"December rows: {len(dec_data)}")

if len(dec_data) > 0:
    first_symbol = dec_data['symbol'].iloc[0]
    print(f"Inspecting symbol: {first_symbol}")
    
    sym_data = dec_data[dec_data['symbol'] == first_symbol]
    print(sym_data[['date', 'open', 'close', 'volume']].head(10))
    
    # Check between_time
    sym_data = sym_data.set_index('date')
    morning = sym_data.between_time('09:30', '09:55')
    print(f"\nMorning candles (09:30-09:55): {len(morning)}")
    print(morning[['open', 'close']].head(10))
