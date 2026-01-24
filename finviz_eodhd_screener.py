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

print("="*70)
print("📊 FINVIZ FILTERED + EODHD CANDLES")
print("="*70)
print("✅ المعايير:")
print("   - السعر: 0.02 - 10 دولار")
print("   - السيولة: 200,000 على الأقل")
print("   - عدد الأسهم: 300 من Finviz")
print()

# =========================================================
# 1. جلب 300 سهم من Finviz مع الفلتر
# =========================================================
print("🔍 الخطوة 1: جلب الأسهم من Finviz Elite...")

try:
    FINVIZ_COOKIE = """chartsTheme=dark; notice-newsletter=show; .ASPXAUTH=C7E2E86BC876CD078E1DC69C25671D062A909C67501ECF211333FAAD7F54A40FE9B6772EF4E88ED21E26C6C99BCAE5C39C5C8D598CD73357A5FCB4B556AD83E55002A827606EFFFE1F1315C9E8A4E05BC99B517D7E533905EE95F029D8FE0B930EC18E2E5F5037693AE688694BFDFDD82DADE25BA4063B448D18DDC85EAB40FD9D717716F2FEABA2A813D932072BFF5C6F723BACD8D3E4CA5161C3B1E0FF3088C9CC8AA7E67C3A4C94EA5122A68D9ADC7F85B091D98A31BF66F654490F1F7601FA7E420E3ECAF266BF62C1A7C9733A57BC866F92; survey_dialog_cohort=0"""

    FINVIZ_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": FINVIZ_COOKIE
    }

    url = (
        "https://elite.finviz.com/export.ashx?v=111"
        "&f=sh_price_u11,sh_float_u15,sh_curvol_o50,ta_change_u"
        "&o=-volume"
    )

    response = requests.get(url, headers=FINVIZ_HEADERS, timeout=15)
    csv_data = io.StringIO(response.text)
    df_all = pd.read_csv(csv_data)
    
    print(f"✅ تم جلب {len(df_all)} سهم من Finviz")
    
    # تصفية حسب السعر والسيولة
    df_filtered = df_all[
        (df_all['Price'] >= 0.02) & 
        (df_all['Price'] <= 10) & 
        (df_all['Volume'] >= 200000)
    ].copy()
    
    df_filtered = df_filtered.sort_values('Volume', ascending=False)
    
    print(f"✅ بعد الفلتر: {len(df_filtered)} سهم\n")
    
    if len(df_filtered) > 0:
        print("📋 الأسهم المصفاة:")
        print("-" * 70)
        for idx, (_, row) in enumerate(df_filtered.iterrows(), 1):
            print(f"  {idx:2}. {row['Ticker']:<8} | ${row['Price']:<7.2f} | {int(row['Volume']):>12,}")
        print()
    
    filtered_stocks = df_filtered['Ticker'].tolist()[100:150]  # الـ 50 السهم الثالث (101-150)

except Exception as e:
    print(f"❌ خطأ في جلب الأسهم من Finviz: {str(e)}")
    filtered_stocks = []

if not filtered_stocks:
    print("❌ لم يتم العثور على أسهم تطابق المعايير")
    exit(1)

# =========================================================
# 2. جلب شموع EODHD للأسهم المصفاة
# =========================================================
print(f"🔍 الخطوة 2: جلب شموع EODHD...")

# تحديد التاريخ (آخر يوم تداول)
now_ny = datetime.now(ny_tz)
target_date = now_ny.date()

# إذا كان الأحد أو السبت، استخدم آخر جمعة
if target_date.weekday() == 6:  # الأحد
    target_date = target_date - timedelta(days=2)
elif target_date.weekday() == 5:  # السبت
    target_date = target_date - timedelta(days=1)

print(f"   📅 التاريخ: {target_date.strftime('%Y-%m-%d %A')}")
print(f"   ⏰ الفترة: 9:30 AM - 10:00 AM EST")
print(f"   📊 عدد الأسهم: {len(filtered_stocks)}\n")

# صيغة الـ timestamp
start_time = datetime(target_date.year, target_date.month, target_date.day, 9, 30)
end_time = datetime(target_date.year, target_date.month, target_date.day, 10, 0)

# تحويل إلى UTC
start_utc = ny_tz.localize(start_time).astimezone(pytz.UTC).timestamp()
end_utc = ny_tz.localize(end_time).astimezone(pytz.UTC).timestamp()

all_candles = []
success_count = 0
failed_stocks = []

for i, symbol in enumerate(filtered_stocks, 1):
    try:
        print(f"⏳ [{i}/{len(filtered_stocks)}] {symbol}...", end='\r')
        
        # استدعاء EODHD API
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': int(start_utc),
            'to': int(end_utc),
            'period': '1m'  # شموع دقيقة واحدة
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            failed_stocks.append(symbol)
            continue
        
        # EODHD يرجع CSV
        csv_data = io.StringIO(response.text)
        df_response = pd.read_csv(csv_data)
        
        if df_response.empty or df_response['Close'].isna().all():
            failed_stocks.append(symbol)
            continue
        
        # إضافة البيانات
        for _, row in df_response.iterrows():
            if pd.isna(row['Close']):
                continue
                
            # تحويل التاريخ والوقت
            datetime_str = row['Datetime']
            timestamp_utc = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            timestamp_utc = pytz.UTC.localize(timestamp_utc)
            timestamp_ny = timestamp_utc.astimezone(ny_tz)
            
            all_candles.append({
                'symbol': symbol,
                'datetime': timestamp_ny.strftime('%Y-%m-%d %H:%M:%S'),
                'date': timestamp_ny.strftime('%Y-%m-%d'),
                'time': timestamp_ny.strftime('%H:%M:%S'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']) if row['Volume'] > 0 else 0
            })
        
        success_count += 1
        
    except Exception as e:
        failed_stocks.append(symbol)
        continue

print(f"\n✅ تم جلب شموع {success_count} سهم بنجاح\n")

# =========================================================
# 3. حفظ النتائج
# =========================================================
if all_candles:
    df_result = pd.DataFrame(all_candles)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"finviz_eodhd_candles_{timestamp}.csv"
    
    df_result.to_csv(filename, index=False, encoding='utf-8')
    
    print("="*70)
    print(f"✅ تم حفظ النتائج في: {filename}")
    print("="*70)
    
    print(f"\n📊 ملخص النتائج:")
    print(f"   - عدد الأسهم (مع بيانات): {len(df_result['symbol'].unique())}")
    print(f"   - إجمالي الشموع: {len(all_candles)}")
    print(f"   - متوسط الشموع لكل سهم: {len(all_candles) // max(1, len(df_result['symbol'].unique()))}")
    print(f"   - نطاق السعر: ${df_result['close'].min():.2f} - ${df_result['close'].max():.2f}")
    print(f"   - إجمالي السيولة: {int(df_result['volume'].sum()):,}")
    
    print(f"\n📄 الأسهم المضمنة:")
    stocks_with_data = sorted(df_result['symbol'].unique())
    for symbol in stocks_with_data:
        count = len(df_result[df_result['symbol'] == symbol])
        price_range = df_result[df_result['symbol'] == symbol]
        print(f"   • {symbol}: {count} شمعة | ${price_range['close'].min():.2f}-${price_range['close'].max():.2f}")
    
    if failed_stocks:
        print(f"\n⚠️  الأسهم بدون بيانات ({len(failed_stocks)}):")
        for symbol in failed_stocks[:10]:
            print(f"   • {symbol}")
        if len(failed_stocks) > 10:
            print(f"   ... و {len(failed_stocks) - 10} سهم آخر")

else:
    print("❌ لم يتم جلب أي شموع!")
