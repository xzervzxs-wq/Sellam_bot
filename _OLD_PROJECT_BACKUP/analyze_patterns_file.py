import pandas as pd
import numpy as np
import os

PATTERNS_FILE = 'successful_candles.csv'

# قراءة الأنماط الناجحة
df = pd.read_csv(PATTERNS_FILE)
df.columns = df.columns.str.strip().str.lower()

print("=" * 90)
print("📊 تحليل ملف الأنماط الناجحة (successful_candles.csv)")
print("=" * 90)

# عدد الأسهم
unique_symbols = df['symbol'].unique()
print(f"\n📈 عدد الأسهم: {len(unique_symbols)}")
print(f"الأسهم: {list(unique_symbols)}")

# تحليل كل نمط
print(f"\n🔬 تحليل تفصيلي لكل نمط:")
print("-" * 90)

pattern_analysis = []

for sym in unique_symbols:
    sym_data = df[df['symbol'] == sym].sort_values('time')
    if len(sym_data) < 6:
        continue
    
    candles = sym_data.iloc[:6][['open', 'high', 'low', 'close']].values
    
    # حساب الخصائص
    directions = [1 if c[3]>=c[0] else -1 for c in candles]
    bodies = [abs(c[3]-c[0])/c[0]*100 for c in candles]
    
    dir_pattern = ''.join(['↑' if d == 1 else '↓' for d in directions])
    up_count = sum(1 for d in directions if d == 1)
    avg_body = np.mean(bodies)
    
    # الحركة الكلية (من فتح أول شمعة إلى إغلاق آخر شمعة)
    total_move = (candles[-1][3] - candles[0][0]) / candles[0][0] * 100
    
    pattern_analysis.append({
        'symbol': sym,
        'dir_pattern': dir_pattern,
        'up_count': up_count,
        'avg_body': avg_body,
        'total_move': total_move
    })
    
    print(f"{sym:<10} | Pattern: {dir_pattern} | Up: {up_count}/6 | Avg Body: {avg_body:.2f}% | Total Move: {total_move:+.2f}%")

df_analysis = pd.DataFrame(pattern_analysis)

print(f"\n🎯 توزيع الأنماط:")
print("-" * 90)
print(df_analysis['dir_pattern'].value_counts())

print(f"\n📊 إحصائيات:")
print(f"متوسط عدد الشموع الصاعدة: {df_analysis['up_count'].mean():.1f}")
print(f"متوسط حجم الجسم: {df_analysis['avg_body'].mean():.2f}%")
print(f"متوسط الحركة الكلية: {df_analysis['total_move'].mean():.2f}%")

# الأنماط الأكثر شيوعاً
print(f"\n🔥 الأنماط الأكثر شيوعاً (قد تكون الأفضل للمطابقة):")
print("-" * 90)
common_patterns = df_analysis['dir_pattern'].value_counts().head(5)
for pattern, count in common_patterns.items():
    symbols = df_analysis[df_analysis['dir_pattern'] == pattern]['symbol'].tolist()
    print(f"   {pattern}: {count} أسهم ({', '.join(symbols)})")
