import pandas as pd
import numpy as np

print("="*70)
print("🧪 اختبار نظام المطابقة الجديد")
print("="*70)

# شموع ATAI (من اليوم)
atai = np.array([
    [4.1593, 4.18, 4.155, 4.18],    # 🟢 صاعدة
    [4.175, 4.18, 4.165, 4.165],    # 🔴 هابطة
    [4.16, 4.1993, 4.16, 4.185],    # 🟢 صاعدة
    [4.1844, 4.1899, 4.18, 4.18],   # 🔴 هابطة
    [4.19, 4.19, 4.165, 4.175],     # 🔴 هابطة
    [4.175, 4.21, 4.165, 4.2],      # 🟢 صاعدة
])

# شموع WIT (من الملف)
wit = np.array([
    [2.91, 2.91, 2.89, 2.90],       # 🔴 هابطة
    [2.905, 2.93, 2.905, 2.92],     # 🟢 صاعدة
    [2.925, 2.935, 2.925, 2.935],   # 🟢 صاعدة
    [2.935, 2.94, 2.925, 2.93],     # 🔴 هابطة
    [2.93, 2.94, 2.925, 2.935],     # 🟢 صاعدة
    [2.94, 2.97, 2.94, 2.965],      # 🟢 صاعدة
])

# استخراج تفاصيل الشموع
def get_details(candles):
    details = []
    for i in range(len(candles)):
        o, h, l, c = candles[i]
        body_pct = (c - o) / o * 100
        direction = 1 if c >= o else -1
        body_size = abs(body_pct)
        details.append({
            'direction': direction,
            'body_pct': body_pct,
            'body_size': body_size,
            'open': o, 'high': h, 'low': l, 'close': c
        })
    return details

atai_details = get_details(atai)
wit_details = get_details(wit)

print("\n📊 مقارنة شمعة بشمعة:")
print("-"*60)
print(f"{'شمعة':<8} {'ATAI':<15} {'WIT':<15} {'تطابق؟'}")
print("-"*60)

direction_matches = 0
for i in range(6):
    a_dir = "🟢 صاعدة" if atai_details[i]['direction'] == 1 else "�� هابطة"
    w_dir = "🟢 صاعدة" if wit_details[i]['direction'] == 1 else "🔴 هابطة"
    match = "✅" if atai_details[i]['direction'] == wit_details[i]['direction'] else "❌"
    if atai_details[i]['direction'] == wit_details[i]['direction']:
        direction_matches += 1
    print(f"  {i+1:<6} {a_dir:<15} {w_dir:<15} {match}")

direction_ratio = direction_matches / 6
print("-"*60)
print(f"تطابق الاتجاهات: {direction_matches}/6 ({direction_ratio*100:.0f}%)")

# الشرط الجديد: يجب 67% على الأقل
if direction_ratio < 0.67:
    print(f"\n🚫 مرفوض! (أقل من 67%)")
else:
    print(f"\n✅ مقبول للمقارنة")

# حساب الدرجة الكاملة
print("\n" + "="*70)
print("📈 حساب الدرجة النهائية:")
print("="*70)

if direction_ratio >= 0.67:
    direction_score = direction_ratio * 100
    print(f"1️⃣ درجة الاتجاهات: {direction_score:.0f}%")
    
    # حجم الشموع
    size_penalties = 0
    for i in range(6):
        curr_size = atai_details[i]['body_size']
        ref_size = wit_details[i]['body_size']
        if ref_size > 0:
            size_diff = abs(curr_size - ref_size) / max(ref_size, 0.1)
        else:
            size_diff = curr_size
        if size_diff > 1.0:
            size_penalties += min(size_diff - 1.0, 1.0) * 20
    size_score = max(0, 100 - size_penalties)
    print(f"2️⃣ درجة أحجام الشموع: {size_score:.0f}%")
    
    # الاتجاه العام
    curr_trend = (atai_details[-1]['close'] - atai_details[0]['open']) / atai_details[0]['open'] * 100
    ref_trend = (wit_details[-1]['close'] - wit_details[0]['open']) / wit_details[0]['open'] * 100
    print(f"   - صعود ATAI: {curr_trend:+.2f}%")
    print(f"   - صعود WIT: {ref_trend:+.2f}%")
    
    if curr_trend <= 0:
        trend_score = 0
    else:
        trend_diff = abs(curr_trend - ref_trend) / max(ref_trend, 0.1)
        trend_score = max(0, 100 - (trend_diff * 30))
    print(f"3️⃣ درجة الاتجاه العام: {trend_score:.0f}%")
    
    final_score = direction_score * 0.50 + size_score * 0.30 + trend_score * 0.20
    print(f"\n🏁 الدرجة النهائية: {final_score:.1f}%")
else:
    print("🚫 لم يتم حساب الدرجة (مرفوض من البداية)")
