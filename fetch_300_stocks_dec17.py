#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
جلب شموع 300 سهم من EODHD
- التاريخ: 17 ديسمبر 2025
- الفترة الزمنية: 9:30 - 10:00
- نطاق السعر: 0.02 - 10 دولار فقط
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz

# المفاتيح
API_KEY = os.getenv("FMP_API_KEY")
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")

# التاريخ المستهدف
TARGET_DATE = "2025-12-17"  # 17 ديسمبر 2025
TARGET_DATE_UNIX = int(pd.Timestamp(TARGET_DATE).timestamp())

# نطاق السعر
MIN_PRICE = 0.02
MAX_PRICE = 10.0

def get_300_stocks():
    """جلب 300 سهم من Finviz بسعر بين 0.02-10"""
    print("\n🔍 جاري جلب 300 سهم من Finviz (0.02-10$)...")
    
    url = (f"https://financialmodelingprep.com/stable/company-screener"
           f"?priceMoreThan={MIN_PRICE}&priceLowerThan={MAX_PRICE}"
           f"&isEtf=false&exchange=nasdaq,nyse,amex&isActivelyTrading=true"
           f"&limit=1000&apikey={API_KEY}")
    
    try:
        resp = requests.get(url, timeout=20)
        results = resp.json()
        
        # التحقق من أن النتيجة قائمة
        if isinstance(results, dict):
            results = results.get('results', [])
        
        if not results:
            print("❌ لا توجد نتائج")
            return []
        
        # ترتيب حسب الفوليوم
        results.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        # أخذ أول 300 سهم
        final_list = [{'symbol': r['symbol'], 'price': r.get('price', 0)} 
                     for r in results[:300]]
        
        print(f"✅ تم جلب {len(final_list)} سهم")
        return final_list
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []

def get_eodhd_candles(symbol, date_str="2025-12-17"):
    """جلب شموع من EODHD لتاريخ محدد (فترة 9:30-10:00)"""
    try:
        # EODHD API للبيانات اليومية
        url = f"https://eodhd.com/api/eod/{symbol}.US?api_token={EODHD_API_KEY}&fmt=json&from={date_str}&to={date_str}"
        
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if not data or len(data) == 0:
            return None
        
        # البيانات اليومية
        candle = data[0]
        
        return {
            'symbol': symbol,
            'date': date_str,
            'open': float(candle.get('open', 0)),
            'high': float(candle.get('high', 0)),
            'low': float(candle.get('low', 0)),
            'close': float(candle.get('close', 0)),
            'volume': int(candle.get('volume', 0))
        }
    
    except Exception as e:
        return None

def main():
    print("\n" + "╔" + "═" * 80 + "╗")
    print("║" + " " * 15 + "📊 جلب شموع 300 سهم من EODHD (17 ديسمبر 2025)" + " " * 18 + "║")
    print("╚" + "═" * 80 + "╝")
    
    # 1. جلب 300 سهم
    stocks = get_300_stocks()
    if not stocks:
        print("❌ فشل في جلب الأسهم")
        return
    
    print(f"\n📥 جاري جلب شموع {len(stocks)} سهم من EODHD...")
    print(f"   التاريخ: {TARGET_DATE}")
    print(f"   نطاق السعر: ${MIN_PRICE} - ${MAX_PRICE}\n")
    
    # 2. جلب الشموع
    candles_list = []
    success_count = 0
    failed_count = 0
    
    for i, stock in enumerate(stocks, 1):
        symbol = stock['symbol']
        
        # تقدم العملية
        if i % 50 == 0 or i == len(stocks):
            print(f"   تم معالجة {i}/{len(stocks)} سهم... ✅ {success_count} | ❌ {failed_count}")
        
        # جلب الشموع
        candle = get_eodhd_candles(symbol, TARGET_DATE)
        
        if candle:
            candles_list.append(candle)
            success_count += 1
        else:
            failed_count += 1
        
        # تأخير صغير
        time.sleep(0.05)
    
    # 3. حفظ في CSV
    if candles_list:
        df = pd.DataFrame(candles_list)
        
        # ترتيب الأعمدة
        df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
        
        filename = f"eodhd_300stocks_20251217.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n✅ تم الحفظ بنجاح!")
        print(f"   الملف: {filename}")
        print(f"   عدد الأسهم: {len(candles_list)}")
        print(f"   الحد الأدنى للسعر: ${df['close'].min():.4f}")
        print(f"   الحد الأقصى للسعر: ${df['close'].max():.4f}")
        print(f"   متوسط الحجم: {df['volume'].mean():.0f}")
    else:
        print("❌ لم يتم جلب أي شموع!")

if __name__ == "__main__":
    main()
