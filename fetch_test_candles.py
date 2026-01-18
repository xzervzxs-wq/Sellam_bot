#!/usr/bin/env python3
"""
جلب شموع الاختبار ليوم 19 سبتمبر 2024
"""
import requests
import pandas as pd
import time

API_KEY = "AzN1tXfit4MUgxLSvWO73Wusjz8f2v21"

# الأسهم المطلوبة من المستخدم
user_stocks = ['SIDU', 'NBY', 'NBIS', 'CYPH', 'GANX', 'LAZR', 'IRE', 'CNCK', 'BENF']

# 10 أسهم عشوائية إضافية (سعر < 10$)
random_stocks = ['ABAT', 'AMPX', 'BLNK', 'DRMA', 'FFAI', 'GOSS', 'RAIL', 'MARA', 'RIOT', 'SOFI']

# 20 سهم من ملف ديسمبر
december_stocks = ['BEAT', 'ENVX', 'APLT', 'GOVX', 'GPUS', 'CTXR', 'CRGY', 'DRCT', 
                   'ECDA', 'EUDA', 'FMFC', 'CRML', 'CANF', 'AIRI', 'AIV', 'BDN',
                   'BFLY', 'ATPC', 'ASBP', 'ASPI']

all_stocks = list(set(user_stocks + random_stocks + december_stocks))
print(f"📦 جلب شموع {len(all_stocks)} سهم من FMP...")

all_candles = []
target_date = "2024-09-19"  # تاريخ أقدم للتأكد من وجود البيانات

for i, symbol in enumerate(all_stocks):
    try:
        url = f"https://financialmodelingprep.com/stable/historical-chart/5min?symbol={symbol}&from={target_date}&to={target_date}&apikey={API_KEY}"
        r = requests.get(url, timeout=15)
        data = r.json()
        
        if data and isinstance(data, list):
            count = 0
            for candle in data:
                dt_str = candle.get('date', '')
                # شموع من 9:30 إلى 10:00
                if dt_str and '09:30' <= dt_str[11:16] <= '10:00':
                    all_candles.append({
                        'symbol': symbol,
                        'date': dt_str,
                        'open': candle.get('open'),
                        'high': candle.get('high'),
                        'low': candle.get('low'),
                        'close': candle.get('close'),
                        'volume': candle.get('volume')
                    })
                    count += 1
            print(f"✅ {i+1}/{len(all_stocks)}: {symbol} - {count} شموع")
        else:
            print(f"❌ {i+1}/{len(all_stocks)}: {symbol} - لا بيانات")
        
        time.sleep(0.2)  # تأخير بسيط
        
    except Exception as e:
        print(f"⚠️ {symbol}: {e}")

# حفظ الملف
if all_candles:
    df = pd.DataFrame(all_candles)
    df = df.sort_values(['symbol', 'date'])
    df.to_csv('test_candles_sep19.csv', index=False)
    print(f"\n" + "="*50)
    print(f"📊 تم حفظ {len(all_candles)} شمعة في test_candles_sep19.csv")
    print(f"📅 التاريخ: {target_date}")
    print(f"🔢 الأسهم: {df['symbol'].nunique()} سهم")
    print(f"⏰ الفترة: 9:30 - 10:00 AM")
    print("="*50)
else:
    print("❌ لم يتم جلب أي بيانات")
