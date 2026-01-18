import pandas as pd

DATA_FILE = 'extended_candles_60days.csv'
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])
df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')

dec_data = df_all[df_all['date'].dt.month == 12]
dec_data['day'] = dec_data['date'].dt.date
dec_data['time'] = dec_data['date'].dt.time

# Group by symbol and day, get min time
min_times = dec_data.groupby(['symbol', 'day'])['time'].min().reset_index()

print("Earliest times distribution:")
print(min_times['time'].value_counts().head(10))

print("\nSample of min times:")
print(min_times.head(20))
