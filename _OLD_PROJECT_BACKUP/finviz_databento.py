import databento as db
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
import concurrent.futures

# ==============================================================================
# 🔑 إعدادات البيئة
# ==============================================================================
load_dotenv()
DATABENTO_API_KEY = "db-geWqvqXcHfK5BbyikhUW83qUeFnYM"

MAX_WORKERS = 20
OUTPUT_CSV = f"candles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# ==============================================================================
# 📊 قائمة الأسهم الشهيرة (300 سهم)
# ==============================================================================
STOCK_SYMBOLS = [
    'AAPL', 'MSFT', 'NVDA', 'META', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'BRK.B', 'JNJ',
    'V', 'WMT', 'PG', 'MA', 'HD', 'DIS', 'PYPL', 'NFLX', 'ADBE', 'CRM',
    'INTC', 'AMD', 'IBM', 'CSCO', 'QCOM', 'AVGO', 'MU', 'SNOW', 'DDOG', 'NET',
    'OKTA', 'ZM', 'CRWD', 'SPLK', 'COR', 'FTNT', 'WDAY', 'NOW', 'TWLO', 'SHOP',
    'UBER', 'LYFT', 'DASH', 'COIN', 'RIOT', 'MARA', 'MSTR', 'PLTR', 'SOFI', 'UPST',
    'RBLX', 'U', 'HOOD', 'LRCX', 'MRVL', 'MDLZ', 'PEP', 'PDD', 'WDC', 'ARM',
    'SBUX', 'ATVI', 'MDLN', 'TXN', 'PANW', 'TMUS', 'NDAQ', 'ABNB', 'ORLY', 'HON',
    'AZN', 'IBKR', 'AEP', 'ROST', 'PCAR', 'CTAS', 'NXPI', 'TRI', 'NTES', 'LLY',
    'UNH', 'CVX', 'XOM', 'MRK', 'PFE', 'KO', 'MCD', 'NKE', 'BA', 'CAT',
    'GE', 'MMM', 'HON', 'RTX', 'LMT', 'GD', 'NOC', 'TXT', 'HII', 'LDOS',
    'VIAC', 'PARA', 'FOXA', 'FOX', 'DIS', 'CMCSA', 'CHTR', 'DISH', 'TMUS', 'VZ',
    'T', 'SWKS', 'INTU', 'RGEN', 'ALNY', 'BIIB', 'CELG', 'GILD', 'SAVE', 'SQ',
    'PYPL', 'MA', 'V', 'AXP', 'DFS', 'APD', 'DD', 'DOW', 'ECL', 'EMR',
    'ETN', 'EWBC', 'EW', 'EXC', 'EXPE', 'FFIV', 'FB', 'FCX', 'FDX', 'FIS',
    'FITB', 'FRT', 'FUL', 'GIS', 'GL', 'GLW', 'GM', 'GPC', 'GWW', 'HAL',
    'HAS', 'HBAN', 'HBI', 'HCA', 'HEI', 'HES', 'HIG', 'HLT', 'HOG', 'HRL',
    'HSIC', 'HST', 'HSY', 'HUM', 'HZNP', 'IAC', 'IEX', 'IFF', 'ILPT', 'INCY',
    'INFO', 'IVZ', 'IP', 'IPG', 'IQV', 'IR', 'IRM', 'ISRG', 'IT', 'IVZ',
    'J', 'JBHT', 'JCI', 'JCOM', 'JEF', 'JKHY', 'JLL', 'JNPR', 'JPM', 'JULUS',
    'K', 'KEY', 'KEYS', 'KIM', 'KMB', 'KMI', 'KMT', 'KO', 'KR', 'KRC',
    'KRG', 'KROS', 'KSS', 'KTB', 'KTO', 'KTOS', 'KYO', 'L', 'LAC', 'LAMR',
    'LB', 'LBRDK', 'LBRDA', 'LCII', 'LCI', 'LDOS', 'LEA', 'LEE', 'LEG', 'LEI',
    'LEN', 'LET', 'LF', 'LGND', 'LH', 'LHCG', 'LHCGX', 'LHCGY', 'LI', 'LIBL',
    'LIN', 'LINK', 'LKQ', 'LMBS', 'LMT', 'LNCE', 'LNC', 'LNTH', 'LNW', 'LPLA',
    'LPS', 'LRCX', 'LSCC', 'LSEG', 'LSI', 'LSL', 'LST', 'LTC', 'LTCH', 'LTM',
    'LULU', 'LUMN', 'LUV', 'LVS', 'LVTX', 'LW', 'LXP', 'LXU', 'LYB', 'LYG',
    'LYV', 'MAA', 'MAC', 'MAG', 'MAGS', 'MAN', 'MANU', 'MAP', 'MARA', 'MARK',
    'MARPS', 'MAS', 'MASI', 'MAT', 'MATS', 'MATW', 'MAXX', 'MB', 'MBG', 'MBIN',
    'MBRX', 'MBS', 'MBT', 'MC', 'MCA', 'MCB', 'MCD', 'MCHP', 'MCK', 'MCO',
    'MCP', 'MD', 'MDA', 'MDC', 'MDCO', 'MDT', 'MDVN', 'MEI', 'MEIR', 'MELM',
    'MEN', 'MEOH', 'MER', 'MERI', 'MERL', 'MET', 'META', 'METC', 'METX', 'MF',
    'MFA', 'MFC', 'MFIV', 'MFM', 'MG', 'MGA', 'MGI', 'MGLN', 'MGM', 'MGPI',
    'MGR', 'MGY', 'MHH', 'MHLD', 'MHO', 'MHRA', 'MHRG', 'MHSP', 'MI', 'MIB',
    'MIC', 'MIDD', 'MIEN', 'MIK', 'MIKR', 'MILE', 'MIR', 'MIRM', 'MIST', 'MIT',
    'MITA', 'MIX', 'MIXT', 'MKC', 'MKEBX', 'MKLN', 'MKTX', 'MLAB', 'MLB', 'MLC',
    'MLD', 'MLHR', 'MLI', 'MLIT', 'MLNK', 'MLRY', 'MLSS', 'MM', 'MMA', 'MMAC',
    'MMAXF', 'MMBY', 'MMC', 'MMCAP', 'MMCCF', 'MMCD', 'MMCHI', 'MMCIF', 'MMCL', 'MMCRF',
    'MMCRX', 'MMCT', 'MMCTY', 'MMCY', 'MMDM', 'MMEC', 'MMECF', 'MMEH', 'MMEI', 'MMEIF',
    'MMEIX', 'MMEJ', 'MMEK', 'MMEL', 'MMEM', 'MMEN', 'MMEO', 'MMERF', 'MMESX', 'MMETX',
][:300]  # أخذ أول 300 سهم

# ==============================================================================
# 📈 جلب شموع الدقيقة من DataBento
# ==============================================================================
def get_morning_candles_databento(symbol):
    """
    جلب شموع الدقيقة الواحدة من 9:30-10:00 صباحاً من DataBento
    9:30 AM EST = 14:30 UTC
    10:00 AM EST = 15:00 UTC
    """
    try:
        client = db.Historical(key=DATABENTO_API_KEY)
        
        # استخدام آخر يوم تداول متاح
        # بما أن اليوم الثلاثاء والسوق قد تكون مغلقة، استخدم يوم الاثنين
        from datetime import timedelta
        today = datetime.now()
        
        # البحث عن آخر يوم تداول (الاثنين إذا كان الثلاثاء)
        if today.weekday() == 1:  # الثلاثاء
            target_date = today - timedelta(days=1)  # الاثنين
        elif today.weekday() == 0:  # الاثنين
            target_date = today
        else:
            target_date = today
        
        today_str = target_date.strftime('%Y-%m-%d')
        
        # الأوقات بصيغة ISO 8601 UTC
        start_time_utc = f"{today_str}T14:30:00"
        end_time_utc = f"{today_str}T15:00:00"
        
        # طلب البيانات من DataBento
        data = client.timeseries.get_range(
            dataset="XNAS.ITCH",  # بيانات NASDAQ
            symbols=symbol,
            schema="ohlcv-1m",    # شموع دقيقة واحدة
            start=start_time_utc,
            end=end_time_utc
        )
        
        # تحويل إلى DataFrame
        df = data.to_df()
        
        if df.empty:
            return None
        
        # تحويل الـ Index إلى توقيت نيويورك
        df.index = df.index.tz_convert('America/New_York')
        
        # تنظيف البيانات (إبقاء الأعمدة المهمة فقط)
        df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        
        # إضافة السهم كعمود
        df['symbol'] = symbol
        df['timestamp'] = df.index
        
        # إعادة ترتيب الأعمدة
        df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        return df.reset_index(drop=True)
    
    except Exception as e:
        return None

# ==============================================================================
# 💾 حفظ الشموع في CSV
# ==============================================================================
def save_candles_to_csv(all_candles):
    """
    حفظ جميع الشموع في ملف CSV
    """
    try:
        if all_candles.empty:
            print("⚠️ لا توجد شموع للحفظ")
            return False
        
        # ترتيب البيانات
        all_candles['timestamp'] = pd.to_datetime(all_candles['timestamp'])
        all_candles = all_candles.sort_values(['symbol', 'timestamp'])
        
        # حفظ في CSV
        all_candles.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        
        print(f"✅ تم حفظ {len(all_candles)} شمعة في: {OUTPUT_CSV}")
        
        # طباعة ملخص
        print(f"\n📊 ملخص البيانات:")
        print(f"   - عدد الأسهم: {all_candles['symbol'].nunique()}")
        print(f"   - إجمالي الشموع: {len(all_candles)}")
        if len(all_candles) > 0:
            print(f"   - نطاق الأوقات: {all_candles['timestamp'].min()} إلى {all_candles['timestamp'].max()}")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ في حفظ الملف: {e}")
        return False

# ==============================================================================
# 🚀 البرنامج الرئيسي
# ==============================================================================
def main():
    print("="*80)
    print("🚀 بدء جلب شموع الأسهم من DataBento")
    print("="*80)
    
    symbols = STOCK_SYMBOLS
    
    # حساب آخر يوم تداول
    from datetime import timedelta
    today = datetime.now()
    if today.weekday() == 1:  # الثلاثاء
        target_date = today - timedelta(days=1)  # الاثنين
    elif today.weekday() == 0:  # الاثنين
        target_date = today
    else:
        target_date = today
    
    print(f"\n📡 جاري جلب شموع الدقيقة من 9:30-10:00 صباحاً...")
    print(f"📊 الفترة الزمنية: {target_date.strftime('%Y-%m-%d')}")
    print(f"🔢 عدد الأسهم: {len(symbols)}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    all_candles = pd.DataFrame()
    
    # معالجة الأسهم بالتوازي
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(get_morning_candles_databento, symbols))
        
        for i, df in enumerate(results, 1):
            if df is not None and not df.empty:
                all_candles = pd.concat([all_candles, df], ignore_index=True)
                print(f"✅ [{i}/{len(symbols)}] {symbols[i-1]}: {len(df)} شمعة")
            else:
                print(f"⏭️  [{i}/{len(symbols)}] {symbols[i-1]}: لا توجد بيانات")
            
            # طباعة تقدم كل 30 سهم
            if i % 30 == 0:
                print(f"⏳ تم معالجة {i}/{len(symbols)} سهم - إجمالي الشموع: {len(all_candles)}\n")
    
    print(f"\n{'='*80}")
    print(f"📊 النتائج النهائية:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ إجمالي الشموع المجلوبة: {len(all_candles)}")
    
    # حفظ الشموع في CSV
    if not all_candles.empty:
        save_candles_to_csv(all_candles)
        print(f"\n✅ يمكنك الآن اختبار الاستراتيجيات على البيانات المحفوظة!")
        print(f"\nعينة من البيانات:")
        print(all_candles.head(10))
    else:
        print(f"⚠️ لم يتم جلب أي شموع")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()

