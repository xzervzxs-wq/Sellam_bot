import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime

# 1. جلب شموع ATAI من Yahoo Finance
print("="*60)
print("📊 جلب شموع ATAI من Yahoo Finance...")
print("="*60)

ticker = yf.Ticker("ATAI")
df = ticker.history(period="5d", interval="5m")

if df.index.tz is None:
    df.index = df.index.tz_localize('America/New_York')
else:
    df.index = df.index.tz_convert('America/New_York')

df.columns = df.columns.str.lower()

# فلترة شموع اليوم
ny_tz = pytz.timezone('America/New_York')
today = datetime.now(ny_tz).date()
df_today = df[df.index.date == today]

print(f"\n��️ آخر 6 شموع لـ ATAI (اليوم {today}):")
last_6 = df_today.tail(6)[['open', 'high', 'low', 'close']]
print(last_6.to_string())

# حساب نسب التغير
print("\n📈 تحليل الشموع:")
for i, (idx, row) in enumerate(last_6.iterrows()):
    body_pct = (row['close'] - row['open']) / row['open'] * 100
    direction = "🟢 صاعدة" if body_pct > 0 else "🔴 هابطة"
    print(f"  شمعة {i+1}: {direction} ({body_pct:+.2f}%)")

# 2. جلب نمط WIT من الملف
print("\n" + "="*60)
print("📜 جلب نمط WIT من successful_candles.csv...")
print("="*60)

patterns_df = pd.read_csv('successful_candles.csv')
patterns_df.columns = patterns_df.columns.str.strip().str.lower()

# البحث عن WIT
wit_pattern = patterns_df[patterns_df['symbol'].str.upper() == 'WIT']

if wit_pattern.empty:
    print("❌ لم يتم العثور على نمط WIT!")
    # اطبع كل الأنماط المتاحة
    print("\n📋 الأنماط المتاحة:")
    print(patterns_df['symbol'].unique())
else:
    wit_pattern = wit_pattern.sort_values('time').head(6)
    print(f"\n🕯️ شموع نمط WIT:")
    print(wit_pattern[['open', 'high', 'low', 'close']].to_string())
    
    print("\n📈 تحليل نمط WIT:")
    for i, (idx, row) in enumerate(wit_pattern.iterrows()):
        body_pct = (row['close'] - row['open']) / row['open'] * 100
        direction = "🟢 صاعدة" if body_pct > 0 else "🔴 هابطة"
        print(f"  شمعة {i+1}: {direction} ({body_pct:+.2f}%)")

# 3. مقارنة بصرية
print("\n" + "="*60)
print("⚖️ المقارنة البصرية:")
print("="*60)

def normalize(arr):
    arr = np.array(arr, dtype=float)
    min_v = arr.min()
    max_v = arr.max()
    if max_v == min_v:
        return np.zeros_like(arr)
    return (arr - min_v) / (max_v - min_v)

# ATAI normalized
atai_candles = last_6[['open', 'high', 'low', 'close']].values
atai_norm = normalize(atai_candles)

print("\n🔵 ATAI (مُطَبَّع 0-1):")
for i, row in enumerate(atai_norm):
    print(f"  [{row[0]:.2f}, {row[1]:.2f}, {row[2]:.2f}, {row[3]:.2f}]")

if not wit_pattern.empty:
    wit_candles = wit_pattern[['open', 'high', 'low', 'close']].values
    wit_norm = normalize(wit_candles)
    
    print("\n🟡 WIT (مُطَبَّع 0-1):")
    for i, row in enumerate(wit_norm):
        print(f"  [{row[0]:.2f}, {row[1]:.2f}, {row[2]:.2f}, {row[3]:.2f}]")
    
    # حساب الفرق
    if atai_norm.shape == wit_norm.shape:
        diff = np.mean(np.abs(atai_norm - wit_norm))
        similarity = 100 * (1 - diff)
        print(f"\n📊 نسبة التشابه الشكلي: {similarity:.1f}%")
        print(f"   (الفرق المتوسط: {diff:.3f})")
