import pandas as pd
import reeshah
import os

# ملف البيانات المحفوظ
CSV_FILE = "morning_scan_20251224_214410.csv"

def test_offline():
    print(f"📂 جاري تحميل البيانات من {CSV_FILE}...")
    
    if not os.path.exists(CSV_FILE):
        print("❌ الملف غير موجود!")
        return

    # تحميل البيانات
    df_all = pd.read_csv(CSV_FILE)
    
    # تحويل التاريخ
    if 'date' in df_all.columns:
        df_all['date'] = pd.to_datetime(df_all['date'])
        df_all.set_index('date', inplace=True)
    elif 'index' in df_all.columns:
        df_all['date'] = pd.to_datetime(df_all['index'])
        df_all.set_index('date', inplace=True)
        
    # تحميل الأنماط
    print("🧠 تحميل الأنماط...")
    patterns, pattern_metrics = reeshah.load_successful_patterns()
    
    print("\n🔍 بدء الفحص (Offline Mode)...")
    
    # تجميع حسب السهم
    grouped = df_all.groupby('symbol')
    
    results = []
    
    for symbol, group in grouped:
        # ترتيب زمني
        df = group.sort_index()
        
        # 1. الفلتر الفني (بعد التعديل)
        is_gold = reeshah.is_golden_grinder(df.copy(), symbol_debug=symbol)
        
        # 2. الجمال
        beauty = reeshah.calculate_beauty_score(df.copy())
        
        # 3. الأنماط
        match_score = 0
        match_name = "None"
        
        # محاولة مطابقة الأنماط (آخر 6 شموع)
        if len(df) >= 6:
            pattern_data = df[['open', 'high', 'low', 'close']].tail(6).values
            match_score, match_name = reeshah.calculate_similarity(pattern_data, patterns, pattern_metrics)
            
        # طباعة النتائج المهمة
        if symbol in ['GNL', 'ENVX', 'NB', 'APPS'] or is_gold or match_score > 70:
            status = "✅" if is_gold else "❌"
            print(f"{status} {symbol:<6} | الجمال: {beauty}% | نمط: {match_name} ({match_score:.0f}%)")
            
            if symbol == 'GNL':
                print(f"   -> تفاصيل GNL: Gold={is_gold}, Beauty={beauty}, Match={match_score}")

if __name__ == "__main__":
    test_offline()
