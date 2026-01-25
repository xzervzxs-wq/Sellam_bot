import pandas as pd
import numpy as np
import os
import itertools

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
    if name in BLACKLIST_PATTERNS: continue
    if name not in TOP_PATTERNS: continue
    
    vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0
    if vol_growth >= 1.0: continue
    if avg_body >= 0.9: continue
    
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
    
    # تحليل عميق للشمعات
    directions = [1 if c[3]>=c[0] else -1 for c in candles_vals]
    dir_pattern = ''.join(['↑' if d == 1 else '↓' for d in directions])
    up_count = sum(1 for d in directions if d == 1)
    
    # الحركة الكلية في أول 6 شموع
    total_move = (candles_vals[-1][3] - candles_vals[0][0]) / candles_vals[0][0] * 100
    
    results.append({
        'symbol': symbol,
        'day': day,
        'pattern': name,
        'outcome': outcome,
        'score': score,
        'avg_body': avg_body,
        'vol_growth': vol_growth,
        'dir_pattern': dir_pattern,
        'up_count': up_count,
        'total_move': total_move,
        'max_gain': max_gain
    })

df = pd.DataFrame(results)

print("=" * 90)
print("🔬 بحث شامل عن أفضل مجموعة أنماط تحقق 70%+ نسبة نجاح")
print("=" * 90)

# اختبار كل مجموعة ممكنة من الأنماط
all_patterns = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']

best_combo = None
best_rate = 0
best_result = None

print(f"\n🧪 اختبار كل مجموعة ممكنة من الأنماط:")
print("-" * 90)

results_list = []

# اختبار كل مجموعة فرعية
for r in range(1, len(all_patterns) + 1):
    for combo in itertools.combinations(all_patterns, r):
        filtered = df[df['pattern'].isin(combo)]
        wins = len(filtered[filtered['outcome'] == 'win'])
        total = len(filtered)
        if total >= 5:
            rate = (wins/total*100)
            net = (wins * 3) - ((total - wins) * 3)
            results_list.append({
                'combo': combo,
                'total': total,
                'wins': wins,
                'rate': rate,
                'net': net
            })

# ترتيب حسب النسبة
results_list = sorted(results_list, key=lambda x: (-x['rate'], -x['total']))

print(f"\n🏆 أفضل 15 مجموعة أنماط:")
print("-" * 90)
for i, r in enumerate(results_list[:15], 1):
    marker = "🔥🔥" if r['rate'] >= 70 else "🔥" if r['rate'] >= 60 else "⭐" if r['rate'] >= 50 else ""
    print(f"{i:>2}. {str(r['combo']):<50} | {r['total']:>2} trades | {r['wins']:>2} wins | {r['rate']:>5.1f}% | Net: {r['net']:>+5.1f} {marker}")

# البحث عن فلتر إضافي مع أفضل مجموعة
print(f"\n🔬 تحليل أفضل مجموعة مع فلاتر إضافية:")
print("-" * 90)

if results_list:
    best = results_list[0]
    best_combo = best['combo']
    print(f"أفضل مجموعة: {best_combo}")
    
    filtered_best = df[df['pattern'].isin(best_combo)]
    
    # اختبار فلاتر على أفضل مجموعة
    extra_tests = [
        ("+ total_move > 1%", filtered_best[filtered_best['total_move'] > 1.0]),
        ("+ total_move > 0.5%", filtered_best[filtered_best['total_move'] > 0.5]),
        ("+ vol_growth < 0.6", filtered_best[filtered_best['vol_growth'] < 0.6]),
        ("+ avg_body < 0.6", filtered_best[filtered_best['avg_body'] < 0.6]),
    ]
    
    for name, filtered in extra_tests:
        wins = len(filtered[filtered['outcome'] == 'win'])
        total = len(filtered)
        if total >= 3:
            rate = (wins/total*100)
            net = (wins * 3) - ((total - wins) * 3)
            marker = "🔥🔥" if rate >= 70 else "🔥" if rate >= 60 else ""
            print(f"   {name:<30} | {total:>2} trades | {wins:>2} wins | {rate:>5.1f}% | Net: {net:>+5.1f} {marker}")
