import pandas as pd
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# =========================================================
# قراءة البيانات الأصلية (شموع 1-دقيقة)
# =========================================================
print("="*80)
print("🔄 تحويل شموع 1-دقيقة إلى شموع 5-دقائق")
print("="*80)

df = pd.read_csv("friday_results.csv")

print(f"\n📊 البيانات الأصلية:")
print(f"   - عدد الشموع: {len(df)}")
print(f"   - عدد الأسهم: {df['symbol'].nunique()}")

# تحويل datetime
df['datetime'] = pd.to_datetime(df['datetime'])

# =========================================================
# دالة تجميع شموع 5-دقائق صحيحة
# =========================================================
def aggregate_to_5min(group):
    """تجميع شموع 1-دقيقة إلى شموع 5-دقائق حقيقية"""
    if group.empty:
        return pd.DataFrame()
    
    group = group.sort_values('datetime')
    
    # تجميع كل 5 دقائق
    group_5min = group.set_index('datetime').resample('5min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna(subset=['close'])
    
    if group_5min.empty:
        return pd.DataFrame()
    
    group_5min['symbol'] = group.iloc[0]['symbol']
    group_5min['datetime'] = group_5min.index
    group_5min['time'] = group_5min.index.strftime('%Y-%m-%d %H:%M:%S')
    
    # ترتيب الأعمدة
    group_5min = group_5min[['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'time']]
    
    return group_5min.reset_index(drop=True)

# =========================================================
# تجميع جميع الأسهم
# =========================================================
print("\n🔄 جاري تجميع الشموع...")

all_5min = []
for symbol in sorted(df['symbol'].unique()):
    stock_data = df[df['symbol'] == symbol]
    candles_5min = aggregate_to_5min(stock_data)
    
    if not candles_5min.empty:
        all_5min.append(candles_5min)
        print(f"   ✅ {symbol}: {len(candles_5min)} شمعة 5-دقائق")

df_5min = pd.concat(all_5min, ignore_index=True)
df_5min = df_5min.sort_values(['symbol', 'datetime']).reset_index(drop=True)

# =========================================================
# حفظ الملف
# =========================================================
output_file = "friday_results.csv"
df_5min.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n✅ تم حفظ شموع 5-دقائق في: {output_file}")
print(f"   - عدد الشموع: {len(df_5min)}")
print(f"   - عدد الأسهم: {df_5min['symbol'].nunique()}")
print(f"   - متوسط شموع السهم: {len(df_5min) // df_5min['symbol'].nunique()}")

print("\n" + "="*80)
