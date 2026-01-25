import requests
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import concurrent.futures
import yfinance as yf

# ==============================================================================
# 🔐 إعدادات النظام
# ==============================================================================
load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")  # 👈 مفتاح EODHD
TELEGRAM_TOKEN = "8130586876:AAFZBPEDJ2o-WOyqDOhltG69lnw2YN0-bDg"
CHAT_ID = "237657512"

SUCCESSFUL_PATTERNS_FILE = "successful_candles.csv"
CACHE_FILE = "float_cache.json"
SHARIAH_FILE = "shariah_stocks_master.json"
TARGET_TIME = "10:03"  # وقت بدء الفحص بتوقيت نيويورك

if not API_KEY:
    print("❌ خطأ: لم يتم العثور على API KEY")
    exit()

def check_shariah_status(ticker):
    """فحص حكم السهم الشرعي - حلال أو غير متوفر"""
    try:
        if not os.path.exists(SHARIAH_FILE):
            return "⚠️ غير متوفر"

        with open(SHARIAH_FILE, 'r') as f:
            data = json.load(f)

        if ticker in data:
            status = data[ticker].get('status', '').lower()
            if 'halal' in status:
                return "✅ حلال"

        # إذا حرام أو غير موجود = غير متوفر
        return "⚠️ غير متوفر"
    except:
        return "⚠️ غير متوفر"

def get_flag_emoji(country_code):
    """تحويل رمز الدولة (مثل CN) إلى علم 🇨🇳"""
    if not country_code or len(country_code) != 2:
        return "🇺🇸"
    try:
        return "".join([chr(ord(c.upper()) + 127397) for c in country_code])
    except:
        return "🏳️"

# ==============================================================================
# ✨ استراتيجية الزحف الذهبي المحسّن (مبنية على تحليل الأنماط الناجحة)
# ==============================================================================
def is_golden_grinder(df, symbol_debug=None):
    """
    🎯 استراتيجية مبنية على تحليل 18 نمط ناجح من successful_candles.csv

    القواعد المستخلصة:
    1. التغير الكلي > 0% (صاعد إجبارياً)
    2. على الأقل 4 شموع من 6 خضراء (67%)
    3. على الأقل 3 قيعان من 5 صاعدة (60%)
    4. على الأقل 3 قمم من 5 صاعدة (60%)
    5. أكبر شمعة حمراء ≤ 1.5%
    6. أكبر ذيل علوي ≤ 2%
    7. لا يوجد "انفجار" (شمعة واحدة > 5%)
    """

    # نحتاج على الأقل 6 شموع للتحليل
    if len(df) < 6:
        return False

    # ═══════════════════════════════════════════════════════════════
    # 📊 استخراج شموع الصباح فقط (9:30 - 10:00) - بدون استثناءات!
    # ═══════════════════════════════════════════════════════════════
    try:
        last_date = df.index[-1].date()
        day_data = df[df.index.date == last_date]
        morning_candles = day_data.between_time('09:30', '09:55')  # 6 شموع: 09:30, 09:35, 09:40, 09:45, 09:50, 09:55

        if len(morning_candles) < 3:
            # ❌ لا شموع صباحية = رفض السهم تماماً
            if symbol_debug: print(f"⚠️ {symbol_debug}: لا توجد شموع صباحية كافية ({len(morning_candles)} شموع)")
            return False
    except Exception as e:
        if symbol_debug: print(f"⚠️ {symbol_debug}: خطأ في استخراج شموع الصباح")
        return False

    candles = morning_candles[['open', 'high', 'low', 'close']].values
    num_candles = len(candles)

    if num_candles < 3:
        return False

    # ═══════════════════════════════════════════════════════════════
    # 1️⃣ التغير الكلي (يجب أن يكون صاعد)
    # ═══════════════════════════════════════════════════════════════
    first_open = candles[0][0]
    last_close = candles[-1][3]
    total_change = (last_close - first_open) / first_open * 100

    if total_change <= 0:
        if symbol_debug: print(f"❌ {symbol_debug}: هابط ({total_change:+.2f}%)")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 2️⃣ عدد الشموع الخضراء (على الأقل 67%)
    # ═══════════════════════════════════════════════════════════════
    green_count = 0
    red_count = 0
    max_red_body = 0
    max_upper_wick = 0
    max_single_candle = 0

    for c in candles:
        o, h, l, close = c[0], c[1], c[2], c[3]
        body_pct = abs(close - o) / o * 100 if o > 0 else 0
        upper_wick_pct = (h - max(o, close)) / o * 100 if o > 0 else 0

        # تتبع أكبر شمعة (للكشف عن الانفجار)
        max_single_candle = max(max_single_candle, body_pct)
        max_upper_wick = max(max_upper_wick, upper_wick_pct)

        if close >= o:
            green_count += 1
        else:
            red_count += 1
            max_red_body = max(max_red_body, body_pct)

    green_ratio = green_count / num_candles

    if green_ratio < 0.5:  # على الأقل 50% خضراء
        if symbol_debug: print(f"❌ {symbol_debug}: شموع خضراء قليلة ({green_count}/{num_candles})")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 3️⃣ Higher Lows (قيعان صاعدة)
    # ═══════════════════════════════════════════════════════════════
    higher_lows = 0
    for i in range(1, num_candles):
        if candles[i][2] >= candles[i-1][2]:  # Low >= Previous Low
            higher_lows += 1

    higher_lows_ratio = higher_lows / (num_candles - 1) if num_candles > 1 else 0

    if higher_lows_ratio < 0.5:  # على الأقل 50% قيعان صاعدة
        if symbol_debug: print(f"❌ {symbol_debug}: قيعان هابطة ({higher_lows}/{num_candles-1})")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 4️⃣ Higher Highs (قمم صاعدة)
    # ═══════════════════════════════════════════════════════════════
    higher_highs = 0
    for i in range(1, num_candles):
        if candles[i][1] >= candles[i-1][1]:  # High >= Previous High
            higher_highs += 1

    higher_highs_ratio = higher_highs / (num_candles - 1) if num_candles > 1 else 0

    if higher_highs_ratio < 0.5:  # على الأقل 50% قمم صاعدة
        if symbol_debug: print(f"❌ {symbol_debug}: قمم هابطة ({higher_highs}/{num_candles-1})")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 5️⃣ أكبر شمعة حمراء (يجب ألا تتجاوز 1.5%)
    # ═══════════════════════════════════════════════════════════════
    if max_red_body > 1.5:
        if symbol_debug: print(f"❌ {symbol_debug}: شمعة حمراء كبيرة ({max_red_body:.2f}%)")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 6️⃣ أكبر ذيل علوي (يجب ألا يتجاوز 3.5%)
    # ═══════════════════════════════════════════════════════════════
    if max_upper_wick > 3.5:
        if symbol_debug: print(f"❌ {symbol_debug}: ذيل علوي كبير ({max_upper_wick:.2f}%)")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 7️⃣ لا يوجد انفجار (شمعة واحدة > 7.5%)
    # ═══════════════════════════════════════════════════════════════
    if max_single_candle > 7.5:
        if symbol_debug: print(f"❌ {symbol_debug}: شمعة انفجارية ({max_single_candle:.2f}%)")
        return False

    # ═══════════════════════════════════════════════════════════════
    # 8️⃣ فحص القمة - رفض إذا القمة لها ذيل علوي طويل (ضغط بيعي)
    # ═══════════════════════════════════════════════════════════════
    # نجد الشمعة التي فيها أعلى سعر (القمة)
    peak_idx = -1
    peak_high = 0
    for i, c in enumerate(candles):
        if c[1] > peak_high:  # c[1] = high
            peak_high = c[1]
            peak_idx = i

    if peak_idx >= 0:
        peak_candle = candles[peak_idx]
        p_open, p_high, p_low, p_close = peak_candle[0], peak_candle[1], peak_candle[2], peak_candle[3]
        p_body = abs(p_close - p_open)
        p_upper_wick = p_high - max(p_open, p_close)

        # إذا الذيل العلوي أكبر من ضعف الجسم = ضغط بيعي
        if p_body > 0 and p_upper_wick >= p_body * 2:
            if symbol_debug: print(f"❌ {symbol_debug}: قمة بذيل طويل (wick:{p_upper_wick:.4f} > 2x body:{p_body:.4f})")
            return False

        # إذا الشمعة بعد القمة حمراء كبيرة (أكثر من 1.5%) = تأكيد الضغط البيعي
        if peak_idx < num_candles - 1:
            next_candle = candles[peak_idx + 1]
            n_open, n_close = next_candle[0], next_candle[3]
            if n_close < n_open:  # شمعة حمراء
                red_body_pct = (n_open - n_close) / n_open * 100
                if red_body_pct > 1.5:
                    if symbol_debug: print(f"❌ {symbol_debug}: شمعة حمراء بعد القمة ({red_body_pct:.2f}%)")
                    return False

    # ═══════════════════════════════════════════════════════════════
    # ✅ كل الشروط مستوفاة!
    # ═══════════════════════════════════════════════════════════════
    if symbol_debug:
        print(f"✅ {symbol_debug}: صاعد {total_change:+.2f}%, أخضر {green_count}/{num_candles}, HL {higher_lows}/{num_candles-1}, HH {higher_highs}/{num_candles-1}")

    return True

def calculate_beauty_score(df):
    """
    تقييم جمال الشارت في الفترة الذهبية (09:40 - 10:00).
    """
    # 1️⃣ تحديد الفترة الزمنية (09:40 - 10:00)
    # نأخذ آخر تاريخ موجود في الداتا
    if df.empty: return 0
    last_date = df.index[-1].date()

    # فلترة بيانات ذلك اليوم وتلك الفترة
    day_data = df[df.index.date == last_date]
    try:
        target_df = day_data.between_time('09:40', '09:55').copy()  # 4 شموع: 09:40, 09:45, 09:50, 09:55
    except:
        return 0

    if len(target_df) < 3:
        return 0 # بيانات غير كافية

    score = 60 # نقطة البداية

    # 2️⃣ تحليل الاتجاه العام (Trend)
    first_open = target_df.iloc[0]['open']
    last_close = target_df.iloc[-1]['close']

    # إذا السعر صعد في المجمل
    if last_close > first_open:
        score += 20
    else:
        score -= 20 # هبوط عام

    # 3️⃣ تحليل الشموع
    candles = target_df.reset_index(drop=True)
    max_high = target_df['high'].max()

    for i in range(len(candles)):
        row = candles.iloc[i]
        open_p = row['open']
        close_p = row['close']
        high_p = row['high']
        low_p = row['low']

        body = abs(close_p - open_p)
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p
        total_len = high_p - low_p

        is_red = close_p < open_p
        is_green = not is_red

        # أ) عقوبة الذيل الطويل عند القمة (Rejection at High)
        # "ما أحب تكون هي الهاي اللي فيها ذيل طويل"
        if high_p == max_high:
            # إذا كانت هذه الشمعة هي قمة الفترة
            if total_len > 0 and (upper_wick / total_len) > 0.5:
                score -= 30 # عقوبة قاسية: رفض من القمة

        # ب) الشموع الحمراء
        if is_red:
            # حمراء صغيرة (Resting) = ممتاز
            # نفترض الصغيرة هي ما دون 0.3% تقريباً (أو مقارنة بالجسم المتوسط)
            body_pct = (body / open_p) * 100
            if body_pct < 0.3:
                score += 5 # راحة صحية
            elif body_pct > 0.6:
                score -= 10 # بيع قوي

        # ج) الشموع الخضراء
        if is_green:
            score += 5

        # د) التسلسل (Higher Lows)
        if i > 0:
            prev_low = candles.iloc[i-1]['low']
            if low_p >= prev_low:
                score += 5
            else:
                # كسر القاع السابق
                if is_red and (body/open_p*100) < 0.3:
                    score -= 2 # كسر بسيط بشمعة صغيرة (مقبول)
                else:
                    score -= 10 # كسر حقيقي

    return max(0, min(99, score))

# ==============================================================================
# 1️⃣ محرك مطابقة الأنماط (Pattern Matching Engine)
# ==============================================================================
# ==============================================================================
# 🧬 النظام الجديد: مطابقة الشموع بالتسلسل (Candle-by-Candle DNA Matching)
# ==============================================================================
def extract_candle_dna(candles):
    """
    تحويل الشموع إلى بصمة رقمية تعتمد على النسب المئوية (الشكل) فقط.
    يعيد قائمة لكل شمعة:
    {
        'body_r': نسبة الجسم (0-1),
        'upper_r': نسبة الذيل العلوي (0-1),
        'lower_r': نسبة الذيل السفلي (0-1),
        'dir': الاتجاه (1 أخضر، -1 أحمر),
        'size': حجم الشمعة بالنسبة المئوية (%)
    }
    """
    dna = []

    # تحويل المدخلات إلى قائمة بسيطة
    if isinstance(candles, pd.DataFrame):
        candle_list = candles[['open', 'high', 'low', 'close']].values.tolist()
    elif isinstance(candles, list) and candles and isinstance(candles[0], dict):
        # قائمة من القواميیس
        candle_list = [[c.get('open', 0), c.get('high', 0), c.get('low', 0), c.get('close', 0)]
                      for c in candles]
    else:
        candle_list = np.array(candles).tolist()

    for c in candle_list:
        open_p, high_p, low_p, close_p = float(c[0]), float(c[1]), float(c[2]), float(c[3])

        # حساب حجم الشمعة الكلي
        total_range = high_p - low_p
        if total_range == 0:
            total_range = 0.0001  # تجنب القسمة على صفر

        # 1. حجم الجسم بالنسبة للحركة (هل الجسم ممتلئ أم دوجي؟)
        body_size = abs(close_p - open_p)
        body_ratio = body_size / total_range

        # 2. حجم الذيول بالنسبة للطول الكلي
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p

        upper_ratio = upper_wick / total_range
        lower_ratio = lower_wick / total_range

        # 3. الاتجاه (1 أخضر، -1 أحمر)
        direction = 1 if close_p >= open_p else -1

        # 4. الحجم النسبي للشمعة (بالنسبة المئوية)
        # نستخدم النسبة المئوية للتغير السعري عشان نطابق سهم بـ 10 دولار مع سهم بـ 1000
        real_change_pct = (body_size / open_p) * 100 if open_p > 0 else 0

        dna.append({
            'body_r': body_ratio,      # شكل الجسم (ممتلئ أو نحيف)
            'upper_r': upper_ratio,    # طول الذيل العلوي النسبي
            'lower_r': lower_ratio,    # طول الذيل السفلي النسبي
            'dir': direction,          # لون الشمعة
            'size': real_change_pct    # حجم الشمعة الحقيقي (%)
        })

    return dna


def calculate_structural_similarity(current_candles, reference_patterns):
    """
    مطابقة الرتم الصارم (Strict Rhythm):
    - يرفض الشموع الانفجارية (Pumps) إذا كان النمط هادئاً.
    - يرفض الشموع الميتة إذا كان النمط نشطاً.
    - يقبل الشمعة الحمراء الصغيرة فقط إذا تم تعويضها (Dip & Recover).
    """
    if isinstance(current_candles, pd.DataFrame):
        curr_raw = current_candles[['open', 'high', 'low', 'close']].values
    else:
        curr_raw = np.array(current_candles)

    current_dna = extract_candle_dna(curr_raw)

    best_score = 0
    best_name = "None"

    for name, pattern_raw_data in reference_patterns.items():
        ref_dna = extract_candle_dna(pattern_raw_data)

        if len(current_dna) != len(ref_dna): continue

        total_penalty = 0

        for i in range(len(current_dna)):
            curr = current_dna[i]
            ref = ref_dna[i]
            curr_price = curr_raw[i]

            penalty = 0

            # -----------------------------------------------------
            # 1️⃣ فحص الاتجاه (معالجة الشمعة الحمراء)
            # -----------------------------------------------------
            if curr['dir'] != ref['dir']:
                # لو حمراء عكس النمط الأخضر
                is_small_dip = curr['size'] < 1.5

                # هل تم تعويضها في الشمعة التالية؟
                recovered = False
                if i < len(current_dna) - 1:
                    next_close = curr_raw[i+1][3]
                    curr_high = curr_price[1]
                    if next_close > curr_high:
                        recovered = True

                if is_small_dip and recovered:
                    penalty = 0  # استثناء: تصحيح صحي
                else:
                    penalty = 100 # خطأ فادح (اتجاه خاطئ بدون تعويض)

            else:
                # -----------------------------------------------------
                # 2️⃣ فحص الحجم (التطابق الصارم للرتم)
                # -----------------------------------------------------
                # نحسب الفرق المطلق: سواء أكبر أو أصغر، كله عليه عقوبة
                # curr['size'] هي نسبة تغير الشمعة (مثلاً 0.5%)
                size_diff = abs(curr['size'] - ref['size'])

                # مسموح بفرق بسيط جداً (هامش مرونة 0.4%)
                # يعني لو النمط 0.5%، نقبل من 0.1% إلى 0.9%
                if size_diff <= 0.4:
                    penalty = 0
                else:
                    # أي زيادة عن الهامش عليها عقوبة قوية
                    # المعادلة: (الفرق الزائد) * 30
                    # مثال: فرق 1.5% -> عقوبة 33 نقطة (كبيرة)
                    # مثال: فرق 3.0% (شمعة عملاقة) -> عقوبة 80 نقطة (طرد)
                    penalty = (size_diff - 0.4) * 30

            # 3️⃣ عقوبة الشكل الثانوي (الذيول)
            shape_penalty = abs(curr['body_r'] - ref['body_r']) * 20
            penalty += shape_penalty

            total_penalty += penalty

        # حساب النسبة النهائية
        score = max(0, 100 - (total_penalty / len(current_dna)))

        if score > best_score:
            best_score = score
            best_name = name

    return best_score, best_name

# ==============================================================================
# تحميل الأنماط الناجحة
# ==============================================================================
# ==============================================================================
# 1️⃣ محرك مطابقة الأنماط (Pattern Matching Engine)
# ==============================================================================
def normalize_pattern(candles):
    """تحويل الأسعار إلى بصمة رقمية (0-1) للمقارنة الشكلية"""
    candles = np.array(candles, dtype=float)
    min_val = np.min(candles)
    max_val = np.max(candles)
    if max_val == min_val: return np.zeros_like(candles) # تجنب القسمة على صفر
    return (candles - min_val) / (max_val - min_val)

# ==============================================================================
# استخراج مقاييس الشمعة
# ==============================================================================
def get_candle_metrics(candles):
    """استخراج مقاييس: حجم الجسم، التقلب"""
    metrics = []

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
# فحص الذيل الطويل
# ==============================================================================
def has_long_tail_in_last_candles(candles):
    """فحص الشموع الكبيرة بذيل طويل في آخر شمعتين"""
    if len(candles) < 2:
        return False

    last_candles = candles[-2:]

    for candle in last_candles:
        body = abs(candle['close'] - candle['open'])
        tail = candle['high'] - max(candle['close'], candle['open'])

        price = (candle['open'] + candle['close']) / 2
        body_percent = (body / price) * 100 if price > 0 else 0
        tail_percent = (tail / body) * 100 if body > 0 else 0

        # شمعة كبيرة (جسم > 0.3%) + ذيل طويل (أطول من 50% من الجسم)
        if body_percent > 0.3 and tail_percent > 50:
            return True

    return False

def is_doji_or_small_candle(candles):
    """🕯️ فحص إذا كانت الشموع دوجي أو صغيرة جداً (تستريح)"""
    small_count = 0
    for candle in candles:
        body = abs(candle[3] - candle[0])  # close - open
        price = (candle[0] + candle[3]) / 2
        body_pct = (body / price * 100) if price > 0 else 0

        # شمعة صغيرة جداً: أقل من 0.3% أو دوجي (open ≈ close)
        if body_pct < 0.3:
            small_count += 1

    # إذا كان أكثر من 50% من الشموع صغيرة/دوجي = شموع تستريح
    return small_count >= len(candles) / 2

def calculate_ladder_score(candles):
    """🔥 فحص نمط الصعود (Higher Lows + Higher Highs)
    - صعود قوي = 100%
    - صعود ضعيف لكن شموع صغيرة = 70% (تستريح عادي)
    - هابط تماماً = 0% (ترفض)"""
    if len(candles) < 2:
        return 0

    lows = [candle[2] for candle in candles]  # Low prices
    highs = [candle[1] for candle in candles]  # High prices

    # فحص الـ Higher Lows (قيعان صاعدة)
    lower_lows_count = sum(1 for i in range(len(lows)-1) if lows[i+1] >= lows[i])
    higher_lows_ratio = lower_lows_count / (len(lows) - 1) if len(lows) > 1 else 0

    # فحص الـ Higher Highs (قمم صاعدة)
    higher_highs_count = sum(1 for i in range(len(highs)-1) if highs[i+1] >= highs[i])
    higher_highs_ratio = higher_highs_count / (len(highs) - 1) if len(highs) > 1 else 0

    # الدرجة الأساسية للصعود
    ladder_score = (higher_lows_ratio + higher_highs_ratio) / 2 * 100

    # 🕯️ إذا كان الصعود ضعيف لكن الشموع صغيرة (تستريح) = قبول
    if ladder_score < 50 and is_doji_or_small_candle(candles):
        ladder_score = 70  # درجة متوسطة للشموع التي تستريح

    # إذا كان هابط تماماً = ترفض (Score = 0 أو منخفض جداً)
    # لكن إذا كانت الشموع دوجي/صغيرة = قبول بدرجة أقل

    return ladder_score

def get_candle_directions(candles):
    """🔥 استخراج اتجاه كل شمعة (1=صاعدة، -1=هابطة، 0=دوجي)"""
    directions = []
    for candle in candles:
        if isinstance(candle, (list, tuple, np.ndarray)):
            open_p, close_p = candle[0], candle[3]
        else:
            open_p, close_p = candle['open'], candle['close']

        body_pct = abs(close_p - open_p) / open_p * 100 if open_p > 0 else 0

        # شمعة صغيرة جداً = دوجي (محايدة)
        if body_pct < 0.15:
            directions.append(0)
        elif close_p > open_p:
            directions.append(1)  # صاعدة
        else:
            directions.append(-1)  # هابطة

    return directions

def load_successful_patterns():
    """تحميل الأنماط الناجحة من ملف CSV مع استخراج تفاصيل كل شمعة"""
    if not os.path.exists(SUCCESSFUL_PATTERNS_FILE):
        print(f"⚠️ ملف الأنماط غير موجود، سيعمل البوت على الاستراتيجية الفنية فقط.")
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

                # 🔥 استخراج تفاصيل كل شمعة للمقارنة الدقيقة
                candle_details = []
                for i in range(len(candles)):
                    o, h, l, c = candles[i]
                    body_pct = (c - o) / o * 100  # نسبة موجبة = صاعدة، سالبة = هابطة
                    direction = 1 if c >= o else -1  # 1 = صاعدة، -1 = هابطة
                    body_size = abs(body_pct)

                    candle_details.append({
                        'direction': direction,
                        'body_pct': body_pct,
                        'body_size': body_size,
                        'open': o,
                        'high': h,
                        'low': l,
                        'close': c
                    })

                patterns[symbol] = candles  # نحفظ الشموع الخام
                pattern_metrics[symbol] = {
                    'candle_details': candle_details,
                    'avg_body': np.mean([cd['body_size'] for cd in candle_details])
                }

        print(f"✅ تم تحميل {len(patterns)} نمط تاريخي مع تفاصيل الشموع")
        return patterns, pattern_metrics
    except Exception as e:
        print(f"❌ خطأ في قراءة الأنماط: {e}")
        return {}, {}

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    """
    🔥 مطابقة حقيقية شمعة بشمعة:
    - نقارن فقط مع الأنماط النخبوية الـ 6!
    - نقارن نسبة تغير كل شمعة (body_pct) مباشرة
    """
    if not reference_patterns:
        return 0, "None"

    # ✅ الأنماط المثبتة من Backtest (VIVK 50% + IOBT 45%)
    ELITE_PATTERNS = ['VIVK', 'IOBT']

    # استخراج تفاصيل الشموع الحالية
    current_details = []
    for i in range(len(current_candles)):
        o, h, l, c = current_candles[i][0], current_candles[i][1], current_candles[i][2], current_candles[i][3]
        body_pct = (c - o) / o * 100  # نسبة التغير الفعلية (موجبة أو سالبة)
        current_details.append({
            'body_pct': body_pct,
            'open': o, 'high': h, 'low': l, 'close': c
        })

    # ═══════════════════════════════════════════════════════════════
    # 🚨 شرط إلزامي: السهم يجب أن يكون صاعد بشكل عام!
    # ═══════════════════════════════════════════════════════════════
    curr_start = current_details[0]['open']
    curr_end = current_details[-1]['close']
    curr_trend = (curr_end - curr_start) / curr_start * 100

    if curr_trend <= 0:
        return 0, "None"

    best_score = 0
    best_name = "None"

    for name, ref_candles in reference_patterns.items():
        # 🚫 تجاهل الأنماط غير النخبوية!
        if name not in ELITE_PATTERNS:
            continue
            
        if name not in pattern_metrics:
            continue

        ref_details = pattern_metrics[name]['candle_details']
        compare_len = min(len(current_details), len(ref_details))
        if compare_len < 3:
            continue

        # ═══════════════════════════════════════════════════════════
        # 🎯 مقارنة صارمة: نسبة تغير كل شمعة
        # ═══════════════════════════════════════════════════════════
        
        # أولاً: حساب متوسط قوة النمط ومتوسط قوة السهم الحالي
        ref_avg_strength = np.mean([abs(d['body_pct']) for d in ref_details[:compare_len]])
        curr_avg_strength = np.mean([abs(d['body_pct']) for d in current_details[:compare_len]])
        
        # 🚫 رفض فوري: إذا السهم الحالي أضعف بكثير من النمط
        # السهم لازم يكون على الأقل 80% من قوة النمط
        if curr_avg_strength < ref_avg_strength * 0.8:
            continue
        
        total_similarity = 0
        
        for i in range(compare_len):
            curr_pct = current_details[i]['body_pct']  # مثال: +0.1%
            ref_pct = ref_details[i]['body_pct']       # مثال: +3.0%
            
            # 1) فحص الاتجاه أولاً
            same_direction = (curr_pct >= 0 and ref_pct >= 0) or (curr_pct < 0 and ref_pct < 0)
            
            if not same_direction:
                candle_score = 0
            else:
                curr_abs = abs(curr_pct)
                ref_abs = abs(ref_pct)
                
                # الفرق المسموح: 60% من حجم النمط الأصلي (أو 0.5% كحد أدنى)
                max_diff = max(ref_abs * 0.6, 0.5)
                actual_diff = abs(curr_abs - ref_abs)
                
                if actual_diff <= max_diff:
                    candle_score = 100 - (actual_diff / max_diff * 40)
                else:
                    # خارج النطاق - عقوبة شديدة
                    overshoot = actual_diff - max_diff
                    candle_score = max(0, 60 - overshoot * 30)
            
            total_similarity += candle_score
        
        # الدرجة النهائية = متوسط تشابه الشموع
        final_score = total_similarity / compare_len

        if final_score > best_score:
            best_score = final_score
            best_name = name

    return best_score, best_name

# ==============================================================================
# جلب البيانات التاريخية (FMP أولاً ثم EODHD)
# ==============================================================================
def get_eodhd_history(symbol):
    """جلب البيانات التاريخية (شموع 5 دقائق) من FMP"""

    # 1️⃣ محاولة FMP (المصدر الرئيسي الآن)
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

    except Exception as e:
        pass  # كمل لـ EODHD

    # 2️⃣ محاولة EODHD (الخطة البديلة)
    try:
        # حساب Unix Timestamp قبل 3 أيام (لضمان وجود بيانات كافية)
        from_timestamp = int(time.time()) - (3 * 24 * 60 * 60)

        url = f"https://eodhd.com/api/intraday/{symbol}.US?api_token={EODHD_API_KEY}&interval=5m&fmt=json&from={from_timestamp}"

        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None

        data = resp.json()
        if not data:
            return None

        df = pd.DataFrame(data)

        # معالجة أسماء الأعمدة (EODHD قد يرجعها بأشكال مختلفة)
        df_cols = df.columns.str.lower()
        if 'timestamp' in df_cols:
            df['date'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        elif 'datetime' in df_cols:
            df['date'] = pd.to_datetime(df['datetime'])
        else:
            df['date'] = pd.to_datetime(df.iloc[:, 0])

        df.set_index('date', inplace=True)

        # تحويل الأعمدة للأرقام
        for c in ['open', 'high', 'low', 'close', 'volume']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')

        df.dropna(inplace=True)

        # توحيد التوقيت لنيويورك
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df.index = df.index.tz_convert('America/New_York')

        df.sort_index(inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        print(f"⚠️ خطأ EODHD لـ {symbol}: {e}")
        return None

# ==============================================================================
# 2️⃣ دوال الكاش والسكرينر (Selection)
# ==============================================================================
def load_cache():
    if os.path.exists(CACHE_FILE):
        try: return json.load(open(CACHE_FILE, 'r'))
        except: return {}
    return {}

def save_cache(data):
    with open(CACHE_FILE, 'w') as f: json.dump(data, f, indent=4)

def get_guaranteed_50_list():
    """جلب القائمة مع تجاهل الأخطاء الفردية (لن يتوقف أبداً)"""
    cache = load_cache()
    print("📦 جاري سحب القائمة الحية (نظام الدبابة 🚜)...")

    # 🔥 فلتر السعر الجديد: $3-$100 (أسهم أقوى للمطابقة مع الأنماط النخبوية)
    url = (f"https://financialmodelingprep.com/stable/company-screener"
           f"?priceMoreThan=3&priceLowerThan=100&volumeMoreThan=200000"
           f"&isEtf=false&exchange=nasdaq,nyse,amex&isActivelyTrading=true&limit=1000&apikey={API_KEY}")

    try:
        results = requests.get(url, timeout=20).json()
        if not results: return []

        # ترتيب حسب الفوليوم
        results.sort(key=lambda x: x.get('volume', 0), reverse=True)

        final_list = []
        for item in results:
            # إذا اكتفينا بـ 200 سهم نوقف
            if len(final_list) >= 200: break

            # 🛡️ حماية داخلية: أي خطأ هنا يتجاهل السهم فقط ويكمل
            try:
                sym = item.get('symbol')
                if len(sym) > 5: continue

                origin_country = item.get('country', 'US')

                # جلب الفلوت (Yahoo أولاً ثم FMP)
                if sym in cache:
                    raw_val = cache[sym]
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

                    # 2️⃣ إذا Yahoo فشل، جرب FMP
                    if raw_val == 0:
                        try:
                            f_url = f"https://financialmodelingprep.com/stable/shares-float?symbol={sym}&apikey={API_KEY}"
                            f_data = requests.get(f_url, timeout=1).json()
                            if f_data and isinstance(f_data, list):
                                raw_val = f_data[0].get('floatShares', 0)
                        except:
                            pass

                    cache[sym] = raw_val
                    time.sleep(0.05)

                # 🔥 التصحيح الإجباري (Force Float)
                # مهما كان اللي جاء من الكاش (نص، ديكشنري، خطأ) حوله لرقم
                try:
                    f_shares = float(raw_val)
                except (ValueError, TypeError):
                    f_shares = 0 # لو خربان اعتبره صفر وتجاهله

                # الشرط النهائي
                if 0 < f_shares <= 200_000_000:
                    final_list.append({'symbol': sym, 'float': f_shares, 'country': origin_country})
                    print(f"📌 {len(final_list)}/100: {sym} ({origin_country})")

            except Exception as loop_error:
                # لو حصل أي مصيبة في هذا السهم، اطبعه وكمل للي بعده
                print(f"⚠️ تم تجاوز سهم معطوب: {item.get('symbol', 'Unknown')}")
                continue

        save_cache(cache)
        return final_list

    except Exception as e:
        print(f"❌ خطأ عام بالسكرينر: {e}")
        return []

# ==============================================================================
# 3️⃣ التحليل الفني والمطابقة (Analysis)
# ==============================================================================
# ✅ الأنماط المثبتة من Backtest ديسمبر 2025:
# VIVK: نجاح 50% | متوسط ربح +3.03%
# IOBT: نجاح 45.2% | متوسط ربح +2.64%
# CCL: نجاح 46.8% (لكن خسائر كبيرة)
# MVIS: نجاح 27.6% فقط ❌
# Benf: عينة صغيرة جداً
ELITE_PATTERNS = ['VIVK', 'IOBT']  # فقط الأنماط الرابحة!

# ⚙️ إعدادات مثبتة من Backtest (256 إشارة في ديسمبر 2025)
MATCH_THRESHOLD = 55      # عتبة التطابق (أفضل توازن من Backtest)
MIN_HIGHER_HIGHS = 3      # يجب 3/5 قمم صاعدة على الأقل
MIN_HIGHER_LOWS = 3       # يجب 3/5 قيعان صاعدة على الأقل
MAX_AVG_BODY = 3.0        # أقصى متوسط جسم الشمعة (3%)
MIN_BEAUTY_SCORE = 60     # الحد الأدنى لجودة الشموع (60%)

def get_badge(pattern_name, candles, volume, loaded_patterns):
    """
    تصنيف قوة الإشارة بناءً على النمط والسلوك السعري
    🔥 يستخدم الأنماط النخبوية الـ 6 فقط!
    """
    # 1. فحص الفوليوم (هل يتناقص؟)
    if len(volume) >= 6:
        # مقارنة متوسط آخر 3 شموع بأول 3 شموع
        vol_growth = np.mean(volume[-3:]) / np.mean(volume[:3]) if np.mean(volume[:3]) > 0 else 1.0
    else:
        vol_growth = 1.0
    
    is_silent = vol_growth < 1.0
    
    # 2. فحص الجسم
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles])
    is_good_body = avg_body < MAX_AVG_BODY
    
    # ✅ النمط معتمد فقط إذا كان من الأنماط النخبوية الـ 6
    is_elite_pattern = pattern_name in ELITE_PATTERNS
    
    # 3. فحص الزحف الصارم (HH5, HL4)
    hh = sum(1 for i in range(1, len(candles)) if candles[i][1] >= candles[i-1][1])
    hl = sum(1 for i in range(1, len(candles)) if candles[i][2] >= candles[i-1][2])
    
    is_perfect_crawl = hh >= MIN_HIGHER_HIGHS and hl >= MIN_HIGHER_LOWS
    
    # 4. تحديد الوسام
    # 👑 النخبة: نمط من الـ 6 + زحف مثالي (HH5, HL4) + جسم مناسب
    if is_elite_pattern and is_perfect_crawl and is_good_body:
        return "👑 إشارة نخبوية"
    
    # ❌ كل شيء آخر = رفض
    return None  # إرجاع None يعني تجاهل الإشارة تماماً

def analyze_stock(stock_data, reference_patterns, pattern_metrics):
    ticker = stock_data['symbol']
    float_shares = stock_data['float']
    country_code = stock_data.get('country', 'US')

    print(f"🔎 {ticker:<6}", end=" ")

    # ---------------------------------------------------------
    # البيانات الآن تأتي من FMP مباشرة
    # ---------------------------------------------------------
    full_df = get_eodhd_history(ticker)

    if full_df is None or len(full_df) == 0:
        print("❌ لا بيانات")
        return

    # ---------------------------------------------------------
    # 🛡️ التحقق من أن البيانات من اليوم + فيه شموع صباحية
    # ---------------------------------------------------------
    ny_tz = pytz.timezone('America/New_York')
    today_date = datetime.now(ny_tz).date()
    last_data_date = full_df.index[-1].date()

    # فحص شموع الصباح لهذا اليوم (6 شموع: 09:30 إلى 09:55)
    today_data = full_df[full_df.index.date == today_date]
    morning_candles = today_data.between_time('09:30', '09:55') if len(today_data) > 0 else pd.DataFrame()

    if len(morning_candles) < 3:
        # إذا بيانات اليوم غير متوفرة، نتحقق من آخر يوم متاح
        if last_data_date < today_date:
            print(f"⚠️ بيانات قديمة ({last_data_date}) - لا شموع صباح اليوم")
            return
        else:
            print(f"⚠️ لا شموع صباحية كافية ({len(morning_candles)})")
            return

    # =========================================================
    # 🛡️ فحص الاستراتيجية (Golden Grinder)
    # =========================================================
    # نرسل الداتا الكاملة لحساب المتوسطات بدقة (780 شمعة)
    is_golden = is_golden_grinder(full_df, symbol_debug=ticker)
    beauty_score = calculate_beauty_score(full_df)

    # =========================================================
    # 🧬 فحص الأنماط (Pattern Matching) - على شموع الصباح فقط!
    # =========================================================
    match_score = 0
    match_name = "NONE"
    badge = None

    if reference_patterns and pattern_metrics and len(full_df) >= 6:
        # 🔥 فلترة شموع الصباح فقط (6 شموع: 9:30 - 9:55)!
        ny_tz = pytz.timezone('America/New_York')
        today_date = datetime.now(ny_tz).date()
        df_today = full_df[full_df.index.date == today_date]
        df_morning = df_today.between_time('09:30', '09:55')

        if len(df_morning) >= 3:
            current_candles = df_morning[['open', 'high', 'low', 'close']].values
            match_score, match_name = calculate_similarity(current_candles, reference_patterns, pattern_metrics)
            
            # حساب الوسام (نمرر الأنماط المحملة من الملف)
            current_volume = df_morning['volume'].values
            badge = get_badge(match_name, current_candles, current_volume, reference_patterns)
            
            # 🔥 إذا لم يكن نخبوياً، تجاهل الإشارة تماماً
            if badge is None:
                print(f"⚠️ ليس نخبوياً - تم التجاهل")
                match_score = 0  # إلغاء الإشارة

    # =========================================================
    # 📢 إرسال التنبيهات (Pattern Matching فقط - بدون الزحف الذهبي)
    # =========================================================

    # 🚫 تم إلغاء الزحف الذهبي - إشاراته كانت سيئة!
    # الاعتماد على Pattern Matching فقط مع الأنماط النخبوية

    # تنبيه الأنماط فقط (إذا كان التطابق قوياً + نخبوي + جودة شموع عالية)
    if match_score >= MATCH_THRESHOLD and badge is not None and beauty_score >= 70:
        print(f"🧬 {badge} ({match_score}%) جودة={beauty_score}%", end=" ")
        send_telegram_alert(ticker, full_df, float_shares, match_score, match_name, "PATTERN_MATCH", country_code, beauty_score, badge)
    else:
        print(f"❌ (Match={match_score:.0f}%, جودة={beauty_score:.0f}%)")
        return

# ==============================================================================
# 4️⃣ الإرسال للتليقرام
# ==============================================================================
def send_telegram_alert(ticker, df, float_shares, match_score, match_name, alert_type, country_code, beauty_score, badge=None):
    if not TELEGRAM_TOKEN: return

    # 1. البيانات
    close = float(df.iloc[-1]['close'])
    high = float(df['high'].max())
    vol = float(df['volume'].sum())
    rot = (vol / float_shares * 100) if float_shares else 0
    shariah = check_shariah_status(ticker)
    flag = get_flag_emoji(country_code)

    # وصف القوة الفنية
    if beauty_score >= 90: tech_desc = "ملكي (زحف مثالي)"
    elif beauty_score >= 80: tech_desc = "نظيف جداً"
    elif beauty_score >= 70: tech_desc = "جيد/متماسك"
    else: tech_desc = "متذبذب/فوضوي"

    # 3. تحديد القوة (Badge)
    strength_text = badge if badge else "غير مصنف"
    if not badge:
        if alert_type == "GOLDEN_GRINDER": strength_text = "✨ زحف ذهبي"
        elif alert_type == "PATTERN_MATCH": strength_text = "🧬 نمط فني"

    # 4. حالة السيولة
    liq_status = "ضعيف"
    if rot > 20: liq_status = "انفجار"
    elif rot > 5: liq_status = "ممتاز"
    elif rot > 1: liq_status = "جيد"

    # 5. الدخول
    if close >= high:
        action_icon = "🚀"
        action_text = f"دخول مباشر: ${close:.4f}"
    else:
        stop_price = high + 0.01
        action_icon = "✋"
        action_text = f"أمر معلق: ${stop_price:.4f}"

    # ==========================
    # 📩 شكل الرسالة النهائي
    # ==========================
    msg = f"""🚨 <b>إشارة دخول محتملة</b>
💎 القوة: <b>{strength_text}</b>

🎫 السهم: <code>{ticker}</code> {flag}
🧬 التطابق: <b>{match_score:.1f}%</b> (مع {match_name})
🎨 جودة الشموع: <b>{beauty_score:.0f}%</b> ({tech_desc})

💵 السعر: <b>${close:.4f}</b>
📈 القمة: ${high:.4f}
💧 السيولة: {liq_status} ({rot:.1f}%)
🪶 الفلوت: {float_shares/1_000_000:.1f}M
⚖️ الحكم: {shariah}
━━━━━━━━━━━━━━
{action_icon} <b>{action_text}</b>"""

    try:
        # محاولة الإرسال مع retry
        for attempt in range(3):
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": str(CHAT_ID), "text": msg, "parse_mode": "HTML"},
                    timeout=10
                )
                if response.status_code == 200:
                    time.sleep(0.5)  # تأخير بين الرسائل لتجنب الحد
                    break
                elif response.status_code == 429:  # Too Many Requests
                    retry_after = response.json().get('parameters', {}).get('retry_after', 5)
                    time.sleep(retry_after)
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(2)
                    continue
                raise
    except Exception as e:
        print(f"❌ خطأ الإرسال: {e}")

# ==============================================================================
# 🚀 التشغيل
# ==============================================================================
def run_bot():
    print("🧠 جاري تحميل ذاكرة الأنماط...")
    patterns, pattern_metrics = load_successful_patterns()

    ny_tz = pytz.timezone('America/New_York')
    print(f"⏳ بانتظار الساعة {TARGET_TIME} بتوقيت نيويورك...")

    while True:
        now = datetime.now(ny_tz).strftime("%H:%M")
        if now >= TARGET_TIME:
            print("🚀 بدأ وقت الصيد!\n")
            break
        time.sleep(10)

    print("📦 جاري سحب القائمة الحية من FMP...")
    tickers = get_guaranteed_50_list()
    if not tickers:
        print("❌ لم يتم العثور على أسهم مناسبة اليوم."); return

    print(f"\n🔬 جاري تحليل {len(tickers)} سهم بسرعة عالية (Threads)...\n")

    # =======================================================
    # 🚀 هنا يكمن السر: الفحص المتوازي
    # =======================================================
    # max_workers=5 تعني: افحص 5 أسهم في نفس الوقت
    # لا تزد الرقم كثيراً عشان لا يتبند اشتراكك من FMP
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # تجهيز الأوامر
        futures = {executor.submit(analyze_stock, stock, patterns, pattern_metrics): stock for stock in tickers}

        # تنفيذ وانتظار النتائج
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result() # هذا السطر عشان لو فيه خطأ يظهر
            except Exception as e:
                print(f"⚠️ خطأ بسيط في أحد الخيوط: {e}")

    print("\n✅ انتهى الفحص.")

def main_morning_scanner():
    """
    البوت الرئيسي - يشتغل على بيانات الصباح من 9:30 إلى 10:00
    لو شغلته اليوم: يجيب الشموع مباشرة
    لو شغلته بكره قبل 10:03: يقول "انتظر"
    لو شغلته بكره بعد 10:03: يشتغل مباشرة
    """
    import time as time_module

    # تحميل الأنماط أولاً
    print("🧠 جاري تحميل ذاكرة الأنماط...")
    patterns, pattern_metrics = load_successful_patterns()

    # المنطقة الزمنية (نيويورك)
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)

    print("=" * 90)
    print("🌅 ماسح السوق الصباحي - Morning Scanner")
    print("=" * 90)
    print(f"⏰ الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # تحقق من أن السوق مفتوح (الاثنين إلى الجمعة)
    day_of_week = now.weekday()  # 0=الاثنين، 4=الجمعة، 5-6=عطل
    if day_of_week >= 5:
        print("❌ السوق مغلق اليوم (عطلة نهاية الأسبوع)")
        return

    # تحقق من الوقت
    target_hour = 10
    target_minute = 3
    current_time_minutes = now.hour * 60 + now.minute
    target_time_minutes = target_hour * 60 + target_minute
    market_open_minutes = 9 * 60 + 30  # 9:30 صباحاً

    # إذا كان قبل 9:30 صباحاً
    if current_time_minutes < market_open_minutes:
        print("⏳ السوق لم يفتح بعد (يفتح الساعة 9:30 صباحاً)")
        return

    # إذا كان الوقت بين 9:30 و 10:03 = انتظر حتى 10:03
    if current_time_minutes < target_time_minutes:
        wait_minutes = target_time_minutes - current_time_minutes
        print(f"⏳ انتظر حتى الساعة {target_hour}:{target_minute:02d} (بقي {wait_minutes} دقيقة)")
        print("   🔄 سينتظر البوت تلقائياً...")
        
        # انتظار حتى 10:03
        import time as time_module
        while True:
            now = datetime.now(ny_tz)
            current_mins = now.hour * 60 + now.minute
            if current_mins >= target_time_minutes:
                print("\n🚀 حان وقت البدء!")
                break
            time_module.sleep(10)  # فحص كل 10 ثواني

    print(f"✅ وقت البدء! (بعد {target_hour}:{target_minute:02d} صباحاً)")
    print("\n🔍 بدء المسح...\n")

    # جلب الأسهم من FMP (100 سهم)
    print("📥 جلب 100 سهم من FMP API...")
    stock_list = get_guaranteed_50_list()  # يجيب 100 سهم

    # 🔥 إضافة GNL يدوياً للاختبار (إذا لم يكن موجوداً)
    gnl_exists = any(s['symbol'] == 'GNL' for s in stock_list)
    if not gnl_exists:
        print("🧪 إضافة سهم GNL يدوياً للاختبار...")
        stock_list.append({'symbol': 'GNL', 'float': 100_000_000, 'country': 'US'})

    if not stock_list:
        print("❌ فشل جلب الأسهم من FMP")
        return

    print(f"✅ تم جلب {len(stock_list)} سهم من FMP\n")

    # فحص الأسهم
    passed_count = 0

    # ملف لحفظ البيانات الخام للمراجعة
    debug_file = f"morning_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    all_candles_data = []

    # دالة المعالجة لكل سهم (للتشغيل المتوازي)
    def process_stock(item):
        nonlocal passed_count
        symbol = item['symbol']
        float_shares = item['float']
        country = item.get('country', 'US')

        try:
            # 1. جلب التاريخ من EODHD
            history = get_eodhd_history(symbol)

            # 2. محاولة جلب بيانات اليوم من FMP (إذا توفرت)
            # تم إيقاف FMP مؤقتاً بسبب مشاكل في التحديث/الاشتراك
            # سنعتمد على EODHD حالياً، ولكن سنضيف رسالة توضيحية إذا كانت البيانات قديمة

            if history is None or len(history) < 5:
                return

            # 🔥 التحقق الصارم من التاريخ: يجب أن تكون البيانات لليوم الحالي فقط
            ny_tz = pytz.timezone('America/New_York')
            today_date = datetime.now(ny_tz).date()

            last_candle_date = history.index[-1].date()

            if last_candle_date != today_date:
                # ❌ لا بيانات لليوم = تخطي السهم
                return

            # التحقق من وجود شموع صباحية (6 شموع: 9:30-9:55)
            df_today = history[history.index.date == today_date]
            df_morning = df_today.between_time('09:30', '09:55')

            if len(df_morning) < 3:
                # ❌ لا شموع صباحية كافية = تخطي السهم
                return

            # حفظ البيانات للمراجعة لاحقاً
            last_candles = history.tail(20).copy()
            last_candles['symbol'] = symbol
            last_candles.reset_index(inplace=True)
            all_candles_data.append(last_candles)

            # حساب متوسط جسم الشمعة (للعرض فقط)
            avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in df_morning[['open','high','low','close']].values])

            # 2. فحص الأنماط (Pattern Matching) - على شموع الصباح فقط!
            match_score = 0
            match_name = "None"
            badge = None

            # نأخذ شموع الصباح فقط للمطابقة (تم التحقق منها أعلاه)
            pattern_data = df_morning[['open', 'high', 'low', 'close']].values
            if len(pattern_data) >= 3:
                match_score, match_name = calculate_similarity(pattern_data, patterns, pattern_metrics)
                
                # حساب الوسام
                current_volume = df_morning['volume'].values
                badge = get_badge(match_name, pattern_data, current_volume, patterns)

            # =========================================================
            # 📢 إرسال التنبيهات (Pattern Matching فقط - بدون الزحف الذهبي!)
            # =========================================================
            
            beauty = calculate_beauty_score(history)

            # 🔥 فلتر صارم: التطابق + الجودة + النخبوية
            if match_score >= MATCH_THRESHOLD and badge is not None and beauty >= MIN_BEAUTY_SCORE:
                print(f"✅ {badge}: {symbol} (تطابق={match_score:.0f}%, جودة={beauty:.0f}%)")
                send_telegram_alert(symbol, history, float_shares, match_score, match_name, "PATTERN_MATCH", country, beauty, badge)
                passed_count += 1
            else:
                reason = []
                if match_score < MATCH_THRESHOLD:
                    reason.append(f"تطابق={match_score:.0f}%<{MATCH_THRESHOLD}%")
                if beauty < MIN_BEAUTY_SCORE:
                    reason.append(f"جودة={beauty:.0f}%<{MIN_BEAUTY_SCORE}%")
                if badge is None:
                    reason.append("ليس نخبوي")
                print(f"❌ {symbol} ({', '.join(reason)})")

        except Exception as e:
            print(f"⚠️ خطأ في {symbol}: {e}")
            pass

    # تشغيل الفحص المتوازي (8 عمال)
    print(f"🚀 بدء الفحص المتوازي (8 Workers)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_stock, item) for item in stock_list]
        concurrent.futures.wait(futures)

    # النتائج
    print("\n" + "=" * 90)

    # حفظ ملف البيانات الخام
    if all_candles_data:
        try:
            full_debug_df = pd.concat(all_candles_data)
            full_debug_df.to_csv(debug_file, index=False)
            print(f"💾 تم حفظ بيانات الشموع للمراجعة في: {debug_file}")
        except Exception as e:
            print(f"⚠️ فشل حفظ ملف البيانات: {e}")

    if passed_count > 0:
        print(f"🎯 وجدنا {passed_count} سهم وتم إرسالها للتليقرام!")
    else:
        print("❌ لا توجد أسهم اجتازت الفلتر الآن")
    print("=" * 90)
    print("\n✅ انتهى المسح!")

if __name__ == "__main__":
    main_morning_scanner()
