#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خوارزمية Strict Rhythm على بيانات اختبار فعلية
"""
import pandas as pd
import sys
sys.path.insert(0, '/workspaces/Sellam_bot')

from reeshah import (
    load_successful_patterns,
    extract_candle_dna,
    calculate_structural_similarity
)

def test_matching_on_file(test_file, output_file=None):
    """اختبار المطابقة على ملف بيانات"""
    
    print("\n" + "="*70)
    print("🧬 اختبار خوارزمية Strict Rhythm")
    print("="*70)
    
    # تحميل البيانات
    print("\n📂 تحميل البيانات...")
    try:
        df_test = pd.read_csv(test_file)
        print(f"✅ تم تحميل {len(df_test)} صف من {test_file}")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None
    
    # تحميل الأنماط الناجحة
    print("\n🎯 تحميل الأنماط الناجحة...")
    patterns = load_successful_patterns()
    print(f"✅ تم تحميل {len(patterns)} نمط ناجح")
    
    # جمع الأسهم الفريدة
    stocks = df_test['symbol'].unique()
    print(f"✅ عدد الأسهم الفريدة: {len(stocks)}")
    
    # نتائج المطابقة
    results = []
    
    print("\n" + "="*70)
    print("🔍 جاري اختبار المطابقة...")
    print("="*70)
    
    total_matches = 0
    all_scores = []
    
    for idx, stock in enumerate(stocks, 1):
        # الحصول على شموع هذا السهم
        stock_data = df_test[df_test['symbol'] == stock].sort_values('time')
        
        if len(stock_data) < 6:
            continue
        
        # الحصول على شموع العينة (أول 6)
        sample_candles = stock_data.head(6).to_dict('records')
        
        # حساب المطابقة
        similarity_scores = calculate_structural_similarity(sample_candles, patterns)
        
        if similarity_scores:
            avg_score = sum(similarity_scores.values()) / len(similarity_scores)
            max_score = max(similarity_scores.values())
            min_score = min(similarity_scores.values())
            
            all_scores.append(avg_score)
            
            # إيجاد أفضل نمط
            best_pattern = max(similarity_scores, key=similarity_scores.get)
            best_match = similarity_scores[best_pattern]
            
            results.append({
                'symbol': stock,
                'avg_match': avg_score,
                'best_match': best_match,
                'best_pattern': best_pattern,
                'num_patterns': len(similarity_scores)
            })
            
            # طباعة النتائج كل 50 سهم
            if idx % 50 == 0 or idx == len(stocks):
                status = f"{stock:<10} Avg: {avg_score:6.1f}% | Best: {best_match:6.1f}% ({best_pattern})"
                print(f"{status:<70} ({idx}/{len(stocks)})")
                total_matches += 1
    
    # الإحصائيات العامة
    print("\n" + "="*70)
    print("📊 الإحصائيات العامة:")
    print("="*70)
    
    if all_scores:
        avg_all = sum(all_scores) / len(all_scores)
        max_all = max(all_scores)
        min_all = min(all_scores)
        
        print(f"  📈 متوسط المطابقة: {avg_all:.2f}%")
        print(f"  🔝 أعلى مطابقة: {max_all:.2f}%")
        print(f"  🔻 أقل مطابقة: {min_all:.2f}%")
        print(f"  📊 عدد الأسهم المختبرة: {len(results)}")
        
        # توزيع النسب
        excellent = len([s for s in all_scores if s >= 90])
        good = len([s for s in all_scores if 70 <= s < 90])
        okay = len([s for s in all_scores if 50 <= s < 70])
        poor = len([s for s in all_scores if s < 50])
        
        print(f"\n  📊 توزيع النسب:")
        print(f"    ⭐⭐⭐⭐⭐ ممتاز (90%+):   {excellent} ({100*excellent/len(all_scores):.1f}%)")
        print(f"    ⭐⭐⭐⭐   جيد (70-90%): {good} ({100*good/len(all_scores):.1f}%)")
        print(f"    ⭐⭐⭐     حسن (50-70%): {okay} ({100*okay/len(all_scores):.1f}%)")
        print(f"    ⭐       ضعيف (<50%):  {poor} ({100*poor/len(all_scores):.1f}%)")
    
    # الأسهم الأفضل
    if results:
        print("\n" + "="*70)
        print("🏆 أفضل 15 أسهم مطابقة:")
        print("="*70)
        
        df_results = pd.DataFrame(results)
        top_15 = df_results.nlargest(15, 'avg_match')
        
        print(f"\n{'#':<3} {'Symbol':<10} {'Avg Match':<12} {'Best Match':<12} {'Best Pattern':<15}")
        print("-" * 70)
        
        for idx, row in enumerate(top_15.values, 1):
            print(f"{idx:<3} {row[0]:<10} {row[1]:>10.1f}% {row[2]:>10.1f}% {row[3]:<15}")
    
    # حفظ النتائج
    if output_file and results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('avg_match', ascending=False)
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ تم حفظ النتائج في: {output_file}")
    
    return results

if __name__ == '__main__':
    test_file = '/workspaces/Sellam_bot/test_candles_20251223_170248.csv'
    output_file = '/workspaces/Sellam_bot/matching_results_20251223.csv'
    
    test_matching_on_file(test_file, output_file)
