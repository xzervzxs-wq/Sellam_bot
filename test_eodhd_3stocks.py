import pandas as pd
import requests
import os
import io
from datetime import datetime, time, timedelta
import pytz
from dotenv import load_dotenv

# =========================================================
# إعدادات
# =========================================================
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")

ny_tz = pytz.timezone('America/New_York')

# =========================================================
# 3 أسهم للاختبار
# =========================================================
TEST_STOCKS = ['HBI', 'DISH', 'LUMN']

print("="*60)
print("🧪 TESTING EODHD - 3 STOCKS ONLY")
print("="*60)
print(f"📅 الأسهم: {TEST_STOCKS}")
print(f"📊 مصدر البيانات: EODHD")
print(f"⏰ الفترة: 9:30 AM - 10:00 AM EST\n")

# تحديد التاريخ (آخر يوم تداول)
now_ny = datetime.now(ny_tz)
target_date = now_ny.date()

# إذا كان الأحد أو السبت، استخدم آخر جمعة
if target_date.weekday() == 6:  # الأحد
    target_date = target_date - timedelta(days=2)
elif target_date.weekday() == 5:  # السبت
    target_date = target_date - timedelta(days=1)

print(f"📆 تاريخ البيانات: {target_date.strftime('%Y-%m-%d %A')}\n")

all_candles = []
success_count = 0

for symbol in TEST_STOCKS:
    try:
        print(f"🔄 جاري جلب شموع {symbol} من EODHD...")
        
        # صيغة الـ timestamp
        start_time = datetime(target_date.year, target_date.month, target_date.day, 9, 30)
        end_time = datetime(target_date.year, target_date.month, target_date.day, 10, 0)
        
        # تحويل إلى UTC
        start_utc = ny_tz.localize(start_time).astimezone(pytz.UTC).timestamp()
        end_utc = ny_tz.localize(end_time).astimezone(pytz.UTC).timestamp()
        
        # استدعاء EODHD API
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': int(start_utc),
            'to': int(end_utc),
            'period': '1m'  # شموع دقيقة واحدة
        }
        
        print(f"   URL: {url}")
        print(f"   Params: from={int(start_utc)}, to={int(end_utc)}, period=1m\n")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ خطأ HTTP {response.status_code}\n")
            continue
        
        # EODHD يرجع CSV وليس JSON!
        csv_data = io.StringIO(response.text)
        df_response = pd.read_csv(csv_data)
        
        if df_response.empty:
            print(f"   ⚠️  لا توجد شموع\n")
            continue
        
        print(f"   ✅ تم جلب {len(df_response)} شمعة\n")
        
        for _, row in df_response.iterrows():
            # تحويل التاريخ والوقت
            datetime_str = row['Datetime']
            timestamp_utc = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            timestamp_utc = pytz.UTC.localize(timestamp_utc)
            timestamp_ny = timestamp_utc.astimezone(ny_tz)
            
            all_candles.append({
                'symbol': symbol,
                'datetime': timestamp_ny.strftime('%Y-%m-%d %H:%M:%S'),
                'time': timestamp_ny.strftime('%H:%M:%S'),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': int(row['Volume']) if row['Volume'] > 0 else 0
            })
        
        success_count += 1
        print(f"✅ {symbol}: تم حفظ {len(df_response)} شمعة\n")
        
    except Exception as e:
        print(f"❌ خطأ في {symbol}: {str(e)}\n")

# حفظ النتائج
if all_candles:
    df = pd.DataFrame(all_candles)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_candles_1min_{timestamp}.csv"
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print("="*60)
    print(f"✅ تم حفظ النتائج في: {filename}")
    print("="*60)
    print(f"\n📊 ملخص:")
    print(f"   - عدد الأسهم: {success_count}/3")
    print(f"   - إجمالي الشموع: {len(all_candles)}")
    print(f"\n📄 محتوى الملف:")
    print(df.to_string())
else:
    print("❌ لم يتم جلب أي بيانات!")
