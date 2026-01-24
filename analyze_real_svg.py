#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحليل حقيقي لمواضع الآيات في ملفات SVG الفعلية
بدون تخمين - بيانات حقيقية فقط!
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

SVG_BASE_URL = "https://raw.githubusercontent.com/batoulapps/quran-svg/main/svg/"
PAGE_WIDTH = 510.236
PAGE_HEIGHT = 729.448

def fetch_and_analyze_svg(page_num):
    """تحميل وتحليل ملف SVG الفعلي"""
    padded = str(page_num).zfill(3)
    url = f"{SVG_BASE_URL}{padded}.svg"
    
    print(f"\n📄 تحليل الصفحة {page_num}: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # حفظ SVG محلياً للتحليل
        svg_content = response.text
        
        # تحليل XML
        root = ET.fromstring(svg_content.encode('utf-8'))
        
        # البحث عن جميع عناصر text و tspan
        verse_positions = []
        
        # التعامل مع namespaces
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        text_elements = root.findall('.//svg:text', ns)
        if not text_elements:
            text_elements = root.findall('.//text')
        
        print(f"   وجدت {len(text_elements)} عنصر نص")
        
        for idx, text_elem in enumerate(text_elements):
            x = text_elem.get('x', '0')
            y = text_elem.get('y', '0')
            text_content = text_elem.text or ''
            
            # هل يحتوي على أرقام قرآنية؟
            text_content = text_content.strip()
            
            # البحث عن أرقام عربية وإنجليزية
            if text_content and any(c in '0123456789٠١٢٣٤٥٦٧٨٩' for c in text_content):
                try:
                    x_val = float(x) if x else 0
                    y_val = float(y) if y else 0
                    
                    x_percent = (x_val / PAGE_WIDTH) * 100
                    y_percent = (y_val / PAGE_HEIGHT) * 100
                    
                    print(f"   ✓ {text_content:>3} | X: {x_val:7.2f}px ({x_percent:5.1f}%) | Y: {y_val:7.2f}px ({y_percent:5.1f}%)")
                    
                    verse_positions.append({
                        'text': text_content,
                        'x_pixel': x_val,
                        'y_pixel': y_val,
                        'x_percent': x_percent,
                        'y_percent': y_percent
                    })
                except ValueError:
                    pass
        
        if verse_positions:
            # حساب الإحصائيات
            y_values = [p['y_pixel'] for p in verse_positions]
            x_values = [p['x_pixel'] for p in verse_positions]
            
            print(f"\n   📊 الإحصائيات:")
            print(f"      - أرقام الآيات الموجودة: {len(verse_positions)}")
            print(f"      - نطاق Y: {min(y_values):.1f}px - {max(y_values):.1f}px ({(min(y_values)/PAGE_HEIGHT)*100:.1f}% - {(max(y_values)/PAGE_HEIGHT)*100:.1f}%)")
            print(f"      - نطاق X: {min(x_values):.1f}px - {max(x_values):.1f}px ({(min(x_values)/PAGE_WIDTH)*100:.1f}% - {(max(x_values)/PAGE_WIDTH)*100:.1f}%)")
            
            # حساب التباعد بين الآيات
            if len(verse_positions) > 1:
                y_diffs = []
                for i in range(1, len(verse_positions)):
                    diff = verse_positions[i]['y_pixel'] - verse_positions[i-1]['y_pixel']
                    y_diffs.append(diff)
                
                avg_spacing = sum(y_diffs) / len(y_diffs) if y_diffs else 0
                print(f"      - متوسط التباعد العمودي: {avg_spacing:.1f}px")
        else:
            print(f"   ⚠️ لم يتم العثور على أرقام!")
        
        return verse_positions
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return None

def main():
    """تحليل عدة صفحات"""
    print("=" * 70)
    print("🔍 تحليل حقيقي لمواضع الآيات في ملفات SVG الفعلية")
    print("=" * 70)
    
    # اختبر الصفحات الأولى
    test_pages = [1, 2, 10, 50, 100]
    
    all_results = {}
    for page in test_pages:
        result = fetch_and_analyze_svg(page)
        all_results[page] = result
    
    # ملخص نهائي
    print("\n" + "=" * 70)
    print("📋 الملخص النهائي")
    print("=" * 70)
    
    for page, positions in all_results.items():
        if positions:
            print(f"✓ الصفحة {page}: {len(positions)} آية")
        else:
            print(f"✗ الصفحة {page}: لم يتم العثور على بيانات")

if __name__ == '__main__':
    main()
