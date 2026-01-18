#!/usr/bin/env python3
"""
نظام تحديد موضع الآيات الذكي:
بدلاً من التخمين، سنستخدم معلومات الصفحة الفعلية
"""

import requests

def get_verse_positions_v3(page_num):
    """
    نظام ذكي لتحديد موضع الآيات:
    1. جلب الآيات على الصفحة
    2. حساب عدد الأسطر تقريبياً (بناءً على طول المصحف)
    3. توزيع الآيات بناءً على ظهورها الفعلي في النص
    
    طريقة التوزيع:
    - الصفحة تبدأ من الأعلى (Y: 5%) وتنتهي من الأسفل (Y: 95%)
    - كل آية موضع تقريبي يعتمد على:
      * موضعها في النص (أول، وسط، نهاية)
      * عدد الكلمات قبلها
    """
    try:
        res = requests.get(f'https://api.alquran.cloud/v1/page/{page_num}/quran-uthmani', timeout=5)
        data = res.json()
        ayahs = data['data']['ayahs']
        
        if not ayahs:
            return []
        
        # معلومات الصفحة الهندسية
        page_width = 510.236
        page_height = 729.448
        
        # المنطقة المتاحة للنص (مع حواشي)
        text_left = 60          # حاشية يسار
        text_right = 450        # حاشية يمين
        text_top = 40           # حاشية أعلى
        text_bottom = 680       # حاشية أسفل
        
        text_width = text_right - text_left
        text_height = text_bottom - text_top
        
        # افتراض عدد الأسطر في الصفحة (تقريباً 15-17 سطر)
        lines_per_page = 15
        line_height = text_height / lines_per_page
        
        positions = []
        
        # حساب إجمالي الكلمات لتقسيم الصفحة بشكل متناسب
        total_words = sum(len(a['text'].split()) for a in ayahs)
        cumulative_words = 0
        current_line = 0
        current_x_in_line = 0  # 0 = يسار، 0.5 = وسط، 1 = يمين
        
        for idx, ayah in enumerate(ayahs):
            word_count = len(ayah['text'].split())
            
            # حساب السطر الحالي بناءً على الكلمات
            if total_words > 0:
                position_ratio = cumulative_words / total_words
                current_line = int(position_ratio * lines_per_page)
                current_line = min(current_line, lines_per_page - 1)
            
            # الموضع Y (العمودي)
            y_pixel = text_top + (current_line * line_height)
            y_percent = (y_pixel / page_height) * 100
            
            # الموضع X (الأفقي) - يتناوب بين اليسار والوسط واليمين
            x_positions = [text_left + 40, text_left + text_width/2, text_left + text_width - 40]
            x_idx = idx % 3
            x_pixel = x_positions[x_idx]
            x_percent = (x_pixel / page_width) * 100
            
            positions.append({
                'ayah_number': ayah['numberInSurah'],
                'x_percent': x_percent,
                'y_percent': y_percent,
                'line': current_line,
                'word_count': word_count
            })
            
            cumulative_words += word_count
        
        return positions
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []


# اختبار
if __name__ == '__main__':
    print("🧪 اختبار نظام التحديد الذكي:\n")
    
    test_pages = [1, 2, 5]
    
    for page in test_pages:
        positions = get_verse_positions_v3(page)
        if positions:
            print(f"📄 الصفحة {page} - {len(positions)} آية")
            print("=" * 60)
            for p in positions[:5]:
                print(f"  آية {p['ayah_number']:2d} | X:{p['x_percent']:6.1f}% Y:{p['y_percent']:6.1f}% | السطر {p['line']:2d} | {p['word_count']} كلمة")
            if len(positions) > 5:
                print(f"  ... و {len(positions) - 5} آيات أخرى")
            print()

