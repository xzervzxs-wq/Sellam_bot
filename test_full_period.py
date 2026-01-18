import pandas as pd
import numpy as np
import os
import itertools

DATA_FILE = 'extended_candles_60days.csv'
PATTERNS_FILE = 'successful_candles.csv'
BLACKLIST_PATTERNS = ['CCL', 'SLV', 'PM', 'NBIS', 'TRP', 'GNL', 'EFA', 'MVIS', 'KODK']

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

# Fix December timestamps
dec_mask = df_all['date'].dt.month == 12
if dec_mask.any():
    dec_times = df_all.loc[dec_mask, 'date'].dt.time
    if (dec_times == pd.Timestamp('14:30:00').time()).any():
        df_all.loc[dec_mask, 'date'] = df_all.loc[dec_mask, 'date'] - pd.Timedelta(hours=5)

# استبعاد نوفمبر فقط (الشهر السيء)
df_all = df_all[df_all['date'].dt.month != 11]

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all['month'] = df_all['date'].dt.strftime('%Y-%m')
df_all = df_all.set_index('date')
df_all = df_all.sort_index()

# عدد الأيام الفعلية
unique_days = df_all['day_str'].unique()
print(f"📅 عدد الأيام في الاختبار: {len(unique_days)} يوم")
print(f"   من {unique_days[0]} إلى {unique_days[-1]}")

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
    
    vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0
    if vol_growth >= 1.0: continue  # Must be silent
    
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
    
    month = day[:7]
    
    results.append({
        'symbol': symbol,
        'day': day,
        'month': month,
        'pattern': name,
        'outcome': outcome,
        'score': score,
        'avg_body': avg_body,
        'vol_growth': vol_growth,
        'max_gain': max_gain
    })

df = pd.DataFrame(results)

print(f"\n📊 إجمالي الصفقات (بعد فلتر الفوليوم الصامت): {len(df)}")

print("\n" + "=" * 100)
print("🔬 اختبار الإعدادات المقترحة على كل البيانات (أكتوبر + ديسمبر)")
print("=" * 100)

# الإعداد 1: VIVK + GOGO + INTR + body < 0.7
print("\n📌 الإعداد 1: VIVK + GOGO + INTR + جسم < 0.7%")
combo1 = ['VIVK', 'GOGO', 'INTR']
filtered1 = df[(df['pattern'].isin(combo1)) & (df['avg_body'] < 0.7)]
wins1 = len(filtered1[filtered1['outcome'] == 'win'])
total1 = len(filtered1)
rate1 = (wins1/total1*100) if total1 > 0 else 0
net1 = (wins1 * 3) - ((total1 - wins1) * 3)
print(f"   الصفقات: {total1} | الربح: {wins1} | الخسارة: {total1-wins1} | النسبة: {rate1:.1f}% | صافي: {net1:+.1f}")

# تفصيل شهري
print("   تفصيل شهري:")
for month in filtered1['month'].unique():
    m_data = filtered1[filtered1['month'] == month]
    m_wins = len(m_data[m_data['outcome'] == 'win'])
    m_total = len(m_data)
    m_rate = (m_wins/m_total*100) if m_total > 0 else 0
    print(f"      {month}: {m_total} صفقات, {m_wins} ربح, {m_rate:.1f}%")

# الإعداد 2: VIVK + GOGO + INTR + body < 0.6
print("\n📌 الإعداد 2: VIVK + GOGO + INTR + جسم < 0.6%")
filtered2 = df[(df['pattern'].isin(combo1)) & (df['avg_body'] < 0.6)]
wins2 = len(filtered2[filtered2['outcome'] == 'win'])
total2 = len(filtered2)
rate2 = (wins2/total2*100) if total2 > 0 else 0
net2 = (wins2 * 3) - ((total2 - wins2) * 3)
print(f"   الصفقات: {total2} | الربح: {wins2} | الخسارة: {total2-wins2} | النسبة: {rate2:.1f}% | صافي: {net2:+.1f}")

# تفصيل شهري
print("   تفصيل شهري:")
for month in filtered2['month'].unique():
    m_data = filtered2[filtered2['month'] == month]
    m_wins = len(m_data[m_data['outcome'] == 'win'])
    m_total = len(m_data)
    m_rate = (m_wins/m_total*100) if m_total > 0 else 0
    print(f"      {month}: {m_total} صفقات, {m_wins} ربح, {m_rate:.1f}%")

# الإعداد 3: كل الأنماط القوية الـ 6 + body < 0.9 (الإعداد السابق)
print("\n📌 الإعداد 3 (السابق): كل الأنماط الـ 6 + جسم < 0.9%")
all_top = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']
filtered3 = df[(df['pattern'].isin(all_top)) & (df['avg_body'] < 0.9)]
wins3 = len(filtered3[filtered3['outcome'] == 'win'])
total3 = len(filtered3)
rate3 = (wins3/total3*100) if total3 > 0 else 0
net3 = (wins3 * 3) - ((total3 - wins3) * 3)
print(f"   الصفقات: {total3} | الربح: {wins3} | الخسارة: {total3-wins3} | النسبة: {rate3:.1f}% | صافي: {net3:+.1f}")

# تفصيل شهري
print("   تفصيل شهري:")
for month in filtered3['month'].unique():
    m_data = filtered3[filtered3['month'] == month]
    m_wins = len(m_data[m_data['outcome'] == 'win'])
    m_total = len(m_data)
    m_rate = (m_wins/m_total*100) if m_total > 0 else 0
    print(f"      {month}: {m_total} صفقات, {m_wins} ربح, {m_rate:.1f}%")

# الإعداد 4: INTR فقط + body < 0.6 (أفضل نسبة)
print("\n📌 الإعداد 4: INTR فقط + جسم < 0.6%")
filtered4 = df[(df['pattern'] == 'INTR') & (df['avg_body'] < 0.6)]
wins4 = len(filtered4[filtered4['outcome'] == 'win'])
total4 = len(filtered4)
rate4 = (wins4/total4*100) if total4 > 0 else 0
net4 = (wins4 * 3) - ((total4 - wins4) * 3)
print(f"   الصفقات: {total4} | الربح: {wins4} | الخسارة: {total4-wins4} | النسبة: {rate4:.1f}% | صافي: {net4:+.1f}")

print("\n" + "=" * 100)
print("🎯 الخلاصة:")
print("=" * 100)
