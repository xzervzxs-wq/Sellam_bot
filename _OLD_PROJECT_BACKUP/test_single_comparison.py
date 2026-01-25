#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار Strict Rhythm - نسخة بسيطة جداً بدون حلقات معقدة
"""
import pandas as pd
import time

start = time.time()
print("Starting test...")

# 1. Load data
df_test = pd.read_csv('test_candles_20251223_170248.csv')
df_patterns = pd.read_csv('successful_candles.csv')

print(f"✅ Loaded test: {len(df_test)} rows")
print(f"✅ Loaded patterns: {len(df_patterns)} rows")

# 2. Extract DNA for one stock (KODK)
def extract_dna(candles):
    """Extract DNA from 6 candles"""
    dna = []
    for c in candles:
        o, h, l, cl = c[0], c[1], c[2], c[3]
        tr = h - l
        if tr == 0: tr = 0.0001
        dna.append({
            'body_r': abs(cl - o) / tr,
            'dir': 1 if cl >= o else -1,
            'size': (abs(cl - o) / o * 100) if o > 0 else 0
        })
    return dna

# Get test data
test_kodk = df_test[df_test['symbol'] == 'KODK'].head(6)[['open', 'high', 'low', 'close']].values.tolist()
pattern_kodk = df_patterns[df_patterns['symbol'] == 'KODK'].head(6)[['open', 'high', 'low', 'close']].values.tolist()

print(f"\nTest KODK: {len(test_kodk)} candles")
print(f"Pattern KODK: {len(pattern_kodk)} candles")

# Extract DNA
test_dna = extract_dna(test_kodk)
pattern_dna = extract_dna(pattern_kodk)

print(f"\n✅ Extracted DNA")

# 3. Compare
def similarity(curr, pattern):
    if len(curr) != len(pattern): return 0
    score = 100.0
    for c, p in zip(curr, pattern):
        if c['dir'] != p['dir']: score -= 50
        size_diff = abs(c['size'] - p['size'])
        if size_diff > 0.4: score -= (size_diff - 0.4) * 20
    return max(0, score)

sim = similarity(test_dna, pattern_dna)
print(f"\nKODK vs KODK: {sim:.1f}%")

# Compare with ONE other pattern (INSM)
pattern_insm = df_patterns[df_patterns['symbol'] == 'INSM'].head(6)[['open', 'high', 'low', 'close']].values.tolist()
insm_dna = extract_dna(pattern_insm)
sim_insm = similarity(test_dna, insm_dna)
print(f"KODK vs INSM: {sim_insm:.1f}%")

elapsed = time.time() - start
print(f"\n⏱️  Elapsed: {elapsed:.2f}s")
