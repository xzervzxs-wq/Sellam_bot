import pandas as pd
import numpy as np
import os
from scipy import stats

DATA_FILE = 'reference_candles_15days_20251225.csv'
PATTERNS_FILE = 'successful_candles.csv'

print('=' * 90)
print('🕵️‍♂️  تحليل جينات النجاح: ماذا يميز الصفقات الرابحة (+3%)؟')
print('=' * 90)

# 1. تحميل الأنماط
def load_patterns():
    if not os.path.exists(PATTERNS_FILE): return {}, {}
    df = pd.read_csv(PATTERNS_FILE)
    df.columns = df.columns.str.strip().str.lower()
    df = df[~df['symbol'].str.upper().isin(['NBY', 'SIDU'])]
    patterns, metrics = {}, {}
    for sym, grp in df.groupby('symbol'):
        grp = grp.sort_values('time')
        if len(grp) >= 6:
            candles = grp.iloc[:6][['open', 'high', 'low', 'close']].values
            details = []
            for c in candles:
                o, h, l, cl = c
                details.append({'direction': 1 if cl >= o else -1, 'body_size': abs((cl-o)/o*100)})
            patterns[sym] = candles
            metrics[sym] = {'candle_details': details}
    return patterns, metrics

# 2. دالة المطابقة (نفس المستخدمة)
def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    current_details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in current_candles]
    
    # شرط الاتجاه العام
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

# 3. استخراج الميزات (Features)
def extract_features(candles, volume):
    # candles: np array [[o,h,l,c], ...], volume: np array [v, v, ...]
    
    opens = candles[:, 0]
    highs = candles[:, 1]
    lows = candles[:, 2]
    closes = candles[:, 3]
    
    # 1. نسبة الشموع الخضراء
    green_candles = sum(1 for i in range(len(closes)) if closes[i] >= opens[i])
    green_ratio = green_candles / len(closes) * 100
    
    # 2. سلوك الفوليوم (آخر 3 شموع vs أول 3 شموع)
    if len(volume) >= 6:
        vol_first_3 = np.mean(volume[:3])
        vol_last_3 = np.mean(volume[-3:])
        vol_growth = (vol_last_3 / vol_first_3) if vol_first_3 > 0 else 1.0
        
        # فوليوم آخر شمعة مقارنة بالمتوسط
        last_vol_ratio = volume[-1] / np.mean(volume[:-1]) if np.mean(volume[:-1]) > 0 else 1.0
    else:
        vol_growth = 1.0
        last_vol_ratio = 1.0
        
    # 3. الذيول
    upper_wicks = [(h - max(o, c)) / o * 100 for o, h, c in zip(opens, highs, closes)]
    lower_wicks = [(min(o, c) - l) / o * 100 for o, l, c in zip(opens, lows, closes)]
    avg_upper_wick = np.mean(upper_wicks)
    avg_lower_wick = np.mean(lower_wicks)
    
    # 4. قوة الإغلاق (هل تغلق الشموع قريبة من الهاي؟)
    # Close Location Value (CLV) = ((C - L) - (H - C)) / (H - L)
    # range -1 to 1. 1 means close at high.
    clvs = []
    for i in range(len(closes)):
        rng = highs[i] - lows[i]
        if rng == 0: clvs.append(0)
        else: clvs.append(((closes[i] - lows[i]) - (highs[i] - closes[i])) / rng)
    avg_clv = np.mean(clvs)

    return {
        'green_ratio': green_ratio,
        'vol_growth': vol_growth,
        'last_vol_ratio': last_vol_ratio,
        'avg_upper_wick': avg_upper_wick,
        'avg_lower_wick': avg_lower_wick,
        'avg_clv': avg_clv
    }

# 4. التحليل الرئيسي
patterns, pattern_metrics = load_patterns()
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'])

# تحويل التوقيت
try:
    if df_all['date'].dt.tz is None:
        df_all['date'] = df_all['date'].dt.tz_localize('UTC')
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except: pass

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all['time_str'] = df_all['date'].dt.strftime('%H:%M')

grouped = df_all.groupby(['symbol', 'day_str'])

analysis_data = []

print("⏳ جاري تحليل البيانات...")

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_values('date')
    
    morning_mask = day_data['time_str'].isin(['09:30', '09:35', '09:40', '09:45', '09:50', '09:55'])
    morning_candles = day_data[morning_mask]
    
    # تنظيف
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    valid_indices = [i for i, c in enumerate(candles_vals) if c[0] > 0 and c[3] > 0]
    if len(valid_indices) < 4: continue
    
    candles_vals = candles_vals[valid_indices]
    volume_vals = morning_candles['volume'].values[valid_indices]
    
    # فلتر الزحف
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: continue
    
    # النمط
    score, name = calculate_similarity(candles_vals, patterns, pattern_metrics)
    if score < 70: continue
    
    # النتيجة
    entry_price = candles_vals[-1][3]
    entry_time = morning_candles.iloc[valid_indices[-1]]['date']
    rest_of_day = day_data[day_data['date'] > entry_time]
    
    if len(rest_of_day) == 0: continue
    
    max_gain = (rest_of_day['high'].max() - entry_price) / entry_price * 100
    
    # استخراج الميزات
    feats = extract_features(candles_vals, volume_vals)
    
    row = {
        'symbol': symbol,
        'pattern': name,
        'max_gain': max_gain,
        'avg_body': avg_body,
        **feats
    }
    analysis_data.append(row)

df_res = pd.DataFrame(analysis_data)

if len(df_res) == 0:
    print("❌ لا توجد بيانات كافية للتحليل")
    exit()

# تقسيم البيانات
winners = df_res[df_res['max_gain'] >= 3]
losers = df_res[df_res['max_gain'] < 1] # نعتبر أقل من 1% فشل أو تعادل

print(f"\n📊 تم تحليل {len(df_res)} صفقة (Patterns + Crawl Filter)")
print(f"✅ الناجحة (>=3%): {len(winners)}")
print(f"❌ الفاشلة/الضعيفة (<1%): {len(losers)}")

print('\n' + '='*60)
print('🧬 مقارنة الخصائص (المتوسطات)')
print('='*60)
print(f"{'الخاصية':<25} | {'الناجحة (Winners)':<15} | {'الفاشلة (Losers)':<15} | {'الفرق'}")
print("-" * 70)

features_to_compare = [
    ('avg_body', 'حجم الجسم (%)'),
    ('green_ratio', 'نسبة الشموع الخضراء (%)'),
    ('vol_growth', 'نمو الفوليوم (آخر 3/أول 3)'),
    ('last_vol_ratio', 'اندفاع فوليوم آخر شمعة'),
    ('avg_upper_wick', 'متوسط الذيل العلوي (%)'),
    ('avg_clv', 'قوة الإغلاق (-1 إلى 1)')
]

for col, label in features_to_compare:
    w_mean = winners[col].mean()
    l_mean = losers[col].mean()
    diff = w_mean - l_mean
    print(f"{label:<25} | {w_mean:>15.2f} | {l_mean:>15.2f} | {diff:>+5.2f}")

print('\n' + '='*60)
print('🏆 أفضل الأنماط أداءً (Win Rate)')
print('='*60)
pattern_stats = df_res.groupby('pattern').agg(
    count=('max_gain', 'count'),
    wins=('max_gain', lambda x: (x>=3).sum()),
    avg_gain=('max_gain', 'mean')
)
pattern_stats['win_rate'] = pattern_stats['wins'] / pattern_stats['count'] * 100
pattern_stats = pattern_stats[pattern_stats['count'] >= 3].sort_values('win_rate', ascending=False)

print(f"{'النمط':<15} | {'العدد':<5} | {'نسبة النجاح':<10} | {'متوسط الربح'}")
print("-" * 55)
for pat, row in pattern_stats.head(10).iterrows():
    print(f"{pat:<15} | {row['count']:<5} | {row['win_rate']:>9.1f}% | {row['avg_gain']:>+8.1f}%")

print('\n💡 الاستنتاجات المقترحة للأوسمة:')
if winners['vol_growth'].mean() > losers['vol_growth'].mean():
    print("- 🔊 الفوليوم المتصاعد: الصفقات الناجحة تميل لزيادة الفوليوم في آخر الشموع.")
if winners['green_ratio'].mean() > losers['green_ratio'].mean():
    print("- 🟢 السيطرة الخضراء: كثرة الشموع الخضراء تزيد احتمالية النجاح.")
if winners['avg_clv'].mean() > losers['avg_clv'].mean():
    print("- 🔨 الإغلاق القوي: الإغلاق قرب الهاي (بدون ذيل علوي طويل) مؤشر قوة.")
