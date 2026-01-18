#!/usr/bin/env python3
"""
🚀 البوت - مسح السوق في الصباح (Morning Scanner)
- يجلب بيانات من 9:30 إلى 10:00 صباحاً (أول 30 دقيقة)
- ينتظر إلى 10:03 صباحاً إذا تم تشغيله بكره أو في وقت آخر
"""

import sys
sys.path.insert(0, '.')

import reeshah
import pandas as pd
from datetime import datetime, time
import pytz
import time as time_module
import os
import requests

# المنطقة الزمنية (Eastern Time)
ET = pytz.timezone('US/Eastern')

# اقرأ المفاتيح
TELEGRAM_TOKEN = ""
CHAT_ID = ""

with open('.env', 'r') as f:
    for line in f:
        if 'TELEGRAM_TOKEN' in line:
            TELEGRAM_TOKEN = line.split('=')[1].strip()
        elif 'CHAT_ID' in line:
            CHAT_ID = line.split('=')[1].strip()
        elif 'FMP_API_KEY' in line:
            FMP_API_KEY = line.split('=')[1].strip()

def send_telegram(message):
    """إرسال رسالة للتليقرام"""
    if not TELEGRAM_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": str(CHAT_ID), "text": message, "parse_mode": "HTML"}
        )
    except:
        pass

def get_morning_data(symbol):
    """جلب بيانات الصباح (9:30 - 10:00)"""
    try:
        history = reeshah.get_eodhd_history(symbol)
        if history is None or len(history) < 50:
            return None
        return history
    except:
        return None

def wait_until_market_open():
    """انتظر إلى 10:03 صباحاً"""
    now = datetime.now(ET)
    target = now.replace(hour=10, minute=3, second=0, microsecond=0)
    
    # إذا الوقت الحالي بعد 10:03، انتظر للغد
    if now > target:
        target = target.replace(day=target.day + 1)
    
    wait_seconds = (target - now).total_seconds()
    
    if wait_seconds > 0:
        print(f"⏳ في انتظار 10:03 صباحاً...")
        print(f"   الوقت الحالي: {now.strftime('%H:%M:%S')}")
        print(f"   الانتظار: {int(wait_seconds)} ثانية ({int(wait_seconds/60)} دقيقة)")
        time_module.sleep(wait_seconds)

def is_within_morning_session():
    """تحقق إذا كنا ضمن جلسة الصباح (9:30 - 10:00)"""
    now = datetime.now(ET)
    morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    morning_end = now.replace(hour=10, minute=0, second=0, microsecond=0)
    return morning_start <= now <= morning_end

def run_morning_scanner():
    """تشغيل مسح السوق في الصباح"""
    
    print("=" * 100)
    print("🚀 البوت - مسح السوق في الصباح (Morning Scanner)")
    print("=" * 100)
    
    now = datetime.now(ET)
    print(f"⏰ الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # التحقق من الوقت
    morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    morning_end = now.replace(hour=10, minute=3, second=0, microsecond=0)
    
    if now < morning_start:
        print("⏳ السوق لم يفتح بعد، في انتظار 9:30...")
        wait_until = (morning_start - now).total_seconds()
        print(f"   الانتظار: {int(wait_until)} ثانية ({int(wait_until/60)} دقيقة)")
        time_module.sleep(wait_until)
    elif now > morning_end:
        print("⏳ جلسة الصباح انتهت، انتظار غداً في 10:03...")
        wait_until_market_open()
    
    # ابدأ المسح
    print("\n" + "=" * 100)
    print("🎯 جلب الأسهم...")
    print("=" * 100)
    
    stocks_to_test = []
    
    # جلب من الملف
    if os.path.exists('finviz_300_stocks.csv'):
        try:
            df_stocks = pd.read_csv('finviz_300_stocks.csv')
            stocks_to_test = df_stocks['Symbol'].unique()[:100].tolist()
            print(f"✅ جاب {len(stocks_to_test)} سهم من finviz_300_stocks.csv")
        except:
            stocks_to_test = ['AAPL', 'MSFT', 'PM', 'KO', 'PG', 'JNJ', 'V', 'WMT', 'MCD']
    else:
        stocks_to_test = ['AAPL', 'MSFT', 'PM', 'KO', 'PG', 'JNJ', 'V', 'WMT', 'MCD', 'COST']
    
    print(f"\n🔍 فحص {len(stocks_to_test)} سهم من بيانات الصباح...\n")
    print("-" * 100)
    
    passed = []
    passed_data = []
    
    for i, symbol in enumerate(stocks_to_test, 1):
        try:
            # جلب البيانات
            history = get_morning_data(symbol)
            
            if history is None or len(history) < 50:
                continue
            
            # اختبر الفلتر
            is_gold = reeshah.is_golden_grinder(history.copy())
            
            if is_gold:
                # احسب المتوسطات
                df = history.copy()
                df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
                df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
                
                current = df.iloc[-1]
                price = current['close']
                ema9 = current['ema9']
                ema21 = current['ema21']
                
                passed.append(symbol)
                passed_data.append({
                    'Symbol': symbol,
                    'Price': price,
                    'EMA9': ema9,
                    'EMA21': ema21
                })
                
                print(f"[{i:2d}/{len(stocks_to_test)}] ✅ {symbol:6} | ${price:8.2f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f}")
        
        except Exception as e:
            pass
    
    # النتائج
    print("\n" + "=" * 100)
    print("📊 النتائج النهائية:")
    print("=" * 100)
    print(f"✅ أسهم اجتازت الفلتر: {len(passed)}")
    print(f"❌ أسهم رفضت: {len(stocks_to_test) - len(passed)}")
    print(f"📈 نسبة النجاح: {(len(passed)/len(stocks_to_test)*100):.1f}%")
    
    if passed_data:
        print(f"\n🎯 الأسهم الجاهزة للتداول:")
        print("-" * 100)
        df_results = pd.DataFrame(passed_data)
        print(df_results.to_string(index=False))
        
        # حفظ النتائج
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'morning_scan_{timestamp}.csv'
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ تم حفظ النتائج في: {output_file}")
        
        # إرسال تليقرام
        msg = "🚀 <b>نتائج مسح الصباح</b>\n\n"
        msg += f"⏰ الوقت: {datetime.now(ET).strftime('%H:%M:%S')}\n"
        msg += f"✅ عدد الأسهم: {len(passed)}\n\n"
        msg += "<b>الأسهم:</b>\n"
        for s in passed:
            price = next((p['Price'] for p in passed_data if p['Symbol'] == s), 'N/A')
            msg += f"  • <b>{s}</b> - ${price:.2f}\n"
        
        send_telegram(msg)
        print("\n📱 تم إرسال النتائج للتليقرام")
    else:
        print("\n⚠️ لا توجد أسهم اجتازت الفلتر في هذا الوقت")
        send_telegram("⚠️ لا توجد أسهم اجتازت الفلتر في مسح الصباح")
    
    print("\n" + "=" * 100)
    print("✅ اكتمل!")
    print("=" * 100)

if __name__ == "__main__":
    run_morning_scanner()
