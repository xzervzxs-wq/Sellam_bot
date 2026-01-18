import pandas as pd
import warnings
from datetime import datetime, time
import requests
import os
import io
import time as time_module
import pytz
from dotenv import load_dotenv

# =========================================================
# إعدادات
# =========================================================
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "68c0ad0b52af78.88121932")

warnings.simplefilter(action='ignore', category=FutureWarning)

# =========================================================
# ⚙️ عدّل هذه القيم يدويًا كل يوم
# =========================================================
# التاريخ (السنة, الشهر, اليوم)
TARGET_DATE = datetime(2025, 12, 19)

# الأسهم الناجحة اليوم (بفاصل: فاصلة وسطة)
SYMBOLS = ['NBIS', 'NBY', 'MVIS', 'SIDU', 'RIVN', 'WIT', 'IXHL', 'EFA', 'CCL', 'CRCO', 'MRNA', 'INSM']

# =========================================================
# جلب شموع 1-دقيقة من EODHD
# =========================================================
def get_eodhd_minute_candles(symbol, target_date):
    """جلب شموع 1-دقيقة من EODHD من 9:30 إلى 10:00"""
    try:
        # تحويل التاريخ إلى timestamps
        ny_tz = pytz.timezone('America/New_York')
        date_obj = datetime.combine(target_date, time(9, 30), tzinfo=ny_tz)
        
        start_timestamp = int(date_obj.timestamp())
        end_timestamp = int(date_obj.replace(hour=10, minute=0).timestamp())
        
        # استدعاء API
        url = f"https://eodhd.com/api/intraday/{symbol}.US"
        params = {
            'api_token': EODHD_API_KEY,
            'from': start_timestamp,
            'to': end_timestamp,
            'period': '1m'  # 1 دقيقة
        }
        
        print(f"⏳ جاري جلب {symbol}...", end=" ", flush=True)
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ (خطأ: {response.status_code})")
            return []
        
        # الـ API يرجع CSV
        csv_text = response.text
        
        if not csv_text or csv_text.startswith('Timestamp') and csv_text.count('\n') <= 1:
            print("⚠️ (بدون بيانات)")
            return []
        
        # قراءة CSV
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            
            if df.empty:
                print("⚠️ (بدون بيانات)")
                return []
            
            candles = []
            ny_tz = pytz.timezone('America/New_York')
            
            for _, row in df.iterrows():
                ts = int(row['Timestamp'])
                candle_time = datetime.fromtimestamp(ts, tz=pytz.UTC).astimezone(ny_tz)
                
                candles.append({
                    'datetime': candle_time,
                    'symbol': symbol,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'time': candle_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            print(f"✅ ({len(candles)} شموع)")
            return candles
            
        except Exception as e:
            print(f"❌ خطأ في المعالجة: {str(e)}")
            return []
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")
        return []

# =========================================================
# البرنامج الرئيسي
# =========================================================
def main():
    print("="*80)
    print("🎯 جلب شموع الأسهم الناجحة")
    print("="*80)
    print(f"📅 التاريخ: {TARGET_DATE}")
    print(f"📊 الأسهم: {', '.join(SYMBOLS)}\n")
    
    all_candles = []
    
    for symbol in SYMBOLS:
        candles = get_eodhd_minute_candles(symbol, TARGET_DATE)
        all_candles.extend(candles)
        time_module.sleep(0.5)  # تأخير خفيف بين الطلبات
    
    if all_candles:
# حفظ النتائج (append أو create إذا كان الملف الأول)
        df = pd.DataFrame(all_candles)
        df = df.sort_values(['symbol', 'datetime'])
        
        # تحويل إلى شموع 5-دقائق
        print("\n🔄 جاري تحويل إلى شموع 5-دقائق...")
        df_5min = aggregate_to_5min(df)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = "successful_candles.csv"
        
        # إذا كان الملف موجود، أضف البيانات الجديدة
        if os.path.exists(output_file):
            df_existing = pd.read_csv(output_file)
            df_existing['datetime'] = pd.to_datetime(df_existing['datetime'])
            df_combined = pd.concat([df_existing, df_5min], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['symbol', 'time'], keep='last')
            df_combined = df_combined.sort_values(['symbol', 'datetime']).reset_index(drop=True)
            df_combined.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n✅ تم إضافة البيانات إلى: {output_file}")
            print(f"   - إجمالي الشموع الآن: {len(df_combined)}")
        else:
            # ملف جديد
            df_5min.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n✅ تم حفظ البيانات في ملف جديد: {output_file}")
        
        print(f"   - عدد الأسهم: {df_5min['symbol'].nunique()}")
        print(f"   - الشموع المضافة اليوم: {len(df_5min)} (شموع 5-دقائق)")
    else:
        print("❌ لم يتم جلب أي بيانات!")

# =========================================================
# دالة تحويل شموع 1-دقيقة إلى 5-دقائق
# =========================================================
def aggregate_to_5min(df):
    """تحويل شموع 1-دقيقة إلى شموع 5-دقائق"""
    if df.empty:
        return df
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    all_5min = []
    for symbol in df['symbol'].unique():
        stock_data = df[df['symbol'] == symbol].copy()
        stock_data = stock_data.sort_values('datetime')
        
        # تجميع كل 5 دقائق
        stock_5min = stock_data.set_index('datetime').resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna(subset=['close'])
        
        if not stock_5min.empty:
            stock_5min['symbol'] = symbol
            stock_5min['datetime'] = stock_5min.index
            stock_5min['time'] = stock_5min.index.strftime('%Y-%m-%d %H:%M:%S')
            stock_5min = stock_5min[['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'time']]
            all_5min.append(stock_5min.reset_index(drop=True))
    
    return pd.concat(all_5min, ignore_index=True) if all_5min else pd.DataFrame()

if __name__ == "__main__":
    main()
