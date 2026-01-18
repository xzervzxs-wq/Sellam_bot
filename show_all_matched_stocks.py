#!/usr/bin/env python3
"""تقرير مفصل بجميع الأسهم التي طابقت مع التواريخ"""

import pandas as pd
import numpy as np
import os

def load_successful_patterns():
    """تحميل الأنماط"""
    if not os.path.exists("successful_candles.csv"):
        return {}, {}
    
    try:
        df = pd.read_csv("successful_candles.csv")
        df.columns = df.columns.str.strip().str.lower()
        
        patterns = {}
        pattern_metrics = {}
        
        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 6:
                candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
                patterns[symbol] = normalize_pattern(candles)
                
                bodies = []
                for i in range(len(candles)):
                    body = abs(candles[i][3] - candles[i][0]) / candles[i][0] * 100
                    bodies.append(body)
                
                pattern_metrics[symbol] = {
                    'avg_body': np.mean(bodies),
                    'bodies': bodies
                }
        
        return patterns, pattern_metrics
    except:
        return {}, {}

def normalize_pattern(candles):
    candles = np.array(candles, dtype=float)
    min_val = np.min(candles)
    max_val = np.max(candles)
    if max_val == min_val: 
        return np.zeros_like(candles)
    return (candles - min_val) / (max_val - min_val)

def get_candle_metrics(candles):
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

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    if not reference_patterns: 
        return 0, "None"
    
    current_fingerprint = normalize_pattern(current_candles)
    current_metrics = get_candle_metrics(current_candles)
    
    current_bodies = [abs(current_candles[i][3] - current_candles[i][0]) / current_candles[i][0] * 100 
                     for i in range(len(current_candles))]
    current_avg_body = np.mean(current_bodies)
    
    best_score = 0
    best_name = "None"
    
    for name, ref_fingerprint in reference_patterns.items():
        if current_fingerprint.shape != ref_fingerprint.shape: 
            continue
        
        diff = np.mean(np.abs(current_fingerprint - ref_fingerprint))
        pattern_score = 100 * (1 - diff)
        
        volatility_diffs = [m['volatility'] for m in current_metrics]
        avg_volatility = np.mean(volatility_diffs) if volatility_diffs else 1.0
        volatility_match = max(0, 100 - (abs(avg_volatility - 1.2) * 5))
        
        if name in pattern_metrics:
            ref_avg_body = pattern_metrics[name]['avg_body']
            body_diff = abs(current_avg_body - ref_avg_body)
            body_match = max(0, 100 - (body_diff * 50))
        else:
            body_match = 50
        
        final_score = (
            pattern_score * 0.60 +
            volatility_match * 0.25 +
            body_match * 0.15
        )
        
        if final_score > best_score:
            best_score = final_score
            best_name = name
            
    return best_score, best_name

def test_300_stocks():
    """اختبر على ملف الـ 300 سهم وأعرض كل التفاصيل"""
    
    # تحميل الأنماط
    patterns, pattern_metrics = load_successful_patterns()
    if not patterns:
        print("❌ فشل تحميل الأنماط")
        return
    
    # اختبر الملف
    test_file = "finviz_eodhd_candles_20251223_015906.csv"
    
    if not os.path.exists(test_file):
        print(f"❌ الملف {test_file} غير موجود")
        return
    
    df = pd.read_csv(test_file)
    df.columns = df.columns.str.strip().str.lower()
    
    matched_stocks = []
    rejected_stocks = []
    
    print("\n" + "="*100)
    print("🎯 جميع الأسهم التي طابقت (مع التواريخ)")
    print("="*100 + "\n")
    
    for ticker in sorted(df['symbol'].unique()):
        ticker_str = str(ticker).upper()
        ticker_data = df[df['symbol'].str.upper() == ticker_str].copy()
        
        if len(ticker_data) < 6:
            rejected_stocks.append((ticker, "شموع قليلة", "N/A"))
            continue
        
        ticker_data = ticker_data.sort_values('date')
        first_6 = ticker_data.iloc[:6]
        
        date_str = f"{first_6.iloc[0]['date']}"
        
        # احسب متوسط الأجسام
        bodies = []
        for i in range(len(first_6)):
            row = first_6.iloc[i]
            body = abs(float(row['close']) - float(row['open'])) / float(row['open']) * 100
            bodies.append(body)
        
        avg_body = np.mean(bodies)
        
        # تجميد؟
        if avg_body < 0.15:
            rejected_stocks.append((ticker, f"🥶 متجمدة ({avg_body:.3f}%)", date_str))
            continue
        
        # احسب التطابق
        candles = first_6[['open', 'high', 'low', 'close']].values.astype(float)
        match_score, match_name = calculate_similarity(candles, patterns, pattern_metrics)
        
        # جمّع النتائج
        if match_score >= 85:
            status = "💎 ماسة"
        elif match_score >= 75:
            status = "🔥 ذهب"
        elif match_score >= 60:
            status = "⚪ فضة"
        else:
            status = "❌ مرفوض"
            rejected_stocks.append((ticker, f"{status} ({match_score:.1f}%)", date_str))
            continue
        
        matched_stocks.append((ticker, status, match_score, match_name, avg_body, date_str))
    
    # اعرض النتائج
    print("\n📊 الأسهم التي طابقت:")
    print("-" * 100)
    print(f"{'#':<4} {'السهم':<8} {'النوع':<12} {'التطابق':<10} {'النمط':<8} {'الجسم':<10} {'التاريخ':<15}")
    print("-" * 100)
    
    for i, (ticker, status, score, pattern, body, date) in enumerate(matched_stocks, 1):
        print(f"{i:<4} {ticker:<8} {status:<12} {score:>7.1f}% {pattern:<8} {body:>8.3f}% {date:<15}")
    
    print("\n" + "="*100)
    print(f"✅ إجمالي المطابقات: {len(matched_stocks)} سهم")
    print(f"❌ إجمالي المرفوضة: {len(rejected_stocks)} سهم")
    print("="*100 + "\n")
    
    # تحقق من التواريخ
    all_dates = set()
    for ticker, status, score, pattern, body, date in matched_stocks:
        all_dates.add(date)
    
    print("📅 التواريخ الموجودة في النتائج:")
    for date in sorted(all_dates):
        count = sum(1 for t, s, sc, p, b, d in matched_stocks if d == date)
        print(f"   • {date}: {count} سهم")
    
    print("\n" + "="*100)
    print("📋 تفصيل الأسهم حسب النوع:")
    print("="*100 + "\n")
    
    # ماسات
    diamonds = [(t, sc, p, b, d) for t, st, sc, p, b, d in matched_stocks if sc >= 85]
    print(f"\n💎 الماسات ({len(diamonds)} سهم):")
    print("-" * 100)
    for i, (ticker, score, pattern, body, date) in enumerate(diamonds, 1):
        print(f"  {i:2}. {ticker:<8} - {score:>6.1f}% (مع {pattern:<6}) - الجسم: {body:.3f}% - {date}")
    
    # ذهب
    gold = [(t, sc, p, b, d) for t, st, sc, p, b, d in matched_stocks if 75 <= sc < 85]
    print(f"\n🔥 الذهب ({len(gold)} سهم):")
    print("-" * 100)
    for i, (ticker, score, pattern, body, date) in enumerate(gold, 1):
        print(f"  {i:2}. {ticker:<8} - {score:>6.1f}% (مع {pattern:<6}) - الجسم: {body:.3f}% - {date}")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    test_300_stocks()
