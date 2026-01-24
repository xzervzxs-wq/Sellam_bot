#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار Strict Rhythm - نسخة محسّنة وسريعة
"""
import pandas as pd
import numpy as np
import time

start_time = time.time()

print("\n" + "="*70)
print("🧬 اختبار خوارزمية Strict Rhythm (المتقدمة)")
print("="*70)

# 1. تحميل البيانات
print("\n📂 المرحلة 1: تحميل البيانات...")
df_test = pd.read_csv('test_candles_20251223_170248.csv')
df_patterns = pd.read_csv('successful_candles.csv')
df_patterns.columns = df_patterns.columns.str.strip().str.lower()

print(f"  ✅ بيانات الاختبار: {len(df_test)} صف")
print(f"  ✅ بيانات الأنماط: {len(df_patterns)} صف")
print(f"  ✅ أسهم فريدة: {df_test['symbol'].nunique()} في الاختبار، {df_patterns['symbol'].nunique()} في الأنماط")

# 2. دوال معالجة البيانات
def extract_dna(candles):
    """استخراج الحمض النووي"""
    dna = []
    if isinstance(candles, pd.DataFrame):
        candles = candles[['open', 'high', 'low', 'close']].values.tolist()
    
    for c in candles:
        o, h, l, cl = float(c[0]), float(c[1]), float(c[2]), float(c[3])
        tr = h - l
        if tr == 0: tr = 0.0001
        
        dna.append({
            'body_r': abs(cl - o) / tr,
            'upper_r': (h - max(o, cl)) / tr,
            'lower_r': (min(o, cl) - l) / tr,
            'dir': 1 if cl >= o else -1,
            'size': (abs(cl - o) / o * 100) if o > 0 else 0
        })
    return dna

def calculate_similarity(curr_dna, pattern_dna):
    """حساب التشابه باستخدام Strict Rhythm"""
    if len(curr_dna) != len(pattern_dna):
        return 0
    
    score = 100.0
    for curr, pattern in zip(curr_dna, pattern_dna):
        # 1. اتجاه مختلف = عقوبة كبيرة
        if curr['dir'] != pattern['dir']:
            score -= 50
        
        # 2. فرق في حجم الجسم
        body_diff = abs(curr['body_r'] - pattern['body_r'])
        if body_diff > 0.15:
            score -= body_diff * 30
        
        # 3. فرق في حجم الشمعة (مضخات انفجارية)
        size_diff = abs(curr['size'] - pattern['size'])
        if size_diff > 0.4:
            score -= (size_diff - 0.4) * 20
    
    return max(0, score)

# 3. تحميل الأنماط
print("\n📊 المرحلة 2: استخراج DNA للأنماط...")
patterns_dict = {}
for symbol, group in df_patterns.groupby('symbol'):
    if len(group) >= 6:
        candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
        patterns_dict[symbol] = extract_dna(candles)

print(f"  ✅ عدد الأنماط: {len(patterns_dict)}")

# 4. المقارنة
print("\n📊 المرحلة 3: حساب التشابه...")
results = []
all_scores = []

stocks = df_test['symbol'].unique()
print(f"  🔍 جاري فحص {len(stocks)} سهم...")

for idx, stock in enumerate(stocks):
    stock_data = df_test[df_test['symbol'] == stock].sort_values('time')
    
    if len(stock_data) < 6:
        continue
    
    # استخراج DNA
    candles = stock_data.head(6)[['open', 'high', 'low', 'close']].values
    curr_dna = extract_dna(candles)
    
    # المقارنة
    scores = {}
    for pname, pdna in patterns_dict.items():
        scores[pname] = calculate_similarity(curr_dna, pdna)
    
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

print(f"\n  ✅ نتائج: {len(results)} سهم تم فحصهم")

# 5. الإحصائيات
print("\n" + "="*70)
print("📈 الإحصائيات:")
print("="*70)

if all_scores:
    avg_all = sum(all_scores) / len(all_scores)
    print(f"  📊 متوسط المطابقة: {avg_all:.2f}%")
    print(f"  🔝 أعلى مطابقة: {max(all_scores):.2f}%")
    print(f"  🔻 أقل مطابقة: {min(all_scores):.2f}%")
    
    excellent = sum(1 for s in all_scores if s >= 90)
    good = sum(1 for s in all_scores if 70 <= s < 90)
    okay = sum(1 for s in all_scores if 50 <= s < 70)
    poor = sum(1 for s in all_scores if s < 50)
    
    print(f"\n  📊 التوزيع:")
    print(f"    ⭐⭐⭐⭐⭐ ممتاز (90%+):     {excellent} ({100*excellent/len(all_scores):.1f}%)")
    print(f"    ⭐⭐⭐⭐   جيد (70-90%):   {good} ({100*good/len(all_scores):.1f}%)")
    print(f"    ⭐⭐⭐     حسن (50-70%):   {okay} ({100*okay/len(all_scores):.1f}%)")
    print(f"    ⭐       ضعيف (<50%):    {poor} ({100*poor/len(all_scores):.1f}%)")

# 6. أفضل الأسهم
print("\n" + "="*70)
print("🏆 أفضل 20 سهم مطابقة:")
print("="*70)

df_results = pd.DataFrame(results)
df_results_sorted = df_results.sort_values('avg_match', ascending=False)

print(f"\n{'#':<3} {'Symbol':<10} {'Avg %':<10} {'Best %':<10} {'Pattern':<15}")
print("-" * 70)

for idx, (_, row) in enumerate(df_results_sorted.head(20).iterrows(), 1):
    print(f"{idx:<3} {row['symbol']:<10} {row['avg_match']:>8.1f}% {row['best_match']:>8.1f}% {row['best_pattern']:<15}")

# 7. حفظ النتائج
output_file = 'matching_results_optimized.csv'
df_results_sorted.to_csv(output_file, index=False)
print(f"\n✅ تم حفظ النتائج: {output_file}")

elapsed = time.time() - start_time
print(f"\n⏱️  الوقت المستغرق: {elapsed:.2f} ثانية")
print("\n✅ اكتمل الاختبار بنجاح!")
