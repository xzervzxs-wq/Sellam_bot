import pandas as pd
import glob
import os
from datetime import datetime

print("="*80)
print("🧪 BACKTEST LADDER STRATEGY - PROPER IMPLEMENTATION")
print("="*80)

# =========================================================
# البحث عن جميع ملفات CSV المحملة
# =========================================================
print("\n🔍 جاري البحث عن ملفات CSV...")

csv_files = glob.glob("finviz_eodhd_candles_*.csv")
csv_files.sort()

if not csv_files:
    print("❌ لم يتم العثور على ملفات CSV")
    exit(1)

print(f"✅ تم العثور على {len(csv_files)} ملف CSV\n")
for f in csv_files:
    print(f"   📄 {f}")

# =========================================================
# دمج جميع الملفات
# =========================================================
print(f"\n📊 جاري دمج البيانات...")

all_data = []
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    all_data.append(df)
    print(f"   ✅ {csv_file}: {len(df)} شمعة")

df_combined = pd.concat(all_data, ignore_index=True)
print(f"\n✅ إجمالي الشموع: {len(df_combined)}")
print(f"✅ عدد الأسهم الفريدة: {df_combined['symbol'].nunique()}")

# =========================================================
# استراتيجية السلم الصاعد - الشروط الدقيقة
# =========================================================
def check_ladder_strategy(group):
    """
    فحص نمط السلم الصاعد - الشروط الدقيقة:
    1. آخر 3 شموع فقط
    2. قمم صاعدة: High3 >= High2 >= High1
    3. قيعان صاعدة: Low3 >= Low2 >= Low1
    4. فلتر الذيل الحرج: الشمعة الأخيرة ما تقل أكثر من 2x الجسم
    5. حساب السيولة للتصنيف
    """
    if len(group) < 3:
        return []
    
    results = []
    group = group.sort_values('time')
    
    # خذ آخر 3 شموع فقط
    recent = group.tail(3)
    
    if len(recent) < 3:
        return []
    
    candles = recent.to_dict('records')
    c1 = candles[0]  # الشمعة الأولى
    c2 = candles[1]  # الشمعة الثانية
    c3 = candles[2]  # الشمعة الثالثة (الحالية)
    
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
    
    # الشرط 4: فلتر الذيل الحرج (أهم شرط!)
    # الشمعة الأخيرة ما تقل أكثر من 2x الجسم
    c3_body = abs(c3['close'] - c3['open'])
    c3_wick_top = c3['high'] - max(c3['close'], c3['open'])
    
    if c3_wick_top > (c3_body * 2):
        # ذيل طويل = Shooting Star = بائعون قويون = رفض
        return []
    
    # وصلنا هنا = إشارة صحيحة!
    # الآن نحسب السيولة والسعر
    
    current_price = c3['close']
    high_of_day = c3['high']
    
    # حساب السيولة (تقديري بدون float حقيقي)
    # نستخدم الحجم بدل الفلوت للتصنيف
    total_volume = c1['volume'] + c2['volume'] + c3['volume']
    
    # تقدير الفلوت المعقول لـ penny stocks (10-15M)
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
    
    # حساب قوة الإشارة
    high_range = c3['high'] - c1['high']
    low_range = c3['low'] - c1['low']
    strength = min(100, int(((high_range + low_range) / (c1['close'] * 2)) * 100))
    
    # تحديد نوع الإشارة
    price_diff_pct = ((high_of_day - current_price) / high_of_day) * 100
    
    if price_diff_pct < 0.5:
        # قريب جداً من القمة = دخول مباشر
        action = "🚀 دخول مباشر"
        entry_price = current_price
    else:
        # نزل شوي = أمر معلق
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
        'volume': int(total_volume),
        'c1_open': c1['open'],
        'c1_close': c1['close'],
        'c2_open': c2['open'],
        'c2_close': c2['close'],
        'c3_open': c3['open'],
        'c3_close': c3['close'],
    })
    
    return results

# =========================================================
# تحليل كل سهم
# =========================================================
print(f"\n🚀 جاري تحليل الأسهم...")
print("-" * 80)

all_signals = []

for symbol in df_combined['symbol'].unique():
    stock_data = df_combined[df_combined['symbol'] == symbol]
    signals = check_ladder_strategy(stock_data)
    
    if signals:
        all_signals.extend(signals)
        print(f"✅ {symbol}: إشارة قوية!")

# =========================================================
# عرض النتائج
# =========================================================
print(f"\n\n{'='*80}")
print(f"📊 النتائج النهائية:")
print(f"{'='*80}\n")

if all_signals:
    df_signals = pd.DataFrame(all_signals)
    df_signals = df_signals.sort_values('strength', ascending=False)
    
    print(f"✅ تم العثور على {len(df_signals)} إشارة سلم صاعد\n")
    
    print(f"{'Symbol':<10} {'Price':<10} {'Entry':<10} {'Action':<15} {'Strength':<10} {'Rotation%':<12} {'Liquidity':<15}")
    print("-" * 90)
    
    for _, row in df_signals.iterrows():
        strength_bar = "🔥" * int(row['strength'] / 20) if row['strength'] > 50 else "⭐" * int(row['strength'] / 33)
        print(f"{row['symbol']:<10} ${row['current_price']:<9.3f} ${row['entry_price']:<9.3f} {row['action']:<15} {row['strength']:>6.0f}% {strength_bar:<5} {row['rotation_pct']:>8.1f}% {row['liquidity']:<15}")
    
    # حفظ النتائج
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"backtest_signals_{timestamp}.csv"
    df_signals.to_csv(result_file, index=False, encoding='utf-8')
    
    print(f"\n✅ تم حفظ النتائج في: {result_file}")
    
    # ملخص إحصائي
    print(f"\n📈 إحصائيات:")
    print(f"   - متوسط القوة: {df_signals['strength'].mean():.1f}%")
    print(f"   - أقوى إشارة: {df_signals['strength'].max():.1f}%")
    print(f"   - أضعف إشارة: {df_signals['strength'].min():.1f}%")
    print(f"   - متوسط التغير: {df_signals['price_change'].mean():.2f}%")
    print(f"   - متوسط نسبة الدوران: {df_signals['rotation_pct'].mean():.2f}%")
    
    # عدد الأسهم بإشارات إيجابية
    positive = len(df_signals[df_signals['price_change'] > 0])
    print(f"   - أسهم بارتفاع: {positive}/{len(df_signals)}")
    
    # عدد الإشارات حسب النوع
    market_orders = len(df_signals[df_signals['action'].str.contains('مباشر')])
    pending_orders = len(df_signals[df_signals['action'].str.contains('معلق')])
    print(f"   - دخول مباشر: {market_orders}")
    print(f"   - أمر معلق: {pending_orders}")
    
else:
    print("⚠️ لم يتم العثور على أي إشارات سلم صاعد")

print(f"\n{'='*80}\n")
