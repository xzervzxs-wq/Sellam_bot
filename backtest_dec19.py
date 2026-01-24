#!/usr/bin/env python3
"""
🧪 Backtest السلم الصاعد - يوم 19 ديسمبر 2025
اختبار استراتيجية السلم على أسهم محددة
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

# =========================================================
# الإعدادات
# =========================================================
EODHD_API_KEY = "68c0ad0b52af78.88121932"
TEST_DATE = "2024-12-19"  # التاريخ المطلوب (استخدمت 2024 لأن 2025 لسه ما جا)

# الأسهم المطلوب اختبارها
USER_STOCKS = ["SIDU", "CRWG", "NBY", "NBIL", "GANX", "BDRX", "KAPA", "NINE", "IOVX", "SNAP"]

# 4 أسهم إضافية (أسعار أقل من $10)
EXTRA_STOCKS = ["LCID", "NIO", "TELL", "BBIG"]

ALL_STOCKS = USER_STOCKS + EXTRA_STOCKS

# =========================================================
# جلب بيانات الشموع من EODHD
# =========================================================
def get_eodhd_intraday(symbol, date_str):
    """
    جلب شموع 5 دقائق من EODHD ليوم محدد
    """
    # EODHD يحتاج from/to timestamps
    # نحسب بداية ونهاية اليوم
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # من بداية اليوم لنهايته
    start_ts = int(date_obj.timestamp())
    end_ts = int((date_obj + timedelta(days=1)).timestamp())
    
    url = f"https://eodhd.com/api/intraday/{symbol}.US"
    params = {
        "api_token": EODHD_API_KEY,
        "interval": "5m",
        "from": start_ts,
        "to": end_ts,
        "fmt": "json"
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        
        if not data or not isinstance(data, list):
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if df.empty:
            return df
        
        # تحويل التاريخ
        if 'datetime' in df.columns:
            df['date'] = pd.to_datetime(df['datetime'])
        elif 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        else:
            return pd.DataFrame()
        
        df = df.set_index('date').sort_index()
        
        # توحيد أسماء الأعمدة
        df.columns = df.columns.str.capitalize()
        
        # التأكد من وجود الأعمدة المطلوبة
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            if col not in df.columns:
                # محاولة إيجاد العمود بأسماء مختلفة
                for alt in [col.lower(), col.upper()]:
                    if alt in df.columns:
                        df[col] = df[alt]
                        break
        
        return df
        
    except Exception as e:
        print(f"   ❌ خطأ في جلب {symbol}: {e}")
        return pd.DataFrame()

# =========================================================
# استراتيجية السلم الصاعد (نسخة طبق الأصل)
# =========================================================
def check_ladder_pattern(df_window):
    """
    تحليل نموذج السلم الصاعد
    """
    # نحتاج 3 شمعات على الأقل
    if len(df_window) < 3:
        return False, 0, "بيانات غير كافية"

    candles = [row for _, row in df_window.iterrows()]

    start_price = float(candles[0]['Open'])
    current_price = float(candles[-1]['Close'])

    # 1. شرط مبدئي: لازم السعر الحالي أعلى من البداية
    if current_price <= start_price:
        return False, 0, "السعر لم يصعد"

    highest_high = float(candles[0]['High'])
    prev_low = float(candles[0]['Low'])
    prev_close = float(candles[0]['Close'])

    stagnation_count = 0
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

        if c_high > highest_high:
            highest_high = c_high
            new_highs_count += 1
            stagnation_count = 0
        else:
            distance_from_high = (highest_high - c_close) / highest_high if highest_high > 0 else 0

            if distance_from_high < 0.015:
                stagnation_count += 0.5
            else:
                stagnation_count += 1

        if stagnation_count >= 3.5:
            return False, 0, "فقد الزخم (ركود طويل)"

        if c_close < (prev_low * 0.998):
            return False, 0, f"كسر قاع سابق (شمعة {i+1})"

        avg_body_ref = abs(prev_close - prev_low) + 0.01
        if upper_wick > body * 2.5 and upper_wick > avg_body_ref * 1.5:
            return False, 0, "ذيل تصريف واضح"

        prev_low = c_low
        prev_close = c_close
        valid_candles += 1

    # الفحص النهائي
    if current_price < (highest_high * 0.985):
        return False, 0, "إغلاق ضعيف بعيد عن القمة"

    total_gain_pct = (current_price - start_price) / start_price
    if total_gain_pct < 0.005:
        return False, 0, "حركة ضعيفة جداً"

    if new_highs_count < 1:
        return False, 0, "لم يحقق قمم جديدة"

    strength_pct = int((new_highs_count / len(candles)) * 100)
    if current_price >= highest_high * 0.995:
        strength_pct = 95

    return True, strength_pct, "نموذج قوي ومتماسك 🚀"

# =========================================================
# الباك تست الرئيسي
# =========================================================
def run_backtest():
    print("=" * 60)
    print(f"🧪 Backtest السلم الصاعد - يوم {TEST_DATE}")
    print("=" * 60)
    print(f"📋 عدد الأسهم: {len(ALL_STOCKS)}")
    print(f"   - أسهم المستخدم: {USER_STOCKS}")
    print(f"   - أسهم إضافية: {EXTRA_STOCKS}")
    print("=" * 60)
    
    results = []
    
    for symbol in ALL_STOCKS:
        print(f"\n🔍 فحص {symbol}...")
        
        # جلب البيانات
        df = get_eodhd_intraday(symbol, TEST_DATE)
        
        if df.empty:
            print(f"   ⚠️ لا توجد بيانات")
            results.append({
                'symbol': symbol,
                'status': 'NO_DATA',
                'strength': 0,
                'reason': 'لا توجد بيانات',
                'price_930': 0,
                'price_1000': 0,
                'candles': 0
            })
            continue
        
        # طباعة معلومات البيانات
        print(f"   📊 إجمالي الشموع: {len(df)}")
        print(f"   📅 من {df.index[0]} إلى {df.index[-1]}")
        
        # فلترة شموع 9:30 - 10:00
        # EODHD يرجع بتوقيت UTC، نحتاج تحويل لـ NY
        ny_tz = pytz.timezone('America/New_York')
        
        # تحويل الـ index لـ timezone-aware
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(ny_tz)
        
        # فلترة الوقت
        morning_mask = (df.index.time >= pd.Timestamp('09:30').time()) & \
                      (df.index.time <= pd.Timestamp('10:00').time())
        setup = df[morning_mask]
        
        if setup.empty or len(setup) < 3:
            print(f"   ⚠️ شموع الصباح غير كافية ({len(setup)})")
            results.append({
                'symbol': symbol,
                'status': 'FEW_CANDLES',
                'strength': 0,
                'reason': f'شموع غير كافية ({len(setup)})',
                'price_930': 0,
                'price_1000': 0,
                'candles': len(setup)
            })
            continue
        
        print(f"   ⏰ شموع 9:30-10:00: {len(setup)}")
        
        # سعر البداية والنهاية
        price_930 = float(setup['Open'].iloc[0])
        price_1000 = float(setup['Close'].iloc[-1])
        
        print(f"   💵 السعر 9:30: ${price_930:.2f}")
        print(f"   💵 السعر 10:00: ${price_1000:.2f}")
        
        # اختبار الاستراتيجية
        is_valid, strength, reason = check_ladder_pattern(setup)
        
        if is_valid:
            print(f"   ✅ نجح! القوة: {strength}%")
            status = 'PASSED'
        else:
            print(f"   ❌ فشل: {reason}")
            status = 'FAILED'
        
        results.append({
            'symbol': symbol,
            'status': status,
            'strength': strength,
            'reason': reason,
            'price_930': price_930,
            'price_1000': price_1000,
            'candles': len(setup),
            'change_pct': ((price_1000 - price_930) / price_930 * 100) if price_930 > 0 else 0
        })
    
    # =========================================================
    # النتائج النهائية
    # =========================================================
    print("\n" + "=" * 60)
    print("📊 النتائج النهائية")
    print("=" * 60)
    
    passed = [r for r in results if r['status'] == 'PASSED']
    failed = [r for r in results if r['status'] == 'FAILED']
    no_data = [r for r in results if r['status'] in ['NO_DATA', 'FEW_CANDLES']]
    
    print(f"\n✅ الأسهم الناجحة ({len(passed)}):")
    print("-" * 40)
    if passed:
        for r in sorted(passed, key=lambda x: x['strength'], reverse=True):
            print(f"   🏆 {r['symbol']:6s} | القوة: {r['strength']:3d}% | ${r['price_930']:.2f} → ${r['price_1000']:.2f} ({r['change_pct']:+.1f}%)")
    else:
        print("   لا يوجد أسهم ناجحة")
    
    print(f"\n❌ الأسهم الفاشلة ({len(failed)}):")
    print("-" * 40)
    for r in failed:
        print(f"   ✗ {r['symbol']:6s} | السبب: {r['reason']}")
    
    if no_data:
        print(f"\n⚠️ بدون بيانات ({len(no_data)}):")
        print("-" * 40)
        for r in no_data:
            print(f"   ? {r['symbol']:6s} | {r['reason']}")
    
    # حفظ النتائج
    df_results = pd.DataFrame(results)
    df_results.to_csv('backtest_dec19_results.csv', index=False)
    print(f"\n💾 تم حفظ النتائج في backtest_dec19_results.csv")
    
    return results

# =========================================================
# تشغيل
# =========================================================
if __name__ == "__main__":
    run_backtest()
