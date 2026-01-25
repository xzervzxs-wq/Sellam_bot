import requests
import pandas as pd
import io
import os
import pytz
import json
import re
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv
import concurrent.futures

# ==============================================================================
# 🔑 إعدادات البيئة
# ==============================================================================
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MAX_WORKERS = 15  # تسريع أكثر لمعالجة 150 سهم
FLOAT_CACHE_FILE = "float_cache.json"

# ==============================================================================
# 🛠️ أدوات التنظيف والجلب
# ==============================================================================
def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json_file(filename, data):
    try:
        with open(filename, 'w') as f: json.dump(data, f, indent=4)
    except: pass

float_cache = load_json_file(FLOAT_CACHE_FILE)

def get_float_shares_safe(symbol):
    if symbol in float_cache: return float_cache[symbol]
    try:
        ticker = yf.Ticker(symbol)
        val = ticker.info.get('floatShares') or ticker.info.get('sharesOutstanding') or 0
        if val > 0:
            float_cache[symbol] = val
            save_json_file(FLOAT_CACHE_FILE, float_cache)
            return val
    except: return 0

# ==============================================================================
# 📊 جلب الأسهم من FMP Stock Screener
# ==============================================================================
def fetch_nasdaq_under_10():
    """جلب أسهم NASDAQ بسعر أقل من 10 دولار من FMP"""
    try:
        screener_url = f"https://financialmodelingprep.com/stable/company-screener?limit=5000&apikey={FMP_API_KEY}"
        
        print("🔄 جاري جلب أسهم NASDAQ من FMP API...")
        response = requests.get(screener_url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print("⚠️ لا توجد بيانات")
            return []
        
        # تحويل إلى DataFrame
        df = pd.DataFrame(data)
        
        # استبعاد ETFs والـ Funds
        df = df[
            (df.get('isEtf', False) == False) & 
            (df.get('isFund', False) == False)
        ]
        
        # تحويل السعر وفلترة < 10 دولار
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df[df['price'] < 10].copy()
        
        # ترتيب حسب Volume
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df = df.sort_values('volume', ascending=False, na_position='last')
        
        # أخذ أفضل 150 سهم
        symbols = df['symbol'].head(150).tolist()
        
        print(f"✅ تم جلب {len(symbols)} سهم بسعر < $10")
        return symbols
    
    except Exception as e:
        print(f"❌ خطأ في جلب الأسهم: {e}")
        return []

# ==============================================================================
# 📈 جلب بيانات الشموع من 9:30 إلى 10:00 صباح اليوم
# ==============================================================================
def get_morning_candles(symbol, interval='5min'):
    """
    جلب بيانات الشموع من 9:30 إلى 10:00 صباح اليوم من FMP API
    interval: 5min = 5 دقائق, 1min = دقيقة واحدة
    """
    try:
        # استخدام FMP Intraday API
        url = f"https://financialmodelingprep.com/stable/historical-chart/{interval}?symbol={symbol}&apikey={FMP_API_KEY}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # البيانات تأتي كـ list مباشرة
        if not data or not isinstance(data, list):
            return None
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
        
        # تحويل العمود date إلى datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # تحويل الـ timezone إلى Eastern Time
        df['date'] = df['date'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')
        
        # تعيين date كـ index
        df.set_index('date', inplace=True)
        
        # تحويل الأعمدة إلى أرقام
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # إعادة تسمية الأعمدة لتطابق yfinance
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        # فلترة البيانات من 9:30 إلى 10:00 صباحاً
        morning_data = df.between_time('09:30', '10:00')
        
        if morning_data.empty:
            return None
        
        return morning_data
    
    except Exception as e:
        return None

# ==============================================================================
# 🧠 فحص استراتيجية السلم الصاعد (Ladder Strategy)
# ==============================================================================
def evaluate_ladder_strategy(ticker):
    """
    تقييم استراتيجية السلم الصاعد على بيانات 9:30-10:00 الصباح
    """
    try:
        # جلب بيانات الشموع من 9:30 إلى 10:00
        day_data = get_morning_candles(ticker, interval='5min')
        
        if day_data is None or len(day_data) < 3:
            return None
        
        # شمعات آخر ثلاث شموع في الفترة
        c1 = day_data.iloc[-3]  # الشمعة قبل السابقة
        c2 = day_data.iloc[-2]  # الشمعة السابقة
        c3 = day_data.iloc[-1]  # الشمعة الحالية
        
        # شرط السلم الصاعد: 
        # - آخر شمعتين خضراء (Close > Open)
        # - كل شمعة أعلى من السابقة في القيعان (Low)
        if c3['Close'] > c3['Open'] and c2['Close'] > c2['Open']:
            if c3['Low'] >= c2['Low'] and c2['Low'] >= c1['Low']:
                
                current_price = float(c3['Close'])
                morning_high = day_data['High'].max()
                morning_low = day_data['Low'].min()
                
                # حساب الحجم
                total_volume = day_data['Volume'].sum()
                
                # الوقت الحالي
                current_time = c3.name.strftime('%H:%M:%S')
                
                # رسالة التنبيه
                msg = (
                    f"🪜 استراتيجية السلم الصاعد ✅\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"🏆 السهم: {ticker}\n"
                    f"💵 السعر الحالي: ${current_price:.2f}\n"
                    f"📈 أعلى السعر (9:30-10:00): ${morning_high:.2f}\n"
                    f"📉 أدنى السعر (9:30-10:00): ${morning_low:.2f}\n"
                    f"📊 إجمالي الحجم: {int(total_volume):,}\n"
                    f"⏰ الوقت: {current_time} ET\n"
                    f"━━━━━━━━━━━━━━━━━"
                )
                
                return msg
    
    except Exception as e:
        pass
    
    return None

# ==============================================================================
# 🚀 المشغل الرئيسي
# ==============================================================================
def main():
    print("="*80)
    print("🚀 بدء فحص الاستراتيجيات على أسهم NASDAQ < $10")
    print("="*80)
    
    # جلب الأسهم من FMP
    watch_list = fetch_nasdaq_under_10()
    
    if not watch_list:
        print("❌ فشل في جلب قائمة الأسهم")
        return
    
    print(f"\n📡 جاري فحص {len(watch_list)} سهم للاستراتيجيات...")
    print(f"📊 الفترة الزمنية: 9:30 - 10:00 صباحاً\n")
    
    signals = []
    
    # معالجة الأسهم بالتوازي لتسريع العملية
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(evaluate_ladder_strategy, watch_list))
        
        for i, msg in enumerate(results, 1):
            if msg:
                signals.append(msg)
                print(f"✅ [{i}/{len(watch_list)}] تم العثور على فرصة!")
            
            # طباعة تقدم العملية كل 20 سهم
            if i % 20 == 0:
                print(f"⏳ تم فحص {i}/{len(watch_list)} سهم...")
    
    print(f"\n{'='*80}")
    print(f"📊 النتائج النهائية:")
    print(f"✅ عدد الإشارات: {len(signals)}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # إرسال الإشارات للتيليجرام
    if signals:
        # رسالة البداية
        start_msg = (
            f"🚨 تنبيهات استراتيجيات الاسهم\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 الفترة: 9:30 - 10:00 صباحاً\n"
            f"✅ عدد الإشارات: {len(signals)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        print("📤 إرسال الإشارات للتيليجرام...")
        send_telegram_message(start_msg)
        
        # إرسال كل إشارة
        for i, signal in enumerate(signals, 1):
            send_telegram_message(signal)
            # استخراج اسم السهم من الرسالة
            ticker = signal.split('السهم:')[1].split('\n')[0].strip()
            print(f"✅ [{i}] {ticker}")
        
        # رسالة الإنهاء
        end_msg = f"{'━'*30}\n✅ انتهى الفحص - تم إرسال {len(signals)} إشارة"
        send_telegram_message(end_msg)
        
        print(f"\n✅ تم إرسال {len(signals)} إشارة للتيليجرام")
    else:
        print("⚠️ لم يتم العثور على أي إشارات")
        send_telegram_message(
            f"📊 تقرير الاستراتيجيات\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⚠️ لم يتم العثور على إشارات اليوم"
        )
    
    print(f"\n{'='*80}")
    print("🏁 انتهت دورة الفحص.\n")

# ==============================================================================
# 📲 إرسال الرسائل للتيليجرام
# ==============================================================================
def send_telegram_message(message):
    """إرسال رسالة إلى التيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")
        return False

if __name__ == "__main__":
    main()
