import pandas as pd

df = pd.read_csv('extended_candles_40days.csv')
df['date'] = pd.to_datetime(df['date'])
print(df.groupby('symbol')['date'].min().value_counts())
print(f"Total symbols: {df['symbol'].nunique()}")
