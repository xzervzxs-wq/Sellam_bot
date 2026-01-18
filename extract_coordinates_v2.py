import requests
import json
import re
from xml.etree import ElementTree as ET

def extract_verse_coordinates_v2(page_num):
    """
    استخراج الإحداثيات من SVG بناءً على translate attributes
    """
    try:
        res = requests.get(f'https://api.alquran.cloud/v1/page/{page_num}/quran-uthmani')
        data = res.json()
        ayahs = data['data']['ayahs']
    except:
        return None
    
    print(f"\n{'='*60}")
    print(f"صفحة {page_num}: {ayahs[0]['surah']['name']} ({len(ayahs)} آيات)")
    print(f"{'='*60}\n")
    
    # جلب SVG
    padded = str(page_num).zfill(3)
    svg_url = f'https://raw.githubusercontent.com/batoulapps/quran-svg/main/svg/{padded}.svg'
    
    try:
        svg_response = requests.get(svg_url, timeout=10)
        svg_text = svg_response.text
        
        # البحث عن جميع عناصر translate
        # pattern: translate(x,y) وغالباً تكون أرقام الآيات بالقرب منها
        pattern = r'translate\(([0-9.]+),([0-9.]+)\)'
        coordinates = []
        
        for match in re.finditer(pattern, svg_text):
            x = float(match.group(1))
            y = float(match.group(2))
            coordinates.append((x, y))
        
        print(f"تم العثور على {len(coordinates)} عنصر translate")
        
        # الآن سنحاول ربط الإحداثيات بالآيات
        # بما أن الصفحة من اليمين لليسار، والآيات مرتبة عمودياً
        coordinates_map = {}
        
        # ترتيب الإحداثيات الفريدة والمهمة (تخطي التكرارات الصغيرة)
        unique_coords = list(set(coordinates))
        unique_coords.sort(key=lambda c: c[1])  # ترتيب حسب Y (من الأعلى للأسفل)
        
        print(f"\nإحداثيات فريدة: {len(unique_coords)}")
        
        # ربط الآيات بالإحداثيات
        for idx, ayah in enumerate(ayahs):
            verse_num = ayah['numberInSurah']
            
            # استخدم أول إحداثيات فريدة متاحة
            if idx < len(unique_coords):
                x, y = unique_coords[idx]
                coordinates_map[verse_num] = {
                    'x': round(x, 2),
                    'y': round(y, 2),
                    'text': ayah['text'][:15],
                    'surah': ayah['surah']['name'],
                    'source': 'svg_analysis'
                }
                print(f"  الآية {verse_num}: ({round(x,2)}, {round(y,2)})")
            else:
                print(f"  الآية {verse_num}: لا توجد إحداثيات كافية")
        
        return coordinates_map
    
    except Exception as e:
        print(f"خطأ: {e}")
        return None

# اختبار
all_coords = {}
for page in [1, 2]:
    coords = extract_verse_coordinates_v2(page)
    if coords:
        all_coords[page] = coords

# الحفظ
with open('/workspaces/Sellam_bot/verse_coordinates_v2.json', 'w', encoding='utf-8') as f:
    json.dump(all_coords, f, ensure_ascii=False, indent=2)

print("\n✅ تم الحفظ في verse_coordinates_v2.json")
