import csv
import json
import math
import os
from collections import defaultdict, Counter

BASE_DIR = r"C:\Users\Sudeep M\Documents\Project Antigravity"
feat_file = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "sources", "rainfall_in_india_features.csv")
dist_file = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "sources", "district_wise_rainfall_normal_cleaned.csv")

with open(feat_file, 'r', encoding='utf-8') as f:
    f_rows = list(csv.DictReader(f))

with open(dist_file, 'r', encoding='utf-8') as f:
    d_rows = list(csv.DictReader(f))

# 1. IMD Drought Distribution
drought_counts = Counter(r['IMD_DROUGHT_CATEGORY'] for r in f_rows)
total_rows = len(f_rows)
drought_pcts = {k: (v / total_rows) * 100 for k, v in drought_counts.items()}

# Drought frequency by subdivision
sub_drought = defaultdict(lambda: {'total': 0, 'drought': 0, 'excess': 0})
for r in f_rows:
    sub = r['SUBDIVISION']
    sub_drought[sub]['total'] += 1
    if int(r['IS_DROUGHT_YEAR']) == 1:
        sub_drought[sub]['drought'] += 1
    if r['IMD_DROUGHT_CATEGORY'] == 'Excess (Deluge)':
        sub_drought[sub]['excess'] += 1

sub_drought_pct = {}
for sub, d in sub_drought.items():
    sub_drought_pct[sub] = {
        'drought_risk_pct': (d['drought'] / d['total']) * 100,
        'excess_risk_pct': (d['excess'] / d['total']) * 100,
        'total_years': d['total']
    }

top_drought_sub = sorted(sub_drought_pct.items(), key=lambda x: x[1]['drought_risk_pct'], reverse=True)[:5]
top_excess_sub = sorted(sub_drought_pct.items(), key=lambda x: x[1]['excess_risk_pct'], reverse=True)[:5]

# 2. Persistence / Transition Probability
# If year t-1 was a drought year, what is probability year t is also drought?
drought_after_drought = 0
total_after_drought = 0
drought_after_normal = 0
total_after_normal = 0

sub_years = defaultdict(list)
for r in f_rows:
    sub_years[r['SUBDIVISION']].append(r)

for sub, srows in sub_years.items():
    for i in range(1, len(srows)):
        prev_drought = int(srows[i-1]['IS_DROUGHT_YEAR'])
        curr_drought = int(srows[i]['IS_DROUGHT_YEAR'])
        if prev_drought == 1:
            total_after_drought += 1
            if curr_drought == 1:
                drought_after_drought += 1
        else:
            total_after_normal += 1
            if curr_drought == 1:
                drought_after_normal += 1

prob_drought_given_prev_drought = (drought_after_drought / total_after_drought) * 100 if total_after_drought else 0
prob_drought_given_prev_normal = (drought_after_normal / total_after_normal) * 100 if total_after_normal else 0

# 3. Early June Deficit vs Final Monsoon Deficit
# If June PDN < -20%, how often does the full Monsoon end in Deficient or Scanty?
june_deficit_count = 0
monsoon_deficit_given_june_deficit = 0
for r in f_rows:
    june_pdn = float(r['JUNE_ONSET_PDN'])
    mon_pdn = float(r['MONSOON_PDN'])
    if june_pdn <= -20.0:
        june_deficit_count += 1
        if mon_pdn <= -20.0:
            monsoon_deficit_given_june_deficit += 1

june_lead_prob = (monsoon_deficit_given_june_deficit / june_deficit_count) * 100 if june_deficit_count else 0

# 4. District Micro Analysis
# Intra-state inequality (Max district / Min district ratio per state)
state_dists = defaultdict(list)
for r in d_rows:
    state_dists[r['STATE_UT_NAME']].append((r['DISTRICT'], float(r['ANNUAL'])))

state_inequality = []
for state, dlist in state_dists.items():
    if len(dlist) >= 2:
        sorted_d = sorted(dlist, key=lambda x: x[1])
        driest_d, driest_val = sorted_d[0]
        wettest_d, wettest_val = sorted_d[-1]
        ratio = wettest_val / driest_val if driest_val > 0 else 0
        diff = wettest_val - driest_val
        state_inequality.append({
            'state': state,
            'num_districts': len(dlist),
            'driest_dist': driest_d,
            'driest_val': driest_val,
            'wettest_dist': wettest_d,
            'wettest_val': wettest_val,
            'ratio': ratio,
            'diff': diff
        })

top_inequality_states = sorted(state_inequality, key=lambda x: x['ratio'], reverse=True)[:5]

# High vs Low Monsoon Dependence at District Level
dist_monsoon_share = []
for r in d_rows:
    ann = float(r['ANNUAL'])
    js = float(r['Jun-Sep'])
    ond = float(r['Oct-Dec'])
    dist_monsoon_share.append({
        'district': r['DISTRICT'],
        'state': r['STATE_UT_NAME'],
        'annual': ann,
        'monsoon_pct': (js / ann) * 100 if ann > 0 else 0,
        'retreating_pct': (ond / ann) * 100 if ann > 0 else 0
    })

top_monsoon_dep = sorted(dist_monsoon_share, key=lambda x: x['monsoon_pct'], reverse=True)[:5]
top_retreating_dep = sorted(dist_monsoon_share, key=lambda x: x['retreating_pct'], reverse=True)[:5]

results = {
    'drought_distribution': dict(drought_counts),
    'drought_percentages': drought_pcts,
    'top_drought_subdivisions': top_drought_sub,
    'top_excess_subdivisions': top_excess_sub,
    'prob_drought_given_prev_drought': prob_drought_given_prev_drought,
    'prob_drought_given_prev_normal': prob_drought_given_prev_normal,
    'june_lead_prob': june_lead_prob,
    'june_deficit_count': june_deficit_count,
    'top_inequality_states': top_inequality_states,
    'top_monsoon_dependent_districts': top_monsoon_dep,
    'top_retreating_dependent_districts': top_retreating_dep
}

with open(os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "insights_summary.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("INSIGHTS COMPUTATION COMPLETE:")
print(f"1. National Drought Frequencies: {drought_pcts}")
print(f"2. Consecutive Drought Persistence: P(D_t | D_t-1) = {prob_drought_given_prev_drought:.1f}% vs P(D_t | Normal_t-1) = {prob_drought_given_prev_normal:.1f}%")
print(f"3. June Onset Deficit Predictive Power: {june_lead_prob:.1f}% of June deficits culminate in full monsoon deficits")
print(f"4. Top 3 Intra-State Divergence States: {[s['state'] + ' (' + str(round(s['ratio'], 1)) + 'x)' for s in top_inequality_states[:3]]}")
