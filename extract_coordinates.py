import requests
import xml.etree.ElementTree as ET
import json
import re

def extract_verse_coordinates(page_num):
    """
    استخراج الإحداثيات التقريبية للآيات من صور SVG
    """
    # الحصول على بيانات الآيات من API
    try:
        res = requests.get(f'https://api.alquran.cloud/v1/page/{page_num}/quran-uthmani')
        data = res.json()
        ayahs = data['data']['ayahs']
    except:
        print(f"خطأ في جلب البيانات للصفحة {page_num}")
        return None
    
    print(f"\n{'='*50}")
    print(f"صفحة {page_num}: {ayahs[0]['surah']['name']}")
    print(f"عدد الآيات: {len(ayahs)}")
    print(f"{'='*50}\n")
    
    # محاولة الحصول على SVG
    padded = str(page_num).zfill(3)
    svg_url = f'https://raw.githubusercontent.com/batoulapps/quran-svg/main/svg/{padded}.svg'
    
    try:
        svg_response = requests.get(svg_url, timeout=10)
        svg_text = svg_response.text
        
        # البحث عن نصوص في SVG
        # SVG قد يحتوي على أرقام الآيات
        coordinates_map = {}
        
        for ayah in ayahs:
            verse_num = ayah['numberInSurah']
            verse_text = ayah['text'][:20]  # أول 20 حرف
            
            # محاولة إيجاد الآية في SVG
            if verse_text in svg_text:
                # البحث عن الإحداثيات حول النص
                pattern = f'translate\\(([\\d.]+),([\\d.]+)\\)'
                matches = re.finditer(pattern, svg_text)
                
                positions = []
                for match in matches:
                    x, y = float(match.group(1)), float(match.group(2))
                    positions.append((x, y))
                
                if positions:
                    # أخذ أول موضع (تقريبي)
                    x, y = positions[0]
                    coordinates_map[verse_num] = {
                        'x': x,
                        'y': y,
                        'text': verse_text
                    }
                    print(f"✓ الآية {verse_num}: تم العثور عليها")
                else:
                    # إذا لم نجد إحداثيات محددة، استخدم توزيع افتراضي
                    # الآيات توزعت من الأعلى للأسفل
                    y_position = 50 + (verse_num - 1) * 30
                    x_position = 250
                    coordinates_map[verse_num] = {
                        'x': x_position,
                        'y': y_position,
                        'text': verse_text,
                        'estimated': True
                    }
                    print(f"⚠ الآية {verse_num}: إحداثيات تقريبية")
            else:
                print(f"✗ الآية {verse_num}: لم يتم العثور عليها في SVG")
        
        return coordinates_map
    
    except Exception as e:
        print(f"خطأ في معالجة SVG: {e}")
        return None

# اختبار على صفحتين
pages_to_test = [1, 2]
all_coordinates = {}

for page in pages_to_test:
    coords = extract_verse_coordinates(page)
    if coords:
        all_coordinates[page] = coords

# حفظ النتائج
with open('/workspaces/Sellam_bot/verse_coordinates.json', 'w', encoding='utf-8') as f:
    json.dump(all_coordinates, f, ensure_ascii=False, indent=2)

print("\n✅ تم حفظ الإحداثيات في verse_coordinates.json")
