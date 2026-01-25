#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جلب شموع EODHD للفترة 9:30-10:00 بتاريخ 17 ديسمبر 2025 (أول ساعة)
"""
import os
import pandas as pd
import requests
from datetime import datetime
import time

EODHD_API_KEY = os.getenv('EODHD_API_KEY', 'your_key_here')
MIN_PRICE = 0.02
MAX_PRICE = 10.0

def get_eodhd_candles(symbol, date_str='2025-12-17', interval='1'):
    """جلب شموع EODHD بفاصل زمني محدد"""
    try:
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'period': interval,
            'order': 'asc',
            'from': f"{date_str} 09:30:00",
            'to': f"{date_str} 10:00:00",
            'api_token': EODHD_API_KEY,
            'fmt': 'json'
        }
        
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if isinstance(data, dict) and 'data' in data:
            candles = data['data']
        else:
            candles = data
        
        if not candles:
            return None
        
        return candles
        
    except Exception as e:
        print(f"⚠️ {symbol}: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("📊 جلب شموع EODHD (17 ديسمبر 2025، 9:30-10:00)")
    print("="*60)
    
    # قراءة قائمة الأسهم
    try:
        df_stocks = pd.read_csv('/workspaces/Sellam_bot/finviz_300_stocks.csv')
        stocks = df_stocks['symbol'].tolist()
        print(f"\n✅ تم قراءة {len(stocks)} سهم من finviz_300_stocks.csv")
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return
    
    # جلب الشموع
    all_candles = []
    success_count = 0
    
    print(f"\n🔍 جاري جلب البيانات من EODHD...")
    print(f"{'Symbol':<10} {'Result':<40}")
    print("-" * 50)
    
    for idx, symbol in enumerate(stocks, 1):
        candles = get_eodhd_candles(symbol)
        
        if candles:
            for candle in candles:
                all_candles.append({
                    'symbol': symbol,
                    'datetime': candle.get('datetime', ''),
                    'open': float(candle.get('open', 0)),
                    'high': float(candle.get('high', 0)),
                    'low': float(candle.get('low', 0)),
                    'close': float(candle.get('close', 0)),
                    'volume': int(candle.get('volume', 0))
                })
            success_count += 1
            status = f"✅ {len(candles)} شمعة"
        else:
            status = "⏭️ لا توجد بيانات"
        
        if idx % 50 == 0 or idx == len(stocks):
            print(f"{symbol:<10} {status:<40} ({idx}/{len(stocks)})")
        
        # تأخير صغير لتجنب قيود API
        if idx % 10 == 0:
            time.sleep(1)
    
    print("-" * 50)
    print(f"\n📊 النتائج:")
    print(f"  • عدد الأسهم بنجاح: {success_count}/{len(stocks)}")
    print(f"  • عدد الشموع الكلي: {len(all_candles)}")
    
    # حفظ البيانات
    if all_candles:
        df_result = pd.DataFrame(all_candles)
        
        # ترتيب حسب الرمز والوقت
        df_result = df_result.sort_values(['symbol', 'datetime']).reset_index(drop=True)
        
        # حفظ
        output_file = '/workspaces/Sellam_bot/eodhd_dec17_930_1000.csv'
        df_result.to_csv(output_file, index=False)
        
        print(f"\n✅ تم حفظ البيانات في: {output_file}")
        print(f"\n📋 عينة من البيانات:")
        print(df_result.head(10))
        
        return output_file
    else:
        print("\n❌ لم يتم جلب أي بيانات")
        return None

if __name__ == '__main__':
    main()
