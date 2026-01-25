#!/usr/bin/env python3
"""
اختبار استراتيجية السلم الصاعد المعتمدة على شموع 19 سبتمبر 2024
الدالة مأخوذة من reshah_backtst (النسخة الموزونة بالذهب)
"""
import pandas as pd
import warnings
from datetime import datetime
import os
import json

warnings.simplefilter(action='ignore', category=FutureWarning)

# =========================================================
# 1. إعدادات
# =========================================================
CANDLES_FILE = "test_candles_dec19.csv"
FLOAT_CACHE_FILE = "float_cache.json"

# =========================================================
# 2. أدوات مساعدة
# =========================================================
def fmt_shares(n):
    if not isinstance(n, (int, float)): return "غير متاح"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000: return f"{n/1_000:.1f}K".replace(".0K", "K")
    return str(int(n))

def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f: return json.load(f)
        except: return {}
    return {}

# تحميل الكاش
float_data_store = load_json_file(FLOAT_CACHE_FILE)

def get_float_shares(symbol):
    """جلب الفلوت من الكاش"""
    global float_data_store
    val = float_data_store.get(symbol)
    if isinstance(val, dict):
        val = val.get('float', val.get('value', 0))
    if isinstance(val, (int, float)) and val > 0:
        return val
    return 0

# =========================================================
# 3. تحميل الشموع من الملف
# =========================================================
def load_candles():
    """تحميل شموع الاختبار من CSV"""
    print(f"📂 تحميل الشموع من {CANDLES_FILE}...")
    
    if not os.path.exists(CANDLES_FILE):
        print(f"❌ الملف غير موجود: {CANDLES_FILE}")
        return None
    
    df = pd.read_csv(CANDLES_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    symbols = df['symbol'].unique()
    print(f"✅ تم تحميل {len(df)} شمعة لـ {len(symbols)} سهم")
    
    return df

def get_symbol_candles(df, symbol):
    """استخراج شموع سهم معين"""
    symbol_df = df[df['symbol'] == symbol].copy()
    symbol_df = symbol_df.set_index('date').sort_index()
    symbol_df.columns = symbol_df.columns.str.capitalize()
    return symbol_df

# =========================================================
# 4. تحليل السلم الصاعد (نسخة موزونة بالذهب - من reshah_backtst)
# =========================================================
def check_ladder_pattern(df_window):
    """
    الدالة المعتمدة من الملف الأصلي reshah_backtst
    نسخة موزونة بالذهب - تعمل بنجاح!
    """
    # نحتاج 3 شمعات على الأقل
    if len(df_window) < 3:
        return False, 0, "بيانات غير كافية", 0, False

    candles = [row for _, row in df_window.iterrows()]

    start_price = float(candles[0]['Open'])
    current_price = float(candles[-1]['Close'])

    # 1. شرط مبدئي: لازم السعر الحالي أعلى من البداية
    if current_price <= start_price:
        return False, 0, "السعر لم يصعد", 0, False

    highest_high = float(candles[0]['High'])
    prev_low = float(candles[0]['Low'])
    prev_close = float(candles[0]['Close'])

    stagnation_count = 0  # عداد الملل
    new_highs_count = 0
    valid_candles = 0

    for i in range(1, len(candles)):
        row = candles[i]
        c_close = float(row['Close'])
        c_high = float(row['High'])
        c_low = float(row['Low'])
        c_open = float(row['Open'])

        body = abs(c_close - c_open)
        upper_wick = c_high - max(c_open, c_close)

        # 🟢 منطق القمة والركود (التعديل الذكي لـ LPCN)
        if c_high > highest_high:
            highest_high = c_high
            new_highs_count += 1
            stagnation_count = 0 # تصفير العداد لأنه اخترق
        else:
            # هنا السر: هل هو ركود "ميت" ولا استراحة "محارب"؟

            # نحسب المسافة من أعلى قمة وصلها
            distance_from_high = (highest_high - c_close) / highest_high

            # إذا السعر قريب جداً من القمة (أقل من 1.5% فرق) نعتبرها استراحة مسموحة
            # ونمشي العداد ببطء شديد (0.5) بدل (1)
            if distance_from_high < 0.015:
                stagnation_count += 0.5
            else:
                stagnation_count += 1 # ركود حقيقي بعيد عن القمة

        # 🛑 حد الطرد (ISPO يوصل هنا بسرعة)
        # رفعناه لـ 3.5 عشان نعطي فرصة للي جالس يجمع عزم
        if stagnation_count >= 3.5:
            return False, 0, "فقد الزخم (ركود طويل)", highest_high, False

        # 🛑 فلتر الكسر (Higher Lows) - بمرونة بسيطة
        # LPCN أحيانا ينزل ذيله شوي، فسمحنا بـ 0.2% سماحية
        if c_close < (prev_low * 0.998):
            return False, 0, f"كسر قاع سابق (شمعة {i+1})", highest_high, False

        # 🛑 فلتر الذيول "الخبيثة" (زي JDST)
        # إذا الذيل العلوي طويل جداً والجسم صغير
        avg_body_ref = abs(prev_close - prev_low) + 0.01
        if upper_wick > body * 2.5 and upper_wick > avg_body_ref * 1.5:
             return False, 0, "ذيل تصريف واضح", highest_high, False

        # تحديث المراجع
        prev_low = c_low
        prev_close = c_close
        valid_candles += 1

    # 🎯 الفحص النهائي الشامل
    # 1. القوة: السعر الحالي قريب من القمة
    distance_from_peak = (highest_high - current_price) / highest_high
    is_pending = False
    
    if current_price < (highest_high * 0.985):
        # بعيد عن القمة - لكن هل صعد أصلاً؟
        total_gain = (highest_high - start_price) / start_price
        if total_gain >= 0.03 and new_highs_count >= 2:
            # صعد بقوة لكن أغلق بعيد → أمر معلق
            is_pending = True
        else:
            return False, 0, "إغلاق ضعيف بعيد عن القمة", highest_high, False

    # 2. النمو: هل تحرك السعر فعلاً؟ (عشان نصيد ISPO لو مشى العداد)
    total_gain_pct = (current_price - start_price) / start_price
    if total_gain_pct < 0.005 and not is_pending: # لازم يكون تحرك 0.5% على الأقل
        return False, 0, "حركة ضعيفة جداً", highest_high, False

    # 3. عدد القمم: لازم سوا قمة جديدة وحدة على الأقل
    if new_highs_count < 1:
        return False, 0, "لم يحقق قمم جديدة", highest_high, False

    strength_pct = int((new_highs_count / len(candles)) * 100)
    # بونص لـ LPCN: إذا الإغلاق قريب من الهاي، عطها 100%
    if current_price >= highest_high * 0.995:
        strength_pct = 95

    return True, strength_pct, "نموذج قوي ومتماسك 🚀", highest_high, is_pending

# =========================================================
# 5. التشغيل الرئيسي
# =========================================================
def main():
    print("=" * 60)
    print("🧪 اختبار استراتيجية السلم الصاعد المعتمدة")
    print("📅 التاريخ: 19 سبتمبر 2024")
    print("⏰ الفترة: 9:30 - 10:00 صباحاً")
    print("🔧 الدالة: النسخة الموزونة بالذهب (من reshah_backtst)")
    print("=" * 60)
    
    # تحميل الشموع
    df = load_candles()
    if df is None:
        return
    
    symbols = df['symbol'].unique()
    
    # نتائج الاختبار
    results = []
    passed = []
    pending = []
    failed = []
    
    print(f"\n🔬 فحص {len(symbols)} سهم...\n")
    print("-" * 60)
    
    for symbol in symbols:
        try:
            symbol_df = get_symbol_candles(df, symbol)
            
            if len(symbol_df) < 3:
                failed.append({
                    'symbol': symbol,
                    'reason': f'شموع قليلة ({len(symbol_df)})',
                    'candles': len(symbol_df)
                })
                print(f"❌ {symbol}: شموع قليلة ({len(symbol_df)})")
                continue
            
            # فحص النمط (الدالة ترجع 5 قيم)
            is_valid, strength, reason, highest_high, is_pending = check_ladder_pattern(symbol_df)
            
            # معلومات إضافية
            open_price = symbol_df['Open'].iloc[0]
            close_price = symbol_df['Close'].iloc[-1]
            high_price = symbol_df['High'].max()
            change_pct = ((close_price - open_price) / open_price) * 100
            float_val = get_float_shares(symbol)
            
            result = {
                'symbol': symbol,
                'open': open_price,
                'close': close_price,
                'high': high_price,
                'highest_high': highest_high,
                'change_pct': change_pct,
                'float': float_val,
                'candles': len(symbol_df),
                'is_valid': is_valid,
                'is_pending': is_pending,
                'strength': strength,
                'reason': reason
            }
            results.append(result)
            
            if is_valid:
                if is_pending:
                    pending.append(result)
                    print(f"⏳ {symbol}: أمر معلق | القوة: {strength}% | التغير: {change_pct:+.2f}% | القمة: ${highest_high:.4f}")
                else:
                    passed.append(result)
                    print(f"✅ {symbol}: نجح | القوة: {strength}% | التغير: {change_pct:+.2f}% | الفلوت: {fmt_shares(float_val)}")
            else:
                failed.append(result)
                print(f"❌ {symbol}: فشل | السبب: {reason}")
                
        except Exception as e:
            failed.append({
                'symbol': symbol,
                'reason': str(e),
                'candles': 0
            })
            print(f"⚠️ {symbol}: خطأ - {e}")
    
    # =========================================================
    # 6. التقرير النهائي
    # =========================================================
    print("\n" + "=" * 60)
    print("📊 التقرير النهائي")
    print("=" * 60)
    
    total_success = len(passed) + len(pending)
    print(f"\n📈 إجمالي الأسهم: {len(symbols)}")
    print(f"✅ اختراق مباشر: {len(passed)}")
    print(f"⏳ أمر معلق: {len(pending)}")
    print(f"❌ فشلت: {len(failed)}")
    print(f"📊 نسبة النجاح: {(total_success/len(symbols)*100):.1f}%")
    
    if passed:
        print("\n" + "-" * 60)
        print("🏆 الأسهم الناجحة (اختراق مباشر):")
        print("-" * 60)
        
        # ترتيب حسب القوة
        passed_sorted = sorted(passed, key=lambda x: x['strength'], reverse=True)
        
        for i, p in enumerate(passed_sorted, 1):
            print(f"{i}. {p['symbol']}")
            print(f"   💪 القوة: {p['strength']}%")
            print(f"   📈 التغير: {p['change_pct']:+.2f}%")
            print(f"   💵 الافتتاح: ${p['open']:.4f} → الإغلاق: ${p['close']:.4f}")
            print(f"   🎯 أعلى قمة: ${p['highest_high']:.4f}")
            print(f"   🪶 الفلوت: {fmt_shares(p['float'])}")
            print()
    
    if pending:
        print("\n" + "-" * 60)
        print("⏳ الأسهم المعلقة (تحتاج اختراق القمة):")
        print("-" * 60)
        
        for i, p in enumerate(pending, 1):
            print(f"{i}. {p['symbol']}")
            print(f"   💪 القوة: {p['strength']}%")
            print(f"   📈 التغير: {p['change_pct']:+.2f}%")
            print(f"   🎯 القمة للاختراق: ${p['highest_high']:.4f}")
            print()
    
    # حفظ النتائج
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv('backtest_results_sep19_gold.csv', index=False)
        print(f"\n💾 تم حفظ النتائج في: backtest_results_sep19_gold.csv")
    
    print("\n" + "=" * 60)
    print("🏁 انتهى الاختبار")
    print("=" * 60)

if __name__ == "__main__":
    main()
