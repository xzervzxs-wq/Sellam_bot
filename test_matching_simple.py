#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خوارزمية Strict Rhythm - نسخة مبسطة
"""
import pandas as pd
import numpy as np
import sys
import time
from datetime import datetime

print("🚀 بدء الاختبار...")

# 1. تحميل البيانات
print("\n📂 تحميل بيانات الاختبار...")
df_test = pd.read_csv('/workspaces/Sellam_bot/test_candles_20251223_170248.csv')
print(f"✅ تم تحميل {len(df_test)} صف")

# 2. تحميل الأنماط
print("\n🎯 تحميل الأنماط الناجحة...")
df_patterns = pd.read_csv('/workspaces/Sellam_bot/successful_candles.csv')
print(f"✅ تم تحميل بيانات الأنماط")

# تنظيف أسماء الأعمدة
df_patterns.columns = df_patterns.columns.str.strip().str.lower()
print(f"✅ Columns: {df_patterns.columns.tolist()}")

# 3. دالة استخراج الحمض النووي
def extract_dna(candles):
    """استخراج الحمض النووي للشموع"""
    dna = []
    
    if isinstance(candles, list) and candles and isinstance(candles[0], dict):
        candle_list = [[c.get('open', 0), c.get('high', 0), c.get('low', 0), c.get('close', 0)] 
                      for c in candles]
    else:
        candle_list = candles
    
    for c in candle_list:
        open_p, high_p, low_p, close_p = float(c[0]), float(c[1]), float(c[2]), float(c[3])
        
        total_range = high_p - low_p
        if total_range == 0: 
            total_range = 0.0001
        
        body_size = abs(close_p - open_p)
        body_ratio = body_size / total_range 
        
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p
        
        upper_ratio = upper_wick / total_range
        lower_ratio = lower_wick / total_range
        
        direction = 1 if close_p >= open_p else -1
        real_change_pct = (body_size / open_p) * 100 if open_p > 0 else 0
        
        dna.append({
            'body_r': body_ratio,
            'upper_r': upper_ratio,
            'lower_r': lower_ratio,
            'dir': direction,
            'size': real_change_pct
        })
    
    return dna

# 4. دالة المطابقة
def calculate_similarity(curr_dna, pattern_dna):
    """حساب التشابه بين شموع"""
    if len(curr_dna) != len(pattern_dna):
        return 0
    
    total_score = 100
    
    for curr, pattern in zip(curr_dna, pattern_dna):
        # مقارنة الاتجاه
        if curr['dir'] != pattern['dir']:
            total_score -= 50  # عقوبة كبيرة لتغيير الاتجاه
        
        # مقارنة حجم الجسم
        body_diff = abs(curr['body_r'] - pattern['body_r'])
        if body_diff > 0.15:
            total_score -= body_diff * 30
        
        # مقارنة حجم الشمعة
        size_diff = abs(curr['size'] - pattern['size'])
        if size_diff > 0.4:
            total_score -= (size_diff - 0.4) * 20
    
    return max(0, total_score)

# 5. اختبار المطابقة
print("\n🔍 جاري حساب المطابقة...")

# تحميل الأنماط
patterns_dict = {}
for symbol, group in df_patterns.groupby('symbol'):
    group = group.sort_values('time') if 'time' in group.columns else group
    if len(group) >= 6:
        candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
        dna = extract_dna(candles)
        patterns_dict[symbol] = dna

print(f"✅ تم استخراج DNA لـ {len(patterns_dict)} نمط")

# الأسهم الفريدة في بيانات الاختبار
stocks = df_test['symbol'].unique()
print(f"✅ عدد الأسهم المراد اختبارها: {len(stocks)}")

# المطابقة
results = []
all_scores = []

print(f"\n{'Symbol':<10} {'Avg Match':<12} {'Best Match':<12} {'Best Pattern':<15}")
print("-" * 70)

for idx, stock in enumerate(stocks, 1):
    stock_data = df_test[df_test['symbol'] == stock].sort_values('time')
    
    if len(stock_data) < 6:
        continue
    
    sample_candles = stock_data.head(6)[['open', 'high', 'low', 'close']].values
    curr_dna = extract_dna(sample_candles)
    
    # المقارنة مع جميع الأنماط
    scores = {}
    for pattern_name, pattern_dna in patterns_dict.items():
        scores[pattern_name] = calculate_similarity(curr_dna, pattern_dna)
    
    if scores:
        avg_score = sum(scores.values()) / len(scores)
        max_score = max(scores.values())
        best_pattern = max(scores, key=scores.get)
        
        all_scores.append(avg_score)
        
        results.append({
            'symbol': stock,
            'avg_match': avg_score,
            'best_match': max_score,
            'best_pattern': best_pattern
        })
        
        if idx % 50 == 0 or idx == len(stocks):
            print(f"{stock:<10} {avg_score:>10.1f}% {max_score:>10.1f}% {best_pattern:<15}")

# الإحصائيات
print("\n" + "="*70)
print("📊 الإحصائيات العامة:")
print("="*70)

if all_scores:
    print(f"  📈 متوسط المطابقة: {sum(all_scores)/len(all_scores):.2f}%")
    print(f"  🔝 أعلى مطابقة: {max(all_scores):.2f}%")
    print(f"  🔻 أقل مطابقة: {min(all_scores):.2f}%")
    print(f"  📊 عدد الأسهم المختبرة: {len(all_scores)}")
    
    excellent = len([s for s in all_scores if s >= 90])
    good = len([s for s in all_scores if 70 <= s < 90])
    
    print(f"\n  ⭐⭐⭐⭐⭐ ممتاز (90%+): {excellent}")
    print(f"  ⭐⭐⭐⭐   جيد (70-90%): {good}")

# أفضل 15 أسهم
print("\n" + "="*70)
print("🏆 أفضل 15 أسهم مطابقة:")
print("="*70)

df_results = pd.DataFrame(results)
top_15 = df_results.nlargest(15, 'avg_match')

print(f"\n{'#':<3} {'Symbol':<10} {'Avg Match':<12} {'Best Match':<12} {'Best Pattern':<15}")
print("-" * 70)

for idx, row in enumerate(top_15.values, 1):
    print(f"{idx:<3} {row[0]:<10} {row[1]:>10.1f}% {row[2]:>10.1f}% {row[3]:<15}")

# حفظ النتائج
output_file = '/workspaces/Sellam_bot/matching_results_simple.csv'
df_results = df_results.sort_values('avg_match', ascending=False)
df_results.to_csv(output_file, index=False)
print(f"\n✅ تم حفظ النتائج في: {output_file}")

print("\n✅ اكتمل الاختبار!")
