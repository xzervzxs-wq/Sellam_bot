import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime

# تحميل الأنماط
patterns_df = pd.read_csv('successful_candles.csv')
patterns_df.columns = patterns_df.columns.str.strip().str.lower()

# جلب ATAI
ticker = yf.Ticker("ATAI")
df = ticker.history(period="5d", interval="5m")
df.columns = df.columns.str.lower()

if df.index.tz is None:
    df.index = df.index.tz_localize('America/New_York')
else:
    df.index = df.index.tz_convert('America/New_York')

ny_tz = pytz.timezone('America/New_York')
today = datetime.now(ny_tz).date()
df_today = df[df.index.date == today]
last_6 = df_today.tail(6)[['open', 'high', 'low', 'close']].values

# استخراج اتجاهات ATAI
atai_dirs = []
for c in last_6:
    atai_dirs.append(1 if c[3] >= c[0] else -1)

print("شموع ATAI:", atai_dirs)
print("=" * 60)

# مقارنة مع كل نمط
for symbol, group in patterns_df.groupby('symbol'):
    group = group.sort_values('time').head(6)
    candles = group[['open', 'high', 'low', 'close']].values
    
    if len(candles) < 6:
        continue
    
    # اتجاهات النمط
    ref_dirs = []
    for c in candles:
        ref_dirs.append(1 if c[3] >= c[0] else -1)
    
    # حساب التطابق
    matches = sum(1 for i in range(6) if atai_dirs[i] == ref_dirs[i])
    ratio = matches / 6
    
    if ratio >= 0.67:  # الشرط الجديد
        print(f"✅ {symbol}: {matches}/6 ({ratio*100:.0f}%) - مقبول")
    #else:
    #    print(f"❌ {symbol}: {matches}/6 ({ratio*100:.0f}%) - مرفوض")
