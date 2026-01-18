import pandas as pd
import numpy as np
import os

DATA_FILE = 'extended_candles_60days.csv'
PATTERNS_FILE = 'successful_candles.csv'
BAD_PATTERNS = ['GNL', 'EFA', 'MVIS', 'KODK']

def load_patterns():
    if not os.path.exists(PATTERNS_FILE): return {}, {}
    df = pd.read_csv(PATTERNS_FILE)
    df.columns = df.columns.str.strip().str.lower()
    patterns, metrics = {}, {}
    for sym, grp in df.groupby('symbol'):
        grp = grp.sort_values('time')
        if len(grp) >= 6:
            candles = grp.iloc[:6][['open', 'high', 'low', 'close']].values
            details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in candles]
            patterns[sym] = candles
            metrics[sym] = {'candle_details': details}
    return patterns, metrics

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

patterns, pattern_metrics = load_patterns()
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])

try:
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except Exception as e:
    print(f"⚠️ Timezone conversion warning: {e}")

# Fix December timestamps
dec_mask = df_all['date'].dt.month == 12
if dec_mask.any():
    dec_times = df_all.loc[dec_mask, 'date'].dt.time
    if (dec_times == pd.Timestamp('14:30:00').time()).any():
        df_all.loc[dec_mask, 'date'] = df_all.loc[dec_mask, 'date'] - pd.Timedelta(hours=5)

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all = df_all.set_index('date')
df_all = df_all.sort_index()

# Filter for December only
dec_df = df_all[df_all.index.month == 12]
grouped = dec_df.groupby(['symbol', 'day_str'])

results = []

for (symbol, day), day_data in grouped:
    morning_candles = day_data.between_time('09:30', '09:55')
    if len(morning_candles) < 6: continue
    morning_candles = morning_candles.iloc[:6]
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    
    # Filters
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: continue
    
    score, name = calculate_similarity(candles_vals, patterns, pattern_metrics)
    if score < 70: continue
    
    entry_price = candles_vals[-1][3]
    entry_time = morning_candles.index[-1]
    rest_of_day = day_data[day_data.index > entry_time]
    if len(rest_of_day) == 0: continue
    
    max_gain = (rest_of_day['high'].max() - entry_price) / entry_price * 100
    max_loss = (rest_of_day['low'].min() - entry_price) / entry_price * 100
    
    outcome = 'loss'
    if max_gain >= 3.0: outcome = 'win'
    elif max_loss <= -3.0: outcome = 'loss'
    else: outcome = 'neutral' # Treated as loss in strict analysis usually
    
    results.append({
        'pattern': name,
        'outcome': outcome,
        'pl': 3.0 if outcome == 'win' else -3.0
    })

if not results:
    print("No trades found in December.")
    exit()

results_df = pd.DataFrame(results)

print(f"\n📊 تحليل الأنماط السيئة لشهر ديسمبر ({', '.join(BAD_PATTERNS)}):")
print("-" * 60)
print(f"{'Pattern':<10} | {'Signals':<8} | {'Wins':<6} | {'Losses':<6} | {'Net PL':<8} | {'Win Rate':<8}")
print("-" * 60)

total_bad_signals = 0
total_bad_pl = 0

for pat in BAD_PATTERNS:
    pat_data = results_df[results_df['pattern'] == pat]
    count = len(pat_data)
    wins = len(pat_data[pat_data['outcome'] == 'win'])
    losses = len(pat_data[pat_data['outcome'] == 'loss']) # Including neutral as loss for safety? Or just strict loss
    # Let's stick to the PL column
    net_pl = pat_data['pl'].sum()
    win_rate = (wins / count * 100) if count > 0 else 0
    
    print(f"{pat:<10} | {count:<8} | {wins:<6} | {losses:<6} | {net_pl:<8.1f} | {win_rate:<7.1f}%")
    
    total_bad_signals += count
    total_bad_pl += net_pl

print("-" * 60)
print(f"{'TOTAL':<10} | {total_bad_signals:<8} | {'-':<6} | {'-':<6} | {total_bad_pl:<8.1f} | -")
