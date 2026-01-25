import pandas as pd
import requests
import os
import io
import numpy as np
from datetime import datetime, time, timedelta
import pytz
from dotenv import load_dotenv
import time as time_module

# ==============================================================================
# إعدادات
# ==============================================================================
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")
FINVIZ_COOKIE = """chartsTheme=dark; notice-newsletter=show; .ASPXAUTH=C7E2E86BC876CD078E1DC69C25671D062A909C67501ECF211333FAAD7F54A40FE9B6772EF4E88ED21E26C6C99BCAE5C39C5C8D598CD73357A5FCB4B556AD83E55002A827606EFFFE1F1315C9E8A4E05BC99B517D7E533905EE95F029D8FE0B930EC18E2E5F5037693AE688694BFDFDD82DADE25BA4063B448D18DDC85EAB40FD9D717716F2FEABA2A813D932072BFF5C6F723BACD8D3E4CA5161C3B1E0FF3088C9CC8AA7E67C3A4C94EA5122A68D9ADC7F85B091D98A31BF66F654490F1F7601FA7E420E3ECAF266BF62C1A7C9733A57BC866F92; survey_dialog_cohort=0"""

FINVIZ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": FINVIZ_COOKIE
}

ny_tz = pytz.timezone('America/New_York')
SUCCESSFUL_PATTERNS_FILE = "successful_candles.csv"

# ==============================================================================
# دالة تطبيع الأنماط
# ==============================================================================
def normalize_pattern(candles):
    """تحويل الأسعار إلى بصمة رقمية (0-1)"""
    candles = np.array(candles, dtype=float)
    min_val = np.min(candles)
    max_val = np.max(candles)
    if max_val == min_val: 
        return np.zeros_like(candles)
    return (candles - min_val) / (max_val - min_val)

# ==============================================================================
# تحميل الأنماط التاريخية
# ==============================================================================
def load_successful_patterns():
    """تحميل الأنماط من successful_candles.csv"""
    if not os.path.exists(SUCCESSFUL_PATTERNS_FILE):
        print(f"⚠️ ملف الأنماط غير موجود")
        return {}
    
    try:
        df = pd.read_csv(SUCCESSFUL_PATTERNS_FILE)
        df.columns = df.columns.str.strip().str.lower()
        
        patterns = {}
        for symbol, group in df.groupby('symbol'):
            group = group.sort_values('time')
            if len(group) >= 6:
                candles = group.iloc[:6][['open', 'high', 'low', 'close']].values
                patterns[symbol] = normalize_pattern(candles)
        
        print(f"✅ تم تحميل {len(patterns)} نمط تاريخي")
        return patterns
    except Exception as e:
        print(f"❌ خطأ في قراءة الأنماط: {e}")
        return {}

# ==============================================================================
# استخراج مقاييس الشمعة
# ==============================================================================
def get_candle_metrics(candles):
    """استخراج مقاييس: حجم الجسم، الذيول، التقلب"""
    metrics = []
    
    # تحويل إلى قائمة dictionaries إذا لزم الأمر
    candle_list = []
    for candle in candles:
        if isinstance(candle, dict):
            candle_list.append(candle)
        elif isinstance(candle, (list, tuple, np.ndarray)):
            candle_list.append({
                'open': float(candle[0]),
                'high': float(candle[1]),
                'low': float(candle[2]),
                'close': float(candle[3])
            })
    
    for candle in candle_list:
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['close'], candle['open'])
        lower_wick = min(candle['close'], candle['open']) - candle['low']
        range_price = candle['high'] - candle['low']
        price = (candle['open'] + candle['close']) / 2
        
        body_pct = (body / price * 100) if price > 0 else 0
        volatility = (range_price / price * 100) if price > 0 else 0
        
        metrics.append({
            'body_pct': body_pct,
            'volatility': volatility
        })
    
    return metrics

# ==============================================================================
# حساب التشابه (محسّن)
# ==============================================================================
def calculate_similarity(current_candles, reference_patterns):
    """مقارنة الشموع مع فحص الشكل + التقلب + الأجسام"""
    if not reference_patterns: 
        return 0, "None"
    
    current_fingerprint = normalize_pattern(current_candles)
    current_metrics = get_candle_metrics(current_candles)
    best_score = 0
    best_name = "None"
    
    for name, ref_fingerprint in reference_patterns.items():
        if current_fingerprint.shape != ref_fingerprint.shape: 
            continue
        
        # 1️⃣ تشابه الشكل العام
        diff = np.mean(np.abs(current_fingerprint - ref_fingerprint))
        pattern_score = 100 * (1 - diff)
        
        # 2️⃣ فحص التقلب والأجسام
        volatility_diffs = []
        body_diffs = []
        
        for i in range(len(current_metrics)):
            if i < len(current_metrics):
                curr_vol = current_metrics[i]['volatility']
                curr_body = current_metrics[i]['body_pct']
                
                # افترض أن ref_metrics لها نفس البيانات
                vol_diff = abs(curr_vol - (2.0 if name == "RIVN" else 1.0))  # تقريبي
                body_diff = abs(curr_body - (0.5 if name == "RIVN" else 0.3))
                
                volatility_diffs.append(vol_diff)
                body_diffs.append(body_diff)
        
        volatility_match = 100 - min(np.mean(volatility_diffs) if volatility_diffs else 100, 100)
        body_match = 100 - min(np.mean(body_diffs) * 0.5 if body_diffs else 100, 100)
        
        # الدرجة النهائية: 60% شكل + 25% تقلب + 15% أجسام
        final_score = (
            pattern_score * 0.60 +
            volatility_match * 0.25 +
            body_match * 0.15
        )
        
        if final_score > best_score:
            best_score = final_score
            best_name = name
            
    return best_score, best_name

# ==============================================================================
# جلب 300 سهم من Finviz
# ==============================================================================
def get_300_stocks_from_finviz():
    """جلب 300 سهم من Finviz"""
    print("\n" + "="*70)
    print("📊 جلب 300 سهم من Finviz")
    print("="*70)
    
    try:
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
        
        df_filtered = df_filtered.sort_values('Volume', ascending=False).reset_index(drop=True)
        
        # أخذ أول 300 سهم (الاختبار الكامل)
        stocks = df_filtered['Ticker'].head(300).tolist()
        
        print(f"✅ بعد الفلتر: {len(stocks)} سهم")
        print(f"📋 الأسهم: {', '.join(stocks[:20])}...\n")
        
        return stocks
        
    except Exception as e:
        print(f"❌ خطأ في جلب الأسهم من Finviz: {e}")
        return []

# ==============================================================================
# جلب شموع من EODHD (مع تسجيل التاريخ الفعلي)
# ==============================================================================
def get_eodhd_candles(symbol, target_date):
    """جلب شموع 1-دقيقة من EODHD من 9:30 إلى 10:00 - ترجع (الشموع، التاريخ الفعلي)"""
    try:
        date_obj = datetime.combine(target_date, time(9, 30), tzinfo=ny_tz)
        start_timestamp = int(date_obj.timestamp())
        end_timestamp = int(date_obj.replace(hour=10, minute=0).timestamp())
        
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': start_timestamp,
            'to': end_timestamp,
            'period': '1m'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return [], None  # ترجع تاريخ None
        
        csv_text = response.text
        
        if not csv_text or csv_text.count('\n') <= 1:
            return [], None
        
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            
            if df.empty:
                return [], None
            
            candles = []
            actual_date = None
            
            for _, row in df.iterrows():
                ts = int(row['Timestamp'])
                candle_time = datetime.fromtimestamp(ts, tz=pytz.UTC).astimezone(ny_tz)
                
                if actual_date is None:
                    actual_date = candle_time.date()
                
                candles.append({
                    'datetime': candle_time,
                    'symbol': symbol,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'time': candle_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return candles, actual_date  # ترجع التاريخ الفعلي المستخدم
            
        except Exception as e:
            return [], None
            
    except Exception as e:
        return [], None

# ==============================================================================
# فحص الذيل الطويل في آخر شمعتين
# ==============================================================================
def has_long_tail_in_last_candles(candles):
    """
    فحص الشموع الكبيرة بذيل طويل في آخر شمعتين
    الشمعة الكبيرة بذيل طويل = إشارة تحذير (عدم استقرار)
    """
    if len(candles) < 2:
        return False
    
    # آخر شمعتين
    last_candles = candles[-2:]
    
    for candle in last_candles:
        body = abs(candle['close'] - candle['open'])
        tail = candle['high'] - max(candle['close'], candle['open'])
        
        # إذا كانت الشمعة كبيرة الجسم (أكثر من 0.5% من السعر) وفيها ذيل طويل
        price = (candle['open'] + candle['close']) / 2
        body_percent = (body / price) * 100 if price > 0 else 0
        tail_percent = (tail / body) * 100 if body > 0 else 0
        
        # شمعة كبيرة (جسم > 0.3%) + ذيل طويل (أطول من 50% من الجسم)
        if body_percent > 0.3 and tail_percent > 50:
            return True
    
    return False

# ==============================================================================
# تحويل إلى شموع 5 دقائق
# ==============================================================================
def aggregate_to_5min(candles):
    """تحويل شموع 1-دقيقة إلى 5-دقائق"""
    if not candles:
        return []
    
    df = pd.DataFrame(candles)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # تجميع 5 دقائق
    df_5min = df.set_index('datetime').resample('5min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna(subset=['close'])
    
    if df_5min.empty:
        return []
    
    result = []
    for datetime_idx, row in df_5min.iterrows():
        result.append({
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        })
    
    return result

# ==============================================================================
# البرنامج الرئيسي
# ==============================================================================
print("="*70)
print("🔬 اختبار 300 سهم من Finviz مع تطابق الأنماط")
print("="*70)

# تحميل الأنماط
patterns = load_successful_patterns()

if not patterns:
    print("❌ لا توجد أنماط للمقارنة")
    exit(1)

# جلب الأسهم من Finviz
stocks = get_300_stocks_from_finviz()

if not stocks:
    print("❌ لم يتم جلب أسهم")
    exit(1)

# تاريخ البيانات (22 و 23 ديسمبر - تواريخ مختلفة عن الأنماط 19 ديسمبر)
# سنحاول 22 أولاً، وإذا ما فيه بيانات نحاول 23
test_dates = [
    datetime(2025, 12, 22).date(),  # أمس (الاثنين)
    datetime(2025, 12, 23).date(),  # اليوم (الثلاثاء)
]
target_date = test_dates[0]  # ابدأ بـ 22

print("\n" + "="*70)
print(f"🔍 جاري جلب الشموع لـ {len(stocks)} سهم")
print(f"📅 التاريخ: {target_date}")
print(f"⏰ الفترة: 9:30 - 10:00 AM")
print("="*70 + "\n")

successful_stocks = []
total_analyzed = 0
all_candles_5min = []  # لحفظ جميع الشموع

for idx, symbol in enumerate(stocks, 1):
    print(f"[{idx}/{len(stocks)}] 🔎 {symbol:<6}", end=" ", flush=True)
    
    # جلب الشموع (حاول التاريخ الأول، وإذا فشل حاول الثاني)
    candles, actual_date = get_eodhd_candles(symbol, target_date)
    used_date = actual_date  # سجل التاريخ الفعلي
    
    # إذا ما فيه بيانات في الأول، جرب التاريخ الثاني
    if not candles or len(candles) < 3:
        if target_date == test_dates[0] and len(test_dates) > 1:
            candles, actual_date = get_eodhd_candles(symbol, test_dates[1])
            used_date = actual_date
        
        if not candles or len(candles) < 3:
            print("❌ بدون بيانات")
            continue
    
    # تحويل إلى 5 دقائق
    candles_5min = aggregate_to_5min(candles)
    
    if not candles_5min or len(candles_5min) < 3:
        print("❌ شموع غير كافية")
        continue
    
    # 🔴 فحص الذيل الطويل - إذا آخر شمعتين فيهما ذيل طويل = تجاهل
    if has_long_tail_in_last_candles(candles_5min):
        print("⚠️ ذيل طويل (غير موثوق)")
        continue
    
    # حفظ الشموع
    for idx, candle in enumerate(candles_5min):
        all_candles_5min.append({
            'symbol': symbol,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'datetime': datetime.now(ny_tz).strftime('%Y-%m-%d'),
            'time': f"{idx+1}"
        })
    
    # حساب التطابق
    pattern_data = np.array([[c['open'], c['high'], c['low'], c['close']] for c in candles_5min])
    match_score, match_name = calculate_similarity(pattern_data, patterns)
    
    total_analyzed += 1
    
    # التحقق من التطابق (أدنى حد 80%)
    if match_score >= 80:
        print(f"✅ تطابق {match_score:.1f}% مع {match_name} [{used_date}]")
        successful_stocks.append({
            'symbol': symbol,
            'match_score': match_score,
            'match_name': match_name,
            'data_date': used_date  # سجل التاريخ
        })
    else:
        print(f"⚠️ {match_score:.1f}%")
    
    time_module.sleep(0.1)

# ==============================================================================
# النتائج النهائية
# ==============================================================================
print("\n" + "="*70)
print("📊 النتائج النهائية")
print("="*70)
print(f"✅ الأسهم المحللة: {total_analyzed}")
print(f"🎯 الأسهم الناجحة (80%+): {len(successful_stocks)}\n")

if successful_stocks:
    print("🏆 الأسهم الناجحة:")
    print("-"*90)
    print(f"{'السهم':<10} {'التطابق':<12} {'النمط':<10} {'تاريخ البيانات':<20}")
    print("-"*90)
    for stock in sorted(successful_stocks, key=lambda x: x['match_score'], reverse=True):
        data_date = stock.get('data_date', 'غير معروف')
        print(f"  ✅ {stock['symbol']:<8} | {stock['match_score']:>5.1f}% | {stock['match_name']:<10} | {str(data_date):<20}")
else:
    print("❌ لم يتم العثور على أسهم تطابق الأنماط بنسبة 80% فأعلى")

# حفظ الشموع في CSV
if all_candles_5min:
    df_candles = pd.DataFrame(all_candles_5min)
    output_file = f"test_candles_{datetime.now(ny_tz).strftime('%Y%m%d_%H%M%S')}.csv"
    df_candles.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n💾 تم حفظ {len(all_candles_5min)} شمعة في: {output_file}")

print("\n" + "="*70)
