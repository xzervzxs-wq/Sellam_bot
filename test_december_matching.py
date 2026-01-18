"""
🧪 اختبار خوارزمية المطابقة الجديدة على بيانات ديسمبر 2025
============================================================
- يستخدم نفس الأنماط النخبوية الـ 5: Benf, VIVK, CCL, MVIS, IOBT
- يستخدم نفس شروط التطابق (قوة ≥80% من النمط)
- يختبر كل يوم في ديسمبر ويحسب نسبة النجاح
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# الأنماط النخبوية الـ 5 (قوة ≥ 1%)
# ============================================================
ELITE_PATTERNS = ['Benf', 'VIVK', 'CCL', 'MVIS', 'IOBT']
MATCH_THRESHOLD = 65  # عتبة التطابق
TARGET_PROFIT = 1.0   # هدف الربح 1%

# ============================================================
# تحميل الأنماط من الملف
# ============================================================
def load_patterns():
    """تحميل الأنماط النخبوية"""
    df = pd.read_csv('successful_candles.csv')
    df.columns = df.columns.str.strip().str.lower()
    
    patterns = {}
    pattern_metrics = {}
    
    for symbol, group in df.groupby('symbol'):
        if symbol not in ELITE_PATTERNS:
            continue
            
        group = group.sort_values('time')
        if len(group) >= 6:
            candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
            
            candle_details = []
            for i in range(6):
                o, h, l, c = candles[i]
                body_pct = (c - o) / o * 100
                candle_details.append({
                    'body_pct': body_pct,
                    'open': o, 'high': h, 'low': l, 'close': c
                })
            
            patterns[symbol] = candles
            pattern_metrics[symbol] = {
                'candle_details': candle_details,
                'avg_strength': np.mean([abs(cd['body_pct']) for cd in candle_details])
            }
    
    return patterns, pattern_metrics

# ============================================================
# خوارزمية المطابقة الجديدة (نفس الكود في reeshah.py)
# ============================================================
def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    """مطابقة صارمة - نفس الكود في reeshah.py"""
    if not reference_patterns:
        return 0, "None"

    # استخراج تفاصيل الشموع الحالية
    current_details = []
    for i in range(len(current_candles)):
        o, h, l, c = current_candles[i][0], current_candles[i][1], current_candles[i][2], current_candles[i][3]
        body_pct = (c - o) / o * 100
        current_details.append({
            'body_pct': body_pct,
            'open': o, 'high': h, 'low': l, 'close': c
        })

    # شرط إلزامي: صاعد
    curr_start = current_details[0]['open']
    curr_end = current_details[-1]['close']
    curr_trend = (curr_end - curr_start) / curr_start * 100
    if curr_trend <= 0:
        return 0, "None"

    best_score = 0
    best_name = "None"

    for name, ref_candles in reference_patterns.items():
        if name not in pattern_metrics:
            continue

        ref_details = pattern_metrics[name]['candle_details']
        compare_len = min(len(current_details), len(ref_details))
        if compare_len < 3:
            continue

        # حساب متوسط قوة النمط والسهم الحالي
        ref_avg_strength = np.mean([abs(d['body_pct']) for d in ref_details[:compare_len]])
        curr_avg_strength = np.mean([abs(d['body_pct']) for d in current_details[:compare_len]])
        
        # رفض فوري: إذا السهم أضعف من 80% من النمط
        if curr_avg_strength < ref_avg_strength * 0.8:
            continue
        
        total_similarity = 0
        
        for i in range(compare_len):
            curr_pct = current_details[i]['body_pct']
            ref_pct = ref_details[i]['body_pct']
            
            same_direction = (curr_pct >= 0 and ref_pct >= 0) or (curr_pct < 0 and ref_pct < 0)
            
            if not same_direction:
                candle_score = 0
            else:
                curr_abs = abs(curr_pct)
                ref_abs = abs(ref_pct)
                
                max_diff = max(ref_abs * 0.6, 0.5)
                actual_diff = abs(curr_abs - ref_abs)
                
                if actual_diff <= max_diff:
                    candle_score = 100 - (actual_diff / max_diff * 40)
                else:
                    overshoot = actual_diff - max_diff
                    candle_score = max(0, 60 - overshoot * 30)
            
            total_similarity += candle_score
        
        final_score = total_similarity / compare_len

        if final_score > best_score:
            best_score = final_score
            best_name = name

    return best_score, best_name

# ============================================================
# فحص الزحف (HH3, HL4)
# ============================================================
def check_crawl(candles, min_hh=3, min_hl=4):
    """فحص شرط الزحف"""
    if len(candles) < 2:
        return False
    
    hh = sum(1 for i in range(1, len(candles)) if candles[i][1] >= candles[i-1][1])
    hl = sum(1 for i in range(1, len(candles)) if candles[i][2] >= candles[i-1][2])
    
    return hh >= min_hh and hl >= min_hl

# ============================================================
# فحص هل وصل 1% بعد الدخول
# ============================================================
def check_profit_target(df_day, entry_time, entry_price, target_pct=1.0):
    """فحص هل السهم وصل الهدف"""
    after_entry = df_day[df_day['date'] > entry_time]
    
    for _, row in after_entry.iterrows():
        high_pct = (row['high'] - entry_price) / entry_price * 100
        if high_pct >= target_pct:
            return True, high_pct
    
    # لم يصل - احسب أقصى ربح/خسارة
    if len(after_entry) > 0:
        max_high = after_entry['high'].max()
        max_pct = (max_high - entry_price) / entry_price * 100
        return False, max_pct
    
    return False, 0

# ============================================================
# الاختبار الرئيسي
# ============================================================
def main():
    print("=" * 70)
    print("🧪 اختبار خوارزمية المطابقة الجديدة على ديسمبر 2025")
    print("=" * 70)
    
    # تحميل الأنماط
    patterns, pattern_metrics = load_patterns()
    print(f"✅ تم تحميل {len(patterns)} نمط نخبوي: {list(patterns.keys())}")
    
    # عرض قوة كل نمط
    print("\n📊 قوة الأنماط:")
    for name, metrics in pattern_metrics.items():
        print(f"  {name}: {metrics['avg_strength']:.2f}%")
    
    # تحميل بيانات ديسمبر
    df = pd.read_csv('extended_candles_60days.csv')
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df['date'] = df['date'].dt.tz_convert('America/New_York')
    
    december = df[df['date'].dt.month == 12].copy()
    days = sorted(december['date'].dt.date.unique())
    
    print(f"\n📅 اختبار {len(days)} يوم في ديسمبر...")
    print("-" * 70)
    
    # نتائج
    all_signals = []
    
    for day in days:
        day_data = december[december['date'].dt.date == day]
        symbols = day_data['symbol'].unique()
        
        day_signals = 0
        day_wins = 0
        
        for symbol in symbols:
            sym_day = day_data[day_data['symbol'] == symbol].sort_values('date')
            
            # استخراج شموع الصباح (09:30 - 09:55)
            morning = sym_day[(sym_day['date'].dt.time >= pd.Timestamp('09:30').time()) & 
                             (sym_day['date'].dt.time <= pd.Timestamp('09:55').time())]
            
            if len(morning) < 6:
                continue
            
            morning_candles = morning[['open', 'high', 'low', 'close']].values[:6]
            
            # فحص متوسط الجسم (يجب < 1.5%)
            avg_body = np.mean([abs((c[3]-c[0])/c[0]*100) for c in morning_candles])
            if avg_body > 1.5:
                continue
            
            # فحص المطابقة
            match_score, match_name = calculate_similarity(morning_candles, patterns, pattern_metrics)
            
            if match_score < MATCH_THRESHOLD:
                continue
            
            # فحص الزحف (HH3, HL4)
            if not check_crawl(morning_candles, min_hh=3, min_hl=4):
                continue
            
            # ✅ إشارة! الآن نفحص النتيجة
            # سعر الدخول = إغلاق شمعة 10:00
            candle_10 = sym_day[(sym_day['date'].dt.time >= pd.Timestamp('10:00').time()) & 
                               (sym_day['date'].dt.time < pd.Timestamp('10:05').time())]
            
            if len(candle_10) == 0:
                continue
            
            entry_price = candle_10.iloc[0]['close']
            entry_time = candle_10.iloc[0]['date']
            
            # فحص هل وصل 1%
            reached, max_pct = check_profit_target(sym_day, entry_time, entry_price, TARGET_PROFIT)
            
            day_signals += 1
            if reached:
                day_wins += 1
                result = "✅ WIN"
            else:
                result = f"❌ LOSS ({max_pct:.1f}%)"
            
            all_signals.append({
                'date': day,
                'symbol': symbol,
                'match_score': match_score,
                'match_name': match_name,
                'avg_body': avg_body,
                'entry_price': entry_price,
                'reached_target': reached,
                'max_pct': max_pct
            })
            
            print(f"  {day} | {symbol:6} | Match: {match_score:.0f}% ({match_name}) | Body: {avg_body:.2f}% | {result}")
        
        if day_signals > 0:
            print(f"  📊 {day}: {day_wins}/{day_signals} = {day_wins/day_signals*100:.0f}%")
    
    # ============================================================
    # الملخص النهائي
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 الملخص النهائي")
    print("=" * 70)
    
    if len(all_signals) == 0:
        print("❌ لا توجد إشارات!")
        return
    
    df_results = pd.DataFrame(all_signals)
    total = len(df_results)
    wins = df_results['reached_target'].sum()
    win_rate = wins / total * 100
    avg_per_day = total / len(days)
    
    print(f"📈 إجمالي الإشارات: {total}")
    print(f"✅ الرابحة: {wins}")
    print(f"❌ الخاسرة: {total - wins}")
    print(f"📊 نسبة النجاح: {win_rate:.1f}%")
    print(f"📅 متوسط الإشارات/يوم: {avg_per_day:.1f}")
    
    # توزيع حسب النمط
    print("\n📊 توزيع حسب النمط:")
    for pattern in df_results['match_name'].unique():
        pattern_df = df_results[df_results['match_name'] == pattern]
        p_total = len(pattern_df)
        p_wins = pattern_df['reached_target'].sum()
        p_rate = p_wins / p_total * 100 if p_total > 0 else 0
        print(f"  {pattern}: {p_wins}/{p_total} = {p_rate:.0f}%")
    
    # حفظ النتائج
    df_results.to_csv('december_test_results.csv', index=False)
    print(f"\n💾 تم حفظ النتائج في: december_test_results.csv")

if __name__ == "__main__":
    main()
