#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 اختبار استراتيجية الزحف البطيء (Crawl Strategy)
- تجاهل الشمعة الأولى (09:30)
- قياس الجمال الجديد (أجسام صغيرة، زحف بطيء)
- معايير إرسال جديدة
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
        return {}
    
    try:
        df = pd.read_csv("successful_candles.csv")
        df.columns = df.columns.str.strip().str.lower()
        
        patterns = {}
        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 2:
                # تجاهل الشمعة الأولى (09:30)
                clean_candles = group.iloc[1:6][['open', 'high', 'low', 'close']].values
                patterns[symbol] = normalize_pattern(clean_candles)
        
        print(f"✅ تم تحميل {len(patterns)} نمط مرجعي (EFA, CCL, RIVN...)")
        return patterns
    except Exception as e:
        print(f"❌ خطأ الأنماط: {e}")
        return {}

# ==============================================================================
# 🧠 الاستراتيجيات
# ==============================================================================

def calculate_similarity(current_candles, reference_patterns):
    """مطابقة الشكل الهندسي"""
    if not reference_patterns: 
        return 0, "None"
    
    current_fingerprint = normalize_pattern(current_candles)
    best_score, best_name = 0, "None"
    
    for name, ref_fingerprint in reference_patterns.items():
        if current_fingerprint.shape != ref_fingerprint.shape: 
            continue
        
        diff = np.mean(np.abs(current_fingerprint - ref_fingerprint))
        similarity = 100 * (1 - diff)
        
        if similarity > best_score:
            best_score = similarity
            best_name = name
            
    return best_score, best_name

def calculate_beauty_score(df):
    """🔥 مقياس الجمال (الزحف البطيء)"""
    if len(df) < 2: 
        return 0
    
    score = 50  # نقطة البداية
    
    opens = df['open'].values
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # 1. فحص الهيكل - القيعان يجب أن تكون صاعدة
    trend_valid = True
    for i in range(1, len(lows)):
        if lows[i] < lows[i-1]:
            if (lows[i-1] - lows[i]) / lows[i-1] > 0.001:
                trend_valid = False
                break
    
    if trend_valid: 
        score += 20
    else: 
        return 20  # هيكل مكسور = مرفوض
    
    # 2. فحص الأجسام والشموع
    for i in range(len(df)):
        body_pct = abs(closes[i] - opens[i]) / opens[i] * 100
        upper_wick = highs[i] - max(opens[i], closes[i])
        
        # 🟢 شمعة خضراء
        if closes[i] >= opens[i]:
            if body_pct < 0.05: 
                score += 5  # دوجي خضراء
            elif body_pct <= 0.6: 
                score += 10  # جسم صغير (زحف ممتاز) ✅
            elif body_pct > 2.0: 
                score -= 10  # جسم ضخم (انفجار) ❌
            else: 
                score += 5
            
        # 🔴 شمعة حمراء (الاستراحة)
        else:
            if body_pct <= 0.4:
                score += 10  # استراحة صحية ✅
            elif body_pct > 1.0:
                score -= 20  # بيع قوي ❌
            else:
                score -= 5
        
        # معاقبة الذيول الطويلة
        if body_pct > 0 and (upper_wick / body_pct) > 2.0:
            score -= 5
    
    # 3. القمم المتصاعدة (Higher Highs)
    if highs[-1] > highs[0]: 
        score += 10
    
    return min(99, max(10, score))

# ==============================================================================
# 📈 الاختبار الرئيسي
# ==============================================================================

def test_saved_candles():
    """اختبار الاستراتيجية على الشموع المحفوظة"""
    print("🧪 بدء اختبار استراتيجية الزحف...")
    print("=" * 70)
    
    # تحميل الأنماط
    patterns = load_successful_patterns()
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
    
    for test_file in test_files[:50]:  # اختبر أول 50 ملف
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
            
            if len(df) < 3:
                results["REJECTED"].append((ticker, "شموع قليلة"))
                continue
            
            total_stocks += 1
            
            # 🔥 تجاهل الشمعة الأولى
            if len(df) >= 2:
                df_clean = df.iloc[1:]  # حذف الأولى
            else:
                results["REJECTED"].append((ticker, "شموع غير كافية"))
                continue
            
            # 1. شرط الاتجاه الصاعد (اختياري - فقط للمراقبة)
            is_uptrend = df_clean['high'].iloc[-1] >= df_clean['high'].iloc[0]
            
            # لا نرفض بناءً على الاتجاه - نختبر الجمال والتطابق فقط
            
            # 2. حساب الجمال
            beauty_score = calculate_beauty_score(df_clean)
            
            # 3. حساب التطابق
            pattern_data = df_clean[['open', 'high', 'low', 'close']].values
            match_score, match_name = calculate_similarity(pattern_data, patterns)
            
            # 🛑 شروط الإرسال
            alert_type = None
            
            if match_score >= 80:
                alert_type = "DIAMOND"
                results["DIAMOND"].append((ticker, match_score, match_name, beauty_score))
            
            elif beauty_score >= 75:
                alert_type = "GOLD"
                results["GOLD"].append((ticker, beauty_score))
            
            elif match_score >= 60 and beauty_score >= 65:
                alert_type = "GOLD"
                results["GOLD"].append((ticker, beauty_score))
            
            elif match_score >= 50 and beauty_score >= 60:
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
    print("\n" + "=" * 70)
    print("📊 النتائج النهائية")
    print("=" * 70)
    
    total_alerts = len(results["DIAMOND"]) + len(results["GOLD"]) + len(results["PATTERN"])
    
    # 💎 الجواهر (DIAMOND)
    print(f"\n💎 جواهر ({len(results['DIAMOND'])} سهم):")
    for ticker, match, name, beauty in results["DIAMOND"]:
        print(f"   ✅ {ticker:<6} | التطابق: {match:.1f}% (مع {name}) | الجمال: {beauty:.0f}%")
    
    # 🔥 الذهب (GOLD)
    print(f"\n🔥 ذهب ({len(results['GOLD'])} سهم):")
    for ticker, beauty in results["GOLD"]:
        print(f"   ✅ {ticker:<6} | الجمال: {beauty:.0f}%")
    
    # 🧩 أنماط (PATTERN)
    print(f"\n🧩 أنماط ({len(results['PATTERN'])} سهم):")
    for ticker, match, name, beauty in results["PATTERN"]:
        print(f"   ⚡ {ticker:<6} | التطابق: {match:.1f}% (مع {name}) | الجمال: {beauty:.0f}%")
    
    # ❌ مرفوضة (المزيد من التفاصيل)
    if results["REJECTED"]:
        print(f"\n❌ مرفوضة ({len(results['REJECTED'])} سهم):")
        for ticker, reason in results["REJECTED"][:10]:  # أول 10 فقط
            print(f"   ❌ {ticker:<6} | السبب: {reason}")
    
    # الإحصائيات
    print("\n" + "=" * 70)
    print("📈 الإحصائيات:")
    print(f"   📊 إجمالي الأسهم المختبرة: {total_stocks}")
    print(f"   ✅ نسبة النجاح: {(total_alerts / total_stocks * 100) if total_stocks else 0:.1f}% ({total_alerts}/{total_stocks})")
    print(f"   💎 جواهر: {len(results['DIAMOND'])}")
    print(f"   🔥 ذهب: {len(results['GOLD'])}")
    print(f"   🧩 أنماط: {len(results['PATTERN'])}")
    print(f"   ❌ مرفوضة: {total_stocks - total_alerts}")
    print("=" * 70)

if __name__ == "__main__":
    test_saved_candles()
