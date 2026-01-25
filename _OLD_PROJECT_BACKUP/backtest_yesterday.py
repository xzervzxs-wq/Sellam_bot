import pandas as pd
import warnings
from datetime import datetime, time, timedelta
import requests
import os
import json
import time as time_module
import pytz
from dotenv import load_dotenv

# =========================================================
# 1. إعدادات EODHD
# =========================================================
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "AzN1tXfit4MUgxLSvWO73Wusjz8f2v21")

TELEGRAM_BOT_TOKEN = "8130586876:AAFZBPEDJ2o-WOyqDOhltG69lnw2YN0-bDg"
TELEGRAM_CHAT_ID = "237657512"

warnings.simplefilter(action='ignore', category=FutureWarning)
FLOAT_CACHE_FILE = "float_cache.json"
SHARIAH_FILE = "shariah_stocks_master.json"

# تحميل قاعدة البيانات الشرعية
def load_shariah_db():
    if os.path.exists(SHARIAH_FILE):
        try:
            with open(SHARIAH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

shariah_db = load_shariah_db()
print(f"🕌 تم تحميل {len(shariah_db)} سهم من قاعدة البيانات الشرعية.")

# =========================================================
# 2. أدوات جلب البيانات من EODHD
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
    except: pass

float_data_store = load_json_file(FLOAT_CACHE_FILE)

def get_float_shares(symbol):
    """جلب عدد الأسهم العائمة من FMP"""
    global float_data_store
    val = float_data_store.get(symbol)
    if isinstance(val, (int, float)) and val > 0:
        return val

    try:
        url = f"https://financialmodelingprep.com/stable/shares-float"
        params = {'symbol': symbol, 'apikey': FMP_API_KEY}
        data = requests.get(url, params=params, timeout=5).json()
        if data and isinstance(data, list) and len(data) > 0:
            val = float(data[0].get('floatShares', 0))
            if val > 0:
                float_data_store[symbol] = val
                save_json_file(FLOAT_CACHE_FILE, float_data_store)
                return val
    except Exception as e:
        pass
    return 0

def get_eodhd_data(symbol, target_date):
    """جلب بيانات EODHD للتاريخ المطلوب"""
    try:
        date_str = target_date.strftime('%Y-%m-%d')
        
        # استخدام EODHD Intraday API
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': int(datetime(target_date.year, target_date.month, target_date.day, 9, 30).timestamp()),
            'to': int(datetime(target_date.year, target_date.month, target_date.day, 10, 0).timestamp()),
            'period': '5m'  # 5 دقائق
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return pd.DataFrame()
        
        data = response.json()
        
        if not data or 'candles' not in data or not data['candles']:
            return pd.DataFrame()
        
        df = pd.DataFrame(data['candles'])
        
        if df.empty:
            return pd.DataFrame()
        
        # تحويل الـ timestamp
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.set_index('datetime').sort_index()
        
        # تحويل إلى توقيت نيويورك
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York')
        
        # إعادة تسمية الأعمدة
        df.rename(columns={
            'open': 'Open', 
            'high': 'High', 
            'low': 'Low',
            'close': 'Close', 
            'volume': 'Volume'
        }, inplace=True)
        
        return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب {symbol} من EODHD: {str(e)}")
        return pd.DataFrame()

def get_country_flag(symbol):
    """جلب علم الدولة"""
    try:
        url = f"https://financialmodelingprep.com/stable/profile/{symbol}"
        params = {'apikey': FMP_API_KEY}
        data = requests.get(url, params=params, timeout=5).json()
        if data and isinstance(data, list) and len(data) > 0:
            country = data[0].get('country', 'US')
            if len(country) == 2:
                return "".join([chr(ord(c.upper()) + 127397) for c in country])
    except: pass
    return "🇺🇸"

def evaluate_liquidity(volume, float_val):
    """تقييم السيولة"""
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
    """التحقق من الحلال"""
    data = shariah_db.get(symbol)
    return "✅ حلال" if data and data.get('status') == 'halal' else "🚫 غير متوفر"

def check_ladder_pattern(df_window, float_val):
    """فحص نمط السلم الصاعد"""
    if len(df_window) < 3:
        return False, 0, 0, "بيانات قليلة"

    try:
        candles = [row.to_dict() for _, row in df_window.iterrows()]
        start_price = float(candles[0]['Open'])
        current_price = float(candles[-1]['Close'])
        morning_high = float(df_window['High'].max())

        if current_price <= start_price:
            return False, 0, 0, "هابط"

        # التحقق من الشمعتين الأوليتين خضراوتين
        if not (candles[0]['Close'] > candles[0]['Open'] and
                candles[1]['Close'] > candles[1]['Open']):
            return False, 0, 0, "بداية حمراء"

        # فحص القمم الصاعدة
        highest_high = float(candles[0]['High'])
        new_highs = 0
        for i in range(1, len(candles)):
            curr_high = float(candles[i]['High'])
            if curr_high > highest_high:
                highest_high = curr_high
                new_highs += 1

        if new_highs < 1:
            return False, 0, morning_high, "لا توجد قمم صاعدة"

        strength = min(100, int((new_highs / len(candles)) * 150))
        return True, strength, morning_high, "نموذج سليم"

    except Exception as e:
        return False, 0, 0, f"خطأ: {str(e)}"

def save_backtest_results(results, target_date):
    """حفظ نتائج الاختبار في ملف CSV"""
    if not results:
        print("⚠️ لا توجد نتائج للحفظ")
        return None
    
    df_results = pd.DataFrame(results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    date_str = target_date.strftime('%Y%m%d')
    filename = f"backtest_results_{date_str}_{timestamp}.csv"
    
    df_results.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ تم حفظ نتائج الاختبار في: {filename}")
    return filename

# =========================================================
# 3. البوت الرئيسي للاختبار
# =========================================================
def main():
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    
    # تحديد تاريخ البارحة (22 ديسمبر)
    target_date = now_ny.date() - timedelta(days=1)
    
    print("="*60)
    print(f"🧪 BACKTEST LADDER STRATEGY (EODHD)")
    print("="*60)
    print(f"📅 التاريخ: {target_date.strftime('%Y-%m-%d %A')}")
    print(f"⏰ الفترة: 9:30 AM - 10:00 AM EST")
    print(f"📊 مصدر البيانات: EODHD\n")
    
    # قائمة 300 سهم
    print("📋 جاري تحميل قائمة الأسهم...")
    try:
        stocks_df = pd.read_csv('finviz_300_stocks.csv')
        tickers = stocks_df['symbol'].tolist()
        print(f"✅ تم تحميل {len(tickers)} سهم\n")
    except:
        print("❌ لم يتم العثور على ملف الأسهم")
        return
    
    print(f"🚀 بدء الاختبار على {len(tickers)} سهم...\n")
    
    matches = 0
    successful_stocks = []
    backtest_results = []
    failed_symbols = []
    
    for i, symbol in enumerate(tickers, 1):
        try:
            print(f"⏳ [{i}/{len(tickers)}] اختبار {symbol}...", end='\r')
            
            # جلب البيانات من EODHD
            df = get_eodhd_data(symbol, target_date)
            
            if df.empty:
                failed_symbols.append(symbol)
                continue
            
            # فلتر الشموع من 9:30 إلى 10:00
            mask = (df.index.time >= time(9, 30)) & (df.index.time <= time(10, 0))
            setup = df[mask]
            
            if setup.empty or len(setup) < 3:
                continue
            
            # جلب البيانات الإضافية
            float_val = get_float_shares(symbol)
            is_valid, strength, high, reason = check_ladder_pattern(setup, float_val)
            
            if is_valid:
                vol_sum = setup['Volume'].sum()
                liq_msg, liq_pct = evaluate_liquidity(vol_sum, float_val)
                
                current_p = float(setup['Close'].iloc[-1])
                shariah = get_shariah_label(symbol)
                flag = get_country_flag(symbol)
                
                # تسجيل النتيجة
                backtest_results.append({
                    'date': target_date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strength': strength,
                    'current_price': current_p,
                    'high_price': high,
                    'volume': vol_sum,
                    'liquidity': liq_msg,
                    'liquidity_percent': liq_pct,
                    'shariah_status': shariah,
                    'flag': flag,
                    'status': 'SIGNAL'
                })
                
                print(f"\n✅ {symbol}: سلم صاعد ({strength}%)")
                matches += 1
                successful_stocks.append((symbol, strength))
                time_module.sleep(0.3)
        
        except Exception as e:
            print(f"\n⚠️ خطأ في {symbol}: {str(e)}")
            continue
    
    # الملخص النهائي
    print(f"\n\n{'='*60}")
    print(f"📊 نتائج الاختبار:")
    print(f"{'='*60}")
    print(f"📅 التاريخ: {target_date.strftime('%Y-%m-%d')}")
    print(f"✅ الإشارات المكتشفة: {matches}")
    print(f"❌ الأسهم بدون بيانات: {len(failed_symbols)}")
    print(f"📈 إجمالي الأسهم المفحوصة: {len(tickers)}")
    
    if successful_stocks:
        successful_stocks.sort(key=lambda x: x[1], reverse=True)
        print(f"\n🏆 الأسهم الرابحة:")
        print("-" * 60)
        
        for idx, (stock, score) in enumerate(successful_stocks, 1):
            stars = "⭐️⭐️⭐️⭐️⭐️" if score >= 90 else ("⭐️⭐️⭐️" if score >= 70 else "⭐️")
            print(f"{idx}. {stock:<10} | القوة: {score}% {stars}")
    
    # حفظ النتائج
    if backtest_results:
        csv_file = save_backtest_results(backtest_results, target_date)
        print(f"\n✅ تم حفظ {len(backtest_results)} إشارة في الملف")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
