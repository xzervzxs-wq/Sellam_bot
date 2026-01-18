"""
🧪 اختبار خوارزمية المطابقة الجديدة على بيانات ديسمبر 2025
============================================================
يجلب البيانات من FMP API ويختبر الكود الجديد
"""

import requests
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY", "AzN1tXfit4MUgxLSvWO73Wusjz8f2v21")

# ============================================================
# الأنماط النخبوية الـ 5 (قوة ≥ 1%)
# ============================================================
ELITE_PATTERNS = ['Benf', 'VIVK', 'CCL', 'MVIS', 'IOBT']
MATCH_THRESHOLD = 65
TARGET_PROFIT = 1.0

# ============================================================
# تحميل الأنماط
# ============================================================
def load_patterns():
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
            for c in candles:
                o, h, l, cl = c
                body_pct = (cl - o) / o * 100
                candle_details.append({'body_pct': body_pct})
            
            avg_strength = np.mean([abs(cd['body_pct']) for cd in candle_details])
            patterns[symbol] = candles
            pattern_metrics[symbol] = {'candle_details': candle_details, 'avg_strength': avg_strength}
    
    return patterns, pattern_metrics

# ============================================================
# خوارزمية المطابقة
# ============================================================
def calculate_similarity(current_candles, patterns, pattern_metrics):
    if not patterns:
        return 0, "None"

    current_details = []
    for c in current_candles:
        o, h, l, cl = c[0], c[1], c[2], c[3]
        body_pct = (cl - o) / o * 100
        current_details.append({'body_pct': body_pct})

    curr_start = current_candles[0][0]
    curr_end = current_candles[-1][3]
    curr_trend = (curr_end - curr_start) / curr_start * 100
    if curr_trend <= 0:
        return 0, "None"

    best_score = 0
    best_name = "None"

    for name in patterns.keys():
        if name not in pattern_metrics:
            continue

        ref_details = pattern_metrics[name]['candle_details']
        compare_len = min(len(current_details), len(ref_details))
        if compare_len < 3:
            continue

        ref_avg_strength = np.mean([abs(d['body_pct']) for d in ref_details[:compare_len]])
        curr_avg_strength = np.mean([abs(d['body_pct']) for d in current_details[:compare_len]])
        
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
# فحص الزحف
# ============================================================
def check_crawl(candles, min_hh=3, min_hl=4):
    if len(candles) < 2:
        return False
    hh = sum(1 for i in range(1, len(candles)) if candles[i][1] >= candles[i-1][1])
    hl = sum(1 for i in range(1, len(candles)) if candles[i][2] >= candles[i-1][2])
    return hh >= min_hh and hl >= min_hl

# ============================================================
# جلب البيانات من FMP
# ============================================================
def get_fmp_data(symbol):
    url = f"https://financialmodelingprep.com/stable/historical-chart/5min?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data and isinstance(data, list):
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df
    except:
        pass
    return None

# ============================================================
# الاختبار الرئيسي
# ============================================================
def main():
    print("=" * 70)
    print("🧪 اختبار خوارزمية المطابقة على بيانات ديسمبر 2025")
    print("=" * 70)
    
    patterns, pattern_metrics = load_patterns()
    print(f"✅ تم تحميل {len(patterns)} نمط نخبوي: {list(patterns.keys())}")
    
    print("\n📊 قوة الأنماط:")
    for name, metrics in pattern_metrics.items():
        print(f"  {name}: {metrics['avg_strength']:.2f}%")
    
    # أسهم متطايرة + الأنماط النخبوية
    test_symbols = [
        # الأنماط النخبوية
        'MVIS', 'VIVK', 'CCL', 'IOBT', 
        # أسهم متطايرة
        'RIVN', 'LAZR', 'BLNK', 'SPCE', 'LCID', 'NKLA', 'GOEV', 'FSR',
        'SNDL', 'TLRY', 'CGC', 'ACB', 'CLOV', 'WISH', 'WKHS', 'RIDE',
        'GME', 'AMC', 'BB', 'NOK', 'BBBY', 'KOSS', 'NAKD', 'EXPR',
        'PLTR', 'SOFI', 'DKNG', 'PENN', 'SKLZ', 'FUBO', 'OPEN', 'LMND',
        'AFRM', 'UPST', 'HOOD', 'RKLB', 'IONQ', 'STEM', 'QS', 'CHPT',
        'TTCF', 'OATLY', 'BYND', 'CPNG', 'GRAB', 'SE', 'BABA', 'JD',
        # أسهم Biotech
        'MRNA', 'BNTX', 'NVAX', 'VXRT', 'OCGN', 'INO', 'SRNE',
        # أسهم EV
        'TSLA', 'NIO', 'XPEV', 'LI', 'PTRA', 'ARVL',
        # أسهم أخرى متطايرة
        'BBIG', 'ATER', 'PROG', 'FAMI', 'CEI', 'DWAC',
        # من الاختبار السابق (الزبالة)
        'ASBP', 'APLT', 'DENN', 'AACI'
    ]
    
    print(f"\n📈 جلب بيانات {len(test_symbols)} سهم...")
    
    all_signals = []
    
    for symbol in test_symbols:
        print(f"\n🔍 فحص {symbol}...")
        df = get_fmp_data(symbol)
        
        if df is None or len(df) < 100:
            print(f"  ❌ لا بيانات كافية")
            continue
        
        # استخراج الأيام في ديسمبر
        df['day'] = df['date'].dt.date
        december_days = df[df['date'].dt.month == 12]['day'].unique()
        
        print(f"  📅 {len(december_days)} يوم في ديسمبر")
        
        for day in december_days:
            day_data = df[df['day'] == day]
            
            # شموع الصباح (09:30 - 09:55)
            morning = day_data[(day_data['date'].dt.time >= pd.Timestamp('09:30').time()) & 
                              (day_data['date'].dt.time <= pd.Timestamp('09:55').time())]
            
            if len(morning) < 6:
                continue
            
            morning_candles = morning[['open', 'high', 'low', 'close']].values[:6]
            
            # فحص متوسط الجسم
            avg_body = np.mean([abs((c[3]-c[0])/c[0]*100) for c in morning_candles])
            if avg_body > 1.5:
                continue
            
            # فحص المطابقة
            match_score, match_name = calculate_similarity(morning_candles, patterns, pattern_metrics)
            
            if match_score < MATCH_THRESHOLD:
                continue
            
            # فحص الزحف
            if not check_crawl(morning_candles, min_hh=3, min_hl=4):
                continue
            
            # سعر الدخول (شمعة 10:00)
            candle_10 = day_data[(day_data['date'].dt.time >= pd.Timestamp('10:00').time()) & 
                                (day_data['date'].dt.time < pd.Timestamp('10:05').time())]
            
            if len(candle_10) == 0:
                continue
            
            entry_price = candle_10.iloc[0]['close']
            entry_time = candle_10.iloc[0]['date']
            
            # فحص هل وصل 1%
            after_entry = day_data[day_data['date'] > entry_time]
            reached = False
            max_pct = 0
            
            for _, row in after_entry.iterrows():
                high_pct = (row['high'] - entry_price) / entry_price * 100
                if high_pct >= TARGET_PROFIT:
                    reached = True
                    break
                max_pct = max(max_pct, high_pct)
            
            result = "✅ WIN" if reached else f"❌ LOSS ({max_pct:.1f}%)"
            print(f"  📊 {day} | Match: {match_score:.0f}% ({match_name}) | Body: {avg_body:.2f}% | {result}")
            
            all_signals.append({
                'date': day,
                'symbol': symbol,
                'match_score': match_score,
                'match_name': match_name,
                'avg_body': avg_body,
                'reached_target': reached,
                'max_pct': max_pct
            })
    
    # ============================================================
    # الملخص
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
    
    print(f"📈 إجمالي الإشارات: {total}")
    print(f"✅ الرابحة: {wins}")
    print(f"❌ الخاسرة: {total - wins}")
    print(f"📊 نسبة النجاح: {win_rate:.1f}%")
    
    # حفظ النتائج
    df_results.to_csv('december_fmp_test_results.csv', index=False)
    print(f"\n💾 تم حفظ النتائج في: december_fmp_test_results.csv")

if __name__ == "__main__":
    main()
