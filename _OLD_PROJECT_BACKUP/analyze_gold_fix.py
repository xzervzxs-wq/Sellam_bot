import pandas as pd
import numpy as np
import os

DATA_FILE = 'extended_candles_60days.csv'
PATTERNS_FILE = 'successful_candles.csv'
TOP_PATTERNS = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']
BLACKLIST_PATTERNS = ['CCL', 'SLV', 'PM', 'NBIS', 'TRP', 'GNL', 'EFA', 'MVIS', 'KODK']
TARGET_DAYS = ['2025-12-11', '2025-12-12', '2025-12-15', '2025-12-16', '2025-12-17', '2025-12-18', '2025-12-19', '2025-12-22', '2025-12-23']

def get_badge(pattern_name, candles, volume):
    if pattern_name in BLACKLIST_PATTERNS: return "⛔ Blacklisted"
    
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
df_all = df_all[df_all['day_str'].isin(TARGET_DAYS)]
df_all = df_all.set_index('date')
df_all = df_all.sort_index()

grouped = df_all.groupby(['symbol', 'day_str'])
results = []

for (symbol, day), day_data in grouped:
    morning_candles = day_data.between_time('09:30', '09:55')
    if len(morning_candles) < 6: continue
    morning_candles = morning_candles.iloc[:6]
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    volume_vals = morning_candles['volume'].values
    
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
    else: outcome = 'neutral'
    
    badge = get_badge(name, candles_vals, volume_vals)
    
    if badge == '🥇 Gold':
        # Calculate extra features
        upper_wicks = [(c[1] - max(c[0], c[3])) / c[0] * 100 for c in candles_vals]
        avg_upper_wick = np.mean(upper_wicks)
        
        lower_wicks = [(min(c[0], c[3]) - c[2]) / c[0] * 100 for c in candles_vals]
        avg_lower_wick = np.mean(lower_wicks)
        
        vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0

        results.append({
            'outcome': outcome,
            'pattern': name,
            'avg_body': avg_body,
            'avg_upper_wick': avg_upper_wick,
            'avg_lower_wick': avg_lower_wick,
            'vol_growth': vol_growth,
            'score': score
        })

df_gold = pd.DataFrame(results)

if len(df_gold) == 0:
    print("No Gold trades found.")
    exit()

print(f"\n🔍 تحليل عميق لصفقات الذهب ({len(df_gold)} صفقة):")
print("-" * 90)
print(f"{'Feature':<20} | {'Winners Avg':<12} | {'Losers Avg':<12} | {'Diff':<10}")
print("-" * 90)

winners = df_gold[df_gold['outcome'] == 'win']
losers = df_gold[df_gold['outcome'] != 'win']

features = ['avg_body', 'avg_upper_wick', 'avg_lower_wick', 'vol_growth', 'score']

for feat in features:
    w_avg = winners[feat].mean()
    l_avg = losers[feat].mean()
    diff = w_avg - l_avg
    print(f"{feat:<20} | {w_avg:<12.4f} | {l_avg:<12.4f} | {diff:<10.4f}")

print("-" * 90)

print("\n💡 محاولة تحسين الفلتر:")
# Try to find a rule that keeps winners and removes losers
# Example: Body < 0.6?
print("Testing Rule: Avg Body < 0.6")
filtered_gold = df_gold[df_gold['avg_body'] < 0.6]
f_wins = len(filtered_gold[filtered_gold['outcome'] == 'win'])
f_total = len(filtered_gold)
f_rate = (f_wins/f_total*100) if f_total > 0 else 0
print(f"New Win Rate: {f_rate:.1f}% ({f_wins}/{f_total})")

print("\nTesting Rule: Vol Growth < 1.5")
filtered_gold = df_gold[df_gold['vol_growth'] < 1.5]
f_wins = len(filtered_gold[filtered_gold['outcome'] == 'win'])
f_total = len(filtered_gold)
f_rate = (f_wins/f_total*100) if f_total > 0 else 0
print(f"New Win Rate: {f_rate:.1f}% ({f_wins}/{f_total})")

print("\nTesting Rule: Remove METC")
filtered_gold = df_gold[df_gold['pattern'] != 'METC']
f_wins = len(filtered_gold[filtered_gold['outcome'] == 'win'])
f_total = len(filtered_gold)
f_rate = (f_wins/f_total*100) if f_total > 0 else 0
print(f"New Win Rate: {f_rate:.1f}% ({f_wins}/{f_total})")
