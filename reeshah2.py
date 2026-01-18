import pandas as pd
import numpy as np
import warnings
from datetime import datetime, time
import requests
import os
import json
import time as tm
import pytz
from dotenv import load_dotenv
import yfinance as yf

# =========================================================
# 1. إعدادات ومفاتيح التشغيل
# =========================================================
load_dotenv()
API_KEY = os.getenv('FMP_API_KEY')
EODHD_API_KEY = os.getenv('EODHD_API_KEY', '68c0ad0b52af78.88121932')

if not API_KEY:
    print("❌ خطأ: لم يتم العثور على FMP_API_KEY")
    exit()

TELEGRAM_BOT_TOKEN = "8130586876:AAFZBPEDJ2o-WOyqDOhltG69lnw2YN0-bDg"
TELEGRAM_CHAT_ID = "237657512"

warnings.simplefilter(action='ignore', category=FutureWarning)

FLOAT_CACHE_FILE = "float_cache.json"
SUCCESSFUL_PATTERNS_FILE = "successful_candles.csv"

# =========================================================
# 2. أدوات مساعدة
# =========================================================
def fmt_shares(n):
    if not isinstance(n, (int, float)): return "غير متاح"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000: return f"{n/1_000:.1f}K".replace(".0K", "K")
    return str(int(n))

def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_json_file(filename, data):
    try:
        with open(filename, 'w') as f: json.dump(data, f)
    except: pass

float_data_store = load_json_file(FLOAT_CACHE_FILE)

# =========================================================
# 3. جلب 100 سهم (نفس طريقة reeshah.py بالضبط)
# =========================================================
def get_100_stocks():
    """جلب 100 سهم بنفس طريقة reeshah.py"""
    global float_data_store
    print("📦 جاري سحب 100 سهم من FMP Screener...")

    # 🔥 فلتر السعر: $3-$100 (أسهم أقوى)
    # ✅ رابط FMP الجديد (stable)
    url = (f"https://financialmodelingprep.com/stable/company-screener"
           f"?priceMoreThan=3&priceLowerThan=100&volumeMoreThan=200000"
           f"&isEtf=false&exchange=nasdaq,nyse,amex&isActivelyTrading=true&limit=1000&apikey={API_KEY}")

    try:
        results = requests.get(url, timeout=20).json()
        if not results: 
            print("❌ فشل جلب البيانات من Screener")
            return []

        # ترتيب حسب الفوليوم
        results.sort(key=lambda x: x.get('volume', 0), reverse=True)

        final_list = []
        for item in results:
            # إذا اكتفينا بـ 100 سهم نوقف
            if len(final_list) >= 100: 
                break

            try:
                sym = item.get('symbol')
                if not sym or len(sym) > 5: 
                    continue

                origin_country = item.get('country', 'US')

                # جلب الفلوت من الكاش أو API
                if sym in float_data_store:
                    raw_val = float_data_store[sym]
                    # إصلاح الكاش القديم (dict)
                    if isinstance(raw_val, dict):
                        raw_val = raw_val.get('value', 0)
                else:
                    raw_val = 0

                    # 1️⃣ محاولة Yahoo Finance أولاً
                    try:
                        ticker_obj = yf.Ticker(sym)
                        info = ticker_obj.info
                        yahoo_float = info.get('floatShares', 0)
                        if yahoo_float and yahoo_float > 0:
                            raw_val = yahoo_float
                    except:
                        pass

                    # 2️⃣ إذا Yahoo فشل، جرب FMP (رابط جديد stable)
                    if raw_val == 0:
                        try:
                            f_url = f"https://financialmodelingprep.com/stable/shares-float?symbol={sym}&apikey={API_KEY}"
                            f_data = requests.get(f_url, timeout=3).json()
                            if f_data and isinstance(f_data, list):
                                raw_val = f_data[0].get('floatShares', 0)
                        except:
                            pass

                    float_data_store[sym] = raw_val
                    tm.sleep(0.05)

                # تحويل لرقم
                try:
                    f_shares = float(raw_val)
                except (ValueError, TypeError):
                    f_shares = 0

                # الشرط النهائي: فلوت أقل من 200 مليون
                if 0 < f_shares <= 200_000_000:
                    final_list.append({'symbol': sym, 'float': f_shares, 'country': origin_country})
                    print(f"📌 {len(final_list)}/100: {sym}")

            except Exception as e:
                continue

        save_json_file(FLOAT_CACHE_FILE, float_data_store)
        print(f"✅ تم جلب {len(final_list)} سهم")
        return final_list

    except Exception as e:
        print(f"❌ خطأ في Screener: {e}")
        return []

# =========================================================
# 4. جلب شموع 5 دقائق (FMP أولاً ثم EODHD)
# =========================================================
def get_intraday_candles(symbol, target_date=None):
    """جلب شموع 5 دقائق - FMP أولاً ثم EODHD"""
    
    # 1️⃣ محاولة FMP (رابط جديد stable)
    try:
        url = f"https://financialmodelingprep.com/stable/historical-chart/5min?symbol={symbol}&apikey={API_KEY}"
        resp = requests.get(url, timeout=8)
        
        if resp.status_code == 200:
            data = resp.json()
            if data and isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)

                # توحيد التوقيت لنيويورك
                if df.index.tz is None:
                    df.index = df.index.tz_localize('America/New_York')
                else:
                    df.index = df.index.tz_convert('America/New_York')

                # تنظيف الأعمدة
                for c in ['open', 'high', 'low', 'close', 'volume']:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                df.dropna(inplace=True)

                if len(df) > 0:
                    return df[['open', 'high', 'low', 'close', 'volume']]
    except:
        pass

    # 2️⃣ محاولة EODHD (الخطة البديلة)
    try:
        from_timestamp = int(tm.time()) - (10 * 24 * 60 * 60)  # آخر 10 أيام
        url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"
        
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None

        data = resp.json()
        if not data:
            return None

        df = pd.DataFrame(data)
        
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        elif 'datetime' in df.columns:
            df['date'] = pd.to_datetime(df['datetime'])
        else:
            return None

        df.set_index('date', inplace=True)

        for c in ['open', 'high', 'low', 'close', 'volume']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')

        df.dropna(inplace=True)

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df.index = df.index.tz_convert('America/New_York')

        df.sort_index(inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]

    except:
        return None

# =========================================================
# 5. تحميل الأنماط الناجحة
# =========================================================
def load_patterns():
    """تحميل أنماط VIVK و IOBT"""
    if not os.path.exists(SUCCESSFUL_PATTERNS_FILE):
        print("⚠️ ملف الأنماط غير موجود")
        return {}, {}

    try:
        df = pd.read_csv(SUCCESSFUL_PATTERNS_FILE)
        df.columns = df.columns.str.strip().str.lower()

        patterns = {}
        pattern_metrics = {}

        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 6:
                candles = group.iloc[:6][['open', 'high', 'low', 'close']].values

                candle_details = []
                for i in range(len(candles)):
                    o, h, l, c = candles[i]
                    body_pct = (c - o) / o * 100
                    candle_details.append({
                        'direction': 1 if c >= o else -1,
                        'body_pct': body_pct,
                        'body_size': abs(body_pct),
                        'open': o, 'high': h, 'low': l, 'close': c
                    })

                patterns[symbol] = candles
                pattern_metrics[symbol] = {
                    'candle_details': candle_details,
                    'avg_body': np.mean([cd['body_size'] for cd in candle_details])
                }

        print(f"✅ تم تحميل {len(patterns)} نمط")
        return patterns, pattern_metrics
    except Exception as e:
        print(f"❌ خطأ في تحميل الأنماط: {e}")
        return {}, {}

# =========================================================
# 6. مطابقة الأنماط (VIVK + IOBT فقط)
# =========================================================
ELITE_PATTERNS = ['VIVK', 'IOBT']
MATCH_THRESHOLD = 55

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    """مطابقة شمعة بشمعة مع VIVK و IOBT فقط"""
    if not reference_patterns:
        return 0, "None"

    current_details = []
    for i in range(len(current_candles)):
        o, h, l, c = current_candles[i][0], current_candles[i][1], current_candles[i][2], current_candles[i][3]
        body_pct = (c - o) / o * 100
        current_details.append({
            'body_pct': body_pct,
            'open': o, 'high': h, 'low': l, 'close': c
        })

    # شرط إلزامي: السهم صاعد
    curr_start = current_details[0]['open']
    curr_end = current_details[-1]['close']
    curr_trend = (curr_end - curr_start) / curr_start * 100

    if curr_trend <= 0:
        return 0, "None"

    best_score = 0
    best_name = "None"

    for name, ref_candles in reference_patterns.items():
        # فقط VIVK و IOBT
        if name not in ELITE_PATTERNS:
            continue
            
        if name not in pattern_metrics:
            continue

        ref_details = pattern_metrics[name]['candle_details']
        compare_len = min(len(current_details), len(ref_details))
        if compare_len < 3:
            continue

        # فحص القوة
        ref_avg_strength = np.mean([abs(d['body_pct']) for d in ref_details[:compare_len]])
        curr_avg_strength = np.mean([abs(d['body_pct']) for d in current_details[:compare_len]])
        
        if curr_avg_strength < ref_avg_strength * 0.8:
            continue
        
        total_similarity = 0
        
        for i in range(compare_len):
            curr_pct = current_details[i]['body_pct']
            ref_pct = ref_details[i]['body_pct']
            
            same_direction = (curr_pct >= 0 and ref_pct >= 0) or (curr_pct < 0 and ref_pct < 0)
            
            if not same_direction:
                candle_score = 0
            else:
                curr_abs = abs(curr_pct)
                ref_abs = abs(ref_pct)
                
                max_diff = max(ref_abs * 0.6, 0.5)
                actual_diff = abs(curr_abs - ref_abs)
                
                if actual_diff <= max_diff:
                    candle_score = 100 - (actual_diff / max_diff * 40)
                else:
                    overshoot = actual_diff - max_diff
                    candle_score = max(0, 60 - overshoot * 30)
            
            total_similarity += candle_score
        
        final_score = total_similarity / compare_len

        if final_score > best_score:
            best_score = final_score
            best_name = name

    return best_score, best_name

# =========================================================
# 7. إرسال تليجرام
# =========================================================
def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'},
            timeout=5
        )
    except: pass

# =========================================================
# 8. اختبار على تاريخ محدد
# =========================================================
def test_on_date(target_date_str):
    """اختبار على تاريخ محدد (مثل '2025-12-18')"""
    print(f"\n{'='*70}")
    print(f"🧪 اختبار على تاريخ: {target_date_str}")
    print(f"{'='*70}")
    
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    
    # تحميل الأنماط
    patterns, pattern_metrics = load_patterns()
    if not patterns:
        print("❌ لا توجد أنماط")
        return []
    
    # جلب 100 سهم
    stocks = get_100_stocks()
    if not stocks:
        print("❌ فشل جلب الأسهم")
        return []
    
    signals = []
    
    print(f"\n🔬 فحص {len(stocks)} سهم...")
    
    for item in stocks:
        symbol = item['symbol']
        float_shares = item['float']
        
        try:
            # جلب الشموع
            df = get_intraday_candles(symbol)
            if df is None or len(df) < 6:
                continue
            
            # فلترة اليوم المطلوب
            df_day = df[df.index.date == target_date]
            if len(df_day) < 6:
                continue
            
            # شموع الصباح فقط (9:30 - 9:55)
            df_morning = df_day.between_time('09:30', '09:55')
            if len(df_morning) < 3:
                continue
            
            # المطابقة
            candles = df_morning[['open', 'high', 'low', 'close']].values
            score, match_name = calculate_similarity(candles, patterns, pattern_metrics)
            
            if score >= MATCH_THRESHOLD and match_name in ELITE_PATTERNS:
                price = df_morning.iloc[-1]['close']
                
                # حساب أقصى ربح في اليوم
                df_after = df_day.between_time('10:00', '16:00')
                if len(df_after) > 0:
                    max_price = df_after['high'].max()
                    max_gain = (max_price - price) / price * 100
                else:
                    max_gain = 0
                
                signals.append({
                    'symbol': symbol,
                    'match_score': score,
                    'match_name': match_name,
                    'price': price,
                    'float': float_shares,
                    'max_gain': max_gain
                })
                
                print(f"✅ {symbol}: تطابق {score:.0f}% مع {match_name} | ربح +{max_gain:.1f}%")
        
        except Exception as e:
            continue
    
    print(f"\n{'='*70}")
    print(f"📊 النتائج: {len(signals)} إشارات")
    print(f"{'='*70}")
    
    if signals:
        print("\n📋 الإشارات:")
        for s in signals:
            status = "✅" if s['max_gain'] >= 2 else "🟡" if s['max_gain'] > 0 else "❌"
            print(f"   {status} {s['symbol']}: تطابق {s['match_score']:.0f}% مع {s['match_name']} | ربح +{s['max_gain']:.1f}%")
    
    return signals

# =========================================================
# 9. التشغيل الرئيسي (الوقت الحقيقي)
# =========================================================
def main():
    print("🛡️ البوت جاهز... بانتظار 10:00 NY")

    # تحميل الأنماط
    patterns, pattern_metrics = load_patterns()

    while True:
        ny_tz = pytz.timezone('America/New_York')
        now_ny = datetime.now(ny_tz)

        if now_ny.time() >= time(10, 3, 0):
            print("\n🚀 بدء الفحص...")

            stocks = get_100_stocks()
            if not stocks:
                print("❌ فشل جلب الأسهم")
                break

            matches = 0
            today = now_ny.date()

            for item in stocks:
                symbol = item['symbol']
                float_shares = item['float']

                try:
                    df = get_intraday_candles(symbol)
                    if df is None or len(df) < 6:
                        continue

                    df_today = df[df.index.date == today]
                    if len(df_today) < 6:
                        continue

                    df_morning = df_today.between_time('09:30', '09:55')
                    if len(df_morning) < 3:
                        continue

                    candles = df_morning[['open', 'high', 'low', 'close']].values
                    score, match_name = calculate_similarity(candles, patterns, pattern_metrics)

                    if score >= MATCH_THRESHOLD and match_name in ELITE_PATTERNS:
                        price = df_morning.iloc[-1]['close']
                        
                        msg = (
                            f"🧬 <b>إشارة نمط!</b>\n\n"
                            f"✅ السهم: <code>{symbol}</code>\n"
                            f"🎯 تطابق: <b>{score:.0f}%</b> مع {match_name}\n"
                            f"💵 السعر: <b>${price:.2f}</b>\n"
                            f"🪶 الفلوت: {fmt_shares(float_shares)}"
                        )
                        send_telegram(msg)
                        print(f"✅ {symbol}: {score:.0f}% مع {match_name}")
                        matches += 1

                except Exception as e:
                    continue

            if matches == 0:
                send_telegram("❌ لا توجد إشارات اليوم")
                print("❌ لا توجد إشارات")
            else:
                print(f"🏁 تم إرسال {matches} إشارات")

            break
        else:
            print(f"⏳ {now_ny.strftime('%H:%M:%S')} NY - انتظار...", end='\r')
            tm.sleep(10)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # اختبار على تاريخ محدد
        test_on_date(sys.argv[1])
    else:
        # للتشغيل الحقيقي:
        main()
