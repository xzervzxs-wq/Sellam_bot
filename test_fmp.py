"""
نسخة اختبار سريعة من fmp_sellam - بدون انتظار الساعة 10:02 AM
"""

import pandas as pd
import warnings
from datetime import datetime, time
import requests
import os
import json
import time as time_module
import pytz
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# 1. إعدادات ومفاتيح التشغيل (FMP STABLE VERSION)
# =========================================================
load_dotenv()
API_KEY = os.getenv("FMP_API_KEY", "AzN1tXfit4MUgxLSvWO73Wusjz8f2v21")

warnings.simplefilter(action='ignore', category=FutureWarning)
FLOAT_CACHE_FILE = "float_cache.json"
SHARIAH_FILE = "shariah_stocks_master.json"
CANDLES_DATA_FILE = "test_candles_data.json"
SUCCESSFUL_PATTERNS_FILE = "test_successful_patterns.json"

# تحميل قاعدة البيانات الشرعية
def load_shariah_db():
    if os.path.exists(SHARIAH_FILE):
        try:
            with open(SHARIAH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

shariah_db = load_shariah_db()
print(f"�� تم تحميل {len(shariah_db)} سهم من قاعدة البيانات الشرعية.")

# =========================================================
# 2. أدوات جلب البيانات
# =========================================================
def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_json_file(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ تم حفظ الملف: {filename}")
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ الملف: {e}")
        return False

float_data_store = load_json_file(FLOAT_CACHE_FILE)

def get_country_flag(symbol):
    try:
        url = f"https://financialmodelingprep.com/stable/profile/{symbol}"
        params = {'apikey': API_KEY}
        data = requests.get(url, params=params, timeout=5).json()
        if data and isinstance(data, list) and len(data) > 0:
            country = data[0].get('country', 'US')
            if len(country) == 2:
                return "".join([chr(ord(c.upper()) + 127397) for c in country])
    except: pass
    return "🇺🇸"

def get_float_shares(symbol):
    global float_data_store
    val = float_data_store.get(symbol)
    if isinstance(val, (int, float)) and val > 0:
        return val
    return 0

def get_fmp_data(symbol, target_date):
    """جلب شموع 1 دقيقة من FMP وتجميعها إلى 5 دقائق"""
    try:
        date_str = target_date.strftime('%Y-%m-%d')
        url = "https://financialmodelingprep.com/stable/historical-chart/1min"
        params = {
            'symbol': symbol,
            'apikey': API_KEY,
            'from': date_str,
            'to': date_str
        }

        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        if not data or not isinstance(data, list):
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York')

        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low',
                          'close': 'Close', 'volume': 'Volume'}, inplace=True)
        
        df_5min = df.resample('5T').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return df_5min
    except Exception as e:
        return pd.DataFrame()

def get_screener_stocks():
    """جلب الأسهم من Finviz Elite"""
    FINVIZ_COOKIE = """chartsTheme=dark; notice-newsletter=show; .ASPXAUTH=C7E2E86BC876CD078E1DC69C25671D062A909C67501ECF211333FAAD7F54A40FE9B6772EF4E88ED21E26C6C99BCAE5C39C5C8D598CD73357A5FCB4B556AD83E55002A827606EFFFE1F1315C9E8A4E05BC99B517D7E533905EE95F029D8FE0B930EC18E2E5F5037693AE688694BFDFDD82DADE25BA4063B448D18DDC85EAB40FD9D717716F2FEABA2A813D932072BFF5C6F723BACD8D3E4CA5161C3B1E0FF3088C9CC8AA7E67C3A4C94EA5122A68D9ADC7F85B091D98A31BF66F654490F1F7601FA7E420E3ECAF266BF62C1A7C9733A57BC866F92; survey_dialog_cohort=0; customColors=%7B%22light%22%3A%7B%7D%2C%22dark%22%3A%7B%7D%7D; customColorsExpiration=12%2F12%2F2025%208%3A11%3A59%20PM"""

    FINVIZ_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": FINVIZ_COOKIE
    }

    try:
        import io
        url = (
            "https://elite.finviz.com/export.ashx?v=111"
            "&f=sh_price_u11,sh_float_u15,sh_curvol_o50,ta_change_u"
            "&o=-volume"
        )

        response = requests.get(url, headers=FINVIZ_HEADERS, timeout=15)
        if response.status_code == 200:
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)
            if 'Ticker' in df.columns and 'Price' in df.columns:
                df = df[(df['Price'] >= 0.02) & (df['Price'] <= 11.0)]
                tickers = df['Ticker'].head(5).tolist()  # اختبار مع 5 فقط
                print(f"✅ تم جلب {len(tickers)} سهم من Finviz Elite (اختبار)")
                return tickers
    except Exception as e:
        print(f"❌ خطأ في جلب الأسهم: {str(e)}")

    return []

# =========================================================
# 3. وظائف التحليل والفرز
# =========================================================
def evaluate_liquidity(volume, float_val):
    if not float_val or float_val == 0:
        return "غير محدد", 0
    rotation_pct = (volume / float_val) * 100
    if rotation_pct >= 5.0:
        return "🔥🔥 انفجار", rotation_pct
    elif rotation_pct >= 2.0:
        return "🔥 ممتاز", rotation_pct
    elif rotation_pct >= 0.5:
        return "✅ نشط", rotation_pct
    return "💤 ضعيف", rotation_pct

def get_shariah_label(symbol):
    data = shariah_db.get(symbol)
    return "✅ حلال" if data and data.get('status') == 'halal' else "🚫 غير متوفر"

def check_ladder_pattern(df_window, float_val):
    if len(df_window) < 3:
        return False, 0, 0, "بيانات قليلة"

    try:
        recent = df_window.tail(3).reset_index(drop=True)
        candles = recent.to_dict('records')
        
        c1 = candles[0]
        c2 = candles[1]
        c3 = candles[2]
        
        if not (c2['Close'] > c2['Open'] and c3['Close'] > c3['Open']):
            return False, 0, 0, "شموع حمراء"
        
        if not (c3['High'] >= c2['High'] and c2['High'] >= c1['High']):
            return False, 0, 0, "قمم غير صاعدة"
        
        if not (c3['Low'] >= c2['Low'] and c2['Low'] >= c1['Low']):
            return False, 0, 0, "قيعان غير صاعدة"
        
        strength = 60  # نقطة أساسية للاختبار
        
        morning_high = c3['High']
        return True, strength, morning_high, "نموذج سليم"

    except Exception as e:
        return False, 0, 0, f"خطأ: {str(e)}"

def analyze_stock(symbol, now_ny):
    """فحص سهم واحد - تشغيل متوازي آمن"""
    try:
        df = get_fmp_data(symbol, now_ny)
        if df.empty:
            return None

        mask = (df.index.time >= time(9, 30)) & (df.index.time <= time(10, 0))
        setup = df[mask]

        if setup.empty or len(setup) < 3:
            return None

        candles_dict = {
            symbol: [
                {
                    'time': str(idx),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                }
                for idx, row in setup.iterrows()
            ]
        }

        float_val = get_float_shares(symbol)
        is_valid, strength, high, reason = check_ladder_pattern(setup, float_val)

        if is_valid:
            vol_sum = setup['Volume'].sum()
            liq_msg, liq_pct = evaluate_liquidity(vol_sum, float_val)

            if liq_pct < 0.2:
                return None

            current_p = float(setup['Close'].iloc[-1])
            shariah = get_shariah_label(symbol)
            flag = get_country_flag(symbol)

            print(f"  📊 {symbol}: الشموع = {len(setup)}, الشموع المحفوظة = {len(candles_dict[symbol])}")

            return (symbol, strength, candles_dict, {
                'symbol': symbol,
                'strength': strength,
                'current_price': current_p,
                'high': high,
                'liquidity': liq_msg,
                'liquidity_pct': liq_pct,
                'shariah': shariah,
                'flag': flag,
                'candles': candles_dict[symbol]
            })
    except Exception as e:
        print(f"⚠️ خطأ في {symbol}: {e}")
    
    return None

def main():
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    
    print("="*50)
    print(f"🧪 اختبار MORNING SCANNER - TEST MODE")
    print("="*50)
    print(f"📅 التاريخ: {now_ny.strftime('%Y-%m-%d %A')}")
    print(f"⏰ الوقت: {now_ny.strftime('%H:%M:%S')} NY")
    print("="*50)

    # جلب قائمة الأسهم (5 فقط للاختبار)
    tickers = get_screener_stocks()
    if not tickers:
        print("❌ لم يتم جلب أي أسهم")
        return

    print(f"\n🚀 بدء فحص {len(tickers)} سهم بالتوازي...")
    matches = 0
    successful_stocks = []
    all_candles = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda s: analyze_stock(s, now_ny), tickers))
    
    for res in results:
        if res:
            symbol, strength, candles_dict, success_data = res
            print(f"✅ {symbol}: مقبول ({strength}%)")
            matches += 1
            successful_stocks.append(success_data)
            all_candles.update(candles_dict)

    print("\n" + "="*50)
    print("📋 النتائج النهائية:")
    print("="*50)

    # حفظ بيانات الشموع
    if all_candles:
        if save_json_file(CANDLES_DATA_FILE, all_candles):
            print(f"✅ عدد الأسهم مع شموع محفوظة: {len(all_candles)}")
    else:
        print("⚠️ لم يتم جمع أي بيانات شموع")
    
    # حفظ الأسهم الناجحة
    if successful_stocks:
        if save_json_file(SUCCESSFUL_PATTERNS_FILE, successful_stocks):
            print(f"✅ عدد الأسهم الناجحة المحفوظة: {len(successful_stocks)}")
    else:
        print("⚠️ لم يتم إيجاد أسهم ناجحة")

    print(f"\n�� النتائج النهائية: {matches} أسهم ناجحة")
    print("✅ الاختبار اكتمل بنجاح!")

if __name__ == "__main__":
    main()
