#!/usr/bin/env python3
"""
اختبار استراتيجية السلم الصاعد على شموع 19 سبتمبر 2024
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
CANDLES_FILE = "test_candles_sep19.csv"
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
# 4. تحليل السلم الصاعد (النسخة المحدثة)
# =========================================================
def check_ladder_pattern(df_window):
    """فحص نمط السلم الصاعد - النسخة المحسنة"""
    if len(df_window) < 5: 
        return False, 0, "بيانات ناقصة"

    # حساب متوسط حجم الجسم في آخر نصف ساعة عشان نقارن فيه (مرجعنا)
    # هذا يمنع الشموع اللي ذيولها فجأة تصير أطول من المعدل الطبيعي
    avg_body = (df_window['Close'] - df_window['Open']).abs().mean()
    if avg_body == 0: avg_body = 0.01 # تجنب القسمة على صفر

    greens = 0
    max_green_body = 0.0001
    candles = [row for _, row in df_window.iterrows()]
    
    # تتبع أقل سعر للشمعة السابقة للتأكد من تصاعد القيعان
    previous_low = -1 

    for i, row in enumerate(candles):
        open_p = float(row['Open'])
        close_p = float(row['Close'])
        high_p = float(row['High'])
        low_p = float(row['Low'])
        
        body = abs(close_p - open_p)
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p
        
        # 1. شرط الذيل القاتل (للخضر والحمر):
        # إذا الذيل العلوي أكبر من مرتين ضعف الجسم، أو أكبر من متوسط الأجسام بـ 3 مرات
        # هذا بيطرد أسهم مثل JDST اللي فيها ذيول عشوائية
        if upper_wick > (body * 2.0) and upper_wick > (avg_body * 1.5):
             return False, 0, f"ذيل علوي مزعج (شمعة {i+1})"

        # 2. شرط كسر السلم (Higher Lows):
        # نستثني الشمعة الأولى، الباقي مفروض ما يكسر قاع اللي قبله بقوة
        if i > 0 and previous_low != -1:
            # لو نزل السعر تحت قاع الشمعة السابقة بمسافة ملحوظة
            if low_p < (previous_low - (avg_body * 0.5)): 
                return False, 0, f"كسر قاع سابق (شمعة {i+1})"

        previous_low = low_p

        if close_p > open_p:  # شمعة خضراء
            greens += 1
            max_green_body = max(max_green_body, body)
        else:  # شمعة حمراء
            # 3. شرط الشمعة الحمراء: ممنوع تكون ضخمة وتبلع اللي قبلها
            if body > (max_green_body * 0.7): # صغرنا النسبة لـ 0.7 للتشديد
                return False, 0, "شمعة حمراء كبيرة"

    # الشروط النهائية
    if greens < 4: 
        return False, 0, f"الخضر {greens} فقط"
    
    if df_window['Close'].iloc[-1] <= df_window['Open'].iloc[0]:
        return False, 0, "لم يصعد السعر"
    
    strength_pct = int((greens / len(df_window)) * 100)
    return True, strength_pct, "سلم نظيف ✅"

# =========================================================
# 5. التشغيل الرئيسي
# =========================================================
def main():
    print("=" * 60)
    print("🧪 اختبار استراتيجية السلم الصاعد")
    print("📅 التاريخ: 19 سبتمبر 2024")
    print("⏰ الفترة: 9:30 - 10:00 صباحاً")
    print("=" * 60)
    
    # تحميل الشموع
    df = load_candles()
    if df is None:
        return
    
    symbols = df['symbol'].unique()
    
    # نتائج الاختبار
    results = []
    passed = []
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
            
            # فحص النمط
            is_valid, strength, reason = check_ladder_pattern(symbol_df)
            
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
                'change_pct': change_pct,
                'float': float_val,
                'candles': len(symbol_df),
                'is_valid': is_valid,
                'strength': strength,
                'reason': reason
            }
            results.append(result)
            
            if is_valid:
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
    
    print(f"\n📈 إجمالي الأسهم: {len(symbols)}")
    print(f"✅ نجحت: {len(passed)}")
    print(f"❌ فشلت: {len(failed)}")
    print(f"📊 نسبة النجاح: {(len(passed)/len(symbols)*100):.1f}%")
    
    if passed:
        print("\n" + "-" * 60)
        print("🏆 الأسهم الناجحة:")
        print("-" * 60)
        
        # ترتيب حسب القوة
        passed_sorted = sorted(passed, key=lambda x: x['strength'], reverse=True)
        
        for i, p in enumerate(passed_sorted, 1):
            print(f"{i}. {p['symbol']}")
            print(f"   💪 القوة: {p['strength']}%")
            print(f"   📈 التغير: {p['change_pct']:+.2f}%")
            print(f"   💵 الافتتاح: ${p['open']:.4f} → الإغلاق: ${p['close']:.4f}")
            print(f"   🎯 أعلى سعر: ${p['high']:.4f}")
            print(f"   🪶 الفلوت: {fmt_shares(p['float'])}")
            print()
    
    # حفظ النتائج
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv('backtest_results_sep19.csv', index=False)
        print(f"\n💾 تم حفظ النتائج في: backtest_results_sep19.csv")
    
    print("\n" + "=" * 60)
    print("🏁 انتهى الاختبار")
    print("=" * 60)

if __name__ == "__main__":
    main()
