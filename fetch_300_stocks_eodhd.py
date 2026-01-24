#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
جلب شموع 300 سهم من EODHD
للفترة 9:30-10:00 من تاريخ 2025-12-17
"""

import sys
sys.path.insert(0, '.')

import reeshah
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import pytz

print("\n" + "╔" + "═" * 80 + "╗")
print("║" + " " * 15 + "🚀 جلب شموع 300 سهم من EODHD (9:30-10:00) بتاريخ 2025-12-17" + " " * 8 + "║")
print("╚" + "═" * 80 + "╝\n")

# تحميل قائمة الـ 300 سهم
print("📦 جاري تحميل قائمة الأسهم...")
try:
    stocks_df = pd.read_csv('finviz_300_stocks.csv')
    stocks = stocks_df['symbol'].tolist()[:300]
    print(f"✅ تم تحميل {len(stocks)} سهم")
except Exception as e:
    print(f"❌ خطأ في تحميل القائمة: {e}")
    exit()

# إعدادات EODHD
EODHD_API_KEY = "68c0ad0b52af78.88121932"
TARGET_DATE = "2025-12-17"
START_TIME = "09:30"
END_TIME = "10:00"

# تحويل التاريخ إلى Unix Timestamp
target_datetime = datetime.strptime(f"{TARGET_DATE} {START_TIME}", "%Y-%m-%d %H:%M")
ny_tz = pytz.timezone('America/New_York')
target_datetime_ny = ny_tz.localize(target_datetime)
from_timestamp = int(target_datetime_ny.timestamp())

print(f"\n📅 جاري جلب الشموع:")
print(f"   التاريخ: {TARGET_DATE}")
print(f"   الفترة: {START_TIME} - {END_TIME} (بتوقيت نيويورك)")
print(f"   Unix Timestamp: {from_timestamp}\n")

# جلب البيانات
all_candles = []
successful = 0
failed = 0

for i, stock in enumerate(stocks, 1):
    print(f"\r🔄 {i}/300: {stock:<8}", end="", flush=True)
    
    try:
        # بناء رابط EODHD
        url = f"https://eodhd.com/api/intraday/{stock}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
        
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            failed += 1
            continue
        
        data = response.json()
        if not data:
            failed += 1
            continue
        
        # معالجة البيانات
        for candle in data:
            # تحويل الـ timestamp إلى وقت نيويورك
            timestamp = int(candle.get('timestamp', 0))
            candle_time = datetime.fromtimestamp(timestamp, tz=pytz.UTC).astimezone(ny_tz)
            candle_time_str = candle_time.strftime("%H:%M:%S")
            
            # تصفية الشموع بين 9:30 و 10:00
            candle_hour = candle_time.hour
            candle_minute = candle_time.minute
            
            if candle_hour == 9 and candle_minute >= 30:
                all_candles.append({
                    'symbol': stock,
                    'datetime': candle_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'open': float(candle.get('open', 0)),
                    'high': float(candle.get('high', 0)),
                    'low': float(candle.get('low', 0)),
                    'close': float(candle.get('close', 0)),
                    'volume': int(candle.get('volume', 0)),
                    'time': candle_time_str
                })
            elif candle_hour == 10 and candle_minute < 1:
                all_candles.append({
                    'symbol': stock,
                    'datetime': candle_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'open': float(candle.get('open', 0)),
                    'high': float(candle.get('high', 0)),
                    'low': float(candle.get('low', 0)),
                    'close': float(candle.get('close', 0)),
                    'volume': int(candle.get('volume', 0)),
                    'time': candle_time_str
                })
        
        successful += 1
        time.sleep(0.1)  # تأخير بسيط لتجنب حد المعدل
        
    except Exception as e:
        failed += 1
        continue

print(f"\n\n✅ اكتمل الجلب!")
print(f"   ✔️ نجح: {successful}")
print(f"   ❌ فشل: {failed}")
print(f"   📊 إجمالي الشموع: {len(all_candles)}")

# حفظ البيانات في CSV
if all_candles:
    df = pd.DataFrame(all_candles)
    filename = f"eodhd_300_stocks_{TARGET_DATE}_930_1000.csv"
    df.to_csv(filename, index=False)
    print(f"\n💾 تم حفظ البيانات في: {filename}")
    
    # عرض ملخص
    print(f"\n📋 ملخص البيانات:")
    print(f"   ├─ عدد الأسهم الفريدة: {df['symbol'].nunique()}")
    print(f"   ├─ إجمالي الشموع: {len(df)}")
    print(f"   ├─ أول سهم: {df.iloc[0]['symbol']} @ {df.iloc[0]['datetime']}")
    print(f"   └─ آخر سهم: {df.iloc[-1]['symbol']} @ {df.iloc[-1]['datetime']}")
    
    # الآن اختبر الدالة الجديدة
    print("\n" + "=" * 80)
    print("🧪 اختبار الدالة الجديدة على البيانات المحملة...")
    print("=" * 80)
    
    patterns = reeshah.load_successful_patterns()
    
    # تجميع الشموع حسب السهم وأخذ أول 6 شموع لكل سهم
    results = []
    
    for stock in df['symbol'].unique():
        stock_data = df[df['symbol'] == stock].sort_values('datetime')
        
        if len(stock_data) >= 6:
            candles = stock_data.iloc[:6][['open', 'high', 'low', 'close']].values
            try:
                score, best_match = reeshah.calculate_structural_similarity(candles, patterns)
                results.append({
                    'symbol': stock,
                    'score': score,
                    'best_pattern': best_match,
                    'candles_count': len(stock_data)
                })
            except:
                pass
    
    # ترتيب النتائج
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('score', ascending=False)
    
    print(f"\n✅ اختبار على {len(results)} سهم\n")
    
    # عرض أفضل 15 نتيجة
    print(f"{'#':<4} {'السهم':<8} {'النسبة':<8} {'النمط':<12}")
    print("-" * 50)
    
    for i, (_, row) in enumerate(results_df.head(15).iterrows(), 1):
        print(f"{i:<4} {row['symbol']:<8} {row['score']:>6.1f}% {row['best_pattern']:<12}")
    
    # إحصائيات
    print(f"\n📊 الإحصائيات:")
    print(f"   ├─ متوسط التطابق: {results_df['score'].mean():.1f}%")
    print(f"   ├─ أعلى تطابق: {results_df['score'].max():.1f}%")
    print(f"   ├─ أقل تطابق: {results_df['score'].min():.1f}%")
    
    excellent = sum(results_df['score'] >= 90)
    good = sum((results_df['score'] >= 70) & (results_df['score'] < 90))
    moderate = sum((results_df['score'] >= 50) & (results_df['score'] < 70))
    weak = sum(results_df['score'] < 50)
    
    print(f"   ├─ ممتاز (≥90%): {excellent} سهم")
    print(f"   ├─ جيد (70-90%): {good} سهم")
    print(f"   ├─ معقول (50-70%): {moderate} سهم")
    print(f"   └─ ضعيف (<50%): {weak} سهم")
    
    # حفظ النتائج
    results_filename = f"matching_results_{TARGET_DATE}_930_1000.csv"
    results_df.to_csv(results_filename, index=False)
    print(f"\n💾 تم حفظ النتائج في: {results_filename}")

else:
    print("❌ لم يتم جلب أي بيانات!")

print("\n" + "╔" + "═" * 80 + "╗")
print("║" + " " * 28 + "✅ اكتمل! 🎉" + " " * 41 + "║")
print("╚" + "═" * 80 + "╝\n")
