import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# 🔑 إعدادات البيئة
# ==============================================================================
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")

# ==============================================================================
# 📊 دالة جلب الأسهم الرابحة باستخدام بيانات مجانية
# ==============================================================================

def fetch_gainers_and_active():
    """
    جلب الأسهم من NASDAQ باستخدام Stock Screener API
    السعر أقل من 10 دولار فقط
    """
    try:
        # استخدام Stock Screener API مع limit كبير للحصول على أكثر البيانات
        screener_url = f"https://financialmodelingprep.com/stable/company-screener?limit=5000&apikey={FMP_API_KEY}"
        
        print("🔄 جاري جلب أسهم NASDAQ من Stock Screener API...")
        print("   (جاري جلب 5000 سهم ثم فلترة الأسهم أقل من 10$)\n")
        screener_response = requests.get(screener_url, timeout=20)
        screener_response.raise_for_status()
        screener_data = screener_response.json()
        
        if not screener_data:
            print("⚠️ لا توجد بيانات")
            return pd.DataFrame()
        
        # تحويل البيانات إلى DataFrame
        df = pd.DataFrame(screener_data)
        
        print(f"✓ تم جلب {len(df)} سهم من جميع الأسواق")
        print(f"📋 الأعمدة المتاحة: {list(df.columns)}")
        
        # طباعة معلومات عن الأسعار
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            print(f"\n📈 نطاق الأسعار في البيانات:")
            print(f"   أدنى سعر: ${df['price'].min():.2f}")
            print(f"   أعلى سعر: ${df['price'].max():.2f}")
            print(f"   متوسط السعر: ${df['price'].mean():.2f}")
        
        # تطبيق الفلاتر
        filtered = apply_filters(df)
        return filtered
    
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال بـ FMP API: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return pd.DataFrame()


def apply_filters(df):
    """
    تطبيق الفلاتر على البيانات
    - السعر أقل من 10 دولار فقط
    - استبعاد الـ ETFs والـ Funds
    - اختيار أفضل 50 سهم بناءً على Volume
    """
    
    if df.empty:
        return df
    
    print(f"\n🔍 تطبيق الفلاتر:")
    
    # استبعاد ETFs والـ Funds أولاً
    initial_count = len(df)
    if 'isEtf' in df.columns or 'isFund' in df.columns:
        print(f"  ✓ استبعاد ETFs والـ Funds...")
        df = df[
            (df.get('isEtf', False) == False) & 
            (df.get('isFund', False) == False)
        ]
        print(f"    تم استبعاد {initial_count - len(df)} ETFs/Funds - المتبقي: {len(df)}")
    
    # تحويل السعر إلى أرقام وتطبيق الفلتر
    if 'price' not in df.columns:
        print(f"❌ لا يوجد عمود السعر")
        return pd.DataFrame()
    
    df = df.copy()
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    
    print(f"  ✓ فلتر السعر: أقل من 10 دولار فقط")
    
    # تطبيق فلتر السعر - أقل من 10 فقط
    filtered_df = df[df['price'] < 10].copy()
    
    print(f"\n✅ عدد الأسهم بسعر أقل من 10$: {len(filtered_df)}")
    
    if len(filtered_df) == 0:
        print(f"❌ لم نجد أي أسهم بسعر أقل من 10$!")
        print(f"\n📊 أرخص 10 أسهم في البيانات:")
        cheapest = df.nsmallest(10, 'price')[['symbol', 'companyName', 'price']]
        print(cheapest.to_string(index=False))
        return pd.DataFrame()
    
    # ترتيب حسب Volume (النشاط)
    if 'volume' in filtered_df.columns:
        filtered_df['volume'] = pd.to_numeric(filtered_df['volume'], errors='coerce')
        filtered_df = filtered_df.sort_values('volume', ascending=False, na_position='last')
    
    # اختيار أفضل 50 سهم
    top_50 = filtered_df.head(50)
    print(f"📊 عدد الأسهم النهائي: {len(top_50)} سهم (الأنشط)")
    
    # طباعة معلومات عن النتائج
    if len(top_50) > 0:
        print(f"\n💰 نطاق أسعار النتائج:")
        print(f"   أدنى سعر: ${top_50['price'].min():.2f}")
        print(f"   أعلى سعر: ${top_50['price'].max():.2f}")
    
    return top_50


def display_results(df):
    """
    عرض النتائج بشكل منسق
    """
    if df.empty:
        print("❌ لا توجد نتائج!")
        return
    
    print("\n" + "="*120)
    print(f"📊 أسهم NASDAQ الرابحة والنشطة (0.02-10$) - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*120)
    
    # اختيار الأعمدة المهمة
    display_cols = []
    for col in ['symbol', 'companyName', 'price', 'beta', 'volume', 'marketCap', 'sector']:
        if col in df.columns:
            display_cols.append(col)
    
    # عرض البيانات
    if display_cols:
        result_df = df[display_cols].copy()
    else:
        result_df = df.copy()
    
    print("\n" + result_df.to_string(index=False))
    print("\n" + "="*120)


# ==============================================================================
# 🚀 البرنامج الرئيسي
# ==============================================================================

if __name__ == "__main__":
    print("🚀 بدء جلب أسهم NASDAQ من Stock Screener API...\n")
    
    # جلب البيانات
    gainers = fetch_gainers_and_active()
    
    # عرض النتائج
    if isinstance(gainers, pd.DataFrame) and not gainers.empty:
        display_results(gainers)
        
        # حفظ النتائج في ملف CSV
        output_file = f"nasdaq_gainers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        gainers.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 تم حفظ النتائج في: {output_file}")
    else:
        print("❌ فشل في جلب البيانات")
