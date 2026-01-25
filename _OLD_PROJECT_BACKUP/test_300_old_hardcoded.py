#!/usr/bin/env python3
"""اختبار البوت على 300 سهم بالطريقة القديمة (hardcoded 0.4%)"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def load_successful_patterns():
    """تحميل الأنماط بدون metrics"""
    if not os.path.exists("successful_candles.csv"):
        print("❌ ملف الأنماط غير موجود")
        return {}
    
    try:
        df = pd.read_csv("successful_candles.csv")
        df.columns = df.columns.str.strip().str.lower()
        
        patterns = {}
        
        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 6:
                candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
                patterns[symbol] = normalize_pattern(candles)
        
        print(f"✅ تم تحميل {len(patterns)} نمط مرجعي (بدون metrics)")
        return patterns
    except Exception as e:
        print(f"❌ خطأ الأنماط: {e}")
        return {}

def normalize_pattern(candles):
    """تحويل الأسعار إلى بصمة رقمية (0-1)"""
    candles = np.array(candles, dtype=float)
    min_val = np.min(candles)
    max_val = np.max(candles)
    if max_val == min_val: 
        return np.zeros_like(candles)
    return (candles - min_val) / (max_val - min_val)

def get_candle_metrics(candles):
    """استخراج مقاييس الشمعة"""
    metrics = []
    
    for candle in candles:
        if isinstance(candle, (list, tuple, np.ndarray)):
            candle = {
                'open': float(candle[0]),
                'high': float(candle[1]),
                'low': float(candle[2]),
                'close': float(candle[3])
            }
        
        body = abs(candle['close'] - candle['open'])
        range_price = candle['high'] - candle['low']
        price = (candle['open'] + candle['close']) / 2
        
        body_pct = (body / price * 100) if price > 0 else 0
        volatility = (range_price / price * 100) if price > 0 else 0
        
        metrics.append({'body_pct': body_pct, 'volatility': volatility})
    
    return metrics

def calculate_similarity_OLD(current_candles, reference_patterns):
    """🔴 الطريقة القديمة: hardcoded 0.4% للأجسام"""
    if not reference_patterns: 
        return 0, "None"
    
    current_fingerprint = normalize_pattern(current_candles)
    current_metrics = get_candle_metrics(current_candles)
    
    # متوسط أجسام الشموع الحالية
    current_bodies = [abs(current_candles[i][3] - current_candles[i][0]) / current_candles[i][0] * 100 
                     for i in range(len(current_candles))]
    current_avg_body = np.mean(current_bodies)
    
    best_score = 0
    best_name = "None"
    
    for name, ref_fingerprint in reference_patterns.items():
        if current_fingerprint.shape != ref_fingerprint.shape: 
            continue
        
        # 1️⃣ الشكل (60%)
        diff = np.mean(np.abs(current_fingerprint - ref_fingerprint))
        pattern_score = 100 * (1 - diff)
        
        # 2️⃣ التقلب (25%)
        volatility_diffs = [m['volatility'] for m in current_metrics]
        avg_volatility = np.mean(volatility_diffs) if volatility_diffs else 1.0
        volatility_match = max(0, 100 - (abs(avg_volatility - 1.2) * 5))
        
        # 3️⃣ الأجسام (15%) - 🔴 HARDCODED 0.4% (خطأ!)
        body_match = max(0, 100 - (abs(current_avg_body - 0.4) * 10))
        
        # الدرجة النهائية
        final_score = (
            pattern_score * 0.60 +
            volatility_match * 0.25 +
            body_match * 0.15
        )
        
        if final_score > best_score:
            best_score = final_score
            best_name = name
            
    return best_score, best_name

def test_300_stocks_old():
    """اختبر على ملف الـ 300 سهم بالطريقة القديمة"""
    print("🧪 اختبار البوت على 300 سهم (الطريقة القديمة - HARDCODED 0.4%)...\n")
    print("=" * 80)
    
    # تحميل الأنماط
    patterns = load_successful_patterns()
    if not patterns:
        print("❌ فشل تحميل الأنماط")
        return
    
    print("\n" + "=" * 80)
    
    # اختبر الملف الأكبر
    test_file = "finviz_eodhd_candles_20251223_015906.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ الملف {test_file} غير موجود")
        return
    
    print(f"📂 جاري قراءة {test_file}...\n")
    
    df = pd.read_csv(test_file)
    df.columns = df.columns.str.strip().str.lower()
    
    results = {
        "DIAMOND": [],
        "GOLD": [],
        "SILVER": [],
        "REJECTED": []
    }
    
    total = 0
    for ticker in sorted(df['symbol'].unique()):
        ticker_str = str(ticker).upper()
        ticker_data = df[df['symbol'].str.upper() == ticker_str].copy()
        
        if len(ticker_data) < 6:
            results["REJECTED"].append((ticker, "شموع قليلة"))
            continue
        
        total += 1
        
        # رتب حسب التاريخ
        ticker_data = ticker_data.sort_values('date')
        
        # أول 6 شموع فقط
        first_6 = ticker_data.iloc[:6]
        
        # احسب متوسط الأجسام
        bodies = []
        for i in range(len(first_6)):
            row = first_6.iloc[i]
            body = abs(float(row['close']) - float(row['open'])) / float(row['open']) * 100
            bodies.append(body)
        
        avg_body = np.mean(bodies)
        
        # تجميد؟
        if avg_body < 0.15:
            results["REJECTED"].append((ticker, f"🥶 متجمدة ({avg_body:.3f}%)"))
            continue
        
        # ابني الشموع للمطابقة
        candles = first_6[['open', 'high', 'low', 'close']].values.astype(float)
        
        # احسب التطابق (الطريقة القديمة)
        match_score, match_name = calculate_similarity_OLD(candles, patterns)
        
        # تصنيف
        if match_score >= 85:
            results["DIAMOND"].append((ticker, match_score, match_name))
        elif match_score >= 75:
            results["GOLD"].append((ticker, match_score, match_name))
        elif match_score >= 60:
            results["SILVER"].append((ticker, match_score, match_name))
        else:
            results["REJECTED"].append((ticker, f"❌ {match_score:.1f}%"))
    
    # =========== عرض النتائج ===========
    print("\n" + "=" * 80)
    print("📊 النتائج (الطريقة القديمة - HARDCODED 0.4%)")
    print("=" * 80)
    
    # الماسات
    if results["DIAMOND"]:
        print(f"\n💎 الماسات ({len(results['DIAMOND'])} سهم):")
        for ticker, score, name in results["DIAMOND"][:10]:
            print(f"   ✅ {ticker:<6} | التطابق: {score:.1f}% مع {name:<5}")
        if len(results["DIAMOND"]) > 10:
            print(f"   ... و {len(results['DIAMOND']) - 10} آخرين")
    
    # الذهب
    if results["GOLD"]:
        print(f"\n🔥 ذهب ({len(results['GOLD'])} سهم):")
        for ticker, score, name in results["GOLD"][:5]:
            print(f"   ✅ {ticker:<6} | التطابق: {score:.1f}% مع {name:<5}")
        if len(results["GOLD"]) > 5:
            print(f"   ... و {len(results['GOLD']) - 5} آخرين")
    
    # الفضة
    if results["SILVER"]:
        print(f"\n⚪ فضة ({len(results['SILVER'])} سهم):")
        for ticker, score, name in results["SILVER"][:3]:
            print(f"   ⚠️ {ticker:<6} | التطابق: {score:.1f}% مع {name:<5}")
        if len(results["SILVER"]) > 3:
            print(f"   ... و {len(results['SILVER']) - 3} آخرين")
    
    # الإحصائيات
    print("\n" + "=" * 80)
    print("📈 الإحصائيات (الطريقة القديمة):")
    print(f"   📊 إجمالي المختبرة: {total}")
    print(f"   💎 ماسات: {len(results['DIAMOND'])} ({len(results['DIAMOND'])*100/total if total > 0 else 0:.1f}%)")
    print(f"   🔥 ذهب: {len(results['GOLD'])} ({len(results['GOLD'])*100/total if total > 0 else 0:.1f}%)")
    print(f"   ⚪ فضة: {len(results['SILVER'])} ({len(results['SILVER'])*100/total if total > 0 else 0:.1f}%)")
    print(f"   ❌ مرفوضة: {len(results['REJECTED'])} ({len(results['REJECTED'])*100/total if total > 0 else 0:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    test_300_stocks_old()
