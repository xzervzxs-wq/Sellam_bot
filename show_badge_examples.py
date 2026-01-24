import pandas as pd
import numpy as np
import os

DATA_FILE = 'reference_candles_15days_20251225.csv'
PATTERNS_FILE = 'successful_candles.csv'
TOP_PATTERNS = ['VIVK', 'METC', 'GNL', 'EFA', 'GOGO']

def get_badge(pattern_name, candles, volume):
    if len(volume) >= 6:
        vol_growth = np.mean(volume[-3:]) / np.mean(volume[:3]) if np.mean(volume[:3]) > 0 else 1.0
    else:
        vol_growth = 1.0
    is_silent = vol_growth < 1.0
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles])
    is_perfect_body = 0.4 <= avg_body <= 0.8
    is_top_pattern = pattern_name in TOP_PATTERNS
    
    if is_top_pattern and is_silent: return "👑 Elite"
    if is_top_pattern or (is_silent and is_perfect_body): return "🥇 Gold"
    return "🥈 Silver"

# Load Patterns
df = pd.read_csv(PATTERNS_FILE)
df.columns = df.columns.str.strip().str.lower()
df = df[~df['symbol'].str.upper().isin(['NBY', 'SIDU'])]
patterns, metrics = {}, {}
for sym, grp in df.groupby('symbol'):
    grp = grp.sort_values('time')
    if len(grp) >= 6:
        candles = grp.iloc[:6][['open', 'high', 'low', 'close']].values
        details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in candles]
        patterns[sym] = candles
        metrics[sym] = {'candle_details': details}

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    current_details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in current_candles]
    if (current_candles[-1][3] - current_candles[0][0]) <= 0: return 0, "None"
    best_score, best_name = 0, "None"
    for name, ref_candles in reference_patterns.items():
        if name not in pattern_metrics: continue
        ref_details = pattern_metrics[name]['candle_details']
        clen = min(len(current_details), len(ref_details))
        if clen < 3: continue
        dir_match = sum(1 for i in range(clen) if current_details[i]['direction'] == ref_details[i]['direction'])
        if dir_match/clen < 0.67: continue
        size_penalties = 0
        for i in range(clen):
            diff = abs(current_details[i]['body_size'] - ref_details[i]['body_size'])
            if diff > 1.0: size_penalties += min(diff - 1.0, 1.0) * 20
        score = (dir_match/clen * 100 * 0.6) + (max(0, 100 - size_penalties) * 0.4)
        if score > best_score: best_score, best_name = score, name
    return best_score, best_name

# Load Data
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'])
try:
    if df_all['date'].dt.tz is None: df_all['date'] = df_all['date'].dt.tz_localize('UTC')
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except: pass
df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all['time_str'] = df_all['date'].dt.strftime('%H:%M')

results = []
grouped = df_all.groupby(['symbol', 'day_str'])

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_values('date')
    morning_mask = day_data['time_str'].isin(['09:30', '09:35', '09:40', '09:45', '09:50', '09:55'])
    morning_candles = day_data[morning_mask]
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    valid_indices = [i for i, c in enumerate(candles_vals) if c[0] > 0 and c[3] > 0]
    if len(valid_indices) < 4: continue
    
    candles_vals = candles_vals[valid_indices]
    volume_vals = morning_candles['volume'].values[valid_indices]
    
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: continue
    
    score, name = calculate_similarity(candles_vals, patterns, metrics)
    if score < 70: continue
    
    entry_price = candles_vals[-1][3]
    entry_time = morning_candles.iloc[valid_indices[-1]]['date']
    rest_of_day = day_data[day_data['date'] > entry_time]
    if len(rest_of_day) == 0: continue
    max_gain = (rest_of_day['high'].max() - entry_price) / entry_price * 100
    
    badge = get_badge(name, candles_vals, volume_vals)
    results.append({'symbol': symbol, 'date': day, 'badge': badge, 'gain': max_gain, 'pattern': name})

print("="*80)
print("أمثلة حقيقية من اختبار الـ 15 يوم:")
print("="*80)

for b in ['👑 Elite', '🥇 Gold', '🥈 Silver']:
    print(f"\n{b}:")
    subset = [r for r in results if r['badge'] == b]
    # Show top 3 winners and 1 loser
    winners = sorted([r for r in subset if r['gain'] > 0], key=lambda x: x['gain'], reverse=True)[:3]
    losers = sorted([r for r in subset if r['gain'] <= 0], key=lambda x: x['gain'])[:1]
    
    for r in winners + losers:
        print(f"   - {r['date']} {r['symbol']:<5} ({r['pattern']}): {r['gain']:+.1f}%")
