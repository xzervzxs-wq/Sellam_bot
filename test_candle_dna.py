#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اختبار النظام الجديد: Candle-by-Candle DNA Matching
======================================================

هذا الملف يوضح كيفية استخدام النظام الجديد لمطابقة الشموع بالتسلسل.
"""

import sys
sys.path.insert(0, '.')

import reeshah
import pandas as pd
import numpy as np

def test_candle_dna_extraction():
    """اختبار استخراج بصمة DNA من الشموع"""
    print("\n" + "="*70)
    print("اختبار 1: استخراج بصمة DNA")
    print("="*70)
    
    # أنشئ شموع اختبار
    test_candles = np.array([
        [100.0, 102.0, 99.0, 101.0],    # شمعة أخضر عادية
        [101.0, 103.5, 100.0, 102.5],   # شمعة أخضر أقوى
        [102.5, 103.0, 101.0, 102.0],   # شمعة أحمر صغيرة
        [102.0, 104.5, 101.5, 104.0],   # شمعة أخضر قوية مع ذيل
        [104.0, 105.0, 103.0, 104.5],   # شمعة أخضر معتدلة
        [104.5, 106.0, 103.5, 105.5],   # شمعة أخضر قوية
    ])
    
    dna = reeshah.extract_candle_dna(test_candles)
    
    print("\n📊 بيانات الشموع:")
    print(f"{'شمعة':<8} {'نوع':<8} {'جسم':<8} {'ذ.علوي':<10} {'ذ.سفلي':<10} {'حجم':<10}")
    print("-"*70)
    
    for i, d in enumerate(dna):
        candle_type = "أخضر ✅" if d['dir'] == 1 else "أحمر ❌"
        print(f"{i+1:<8} {candle_type:<8} {d['body_r']:<8.3f} {d['upper_r']:<10.3f} {d['lower_r']:<10.3f} {d['size']:<10.2f}%")
    
    return dna

def test_structural_similarity():
    """اختبار المطابقة الشكلية بين الأنماط"""
    print("\n" + "="*70)
    print("اختبار 2: المطابقة الشكلية بين الأنماط")
    print("="*70)
    
    # أنمط 1: صعود نظيف
    pattern_clean = np.array([
        [100.0, 101.5, 99.8, 101.0],
        [101.0, 102.5, 100.5, 102.0],
        [102.0, 103.5, 101.5, 103.0],
        [103.0, 104.5, 102.5, 104.0],
        [104.0, 105.5, 103.5, 105.0],
        [105.0, 106.5, 104.5, 106.0],
    ])
    
    # نمط 2: نفس الشكل مع تذبذب طفيف
    pattern_slightly_different = np.array([
        [100.0, 101.5, 99.5, 100.8],   # نفس تقريباً
        [100.8, 102.3, 100.3, 101.8],  # نفس تقريباً
        [101.8, 103.3, 101.3, 102.8],
        [102.8, 104.3, 102.3, 103.8],
        [103.8, 105.3, 103.3, 104.8],
        [104.8, 106.3, 104.3, 105.8],
    ])
    
    # نمط 3: نفس الصعود لكن مع ذيول طويلة (مختلف الشكل)
    pattern_different_wicks = np.array([
        [100.0, 103.0, 98.0, 101.0],   # ذيول أطول
        [101.0, 104.0, 99.0, 102.0],
        [102.0, 105.0, 100.0, 103.0],
        [103.0, 106.0, 101.0, 104.0],
        [104.0, 107.0, 102.0, 105.0],
        [105.0, 108.0, 103.0, 106.0],
    ])
    
    patterns_dict = {
        'PATTERN_CLEAN': pattern_clean,
        'PATTERN_SLIGHTLY_DIFFERENT': pattern_slightly_different,
        'PATTERN_DIFFERENT_WICKS': pattern_different_wicks,
    }
    
    print("\n🧪 اختبار 2أ: مطابقة النمط النظيف مع نفسه")
    score, name = reeshah.calculate_structural_similarity(pattern_clean, patterns_dict)
    print(f"   النتيجة: {score:.1f}% تطابق مع {name}")
    print(f"   التفسير: {'💯 تطابق مثالي' if score == 100 else '✅ تطابق جيد'}")
    
    print("\nأختبار 2ب: مطابقة النمط المشابه قليلاً")
    score, name = reeshah.calculate_structural_similarity(pattern_slightly_different, patterns_dict)
    print(f"   النتيجة: {score:.1f}% تطابق مع {name}")
    print(f"   التفسير: {'✅ تطابق ممتاز' if score > 90 else '⚠️ تطابق معقول' if score > 70 else '❌ تطابق ضعيف'}")
    
    print("\nأختبار 2ج: مطابقة النمط بذيول مختلفة")
    score, name = reeshah.calculate_structural_similarity(pattern_different_wicks, patterns_dict)
    print(f"   النتيجة: {score:.1f}% تطابق مع {name}")
    print(f"   التفسير: النمط الأمثل له ذيول أطول، لذا قد يطابق مع PATTERN_DIFFERENT_WICKS")

def test_with_real_patterns():
    """اختبار مع الأنماط الحقيقية المحملة من الملف"""
    print("\n" + "="*70)
    print("اختبار 3: المطابقة مع الأنماط الحقيقية")
    print("="*70)
    
    patterns = reeshah.load_successful_patterns()
    
    if not patterns:
        print("⚠️ لا توجد أنماط محملة")
        return
    
    print(f"\n📚 تم تحميل {len(patterns)} نمط حقيقي:")
    for i, (name, candles) in enumerate(list(patterns.items())[:3]):
        print(f"   {i+1}. {name}: {candles.shape} (6 شموع)")
    
    # استخدم أول نمط كعينة
    sample_pattern_name = list(patterns.keys())[0]
    sample_candles = patterns[sample_pattern_name]
    
    print(f"\n🧪 اختبار المطابقة مع النمط: {sample_pattern_name}")
    score, best_match = reeshah.calculate_structural_similarity(sample_candles, patterns)
    print(f"   النتيجة: {score:.1f}% تطابق مع {best_match}")
    
    # جرب سهم محاكى مع تعديلات طفيفة
    print("\n🧪 محاكاة سهم حقيقي مع تعديلات طفيفة:")
    simulated_candle = sample_candles.copy().astype(float)
    simulated_candle[:, 3] = simulated_candle[:, 3] * 1.01  # أضف 1% صعود
    
    score, best_match = reeshah.calculate_structural_similarity(simulated_candle, patterns)
    print(f"   النتيجة: {score:.1f}% تطابق مع {best_match}")
    print(f"   ملاحظة: {'✅ استمر التطابق العالي' if score > 90 else '⚠️ انخفض التطابق قليلاً'}")

def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*70)
    print("🧬 اختبار نظام مطابقة الشموع بالتسلسل (Candle DNA Matching)")
    print("="*70)
    
    try:
        # اختبر 1: استخراج DNA
        test_candle_dna_extraction()
        
        # اختبر 2: المطابقة الشكلية
        test_structural_similarity()
        
        # اختبر 3: الأنماط الحقيقية
        test_with_real_patterns()
        
        print("\n" + "="*70)
        print("✅ جميع الاختبارات اكتملت بنجاح!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ خطأ أثناء الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
