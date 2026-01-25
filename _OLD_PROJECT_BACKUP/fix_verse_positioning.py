#!/usr/bin/env python3
"""
الحل الصحيح: استخدام API لجلب الآيات ثم توزيعها بذكاء على الصفحة
بدلاً من البحث عن إحداثيات في SVG (التي لا تحتوي على بيانات الآيات)
"""

import requests
import json

def get_page_ayahs_distribution(page_num):
    """
    جلب الآيات والصفحة ثم حساب التوزيع الذكي
    """
    try:
        # جلب الآيات من API
        res = requests.get(f'https://api.alquran.cloud/v1/page/{page_num}/quran-uthmani', timeout=5)
        data = res.json()
        
        if data['status'] != 'OK':
            return None
            
        ayahs = data['data']['ayahs']
        ayah_count = len(ayahs)
        
        # الآن لدينا الآيات الفعلية وعددها الصحيح
        # يجب توزيعها على الصفحة بناءً على:
        # 1. عدد الأسطر التقريبي على الصفحة
        # 2. طول كل آية (عدد الكلمات)
        
        distribution = []
        
        # حساب موضع كل آية بناءً على ترتيبها وطولها
        total_length = sum(len(a['text'].split()) for a in ayahs)
        
        cumulative_position = 0
        
        for idx, ayah in enumerate(ayahs):
            # موضع الآية بناءً على نسبة طولها من إجمالي النص
            word_count = len(ayah['text'].split())
            position_ratio = cumulative_position / max(total_length, 1)
            
            # تحويل إلى نسبة مئوية من ارتفاع الصفحة (مع حاشية)
            percent_y = 5 + (position_ratio * 90)  # من 5% إلى 95%
            
            # الموضع الأفقي: تقريباً في المنتصف مع تذبذب طفيف
            percent_x = 50 + (((idx % 3) - 1) * 15)
            
            distribution.append({
                'ayah_number': ayah['numberInSurah'],
                'global_number': ayah['number'],
                'surah': ayah['surah']['number'],
                'percent_x': max(10, min(90, percent_x)),
                'percent_y': max(5, min(95, percent_y)),
                'word_count': word_count
            })
            
            cumulative_position += word_count
        
        return {
            'page': page_num,
            'ayah_count': ayah_count,
            'distribution': distribution,
            'total_words': total_length
        }
        
    except Exception as e:
        print(f"❌ خطأ في الصفحة {page_num}: {e}")
        return None


def test_distribution():
    """اختبار التوزيع على عدة صفحات"""
    print("🔍 اختبار التوزيع الذكي للآيات:")
    print("-" * 80)
    
    test_pages = [1, 2, 5, 10]
    
    for page in test_pages:
        result = get_page_ayahs_distribution(page)
        if result:
            print(f"\n✓ الصفحة {page} | عدد الآيات: {result['ayah_count']} | إجمالي الكلمات: {result['total_words']}")
            print("  توزيع الآيات:")
            for d in result['distribution'][:3]:  # أول 3 آيات فقط
                print(f"    - الآية {d['ayah_number']} @ X:{d['percent_x']:.1f}% Y:{d['percent_y']:.1f}%")
            if len(result['distribution']) > 3:
                print(f"    ... و {len(result['distribution']) - 3} آيات أخرى")

if __name__ == '__main__':
    test_distribution()
