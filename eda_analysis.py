import csv
import math
import os
from collections import defaultdict

BASE_DIR = r"C:\Users\Sudeep M\Documents\Project Antigravity"
file1_path = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "sources", "rainfall_in_india_1901_2015_cleaned.csv")
file2_path = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "sources", "district_wise_rainfall_normal_cleaned.csv")

MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
SEASONS = ['Jan-Feb', 'Mar-May', 'Jun-Sep', 'Oct-Dec']

def mean(vals):
    return sum(vals) / len(vals) if vals else 0.0

def median(vals):
    if not vals: return 0.0
    s = sorted(vals)
    n = len(s)
    return s[n//2] if n % 2 != 0 else (s[n//2 - 1] + s[n//2]) / 2.0

def std(vals):
    if len(vals) < 2: return 0.0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))

def quantile(vals, q):
    if not vals: return 0.0
    s = sorted(vals)
    idx = int(q * len(s))
    return s[min(idx, len(s) - 1)]

def pearson_corr(x, y):
    if len(x) != len(y) or len(x) < 2: return 0.0
    mx, my = mean(x), mean(y)
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den = math.sqrt(sum((xi - mx)**2 for xi in x) * sum((yi - my)**2 for yi in y))
    return num / den if den != 0 else 0.0

print("=" * 80)
print("COMPREHENSIVE EXPLORATORY DATA ANALYSIS (EDA)")
print("=" * 80)

# Load Dataset 1
with open(file1_path, 'r', encoding='utf-8') as f:
    d1 = list(csv.DictReader(f))

# Load Dataset 2
with open(file2_path, 'r', encoding='utf-8') as f:
    d2 = list(csv.DictReader(f))

# -------------------------------------------------------------
# 1. TEMPORAL TRENDS (1901 - 2015)
# -------------------------------------------------------------
year_vals = defaultdict(list)
year_subdiv_map = defaultdict(dict)
subdiv_list = sorted(list(set(r['SUBDIVISION'] for r in d1)))

for r in d1:
    yr = int(r['YEAR'])
    ann = float(r['ANNUAL'])
    year_vals[yr].append(ann)
    year_subdiv_map[yr][r['SUBDIVISION']] = ann

all_years = sorted(year_vals.keys())
national_annual_by_year = {yr: mean(year_vals[yr]) for yr in all_years}

# Decadal Averages
decades = defaultdict(list)
for yr, val in national_annual_by_year.items():
    dec_start = (yr // 10) * 10
    decades[f"{dec_start}s"].append(val)

print("\n--- 1. DECADAL NATIONAL RAINFALL TRENDS ---")
for dec, vals in sorted(decades.items()):
    print(f"  {dec}: Mean = {mean(vals):.1f} mm, Std = {std(vals):.1f} mm, CV = {(std(vals)/mean(vals))*100:.1f}%")

# Linear trend over 1901 - 2015
years_num = list(all_years)
annual_series = [national_annual_by_year[y] for y in years_num]
slope = (pearson_corr(years_num, annual_series) * std(annual_series)) / std(years_num)
print(f"\nLinear Trend Slope: {slope:+.3f} mm/year ({slope*100:+.2f} mm/century)")

# Top Wettest & Driest Years Nationally
sorted_years = sorted(national_annual_by_year.items(), key=lambda x: x[1])
print("\nTop 5 Driest Years (National Droughts):")
for yr, val in sorted_years[:5]:
    dev = ((val - mean(annual_series)) / mean(annual_series)) * 100
    print(f"  Year {yr}: {val:.1f} mm (Anomaly: {dev:+.1f}%)")

print("\nTop 5 Wettest Years (National Deluges):")
for yr, val in sorted_years[-5:][::-1]:
    dev = ((val - mean(annual_series)) / mean(annual_series)) * 100
    print(f"  Year {yr}: {val:.1f} mm (Anomaly: {dev:+.1f}%)")

# -------------------------------------------------------------
# 2. SEASONALITY ANALYSIS
# -------------------------------------------------------------
season_totals = {s: [] for s in SEASONS}
month_totals = {m: [] for m in MONTHS}

for r in d1:
    for s in SEASONS:
        season_totals[s].append(float(r[s]))
    for m in MONTHS:
        month_totals[m].append(float(r[m]))

nat_annual_mean = mean([float(r['ANNUAL']) for r in d1])

print("\n--- 2. SEASONAL BREAKDOWN (Nationwide Subdiv Averages) ---")
for s in SEASONS:
    s_mean = mean(season_totals[s])
    s_std = std(season_totals[s])
    pct = (s_mean / nat_annual_mean) * 100
    cv = (s_std / s_mean) * 100 if s_mean > 0 else 0
    print(f"  {s:8s}: Mean = {s_mean:7.1f} mm ({pct:5.1f}% of annual) | Std = {s_std:6.1f} mm | CV = {cv:5.1f}%")

print("\n--- MONTHLY DISTRIBUTION & VARIABILITY ---")
for m in MONTHS:
    m_mean = mean(month_totals[m])
    m_med = median(month_totals[m])
    m_std = std(month_totals[m])
    cv = (m_std / m_mean) * 100 if m_mean > 0 else 0
    print(f"  {m:3s}: Mean = {m_mean:6.1f} mm | Median = {m_med:6.1f} mm | Std = {m_std:6.1f} mm | CV = {cv:5.1f}%")

# -------------------------------------------------------------
# 3. REGIONAL PATTERNS (Subdivisions & Districts)
# -------------------------------------------------------------
subdiv_stats = {}
for sub in subdiv_list:
    sub_rows = [r for r in d1 if r['SUBDIVISION'] == sub]
    ann_vals = [float(r['ANNUAL']) for r in sub_rows]
    js_vals = [float(r['Jun-Sep']) for r in sub_rows]
    ond_vals = [float(r['Oct-Dec']) for r in sub_rows]
    subdiv_stats[sub] = {
        'mean_annual': mean(ann_vals),
        'std_annual': std(ann_vals),
        'cv_annual': (std(ann_vals) / mean(ann_vals)) * 100,
        'monsoon_share': (mean(js_vals) / mean(ann_vals)) * 100,
        'retreating_share': (mean(ond_vals) / mean(ann_vals)) * 100
    }

print("\n--- 3. REGIONAL CLUSTERS ---")
# High Rainfall
high_rain = sorted([(s, st) for s, st in subdiv_stats.items() if st['mean_annual'] >= 2500], key=lambda x: x[1]['mean_annual'], reverse=True)
print(f"\nA. Heavy Rainfall Zone (>= 2500 mm/year, {len(high_rain)} subdivisions):")
for s, st in high_rain:
    print(f"  {s:<30s}: {st['mean_annual']:6.1f} mm (CV: {st['cv_annual']:4.1f}%, Monsoon Share: {st['monsoon_share']:4.1f}%)")

# Semi-Arid & Arid
low_rain = sorted([(s, st) for s, st in subdiv_stats.items() if st['mean_annual'] <= 700], key=lambda x: x[1]['mean_annual'])
print(f"\nB. Arid & Semi-Arid Zone (<= 700 mm/year, {len(low_rain)} subdivisions):")
for s, st in low_rain:
    print(f"  {s:<30s}: {st['mean_annual']:6.1f} mm (CV: {st['cv_annual']:4.1f}%, Monsoon Share: {st['monsoon_share']:4.1f}%)")

# High Retreating Monsoon Dependency
retreating = sorted([(s, st) for s, st in subdiv_stats.items() if st['retreating_share'] >= 25.0], key=lambda x: x[1]['retreating_share'], reverse=True)
print(f"\nC. Post-Monsoon / Retreating Monsoon Dependent Zones (Oct-Dec >= 25%):")
for s, st in retreating:
    print(f"  {s:<30s}: Oct-Dec Share: {st['retreating_share']:4.1f}% | Mean Annual: {st['mean_annual']:6.1f} mm")

# -------------------------------------------------------------
# 4. CORRELATION ANALYSIS
# -------------------------------------------------------------
print("\n--- 4. CORRELATION MATRIX (Months vs Annual) ---")
for m in MONTHS:
    r_val = pearson_corr(month_totals[m], [float(r['ANNUAL']) for r in d1])
    print(f"  Corr({m:<3s}, ANNUAL): {r_val:+.3f}")

print("\nSeason vs Annual Correlation:")
for s in SEASONS:
    r_val = pearson_corr(season_totals[s], [float(r['ANNUAL']) for r in d1])
    print(f"  Corr({s:<8s}, ANNUAL): {r_val:+.3f}")

print("\nInter-Month Correlation in Monsoon (JUN, JUL, AUG, SEP):")
mon_corr = {}
for m1 in ['JUN', 'JUL', 'AUG', 'SEP']:
    row_str = f"  {m1:<4s}: "
    for m2 in ['JUN', 'JUL', 'AUG', 'SEP']:
        c = pearson_corr(month_totals[m1], month_totals[m2])
        row_str += f"{m2}={c:+.2f}  "
    print(row_str)

# -------------------------------------------------------------
# 5. OUTLIERS & EXTREMES
# -------------------------------------------------------------
print("\n--- 5. OUTLIERS & ANOMALIES ---")
# National Annual Outlier Detection via IQR
ann_all = [float(r['ANNUAL']) for r in d1]
q1, q3 = quantile(ann_all, 0.25), quantile(ann_all, 0.75)
iqr = q3 - q1
upper_fence = q3 + 1.5 * iqr
lower_fence = max(0, q1 - 1.5 * iqr)

outliers_upper = [r for r in d1 if float(r['ANNUAL']) > upper_fence]
outliers_lower = [r for r in d1 if float(r['ANNUAL']) < lower_fence]

print(f"Annual IQR Fences: Q1={q1:.1f}, Q3={q3:.1f}, IQR={iqr:.1f} | Upper Fence = {upper_fence:.1f} mm")
print(f"High-Rainfall Outlier Rows (> {upper_fence:.1f} mm): {len(outliers_upper)} rows ({len(outliers_upper)/len(d1)*100:.1f}%)")

print("\nTop 5 Extreme Annual Subdivision Deluges in History:")
for r in sorted(outliers_upper, key=lambda x: float(x['ANNUAL']), reverse=True)[:5]:
    print(f"  {r['SUBDIVISION']} ({r['YEAR']}): {float(r['ANNUAL']):.1f} mm (Monsoon: {float(r['Jun-Sep']):.1f} mm)")

# Single Month Deluge Records
print("\nTop 5 Single-Month Record Deluges in India (Any Month):")
month_records = []
for r in d1:
    for m in MONTHS:
        month_records.append((r['SUBDIVISION'], r['YEAR'], m, float(r[m])))

for sub, yr, m, val in sorted(month_records, key=lambda x: x[3], reverse=True)[:5]:
    print(f"  {sub} ({m} {yr}): {val:.1f} mm in a single month!")

# District-level normals extremes (Dataset 2)
print("\nDistrict Normal Outliers (Dataset 2):")
dist_ann = [float(r['ANNUAL']) for r in d2]
dq1, dq3 = quantile(dist_ann, 0.25), quantile(dist_ann, 0.75)
diqr = dq3 - dq1
dupper = dq3 + 1.5 * diqr
dlower = max(0, dq1 - 1.5 * diqr)
dist_outliers_upper = [r for r in d2 if float(r['ANNUAL']) > dupper]
dist_outliers_lower = [r for r in d2 if float(r['ANNUAL']) < dlower]
print(f"District Normals: Upper Fence = {dupper:.1f} mm ({len(dist_outliers_upper)} districts exceed)")
for r in sorted(dist_outliers_upper, key=lambda x: float(x['ANNUAL']), reverse=True)[:5]:
    print(f"  {r['DISTRICT']} ({r['STATE_UT_NAME']}): {float(r['ANNUAL']):.1f} mm/year")

for r in sorted(d2, key=lambda x: float(x['ANNUAL']))[:5]:
    print(f"  Driest: {r['DISTRICT']} ({r['STATE_UT_NAME']}): {float(r['ANNUAL']):.1f} mm/year")

