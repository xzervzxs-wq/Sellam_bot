import pandas as pd
import warnings
from datetime import datetime
import pytz

warnings.simplefilter(action='ignore', category=FutureWarning)

# =========================================================
# قراءة البيانات الأصلية (شموع 1-دقيقة)
# =========================================================
print("="*80)
print("🔄 تحويل شموع 1-دقيقة إلى شموع 5-دقائق + تحليل السلم")
print("="*80)

df = pd.read_csv("friday_results.csv")

print(f"\n📊 البيانات الأصلية:")
print(f"   - عدد الأسهم: {df['symbol'].nunique()}")
print(f"   - إجمالي الشموع: {len(df)}")
print(f"   - فترة زمنية: 1-دقيقة\n")

# =========================================================
# تحويل datetime إلى datetime object مع timezone
# =========================================================
df['datetime'] = pd.to_datetime(df['datetime'])

# =========================================================
# دالة تجميع شموع 5-دقائق
# =========================================================
def aggregate_to_5min(group):
    """تجميع شموع 1-دقيقة إلى 5-دقائق"""
    if group.empty:
        return pd.DataFrame()
    
    # ترتيب حسب الوقت
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
    
    # إضافة معلومات
    group_5min['symbol'] = group.iloc[0]['symbol']
    group_5min['datetime'] = group_5min.index
    group_5min['time'] = group_5min.index.strftime('%Y-%m-%d %H:%M:%S')
    
    return group_5min.reset_index(drop=True)

# =========================================================
# تجميع جميع الأسهم
# =========================================================
print("🔄 جاري تجميع الشموع...")

all_5min = []
for symbol in df['symbol'].unique():
    stock_data = df[df['symbol'] == symbol]
    candles_5min = aggregate_to_5min(stock_data)
    
    if not candles_5min.empty:
        all_5min.append(candles_5min)
        print(f"   ✅ {symbol}: {len(candles_5min)} شمعة 5-دقائق")

df_5min = pd.concat(all_5min, ignore_index=True)

print(f"\n✅ تم التحويل بنجاح!")
print(f"   - إجمالي شموع 5-دقائق: {len(df_5min)}")
print(f"   - متوسط شموع السهم: {len(df_5min) // df_5min['symbol'].nunique()}")

# =========================================================
# استراتيجية السلم على شموع 5-دقائق
# =========================================================
def check_ladder_strategy(group):
    """فحص نمط السلم على شموع 5-دقائق"""
    if len(group) < 3:
        return []
    
    results = []
    group = group.sort_values('datetime')
    
    # خذ آخر 3 شموع فقط
    recent = group.tail(3)
    
    if len(recent) < 3:
        return []
    
    candles = recent.to_dict('records')
    c1 = candles[0]
    c2 = candles[1]
    c3 = candles[2]
    
    symbol = group.iloc[0]['symbol']
    
    # الشرط 1: التحقق من الشمعتين الأخيرتين خضراوتين
    if not (c2['close'] > c2['open'] and c3['close'] > c3['open']):
        return []
    
    # الشرط 2: التحقق من القمم الصاعدة
    if not (c3['high'] >= c2['high'] and c2['high'] >= c1['high']):
        return []
    
    # الشرط 3: التحقق من القيعان الصاعدة
    if not (c3['low'] >= c2['low'] and c2['low'] >= c1['low']):
        return []
    
    # الشرط 4: فلتر الذيل الحرج
    c3_body = abs(c3['close'] - c3['open'])
    c3_wick_top = c3['high'] - max(c3['close'], c3['open'])
    
    if c3_wick_top > (c3_body * 2):
        return []
    
    # وصلنا هنا = إشارة صحيحة!
    current_price = c3['close']
    high_of_day = c3['high']
    
    # حساب السيولة (حجم / فلوت متوقع)
    total_volume = c1['volume'] + c2['volume'] + c3['volume']
    estimated_float = 12_000_000
    rotation_pct = (total_volume / estimated_float) * 100
    
    if rotation_pct > 20:
        liquidity_msg = "🔥🔥 انفجار"
    elif rotation_pct > 10:
        liquidity_msg = "🔥 نار"
    elif rotation_pct > 2:
        liquidity_msg = "✅ جيد"
    else:
        liquidity_msg = "💤 ضعيف"
    
    # قوة الإشارة
    high_range = c3['high'] - c1['high']
    low_range = c3['low'] - c1['low']
    strength = min(100, int(((high_range + low_range) / (c1['close'] * 2)) * 100))
    
    # نوع الإشارة
    price_diff_pct = ((high_of_day - current_price) / high_of_day) * 100
    
    if price_diff_pct < 0.5:
        action = "🚀 دخول مباشر"
        entry_price = current_price
    else:
        action = "✋ أمر معلق"
        entry_price = high_of_day + 0.01
    
    price_change = ((c3['close'] - c1['close']) / c1['close']) * 100
    
    results.append({
        'symbol': symbol,
        'signal_time': c3['datetime'],
        'strength': max(strength, 30),
        'current_price': current_price,
        'high_price': high_of_day,
        'entry_price': entry_price,
        'action': action,
        'liquidity': liquidity_msg,
        'rotation_pct': rotation_pct,
        'price_change': price_change,
        'volume_5min': int(total_volume),
        'c1_open': c1['open'],
        'c1_close': c1['close'],
        'c1_high': c1['high'],
        'c1_low': c1['low'],
        'c2_open': c2['open'],
        'c2_close': c2['close'],
        'c2_high': c2['high'],
        'c2_low': c2['low'],
        'c3_open': c3['open'],
        'c3_close': c3['close'],
        'c3_high': c3['high'],
        'c3_low': c3['low'],
    })
    
    return results

# =========================================================
# تحليل جميع الأسهم
# =========================================================
print("\n" + "="*80)
print("🚀 تحليل نمط السلم على شموع 5-دقائق")
print("="*80 + "\n")

all_signals = []

for symbol in df_5min['symbol'].unique():
    stock_data = df_5min[df_5min['symbol'] == symbol]
    signals = check_ladder_strategy(stock_data)
    
    if signals:
        all_signals.extend(signals)
        print(f"✅ {symbol}: إشارة قوية!")

# =========================================================
# عرض النتائج
# =========================================================
print(f"\n{'='*80}")
print(f"📊 النتائج النهائية:")
print(f"{'='*80}\n")

if all_signals:
    df_signals = pd.DataFrame(all_signals)
    df_signals = df_signals.sort_values('strength', ascending=False)
    
    print(f"✅ تم العثور على {len(df_signals)} إشارة سلم صاعد\n")
    
    print(f"{'Symbol':<10} {'Price':<10} {'Entry':<10} {'Action':<15} {'Strength':<10} {'Rotation%':<12} {'Liquidity':<15}")
    print("-" * 95)
    
    for _, row in df_signals.iterrows():
        strength_bar = "🔥" * int(row['strength'] / 20) if row['strength'] > 50 else "⭐" * int(row['strength'] / 33)
        print(f"{row['symbol']:<10} ${row['current_price']:<9.3f} ${row['entry_price']:<9.3f} {row['action']:<15} {row['strength']:>6.0f}% {strength_bar:<5} {row['rotation_pct']:>8.1f}% {row['liquidity']:<15}")
    
    # حفظ النتائج
    output_file = "friday_results.csv"
    df_signals.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ تم حفظ النتائج في: {output_file}")
    
    print(f"\n📈 إحصائيات:")
    print(f"   - متوسط القوة: {df_signals['strength'].mean():.1f}%")
    print(f"   - متوسط التغير: {df_signals['price_change'].mean():.2f}%")
    print(f"   - متوسط نسبة الدوران: {df_signals['rotation_pct'].mean():.2f}%")
    
    positive = len(df_signals[df_signals['price_change'] > 0])
    print(f"   - أسهم بارتفاع: {positive}/{len(df_signals)}")
    
else:
    print("⚠️ لم يتم العثور على أي إشارات سلم صاعد")
    print("\n💡 التفصيل:")
    print(f"   - عدد الأسهم المحللة: {df_5min['symbol'].nunique()}")
    print(f"   - إجمالي شموع 5-دقائق: {len(df_5min)}")

print(f"\n{'='*80}\n")
