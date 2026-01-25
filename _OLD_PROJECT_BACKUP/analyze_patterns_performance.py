import pandas as pd
import numpy as np

DATA_FILE = 'extended_candles_60days.csv'
TOP_PATTERNS = ['VIVK', 'METC', 'GOGO', 'MRNA', 'INSM', 'INTR']
BLACKLIST = ['CCL', 'SLV', 'PM', 'NBIS', 'TRP']

print(f"📂 Reading {DATA_FILE}...")
df_all = pd.read_csv(DATA_FILE)

# Ensure date is datetime
df_all['date'] = pd.to_datetime(df_all['date'], utc=True, errors='coerce')
df_all = df_all.dropna(subset=['date'])

try:
    df_all['date'] = df_all['date'].dt.tz_convert('America/New_York')
except Exception as e:
    print(f"⚠️ Timezone conversion warning: {e}")

df_all['day_str'] = df_all['date'].dt.strftime('%Y-%m-%d')

# We need to reconstruct the trades to get the pattern names associated with them
# The previous analysis script did this reconstruction. I will reuse that logic briefly
# or better yet, I will assume the previous `analyze_failures.py` logic was correct 
# but I need to run it to get the pattern-level stats.

# Wait, `extended_candles_40days.csv` is raw candle data, not trade results.
# I need to simulate the trades again to get the stats per pattern.

# Load patterns
PATTERNS_FILE = 'successful_candles.csv'
def load_patterns():
    df = pd.read_csv(PATTERNS_FILE)
    df.columns = df.columns.str.strip().str.lower()
    # Exclude bad ones if any hardcoded
    df = df[~df['symbol'].str.upper().isin(['NBY', 'SIDU'])] 
    patterns, metrics = {}, {}
    for sym, grp in df.groupby('symbol'):
        grp = grp.sort_values('time')
        if len(grp) >= 6:
            candles = grp.iloc[:6][['open', 'high', 'low', 'close']].values
            details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in candles]
            patterns[sym] = candles
            metrics[sym] = {'candle_details': details}
    return patterns, metrics

patterns, pattern_metrics = load_patterns()
print(f"✅ Loaded {len(patterns)} patterns.")

def calculate_similarity(current_candles, reference_patterns, pattern_metrics):
    current_details = [{'direction': 1 if c[3]>=c[0] else -1, 'body_size': abs((c[3]-c[0])/c[0]*100)} for c in current_candles]
    if (current_candles[-1][3] - current_candles[0][0]) <= 0: return 0, "None"
    best_score, best_name = 0, "None"
    for name, ref_candles in reference_patterns.items():
        if name not in pattern_metrics: continue
        ref_details = pattern_metrics[name]['candle_details']
        clen = min(len(current_details), len(ref_details))
        if clen < 3: continue
        dir_match = sum(1 for i in range(clen) if current_details[i]['direction'] == ref_details[i]['direction'])
        if dir_match/clen < 0.67: continue
        size_penalties = 0
        for i in range(clen):
            diff = abs(current_details[i]['body_size'] - ref_details[i]['body_size'])
            if diff > 1.0: size_penalties += min(diff - 1.0, 1.0) * 20
        score = (dir_match/clen * 100 * 0.6) + (max(0, 100 - size_penalties) * 0.4)
        if score > best_score: best_score, best_name = score, name
    return best_score, best_name

# Simulation
results = []
grouped = df_all.groupby(['symbol', 'day_str'])

for (symbol, day), day_data in grouped:
    day_data = day_data.sort_values('date')
    day_data['time_str'] = day_data['date'].dt.strftime('%H:%M')
    
    # Morning candles 9:30 - 9:55
    morning_mask = day_data['time_str'].isin(['09:30', '09:35', '09:40', '09:45', '09:50', '09:55'])
    morning_candles = day_data[morning_mask]
    
    candles_vals = morning_candles[['open', 'high', 'low', 'close']].values
    valid_indices = [i for i, c in enumerate(candles_vals) if c[0] > 0 and c[3] > 0]
    
    if len(valid_indices) < 4: continue
    
    candles_vals = candles_vals[valid_indices]
    
    # Crawl Filter
    avg_body = np.mean([abs(c[3]-c[0])/c[0]*100 for c in candles_vals])
    if avg_body >= 1.0: continue
    
    score, name = calculate_similarity(candles_vals, patterns, pattern_metrics)
    
    if score < 70: continue
    
    # Blacklist Check
    if name in BLACKLIST: continue

    # Calculate Outcome
    entry_price = candles_vals[-1][3]
    entry_time = morning_candles.iloc[valid_indices[-1]]['date']
    rest_of_day = day_data[day_data['date'] > entry_time]
    
    if len(rest_of_day) == 0: continue
    
    max_gain = (rest_of_day['high'].max() - entry_price) / entry_price * 100
    max_loss = (rest_of_day['low'].min() - entry_price) / entry_price * 100
    
    results.append({
        'pattern': name,
        'gain': max_gain,
        'loss': max_loss,
        'day': day
    })

if not results:
    print("❌ No trades found matching criteria!")
    exit()

df_res = pd.DataFrame(results)

# Analysis
print("\n📊 Pattern Performance Analysis")
print("="*60)

pattern_stats = df_res.groupby('pattern').agg(
    total=('gain', 'count'),
    wins=('gain', lambda x: (x > 3).sum()),
    losses=('loss', lambda x: (x < -3).sum())
)
pattern_stats['win_rate'] = pattern_stats['wins'] / pattern_stats['total'] * 100
pattern_stats['loss_rate'] = pattern_stats['losses'] / pattern_stats['total'] * 100

# Sort by Win Rate (min 5 trades)
valid_patterns = pattern_stats[pattern_stats['total'] >= 5].sort_values('win_rate', ascending=False)

pd.set_option('display.max_rows', None)
print(valid_patterns[['total', 'wins', 'losses', 'win_rate', 'loss_rate']])


print("\n⚠️ Current TOP_PATTERNS Performance:")
for p in TOP_PATTERNS:
    if p in pattern_stats.index:
        row = pattern_stats.loc[p]
        print(f"{p:<5}: Win {row['win_rate']:.1f}% | Loss {row['loss_rate']:.1f}% | Total {row['total']}")
    else:
        print(f"{p:<5}: No trades found")

print("\n💎 Potential New Gems (Win Rate > 50% & Total >= 5):")
gems = valid_patterns[valid_patterns['win_rate'] > 50]
print(gems)

# Calculate Daily Signals
total_days = df_res['day'].nunique()
total_signals = len(df_res)
avg_signals = total_signals / total_days
print(f"\n📅 Total Days: {total_days}")
print(f"📡 Avg Signals/Day (Current): {avg_signals:.1f}")

# Simulate Removal of GNL/EFA
filtered_df = df_res[~df_res['pattern'].isin(['GNL', 'EFA'])]
avg_signals_filtered = len(filtered_df) / total_days
print(f"📡 Avg Signals/Day (Without GNL/EFA): {avg_signals_filtered:.1f}")
