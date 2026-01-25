#!/usr/bin/env python3
"""
برنامج تحديد الآيات تلقائياً من صور المصحف باستخدام OCR
يقرأ صورة SVG ويحدد مواقع كل آية تلقائياً
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import json
import sys
from pathlib import Path
from collections import defaultdict

class QuranAyahDetector:
    def __init__(self, image_path):
        """
        تهيئة المكشف
        Args:
            image_path: مسار الصورة (SVG أو PNG أو JPG)
        """
        self.image_path = Path(image_path)
        self.image = None
        self.gray = None
        self.height = 0
        self.width = 0
        self.ayahs_detected = []
        
    def load_image(self):
        """تحميل الصورة"""
        print(f"📂 جاري تحميل الصورة: {self.image_path}")
        
        if self.image_path.suffix.lower() == '.svg':
            # تحويل SVG إلى PNG أولاً
            from cairosvg import svg2png
            from io import BytesIO
            png_data = BytesIO()
            svg2png(bytestring=open(self.image_path, 'rb').read(), write_to=png_data)
            png_data.seek(0)
            img_array = np.frombuffer(png_data.read(), dtype=np.uint8)
            self.image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            self.image = cv2.imread(str(self.image_path))
        
        if self.image is None:
            print("❌ فشل تحميل الصورة!")
            return False
        
        self.height, self.width = self.image.shape[:2]
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        print(f"✅ تم تحميل الصورة: {self.width}x{self.height}")
        return True
    
    def enhance_image(self):
        """تحسين جودة الصورة للـ OCR"""
        print("🔧 جاري تحسين الصورة...")
        
        # تطبيق threshold
        _, binary = cv2.threshold(self.gray, 150, 255, cv2.THRESH_BINARY)
        
        # تقليل الضوضاء
        denoised = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, 
                                    cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        
        return denoised
    
    def detect_text_regions(self, enhanced):
        """الكشف عن مناطق النصوص (الآيات)"""
        print("🔍 جاري البحث عن مناطق النصوص...")
        
        # البحث عن الكنتورات (حدود النصوص)
        contours, _ = cv2.findContours(enhanced, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # تصفية الكنتورات الصغيرة جداً
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # تجاهل المناطق الصغيرة جداً
                valid_contours.append(contour)
        
        return sorted(valid_contours, key=lambda c: cv2.boundingRect(c)[1])  # ترتيب من أعلى لأسفل
    
    def extract_ayahs_with_ocr(self, enhanced):
        """استخراج الآيات باستخدام OCR"""
        print("🧠 جاري تشغيل OCR (قد يستغرق وقتاً)...")
        
        # استخدام Tesseract للعربية
        custom_config = r'--oem 3 --psm 6 -l ara'
        ocr_data = pytesseract.image_to_data(enhanced, config=custom_config, 
                                             output_type=pytesseract.Output.DICT)
        
        detected_ayahs = []
        
        # حساب الثقة (confidence)
        for i in range(len(ocr_data['text'])):
            if ocr_data['text'][i].strip():  # تجاهل النصوص الفارغة
                confidence = int(ocr_data['conf'][i])
                
                if confidence > 30:  # حد أدنى من الثقة
                    ayah = {
                        'text': ocr_data['text'][i],
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'confidence': confidence
                    }
                    detected_ayahs.append(ayah)
        
        return detected_ayahs
    
    def group_ayahs_by_line(self, ayahs):
        """تجميع الآيات حسب السطر (Y تقريباً متساوي)"""
        print("📍 جاري تجميع الآيات حسب الأسطر...")
        
        if not ayahs:
            return []
        
        lines = defaultdict(list)
        threshold = 20  # تجميع الآيات القريبة عمودياً
        
        for ayah in ayahs:
            y = ayah['y']
            # العثور على السطر الأقرب
            closest_line = min(lines.keys(), 
                             key=lambda k: abs(k - y), 
                             default=None) if lines else None
            
            if closest_line is None or abs(closest_line - y) > threshold:
                closest_line = y
            
            lines[closest_line].append(ayah)
        
        # ترتيب الآيات داخل كل سطر من اليمين لليسار (عربي)
        for line in lines.values():
            line.sort(key=lambda a: a['x'], reverse=True)
        
        return sorted(lines.items(), key=lambda x: x[0])
    
    def extract_ayah_numbers(self, grouped_ayahs):
        """محاولة استخراج أرقام الآيات"""
        print("🔢 جاري استخراج أرقام الآيات...")
        
        results = []
        ayah_counter = 1
        
        for line_y, ayahs_in_line in grouped_ayahs:
            for ayah in ayahs_in_line:
                # محاولة استخراج الرقم من النص
                text = ayah['text'].strip()
                
                # البحث عن أرقام عربية أو إنجليزية
                numbers = ''.join(filter(str.isdigit, text))
                
                if numbers:
                    ayah_num = int(numbers)
                else:
                    ayah_num = ayah_counter
                
                result = {
                    'ayah_number': ayah_num,
                    'text': text,
                    'x': ayah['x'],
                    'y': ayah['y'],
                    'width': ayah['width'],
                    'height': ayah['height'],
                    'confidence': ayah['confidence']
                }
                results.append(result)
                ayah_counter = ayah_num + 1
        
        return results
    
    def visualize_results(self, output_path=None):
        """رسم صورة توضيحية بالآيات المكتشفة"""
        print("🎨 جاري إنشاء صورة توضيحية...")
        
        if output_path is None:
            output_path = self.image_path.parent / f"{self.image_path.stem}_detected.jpg"
        
        annotated = self.image.copy()
        
        # رسم صناديق حول كل آية
        for ayah in self.ayahs_detected:
            x, y = ayah['x'], ayah['y']
            w, h = ayah['width'], ayah['height']
            
            # اللون حسب مستوى الثقة
            confidence = ayah['confidence']
            color = (0, 255, 0) if confidence > 60 else (0, 165, 255)
            
            # رسم الصندوق
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # كتابة رقم الآية
            cv2.putText(annotated, str(ayah['ayah_number']), 
                       (x + 5, y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imwrite(str(output_path), annotated)
        print(f"✅ تم حفظ الصورة التوضيحية: {output_path}")
        return output_path
    
    def save_results(self, output_path=None):
        """حفظ النتائج في JSON"""
        if output_path is None:
            output_path = self.image_path.parent / f"{self.image_path.stem}_ayahs.json"
        
        data = {
            'image_file': str(self.image_path),
            'image_size': {
                'width': self.width,
                'height': self.height
            },
            'total_ayahs_detected': len(self.ayahs_detected),
            'ayahs': self.ayahs_detected
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم حفظ النتائج: {output_path}")
        return output_path
    
    def process(self):
        """تشغيل العملية الكاملة"""
        print("\n" + "="*50)
        print("🔬 جاري تحليل الصورة...")
        print("="*50 + "\n")
        
        if not self.load_image():
            return False
        
        enhanced = self.enhance_image()
        
        # طريقة 1: استخدام OCR مباشرة
        raw_ayahs = self.extract_ayahs_with_ocr(enhanced)
        print(f"📊 تم الكشف عن {len(raw_ayahs)} منطقة نصية")
        
        # طريقة 2: البحث عن الكنتورات
        contours = self.detect_text_regions(enhanced)
        print(f"📍 تم الكشف عن {len(contours)} منطقة بحث عن الكنتورات")
        
        # دمج النتائج
        if raw_ayahs:
            grouped = self.group_ayahs_by_line(raw_ayahs)
            self.ayahs_detected = self.extract_ayah_numbers(grouped)
        
        if not self.ayahs_detected:
            print("⚠️ لم يتمكن من الكشف عن آيات! حاول صورة أوضح.")
            return False
        
        print(f"\n✅ تم الكشف عن {len(self.ayahs_detected)} آية!\n")
        
        # طباعة النتائج
        for ayah in self.ayahs_detected[:5]:  # أول 5 آيات
            print(f"  • آية {ayah['ayah_number']}: {ayah['text'][:30]}...")
            print(f"    الموقع: x={ayah['x']}, y={ayah['y']}, الثقة: {ayah['confidence']}%\n")
        
        if len(self.ayahs_detected) > 5:
            print(f"  ... و {len(self.ayahs_detected) - 5} آيات أخرى\n")
        
        # حفظ النتائج
        json_path = self.save_results()
        img_path = self.visualize_results()
        
        return True


def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python quran_ocr_detector.py <image_path>")
        print("مثال: python quran_ocr_detector.py page_003.svg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    detector = QuranAyahDetector(image_path)
    success = detector.process()
    
    if success:
        print("\n" + "="*50)
        print("🎉 تم الانتهاء بنجاح!")
        print("="*50)
    else:
        print("\n❌ فشلت العملية")
        sys.exit(1)


if __name__ == "__main__":
    main()
