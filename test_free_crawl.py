import pandas as pd
import numpy as np

DATA_FILE = 'extended_candles_60days.csv'

print('=' * 90)
print('🕵️‍♂️ اختبار استراتيجية الزحف الحر (Free Crawl)')
print('=' * 90)

df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])

try:
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except: pass

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all['time_str'] = df_all['date'].dt.strftime('%H:%M')

results = []
grouped = df_all.groupby(['symbol', 'day_str'])

print("⏳ جاري تحليل الزحف الحر...")

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_values('date')
    
    # Strict 6 candles check (09:30 to 10:00)
    required_times = ['09:30', '09:35', '09:40', '09:45', '09:50', '09:55']
    morning_candles = day_data[day_data['time_str'].isin(required_times)].sort_values('date')
    
    if len(morning_candles) != 6: continue
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    volume_vals = morning_candles['volume'].values
    
    # 1. Crawl Filter (Body < 1.0%)
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: continue
    
    # 2. Silent Volume (Decreasing)
    if len(volume_vals) >= 6:
        vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0
    else:
        vol_growth = 1.0
        
    is_silent = vol_growth < 1.0
    if not is_silent: continue # Strict Silent Condition
    
    # 3. Green Dominance (At least 4 green candles)
    green_candles = sum(1 for c in candles_vals if c[3] >= c[0])
    if green_candles < 4: continue
    
    # 4. Consolidation (Tight Range)
    day_high = morning_candles['high'].max()
    day_low = morning_candles['low'].min()
    range_pct = (day_high - day_low) / day_low * 100
    
    # Entry Logic: Breakout of the High
    entry_price = day_high
    entry_time = morning_candles.iloc[-1]['date']
    
    rest_of_day = day_data[day_data['date'] > entry_time]
    if len(rest_of_day) == 0: continue
    
    # Check if price broke the high
    breakout_candles = rest_of_day[rest_of_day['high'] > entry_price]
    
    if len(breakout_candles) == 0:
        # No breakout, no trade
        continue
        
    # Trade activated
    first_breakout = breakout_candles.iloc[0]
    breakout_time = first_breakout['date']
    
    # Calculate result from breakout point
    post_breakout = rest_of_day[rest_of_day['date'] >= breakout_time]
    
    max_gain = (post_breakout['high'].max() - entry_price) / entry_price * 100
    max_loss = (post_breakout['low'].min() - entry_price) / entry_price * 100
    
    results.append({
        'symbol': symbol,
        'gain': max_gain,
        'loss': max_loss,
        'day': day,
        'range_pct': range_pct
    })

df = pd.DataFrame(results)

if len(df) == 0:
    print("❌ لم يتم العثور على أي صفقات تطابق الشروط.")
    exit()

# Define Losers (Loss < -3%) vs Winners (Gain > 3%)
losers = df[df['loss'] < -3]
winners = df[df['gain'] > 3]

print(f"\n📊 إجمالي الصفقات: {len(df)}")
print(f"✅ الرابحة (>3%): {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
print(f"❌ الخاسرة (<-3%): {len(losers)} ({len(losers)/len(df)*100:.1f}%)")

# Monthly Breakdown
df['month'] = pd.to_datetime(df['day']).dt.strftime('%Y-%m')
monthly_stats = df.groupby('month').agg(
    total=('gain', 'count'),
    win_rate=('gain', lambda x: (x > 3).sum() / len(x) * 100)
)
print("\n📅 الأداء الشهري:")
print(monthly_stats)
