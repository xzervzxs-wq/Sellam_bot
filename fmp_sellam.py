import pandas as pd
import warnings
from datetime import datetime, time
import requests
import os
import json
import time as time_module
import pytz
from dotenv import load_dotenv

# =========================================================
# 1. إعدادات ومفاتيح التشغيل (FMP STABLE VERSION)
# =========================================================
load_dotenv()
API_KEY = os.getenv("FMP_API_KEY", "AzN1tXfit4MUgxLSvWO73Wusjz8f2v21")

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
    """حفظ البيانات - إضافة على البيانات الموجودة وليس استبدالها"""
    try:
        existing_data = {}
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = {}
        
        # إذا كان الملف candles_data.json → دمج القواموس
        if filename == CANDLES_DATA_FILE and isinstance(existing_data, dict) and isinstance(data, dict):
            existing_data.update(data)
            data = existing_data
        
        # إذا كان successful_patterns.json → إضافة على القائمة
        elif filename == SUCCESSFUL_PATTERNS_FILE and isinstance(existing_data, list) and isinstance(data, list):
            data = existing_data + data
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

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

    try:
        # استخدام الرابط الصحيح للفلوت من FMP Stable
        url = f"https://financialmodelingprep.com/stable/shares-float"
        params = {'symbol': symbol, 'apikey': API_KEY}
        data = requests.get(url, params=params, timeout=5).json()
        if data and isinstance(data, list) and len(data) > 0:
            val = float(data[0].get('floatShares', 0))
            if val > 0:
                float_data_store[symbol] = val
                save_json_file(FLOAT_CACHE_FILE, float_data_store)
                return val
    except Exception as e:
        print(f"⚠️ خطأ في جلب الفلوت لـ {symbol}: {str(e)}")
    return 0

def get_fmp_data(symbol, target_date):
    """جلب شموع 1 دقيقة من FMP Stable (live data) وتجميعها إلى 5 دقائق"""
    try:
        date_str = target_date.strftime('%Y-%m-%d')
        # استخدام Stable API endpoint للبيانات الحية (1-minute real-time)
        url = f"https://financialmodelingprep.com/stable/historical-chart/1min/{symbol}"
        params = {
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

        # تحويل إلى توقيت نيويورك
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York')

        # إعادة تسمية الأعمدة
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low',
                          'close': 'Close', 'volume': 'Volume'}, inplace=True)
        
        # تجميع شموع 1-دقيقة إلى شموع 5-دقائق
        df_5min = df.resample('5T').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return df_5min
    except Exception as e:
        print(f"⚠️ خطأ في جلب بيانات {symbol}: {str(e)}")
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
                tickers = df['Ticker'].head(300).tolist()
                print(f"✅ تم جلب {len(tickers)} سهم من Finviz Elite")
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
    """
    فحص نمط السلم الصاعد - نفس الشروط من backtest_strategies.py
    
    الشروط الأساسية (4 شروط يجب أن تتحقق جميعاً):
    1. الشمعة 2: Close > Open (خضراء)
    2. الشمعة 3: Close > Open (خضراء)
    3. High3 >= High2 >= High1 (قمم صاعدة)
    4. Low3 >= Low2 >= Low1 (قيعان صاعدة)
    """
    if len(df_window) < 3:
        return False, 0, 0, "بيانات قليلة"

    try:
        # الحصول على آخر 3 شموع
        recent = df_window.tail(3).reset_index(drop=True)
        candles = recent.to_dict('records')
        
        c1 = candles[0]  # الشمعة الأولى (الأقدم)
        c2 = candles[1]  # الشمعة الثانية
        c3 = candles[2]  # الشمعة الثالثة (الأحدث)
        
        # الشرط 1: التحقق من الشمعتين الأخيرتين خضراوتين
        if not (c2['Close'] > c2['Open'] and c3['Close'] > c3['Open']):
            return False, 0, 0, "شموع حمراء"
        
        # الشرط 2: التحقق من القمم الصاعدة
        if not (c3['High'] >= c2['High'] and c2['High'] >= c1['High']):
            return False, 0, 0, "قمم غير صاعدة"
        
        # الشرط 3: التحقق من القيعان الصاعدة
        if not (c3['Low'] >= c2['Low'] and c2['Low'] >= c1['Low']):
            return False, 0, 0, "قيعان غير صاعدة"
        
        # الشرط 4: حساب قوة الإشارة (نفس الصيغة بالضبط)
        high_range = c3['High'] - c1['High']
        low_range = c3['Low'] - c1['Low']
        strength = min(100, int(((high_range + low_range) / (c1['Close'] * 2)) * 100))
        strength = max(strength, 30)  # حد أدنى 30%
        
        morning_high = c3['High']
        return True, strength, morning_high, "نموذج سليم"

    except Exception as e:
        return False, 0, 0, f"خطأ: {str(e)}"

def send_telegram(message):
    """إرسال رسالة إلى تليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ فشل إرسال التليجرام: {str(e)}")

# =========================================================
# 4. البوت الرئيسي
# =========================================================
def wait_for_10_02_am():
    """انتظر حتى الساعة 10:02 صباحاً بتوقيت نيويورك"""
    ny_tz = pytz.timezone('America/New_York')
    target_time = time(10, 2, 0)  # 10:02:00 AM
    
    while True:
        now_ny = datetime.now(ny_tz)
        current_time = now_ny.time()
        
        if current_time >= target_time and current_time < time(10, 3, 0):
            print(f"✅ وصلنا الساعة 10:02 AM! الوقت الحالي: {current_time}")
            return now_ny.date()
        
        # إذا كنا قبل الساعة 10:02، انتظر
        if current_time < target_time:
            wait_seconds = (
                datetime.combine(now_ny.date(), target_time) - 
                datetime.combine(now_ny.date(), current_time)
            ).total_seconds()
            print(f"⏳ انتظار حتى 10:02 AM... ({int(wait_seconds)} ثانية متبقية)")
            time_module.sleep(min(60, wait_seconds))
        else:
            # إذا تجاوزنا الساعة 10:02، انتظر حتى غداً
            print("⏰ تجاوزنا الساعة 10:02 اليوم، سننتظر حتى غداً...")
            time_module.sleep(3600)

def main():
    ny_tz = pytz.timezone('America/New_York')
    
    print("="*50)
    print(f"🛡️ MORNING SCANNER (FMP 1-MIN TO 5-MIN)")
    print("="*50)
    print("⏰ البرنامج في وضع الانتظار...")
    print("📍 سيبدأ تحليل البيانات عند الساعة 10:02 AM بتوقيت نيويورك")
    
    # انتظر حتى الساعة 10:02 AM
    target_date = wait_for_10_02_am()
    
    now_ny = datetime.now(ny_tz)
    print("="*50)
    print(f"🚀 بدء التحليل!")
    print(f"📅 التاريخ: {now_ny.strftime('%Y-%m-%d %A')}")
    print(f"⏰ الوقت: {now_ny.strftime('%H:%M:%S')} NY")
    print("="*50)

    # جلب قائمة الأسهم
    tickers = get_screener_stocks()
    if not tickers:
        print("❌ لم يتم جلب أي أسهم")
        return

    print(f"\n🚀 بدء فحص {len(tickers)} سهم...")
    matches = 0
    successful_stocks = []

    for i, symbol in enumerate(tickers, 1):
        try:
            print(f"⏳ [{i}/{len(tickers)}] فحص {symbol}...", end='\r')

            df = get_fmp_data(symbol, now_ny)
            if df.empty:
                continue

            # فلتر الشموع من 9:30 إلى 10:00 (5-دقائق)
            mask = (df.index.time >= time(9, 30)) & (df.index.time <= time(10, 0))
            setup = df[mask]

            if setup.empty or len(setup) < 3:
                continue

            float_val = get_float_shares(symbol)
            is_valid, strength, high, reason = check_ladder_pattern(setup, float_val)

            if is_valid:
                vol_sum = setup['Volume'].sum()
                liq_msg, liq_pct = evaluate_liquidity(vol_sum, float_val)

                if liq_pct < 0.2:
                    continue

                current_p = float(setup['Close'].iloc[-1])
                shariah = get_shariah_label(symbol)
                flag = get_country_flag(symbol)

                action = "🚀 دخول مباشر" if current_p >= high * 0.99 else f"✋ معلق: ${high+0.01:.3f}"
                stars = "⭐️⭐️⭐️⭐️⭐️" if strength >= 90 else ("⭐️⭐️⭐️" if strength >= 70 else "⭐️")

                msg = (
                    f"🪜 **سلم صاعد**\n"
                    f"🔋 **القوة:** {strength}% {stars}\n\n"
                    f"🏆: *{symbol}* {flag}\n"
                    f"💵: ${current_p:.3f} | 🎯: ${high:.3f}\n"
                    f"💧: {liq_msg} ({liq_pct:.1f}%)\n"
                    f"⚖️: {shariah}\n"
                    f"---------------------------\n"
                    f"{action}"
                )

                send_telegram(msg)
                print(f"\n✅ {symbol}: مقبول ({strength}%)")
                matches += 1
                successful_stocks.append((symbol, strength))
                time_module.sleep(0.5)

        except Exception as e:
            print(f"\n⚠️ خطأ في {symbol}: {str(e)}")
            continue

    print(f"\n\n🏁 النتائج النهائية: {matches}")

    # إرسال الملخص
    if successful_stocks:
        successful_stocks.sort(key=lambda x: x[1], reverse=True)

        summary = "📊 *ملخص الأسهم اليوم*\n"
        summary += f"📅 التاريخ: {target_date}\n"
        summary += f"✅ عدد الأسهم: {matches}\n\n"

        for stock, score in successful_stocks:
            stars = "⭐️⭐️⭐️⭐️⭐️" if score >= 90 else ("⭐️⭐️⭐️" if score >= 70 else "⭐️")
            summary += f"• *{stock}*: {score}% {stars}\n"

        send_telegram(summary)
        print(f"✅ تم إرسال الملخص على تليجرام")

if __name__ == "__main__":
    main()
