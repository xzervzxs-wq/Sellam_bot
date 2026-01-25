#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 اختبار استراتيجية الزحف البطيء (Crawl Strategy) - نسخة مرنة
- تجاهل الشمعة الأولى (09:30)
- قياس الجمال الجديد (أجسام صغيرة، زحف بطيء)
- معايير مرنة للعمل مع بيانات واقعية
"""

import requests
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import pytz
from glob import glob

# ==============================================================================
# 📊 تحميل الأنماط المرجعية
# ==============================================================================

def normalize_pattern(candles):
    """تحويل الشموع إلى بصمة رقمية"""
    candles = np.array(candles, dtype=float)
    min_val, max_val = np.min(candles), np.max(candles)
    diff = max_val - min_val
    if diff == 0: return np.zeros_like(candles)
    return (candles - min_val) / diff

def load_successful_patterns():
    """تحميل الأنماط المرجعية (تجاهل الشمعة الأولى)"""
    if not os.path.exists("successful_candles.csv"):
        print("❌ ملف الأنماط غير موجود")
        return {}, {}
    
    try:
        df = pd.read_csv("successful_candles.csv")
        df.columns = df.columns.str.strip().str.lower()
        
        patterns = {}
        pattern_metrics = {}
        
        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 2:
                # تجاهل الشمعة الأولى (09:30)
                clean_candles = group.iloc[1:6][['open', 'high', 'low', 'close']].values
                patterns[symbol] = normalize_pattern(clean_candles)
                
                # احسب متوسط أجسام الشموع للنمط
                bodies = [abs(clean_candles[i][3] - clean_candles[i][0]) / clean_candles[i][0] * 100 
                         for i in range(len(clean_candles))]
                pattern_metrics[symbol] = {
                    'avg_body': np.mean(bodies),
                    'bodies': bodies
                }
        
        print(f"✅ تم تحميل {len(patterns)} نمط مرجعي (EFA, CCL, RIVN...)")
        return patterns, pattern_metrics
    except Exception as e:
        print(f"❌ خطأ الأنماط: {e}")
        return {}, {}

# ==============================================================================
# 🧠 الاستراتيجيات
# ==============================================================================

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    """مطابقة الشكل الهندسي + أجسام الشموع"""
    if not reference_patterns: 
        return 0, "None"
    
    # احسب متوسط أجسام الشموع الحالية
    current_bodies = [abs(current_candles[i][3] - current_candles[i][0]) / current_candles[i][0] * 100 
                     for i in range(len(current_candles))]
    current_avg_body = np.mean(current_bodies)
    
    current_fingerprint = normalize_pattern(current_candles)
    best_score, best_name = 0, "None"
    
    for name, ref_fingerprint in reference_patterns.items():
        if current_fingerprint.shape != ref_fingerprint.shape: 
            continue
        
        # الشكل (60%)
        diff = np.mean(np.abs(current_fingerprint - ref_fingerprint))
        shape_score = 100 * (1 - diff)
        
        # الأجسام (40%)
        if name in pattern_metrics:
            ref_avg_body = pattern_metrics[name]['avg_body']
            body_diff = abs(current_avg_body - ref_avg_body)
            body_score = max(0, 100 - (body_diff * 50))
        else:
            body_score = 50
        
        # الدرجة النهائية: 60% شكل + 40% أجسام
        similarity = shape_score * 0.60 + body_score * 0.40
        
        if similarity > best_score:
            best_score = similarity
            best_name = name
            
    return best_score, best_name

def calculate_beauty_score(df):
    """🔥 مقياس الجمال (الزحف البطيء) - مرن للبيانات الواقعية"""
    if len(df) < 2: 
        return 0
    
    score = 50  # نقطة البداية
    
    opens = df['open'].values
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # 1. فحص الهيكل - القيعان والقمم صاعدة (مع سماحية واقعية 0.5%)
    lows_ascending = True
    highs_ascending = True
    
    for i in range(1, len(lows)):
        # قبول أي انخفاض أقل من 0.5%
        if lows[i] < lows[i-1]:
            if (lows[i-1] - lows[i]) / lows[i-1] > 0.005:
                lows_ascending = False
    
    for i in range(1, len(highs)):
        if highs[i] < highs[i-1]:
            if (highs[i-1] - highs[i]) / highs[i-1] > 0.005:
                highs_ascending = False
    
    if lows_ascending and highs_ascending: 
        score += 25  # هيكل مثالي
    elif lows_ascending or highs_ascending:
        score += 15  # هيكل جيد
    else: 
        score += 5   # هيكل ضعيف
    
    # 2. فحص الأجسام والشموع
    green_count = 0
    red_count = 0
    large_body_count = 0
    
    for i in range(len(df)):
        body_pct = abs(closes[i] - opens[i]) / opens[i] * 100
        upper_wick = highs[i] - max(opens[i], closes[i])
        
        # 🟢 شمعة خضراء
        if closes[i] >= opens[i]:
            green_count += 1
            if body_pct < 0.05: 
                score += 3  # دوجي خضراء
            elif body_pct <= 0.8: 
                score += 8  # جسم صغير/متوسط ✅
            elif body_pct > 2.5: 
                score -= 5  # جسم ضخم ❌
                large_body_count += 1
            else: 
                score += 3
            
        # 🔴 شمعة حمراء (الاستراحة)
        else:
            red_count += 1
            if body_pct <= 0.5:
                score += 8  # استراحة صحية ✅
            elif body_pct > 1.5:
                score -= 15  # بيع قوي ❌
                large_body_count += 1
            else:
                score -= 2
        
        # معاقبة الذيول الطويلة (أقل صرامة)
        if body_pct > 0.01 and (upper_wick / body_pct) > 3.0:
            score -= 2
    
    # 3. التوازن بين الأخضر والأحمر (نفضل أخضر أكثر)
    green_ratio = green_count / len(df)
    if green_ratio > 0.6:
        score += 10  # أكثر أخضر = ثقة
    elif green_ratio > 0.4:
        score += 5
    
    # 4. معاقبة عدد الأجسام الكبيرة
    if large_body_count == 0:
        score += 8  # لا توجد أجسام كبيرة = جيد جداً
    elif large_body_count > len(df) // 2:
        score -= 15  # معظم الأجسام كبيرة = سيء
    
    return min(99, max(10, score))

# ==============================================================================
# 📈 الاختبار الرئيسي
# ==============================================================================

def test_saved_candles():
    """اختبار الاستراتيجية على الشموع المحفوظة"""
    print("🧪 بدء اختبار استراتيجية الزحف (نسخة مرنة)...")
    print("=" * 75)
    
    # تحميل الأنماط مع مقاييسها
    patterns, pattern_metrics = load_successful_patterns()
    if not patterns:
        print("❌ لم يتم تحميل الأنماط")
        return
    
    # جلب جميع ملفات الاختبار المحفوظة (الملفات الكبيرة بدون _1min)
    test_files = [f for f in sorted(glob("test_candles_*.csv")) if "_1min" not in f]
    
    if not test_files:
        print("⚠️ لم يتم العثور على ملفات اختبار (test_candles_*.csv)")
        return
    
    print(f"📂 وجدت {len(test_files)} ملف اختبار\n")
    
    results = {
        "DIAMOND": [],
        "GOLD": [],
        "PATTERN": [],
        "REJECTED": []
    }
    
    total_stocks = 0
    
    for test_file in test_files[:100]:  # اختبر أول 100 ملف
        try:
            df = pd.read_csv(test_file)
            df.columns = df.columns.str.strip().str.lower()
            
            # استخراج رمز السهم من اسم الملف أو من البيانات
            if 'symbol' in df.columns:
                ticker = df['symbol'].iloc[0].upper()
            else:
                ticker = test_file.split('_')[2].upper()
            
            # تنظيف البيانات - تحويل الأعمدة الأساسية لأرقام
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
            
            # 🔥 استخراج شموع السهم الحالي فقط (الملف قد يحتوي على أسهم متعددة)
            ticker_data = df[df['symbol'].str.upper() == ticker] if 'symbol' in df.columns else df
            
            if len(ticker_data) < 3:
                results["REJECTED"].append((ticker, "شموع قليلة"))
                continue
            
            total_stocks += 1
            
            # 🔥 تجاهل الشمعة الأولى لهذا السهم تحديداً
            if len(ticker_data) >= 2:
                df_clean = ticker_data.iloc[1:]  # حذف أول شمعة من هذا السهم فقط
            else:
                results["REJECTED"].append((ticker, "شموع غير كافية"))
                continue
            
            # 🔥 أخذ أول 6 شموع فقط (الـ 30 دقيقة الأول: 09:30-10:00)
            # هذا هو الوقت الحقيقي للاستراتيجية، بعده لا تستحق الأسهم التصنيف
            if len(df_clean) > 5:
                df_clean = df_clean.iloc[:5]  # أول 5 شموع = 6 شموع كاملة
            
            # حساب الجمال على هذه الشموع فقط
            beauty_score = calculate_beauty_score(df_clean)
            
            # 🔥 شرط إضافي: منع الأسهم "المتجمدة" (أجسام صغيرة جداً جداً)
            # الأجسام الصغيرة جداً = لا توجد قوة حقيقية = تجميد
            bodies_pct = [abs(df_clean.iloc[i]['close'] - df_clean.iloc[i]['open']) / df_clean.iloc[i]['open'] * 100 
                         for i in range(len(df_clean))]
            avg_body = np.mean(bodies_pct)
            
            if avg_body < 0.15:  # متوسط أجسام أقل من 0.15% = تجميد
                results["REJECTED"].append((ticker, f"متجمدة (أجسام: {avg_body:.3f}%)"))
                continue
            
            # حساب التطابق
            pattern_data = df_clean[['open', 'high', 'low', 'close']].values
            match_score, match_name = calculate_similarity(pattern_data, patterns, pattern_metrics)
            
            # 🛑 شروط الإرسال (مرنة أكثر)
            alert_type = None
            
            # الحالة 1: تطابق عالي مع الملف (تطابق نمط)
            if match_score >= 75: 
                alert_type = "DIAMOND"
                results["DIAMOND"].append((ticker, match_score, match_name, beauty_score))
            
            # الحالة 2: زحف بطيء وجميل جداً (حتى لو نمط جديد)
            elif beauty_score >= 70:
                alert_type = "GOLD"
                results["GOLD"].append((ticker, beauty_score))
            
            # الحالة 3: جمع بين الاثنين
            elif match_score >= 55 and beauty_score >= 60:
                alert_type = "PATTERN"
                results["PATTERN"].append((ticker, match_score, match_name, beauty_score))
            
            elif match_score >= 50 and beauty_score >= 55:
                alert_type = "PATTERN"
                results["PATTERN"].append((ticker, match_score, match_name, beauty_score))
            
            else:
                results["REJECTED"].append((ticker, f"Match:{match_score:.0f}% Beauty:{beauty_score:.0f}%"))
        
        except Exception as e:
            print(f"⚠️ خطأ في {test_file}: {e}")
            continue
    
    # ==========================
    # 📊 عرض النتائج
    # ==========================
    print("\n" + "=" * 75)
    print("📊 النتائج النهائية")
    print("=" * 75)
    
    total_alerts = len(results["DIAMOND"]) + len(results["GOLD"]) + len(results["PATTERN"])
    
    # 💎 الجواهر (DIAMOND)
    if results["DIAMOND"]:
        print(f"\n💎 جواهر ({len(results['DIAMOND'])} سهم):")
        for ticker, match, name, beauty in sorted(results["DIAMOND"], key=lambda x: x[1], reverse=True):
            print(f"   ✅ {ticker:<6} | التطابق: {match:.1f}% (مع {name:6s}) | الجمال: {beauty:.0f}%")
    
    # 🔥 ذهب (GOLD)
    if results["GOLD"]:
        print(f"\n🔥 ذهب ({len(results['GOLD'])} سهم):")
        for ticker, beauty in sorted(results["GOLD"], key=lambda x: x[1], reverse=True)[:15]:
            print(f"   ✅ {ticker:<6} | الجمال: {beauty:.0f}%")
    
    # 🧩 أنماط (PATTERN)
    if results["PATTERN"]:
        print(f"\n🧩 أنماط ({len(results['PATTERN'])} سهم):")
        for ticker, match, name, beauty in sorted(results["PATTERN"], key=lambda x: x[1], reverse=True)[:15]:
            print(f"   ⚡ {ticker:<6} | التطابق: {match:.1f}% (مع {name:6s}) | الجمال: {beauty:.0f}%")
    
    # الإحصائيات
    print("\n" + "=" * 75)
    print("📈 الإحصائيات:")
    print(f"   📊 إجمالي الأسهم المختبرة: {total_stocks}")
    print(f"   ✅ نسبة النجاح: {(total_alerts / total_stocks * 100) if total_stocks else 0:.1f}% ({total_alerts}/{total_stocks})")
    print(f"   💎 جواهر: {len(results['DIAMOND'])}")
    print(f"   🔥 ذهب: {len(results['GOLD'])}")
    print(f"   🧩 أنماط: {len(results['PATTERN'])}")
    print(f"   ❌ مرفوضة: {total_stocks - total_alerts}")
    print("=" * 75)
    
    # عرض عينة من المرفوضة للفهم
    if results["REJECTED"]:
        print(f"\n❌ عينة من المرفوضة ({len(results['REJECTED'])} سهم إجمالي):")
        for ticker, reason in results["REJECTED"][:5]:
            print(f"   ❌ {ticker:<6} | السبب: {reason}")

if __name__ == "__main__":
    test_saved_candles()
