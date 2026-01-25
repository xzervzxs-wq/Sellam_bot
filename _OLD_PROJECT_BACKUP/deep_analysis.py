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
    bodies = [abs(c[3]-c[0])/c[0]*100 for c in candles_vals]
    upper_wicks = [(c[1] - max(c[0], c[3])) / c[0] * 100 for c in candles_vals]
    lower_wicks = [(min(c[0], c[3]) - c[2]) / c[0] * 100 for c in candles_vals]
    
    # نمط الاتجاه
    up_count = sum(1 for d in directions if d == 1)
    down_count = sum(1 for d in directions if d == -1)
    
    # هل هناك تسلسل معين؟
    dir_pattern = ''.join(['↑' if d == 1 else '↓' for d in directions])
    
    # الشمعة الأخيرة
    last_dir = directions[-1]
    last_body = bodies[-1]
    
    results.append({
        'symbol': symbol,
        'day': day,
        'pattern': name,
        'outcome': outcome,
        'score': score,
        'avg_body': avg_body,
        'vol_growth': vol_growth,
        'up_count': up_count,
        'down_count': down_count,
        'dir_pattern': dir_pattern,
        'last_dir': last_dir,
        'last_body': last_body,
        'max_gain': max_gain,
        'max_loss': max_loss,
        'avg_upper_wick': np.mean(upper_wicks),
        'avg_lower_wick': np.mean(lower_wicks)
    })

df = pd.DataFrame(results)

print("=" * 90)
print("🔬 تحليل عميق للصفقات الرابحة vs الخاسرة")
print("=" * 90)

winners = df[df['outcome'] == 'win']
losers = df[df['outcome'] != 'win']

print(f"\n📊 العدد: رابحين {len(winners)} | خاسرين {len(losers)}")

print(f"\n🏆 الصفقات الرابحة:")
print("-" * 90)
for _, row in winners.iterrows():
    print(f"   {row['day']} | {row['symbol']:<6} | {row['pattern']:<6} | Score: {row['score']:.1f} | Pattern: {row['dir_pattern']} | Gain: {row['max_gain']:.1f}%")

print(f"\n💀 الصفقات الخاسرة:")
print("-" * 90)
for _, row in losers.iterrows():
    print(f"   {row['day']} | {row['symbol']:<6} | {row['pattern']:<6} | Score: {row['score']:.1f} | Pattern: {row['dir_pattern']} | Loss: {row['max_loss']:.1f}%")

print(f"\n📈 مقارنة الخصائص:")
print("-" * 90)
print(f"{'الخاصية':<25} | {'الرابحين':<15} | {'الخاسرين':<15} | {'الفرق':<10}")
print("-" * 90)

features = ['score', 'avg_body', 'vol_growth', 'up_count', 'last_body', 'avg_upper_wick', 'avg_lower_wick']
for f in features:
    w = winners[f].mean()
    l = losers[f].mean()
    d = w - l
    print(f"{f:<25} | {w:<15.3f} | {l:<15.3f} | {d:<+10.3f}")

print(f"\n🎯 نمط الاتجاه (Direction Pattern):")
print("-" * 90)
print("الرابحين:")
print(winners['dir_pattern'].value_counts())
print("\nالخاسرين:")
print(losers['dir_pattern'].value_counts())

print(f"\n📊 توزيع نسبة المطابقة (Score):")
print("-" * 90)
print(f"الرابحين: Min={winners['score'].min():.1f}, Max={winners['score'].max():.1f}, Avg={winners['score'].mean():.1f}")
print(f"الخاسرين: Min={losers['score'].min():.1f}, Max={losers['score'].max():.1f}, Avg={losers['score'].mean():.1f}")

# اختبار رفع نسبة المطابقة
print(f"\n🧪 اختبار رفع نسبة المطابقة:")
print("-" * 90)
for threshold in [75, 80, 85, 90, 95]:
    filtered = df[df['score'] >= threshold]
    wins = len(filtered[filtered['outcome'] == 'win'])
    total = len(filtered)
    rate = (wins/total*100) if total > 0 else 0
    net = (wins * 3) - ((total - wins) * 3)
    print(f"   Score >= {threshold}: {total} trades, {wins} wins, {rate:.1f}% win rate, Net: {net:+.1f}")
