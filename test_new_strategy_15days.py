import pandas as pd
import numpy as np
import os
import json

# ==============================================================================
# 1. إعدادات الاختبار
# ==============================================================================
DATA_FILE = 'reference_candles_15days_20251225.csv'
PATTERNS_FILE = 'successful_candles.csv'

print('=' * 90)
print('🛡️  اختبار الاستراتيجية الجديدة (Patterns + Crawl Filter) على بيانات 15 يوم')
print('=' * 90)

# ==============================================================================
# 2. دوال المنطق (نسخة طبق الأصل من reeshah.py)
# ==============================================================================

def load_patterns():
    if not os.path.exists(PATTERNS_FILE):
        print("❌ ملف الأنماط غير موجود!")
        return {}, {}

    df = pd.read_csv(PATTERNS_FILE)
    df.columns = df.columns.str.strip().str.lower()
    
    # استبعاد الأنماط المحظورة
    df = df[~df['symbol'].str.upper().isin(['NBY', 'SIDU'])]

    patterns = {}
    pattern_metrics = {}

    for symbol, group in df.groupby('symbol'):
        group = group.sort_values('time')
        if len(group) >= 6:
            candles = group.iloc[:6][['open', 'high', 'low', 'close']].values

            candle_details = []
            for i in range(len(candles)):
                o, h, l, c = candles[i]
                body_pct = (c - o) / o * 100
                direction = 1 if c >= o else -1
                body_size = abs(body_pct)

                candle_details.append({
                    'direction': direction,
                    'body_pct': body_pct,
                    'body_size': body_size,
                    'open': o, 'high': h, 'low': l, 'close': c
                })

            patterns[symbol] = candles
            pattern_metrics[symbol] = {
                'candle_details': candle_details,
                'avg_body': np.mean([cd['body_size'] for cd in candle_details])
            }
            
    print(f"✅ تم تحميل {len(patterns)} نمط مرجعي")
    return patterns, pattern_metrics

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    # استخراج تفاصيل الشموع الحالية
    current_details = []
    for i in range(len(current_candles)):
        o, h, l, c = current_candles[i]
        body_pct = (c - o) / o * 100
        direction = 1 if c >= o else -1
        body_size = abs(body_pct)

        current_details.append({
            'direction': direction,
            'body_pct': body_pct,
            'body_size': body_size,
            'open': o, 'high': h, 'low': l, 'close': c
        })

    # 🚨 شرط إلزامي: السهم يجب أن يكون صاعد بشكل عام!
    curr_start = current_details[0]['open']
    curr_end = current_details[-1]['close']
    curr_trend = (curr_end - curr_start) / curr_start * 100

    if curr_trend <= 0:
        return 0, "None"

    best_score = 0
    best_name = "None"

    for name, ref_candles in reference_patterns.items():
        if name not in pattern_metrics: continue

        ref_details = pattern_metrics[name]['candle_details']
        compare_len = min(len(current_details), len(ref_details))
        if compare_len < 3: continue

        # 1️⃣ فحص تطابق الاتجاهات
        direction_matches = 0
        for i in range(compare_len):
            if current_details[i]['direction'] == ref_details[i]['direction']:
                direction_matches += 1

        direction_ratio = direction_matches / compare_len
        if direction_ratio < 0.67: continue

        direction_score = direction_ratio * 100

        # 2️⃣ فحص تشابه أحجام الشموع
        size_penalties = 0
        for i in range(compare_len):
            curr_size = current_details[i]['body_size']
            ref_size = ref_details[i]['body_size']

            if ref_size > 0:
                size_diff = abs(curr_size - ref_size) / max(ref_size, 0.1)
            else:
                size_diff = curr_size

            if size_diff > 1.0:
                size_penalties += min(size_diff - 1.0, 1.0) * 20

        size_score = max(0, 100 - size_penalties)

        final_score = (direction_score * 0.60 + size_score * 0.40)

        if final_score > best_score:
            best_score = final_score
            best_name = name

    return best_score, best_name

# ==============================================================================
# 3. تنفيذ الاختبار
# ==============================================================================

# تحميل البيانات
if not os.path.exists(DATA_FILE):
    print(f"❌ ملف البيانات {DATA_FILE} غير موجود")
    exit()

print("⏳ جاري تحميل البيانات التاريخية...")
df_all = pd.read_csv(DATA_FILE)
df_all['date'] = pd.to_datetime(df_all['date'])

# تحويل التوقيت من UTC إلى نيويورك (America/New_York)
# نفترض أن البيانات الأصلية UTC (لأنها تبدأ 14:30)
try:
    if df_all['date'].dt.tz is None:
        df_all['date'] = df_all['date'].dt.tz_localize('UTC')
    
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
    print("✅ تم تحويل التوقيت إلى نيويورك")
except Exception as e:
    print(f"⚠️ تحذير في تحويل الوقت: {e}")

print(f"✅ تم تحميل {len(df_all)} صف من البيانات")

patterns, pattern_metrics = load_patterns()

results = []
filtered_count = 0

# تجميع البيانات حسب السهم واليوم
# نحتاج عمود لليوم فقط
df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')

grouped = df_all.groupby(['symbol', 'day_str'])

print(f"🔍 جاري فحص {len(grouped)} يوم تداول...")

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_values('date')
    
    # استخراج شموع الصباح (09:30 - 09:55)
    # نفترض أن البيانات بتوقيت نيويورك أو التوقيت الموجود في الملف
    # سنستخدم التوقيت الموجود في الملف مباشرة (HH:MM)
    
    # تحويل الوقت لفلترة سهلة
    day_data['time_str'] = day_data['date'].dt.strftime('%H:%M')
    
    morning_mask = day_data['time_str'].isin(['09:30', '09:35', '09:40', '09:45', '09:50', '09:55'])
    morning_candles = day_data[morning_mask]
    
    if len(morning_candles) < 4: continue # نحتاج على الأقل 4 شموع للحكم
    
    # 1. فلتر الزحف (Crawl Filter)
    # متوسط جسم الشمعة < 1.0%
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    
    # تنظيف البيانات من الأصفار
    valid_candles = [c for c in candles_vals if c[0] > 0 and c[3] > 0]
    if len(valid_candles) < 4: continue
    
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in valid_candles])
    
    if np.isnan(avg_body) or avg_body >= 1.0:
        filtered_count += 1
        continue
        
    # 2. مطابقة الأنماط
    score, name = calculate_similarity(valid_candles, patterns, pattern_metrics)
    
    if score >= 70:
        # ✅ إشارة دخول!
        entry_price = valid_candles[-1][3] # إغلاق آخر شمعة صباحية
        
        if entry_price <= 0: continue
        
        entry_time = morning_candles.iloc[-1]['date']
        
        # فحص ما حدث بقية اليوم
        rest_of_day = day_data[day_data['date'] > entry_time]
        
        if len(rest_of_day) == 0: continue
        
        max_price = rest_of_day['high'].max()
        min_price = rest_of_day['low'].min()
        
        max_gain = (max_price - entry_price) / entry_price * 100
        max_loss = (min_price - entry_price) / entry_price * 100
        
        if np.isnan(max_gain) or np.isnan(max_loss): continue

        results.append({
            'date': day,
            'symbol': symbol,
            'pattern': name,
            'score': score,
            'avg_body': avg_body,
            'max_gain': max_gain,
            'max_loss': max_loss
        })

# ==============================================================================
# 4. عرض النتائج
# ==============================================================================
print('\n' + '=' * 90)
print('📊 تقرير النتائج النهائية (15 يوم)')
print('=' * 90)

total_signals = len(results)
if total_signals > 0:
    avg_gain = np.mean([r['max_gain'] for r in results])
    avg_loss = np.mean([r['max_loss'] for r in results])
    
    wins_3 = len([r for r in results if r['max_gain'] >= 3])
    wins_5 = len([r for r in results if r['max_gain'] >= 5])
    wins_10 = len([r for r in results if r['max_gain'] >= 10])
    
    losses_2 = len([r for r in results if r['max_loss'] <= -2])
    losses_5 = len([r for r in results if r['max_loss'] <= -5])
    
    print(f"🔢 إجمالي الإشارات: {total_signals}")
    print(f"🧹 تم استبعاد {filtered_count} حالة بسبب الشموع الكبيرة (Spikes)")
    print(f"📈 متوسط الربح الأقصى: {avg_gain:+.2f}%")
    print(f"📉 متوسط الخسارة القصوى: {avg_loss:.2f}%")
    print("-" * 40)
    print(f"✅ نسبة نجاح (≥3%): {wins_3}/{total_signals} ({wins_3/total_signals*100:.1f}%)")
    print(f"🚀 نسبة نجاح (≥5%): {wins_5}/{total_signals} ({wins_5/total_signals*100:.1f}%)")
    print(f"💎 نسبة نجاح (≥10%): {wins_10}/{total_signals} ({wins_10/total_signals*100:.1f}%)")
    print("-" * 40)
    print(f"⚠️ مخاطرة (هبوط > 2%): {losses_2}/{total_signals} ({losses_2/total_signals*100:.1f}%)")
    print(f"💀 مخاطرة (هبوط > 5%): {losses_5}/{total_signals} ({losses_5/total_signals*100:.1f}%)")
    
    print('\n🏆 أفضل الصفقات:')
    top_gains = sorted(results, key=lambda x: x['max_gain'], reverse=True)[:10]
    for r in top_gains:
        print(f"   {r['date']} | {r['symbol']:<5} | {r['pattern']:<10} | ربح: {r['max_gain']:+.1f}% | خسارة: {r['max_loss']:.1f}% | Body: {r['avg_body']:.2f}%")

    print('\n📉 أسوأ الصفقات:')
    worst_losses = sorted(results, key=lambda x: x['max_loss'])[:5]
    for r in worst_losses:
        print(f"   {r['date']} | {r['symbol']:<5} | {r['pattern']:<10} | ربح: {r['max_gain']:+.1f}% | خسارة: {r['max_loss']:.1f}% | Body: {r['avg_body']:.2f}%")

else:
    print("❌ لم يتم العثور على أي إشارات مطابقة للشروط.")
