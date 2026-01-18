import pandas as pd
import numpy as np
import os

DATA_FILE = 'extended_candles_60days.csv'
PATTERNS_FILE = 'successful_candles.csv'
TOP_PATTERNS = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']
BLACKLIST_PATTERNS = ['CCL', 'SLV', 'PM', 'NBIS', 'TRP', 'GNL', 'EFA', 'MVIS', 'KODK']
TARGET_DAYS = ['2025-12-11', '2025-12-12', '2025-12-15', '2025-12-16', '2025-12-17', '2025-12-18', '2025-12-19', '2025-12-22', '2025-12-23']

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
except: pass

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
all_trades = []

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
    if name in BLACKLIST_PATTERNS: continue
    
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
    
    vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0
    is_top = name in TOP_PATTERNS
    is_perfect_body = 0.4 <= avg_body <= 0.8
    
    all_trades.append({
        'outcome': outcome,
        'pattern': name,
        'vol_growth': vol_growth,
        'avg_body': avg_body,
        'is_top': is_top,
        'is_perfect_body': is_perfect_body
    })

df = pd.DataFrame(all_trades)

print("=" * 80)
print("🔬 البحث عن أفضل مزيج من الفلاتر:")
print("=" * 80)

best_rate = 0
best_config = ""
best_total = 0
best_wins = 0

# Test different combinations
vol_thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
body_max = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

results = []

for vol in vol_thresholds:
    for body in body_max:
        # Test with Top Pattern requirement
        filtered = df[(df['is_top'] == True) & (df['vol_growth'] < vol) & (df['avg_body'] < body)]
        wins = len(filtered[filtered['outcome'] == 'win'])
        total = len(filtered)
        if total >= 10:  # Minimum trades threshold
            rate = (wins/total*100)
            results.append({
                'vol': vol,
                'body': body,
                'total': total,
                'wins': wins,
                'rate': rate,
                'net_pl': (wins * 3) - ((total - wins) * 3)
            })
            if rate > best_rate:
                best_rate = rate
                best_config = f"Vol < {vol}, Body < {body}"
                best_total = total
                best_wins = wins

# Sort by win rate
results = sorted(results, key=lambda x: -x['rate'])

print(f"\n🏆 أفضل 10 مزيج من الفلاتر (مرتبة بنسبة النجاح):")
print("-" * 80)
print(f"{'Vol <':<8} | {'Body <':<8} | {'Total':<6} | {'Wins':<6} | {'Rate':<8} | {'Net PL':<8}")
print("-" * 80)

for r in results[:10]:
    print(f"{r['vol']:<8} | {r['body']:<8} | {r['total']:<6} | {r['wins']:<6} | {r['rate']:<7.1f}% | {r['net_pl']:<8.1f}")

print("\n" + "=" * 80)
print(f"🎯 أفضل إعدادات: {best_config}")
print(f"   النسبة: {best_rate:.1f}% | الصفقات: {best_total} | الأرباح: {best_wins}")
print("=" * 80)
