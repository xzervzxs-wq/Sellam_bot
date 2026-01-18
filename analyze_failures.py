import pandas as pd
import numpy as np
import os

DATA_FILE = 'extended_candles_60days.csv'
PATTERNS_FILE = 'successful_candles.csv'
TOP_PATTERNS = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']
BLACKLIST_PATTERNS = ['CCL', 'SLV', 'PM', 'NBIS', 'TRP', 'GNL', 'EFA', 'MVIS', 'KODK']

print('=' * 90)
print('🕵️‍♂️ تحليل شامل (60 يوم): اختبار المتانة والاستقرار')
print('=' * 90)

def get_badge(pattern_name, candles, volume):
    if pattern_name in BLACKLIST_PATTERNS:
        return "⛔ Blacklisted"

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
    df = df[~df['symbol'].str.upper().isin(['NBY', 'SIDU'])]
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

# Load Data
if not os.path.exists(DATA_FILE):
    print(f"❌ ملف البيانات {DATA_FILE} غير موجود")
    exit()

patterns, pattern_metrics = load_patterns()
df_all = pd.read_csv(DATA_FILE)
# Force UTC and handle errors
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])

try:
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except Exception as e:
    print(f"⚠️ Timezone conversion warning: {e}")

# 🛠️ FIX: Detect and correct shifted timestamps for December
# Problem: December data appears as 14:30 EST instead of 09:30 EST
# This likely happened because UTC time (14:30) was stamped as EST without conversion
dec_mask = df_all['date'].dt.month == 12
if dec_mask.any():
    # Check if the earliest time in December is 14:30
    dec_times = df_all.loc[dec_mask, 'date'].dt.time
    if (dec_times == pd.Timestamp('14:30:00').time()).any():
        print("⚠️ Detected shifted timestamps in December data (Starts at 14:30). Fixing...")
        df_all.loc[dec_mask, 'date'] = df_all.loc[dec_mask, 'date'] - pd.Timedelta(hours=5)
        print("✅ Timestamps corrected. New start time:", df_all.loc[dec_mask, 'date'].dt.time.min())

# 🎯 FILTER SPECIFIC DAYS (User Request)
target_days = [
    '2025-12-11', '2025-12-12', '2025-12-15', '2025-12-16', 
    '2025-12-17', '2025-12-18', '2025-12-19', '2025-12-22', '2025-12-23'
]
print(f"⚠️ Filtering for specific days: {target_days}")
df_all['day_str_temp'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all = df_all[df_all['day_str_temp'].isin(target_days)]

# Debug: Print date range
print(f"📅 Data Range: {df_all['date'].min()} to {df_all['date'].max()}")

# Ensure we have December data in df_all before grouping
dec_data = df_all[df_all['date'].dt.strftime('%Y-%m').str.startswith('2025-12')]
print(f"🔍 Found {len(dec_data)} rows for December.")

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')
df_all['time_str'] = df_all['date'].dt.strftime('%H:%M')

# Debug: Check unique days in December
dec_days = df_all[df_all['day_str'].str.startswith('2025-12')]['day_str'].unique()
print(f"📅 December Days: {dec_days}")

results = []
df_all = df_all.set_index('date')
grouped = df_all.groupby(['symbol', 'day_str'])

print("⏳ جاري تحليل الخسائر...")

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_index()
    # Strict 6 candles check (09:30 to 10:00)
    # Note: EODHD timestamps might be slightly off or different timezone handling
    # Let's be more flexible with time matching
    morning_candles = day_data.between_time('09:30', '09:55')
    
    # Must have exactly 6 candles
    if len(morning_candles) < 6: 
        # Debug for December
        if day.startswith('2025-12'):
             # print(f"Skipping {symbol} on {day}: Found {len(morning_candles)} candles")
             pass
        continue
    
    # Take first 6 if more than 6 (e.g. duplicates or extra data points)
    morning_candles = morning_candles.iloc[:6]
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    volume_vals = morning_candles['volume'].values
    
    # Crawl Filter (< 1.0%)
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: 
        continue
    
    score, name = calculate_similarity(candles_vals, patterns, pattern_metrics)
    if score < 70: 
        continue
    
    # Entry is at the CLOSE of the 6th candle (10:00 AM)
    entry_price = candles_vals[-1][3]
    entry_time = morning_candles.index[-1] # Use index since we set_index('date')
    
    # Look for results AFTER the 6th candle
    rest_of_day = day_data[day_data.index > entry_time]
    if len(rest_of_day) == 0: 
        # Debug why no rest of day
        if day.startswith('2025-12'):
             # print(f"Dec Skip: No rest of day data for {symbol} on {day}. Entry: {entry_time}. Last data: {day_data.index[-1]}")
             pass
        continue
    
    # Debug: Print one success for December
    if day.startswith('2025-12'): 
        # print(f"Dec Success: {symbol} on {day}")
        pass
    
    max_gain = (rest_of_day['high'].max() - entry_price) / entry_price * 100
    max_loss = (rest_of_day['low'].min() - entry_price) / entry_price * 100
    
    # Features for analysis
    vol_growth = np.mean(volume_vals[-3:]) / np.mean(volume_vals[:3]) if np.mean(volume_vals[:3]) > 0 else 1.0
    
    # Gap check (Open of first candle vs Close of previous day - hard to get here, so we use Open of first candle vs Close of first candle as proxy for volatility)
    first_candle_body = abs(candles_vals[0][3] - candles_vals[0][0]) / candles_vals[0][0] * 100
    
    # Wick analysis
    upper_wicks = [(c[1] - max(c[0], c[3])) / c[0] * 100 for c in candles_vals]
    avg_upper_wick = np.mean(upper_wicks)
    
    badge = get_badge(name, candles_vals, volume_vals)
    
    # Gap check
    prev_close = candles_vals[0][0] # Approximation if we don't have prev day
    # Actually, we can't calculate true gap without prev day close.
    # But we can check "Open of first candle" vs "Close of first candle" -> Body.
    # Let's check Time of Day.
    entry_hour = entry_time.hour
    entry_minute = entry_time.minute
    time_bucket = f"{entry_hour}:{entry_minute:02d}"

    # Recalculate technical flags locally
    is_silent = vol_growth < 1.0
    is_perfect_body = 0.4 <= avg_body <= 0.8

    # Pure Technical Badge (No Pattern Name)
    if is_silent and is_perfect_body:
        tech_badge = "💎 Silent+Perfect"
    elif is_silent:
        tech_badge = "🤫 Silent Only"
    elif is_perfect_body:
        tech_badge = "📏 Body Only"
    else:
        tech_badge = "💩 Garbage"

    results.append({
        'symbol': symbol,
        'badge': badge,
        'tech_badge': tech_badge, # New field
        'gain': max_gain,
        'loss': max_loss,
        'avg_body': avg_body,
        'vol_growth': vol_growth,
        'avg_upper_wick': avg_upper_wick,
        'pattern': name,
        'day_str': day,
        'time': time_bucket
    })

df = pd.DataFrame(results)
# ⛔ استبعاد الأنماط المحظورة من التحليل
df = df[df['badge'] != "⛔ Blacklisted"]

# Filter for December
df_dec = df[df['day_str'].str.startswith('2025-12')]
print(f"\n📅 نتائج شهر ديسمبر فقط:")
print(f"عدد الصفقات: {len(df_dec)}")

if len(df_dec) > 0:
    badge_stats_dec = df_dec.groupby('badge').agg(
        total=('gain', 'count'),
        wins=('gain', lambda x: (x > 3).sum()),
        losses=('loss', lambda x: (x < -3).sum()),
        avg_gain=('gain', 'mean'),
        avg_loss=('loss', 'mean')
    )
    badge_stats_dec['win_rate'] = badge_stats_dec['wins'] / badge_stats_dec['total'] * 100
    badge_stats_dec['net_pl'] = (badge_stats_dec['wins'] * 3) - (badge_stats_dec['losses'] * 3)
    print(badge_stats_dec)
else:
    print("⚠️ لا توجد بيانات لشهر ديسمبر في الملف الحالي.")

# Define Losers (Loss < -3%) vs Winners (Gain > 3%)
losers = df[df['loss'] < -3]
winners = df[df['gain'] > 3]

print('\n🧪 الأداء الفني البحت (بدون أسماء أنماط):')
tech_stats = df.groupby('tech_badge').agg(
    total=('gain', 'count'),
    win_rate=('gain', lambda x: (x > 3).sum() / len(x) * 100)
)
print(tech_stats)


print('\n⏰ الأداء حسب وقت الدخول:')
time_stats = df.groupby('time').agg(
    total=('gain', 'count'),
    win_rate=('gain', lambda x: (x > 3).sum() / len(x) * 100)
)
print(time_stats)


print(f"\n📊 إجمالي الصفقات: {len(df)}")
print(f"✅ الرابحة (>3%): {len(winners)}")
print(f"❌ الخاسرة (<-3%): {len(losers)}")

print('\n' + '='*60)
print('🕵️‍♂️ مقارنة الخصائص: الرابحون vs الخاسرون')
print('='*60)
print(f"{'الخاصية':<25} | {'الرابحون':<10} | {'الخاسرون':<10} | {'الفرق'}")
print("-" * 65)

metrics = [
    ('avg_body', 'متوسط جسم الشمعة (%)'),
    ('vol_growth', 'نمو الفوليوم (آخر/أول)'),
    ('avg_upper_wick', 'متوسط الذيل العلوي (%)')
]

for col, label in metrics:
    w_val = winners[col].mean()
    l_val = losers[col].mean()
    diff = w_val - l_val
    print(f"{label:<25} | {w_val:>10.2f} | {l_val:>10.2f} | {diff:>+5.2f}")

print('\n⚠️ الأنماط الأكثر فشلاً (نسبة الخسارة العالية):')
fail_stats = df.groupby('pattern').agg(
    total=('loss', 'count'),
    failures=('loss', lambda x: (x < -3).sum())
)
fail_stats['fail_rate'] = fail_stats['failures'] / fail_stats['total'] * 100
fail_stats = fail_stats[fail_stats['total'] >= 5].sort_values('fail_rate', ascending=False)

for pat, row in fail_stats.head(5).iterrows():
    print(f"   - {pat:<10}: نسبة فشل {row['fail_rate']:.1f}% ({row['failures']}/{row['total']})")

print('\n💡 تحليل الفخاخ المحتملة:')
if losers['vol_growth'].mean() > winners['vol_growth'].mean():
    print("🚨 فخ الفوليوم: الخاسرون لديهم فوليوم متزايد في النهاية (تصريف)!")
if losers['avg_upper_wick'].mean() > winners['avg_upper_wick'].mean():
    print("🚨 فخ الذيول: الخاسرون لديهم ذيول علوية أطول (ضغط بيعي)!")
if losers['avg_body'].mean() < winners['avg_body'].mean():
    print("🚨 فخ الموت: الخاسرون لديهم شموع صغيرة جداً (ضعف السيولة)!")

print('\n🏅 الأداء حسب الوسام (النتيجة النهائية):')
badge_stats = df.groupby('badge').agg(
    total=('gain', 'count'),
    wins=('gain', lambda x: (x > 3).sum()),
    losses=('loss', lambda x: (x < -3).sum()),
    avg_gain=('gain', 'mean'),
    avg_loss=('loss', 'mean')
)
badge_stats['win_rate'] = badge_stats['wins'] / badge_stats['total'] * 100
badge_stats['net_pl'] = (badge_stats['wins'] * 3) - (badge_stats['losses'] * 3) # Simple P/L simulation
print(badge_stats)

print('\n📅 الأداء الشهري (للتأكد من الاستقرار):')
df['month'] = pd.to_datetime(df['day_str']).dt.strftime('%Y-%m')
monthly_stats = df.groupby('month').agg(
    total=('gain', 'count'),
    win_rate=('gain', lambda x: (x > 3).sum() / len(x) * 100)
)
print(monthly_stats)


print('\n🏅 الأداء حسب الوسام:')
badge_stats = df.groupby('badge').agg(
    total=('gain', 'count'),
    wins=('gain', lambda x: (x > 3).sum()),
    losses=('loss', lambda x: (x < -3).sum())
)
badge_stats['win_rate'] = badge_stats['wins'] / badge_stats['total'] * 100
print(badge_stats)
