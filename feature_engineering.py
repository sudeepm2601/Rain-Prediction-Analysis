import csv
import math
import os
from collections import defaultdict

BASE_DIR = r"C:\Users\Sudeep M\Documents\Project Antigravity"
SOURCES_DIR = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "sources")
CLEANED_DIR = os.path.join(BASE_DIR, "projects", "rainprediction_codesis", "cleaned")

INPUT_FILE = os.path.join(SOURCES_DIR, "rainfall_in_india_1901_2015_cleaned.csv")
OUTPUT_SOURCES = os.path.join(SOURCES_DIR, "rainfall_in_india_features.csv")
OUTPUT_CLEANED = os.path.join(CLEANED_DIR, "rainfall_in_india_features.csv")

MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

def run_feature_engineering():
    print("=" * 70)
    print("STARTING FEATURE ENGINEERING PIPELINE")
    print(f"Reading from: {INPUT_FILE}")
    print("=" * 70)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        original_fields = list(reader.fieldnames)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows with {len(original_fields)} base columns.")

    # 1. Group rows by subdivision and sort by year
    subdiv_rows = defaultdict(list)
    for r in rows:
        sub = r['SUBDIVISION'].strip()
        subdiv_rows[sub].append(r)

    # Sort each subdivision's rows chronologically
    for sub in subdiv_rows:
        subdiv_rows[sub].sort(key=lambda x: int(x['YEAR']))

    # 2. Compute long-term historical baseline statistics per subdivision
    subdiv_stats = {}
    for sub, srows in subdiv_rows.items():
        ann_vals = [float(r['ANNUAL']) for r in srows]
        mon_vals = [float(r['Jun-Sep']) for r in srows]
        jun_vals = [float(r['JUN']) for r in srows]

        ann_mean = sum(ann_vals) / len(ann_vals)
        ann_std = math.sqrt(sum((x - ann_mean)**2 for x in ann_vals) / (len(ann_vals) - 1)) if len(ann_vals) > 1 else 1.0

        mon_mean = sum(mon_vals) / len(mon_vals)
        mon_std = math.sqrt(sum((x - mon_mean)**2 for x in mon_vals) / (len(mon_vals) - 1)) if len(mon_vals) > 1 else 1.0

        jun_mean = sum(jun_vals) / len(jun_vals)

        # Climatic zone assignment
        if ann_mean >= 2500.0:
            zone = "Hyper-Pluvial"
        elif ann_mean >= 1000.0:
            zone = "Sub-Humid Core"
        elif ann_mean >= 500.0:
            zone = "Semi-Arid"
        else:
            zone = "Arid"

        subdiv_stats[sub] = {
            'ANNUAL_MEAN': ann_mean,
            'ANNUAL_STD': ann_std,
            'MONSOON_MEAN': mon_mean,
            'MONSOON_STD': mon_std,
            'JUN_MEAN': jun_mean,
            'CLIMATIC_ZONE': zone
        }

    # 3. Generate Features for each row
    new_rows = []
    for sub, srows in subdiv_rows.items():
        stats = subdiv_stats[sub]
        ann_mean = stats['ANNUAL_MEAN']
        ann_std = stats['ANNUAL_STD']
        mon_mean = stats['MONSOON_MEAN']
        mon_std = stats['MONSOON_STD']
        jun_mean = stats['JUN_MEAN']
        zone = stats['CLIMATIC_ZONE']

        for i, r in enumerate(srows):
            yr = int(r['YEAR'])
            ann = float(r['ANNUAL'])
            mon = float(r['Jun-Sep'])
            jun = float(r['JUN'])
            jul = float(r['JUL'])
            aug = float(r['AUG'])
            sep = float(r['SEP'])
            jf = float(r['Jan-Feb'])
            mam = float(r['Mar-May'])
            ond = float(r['Oct-Dec'])

            # Departures & Z-Scores
            ann_pdn = ((ann - ann_mean) / ann_mean) * 100.0
            mon_pdn = ((mon - mon_mean) / mon_mean) * 100.0
            ann_zscore = (ann - ann_mean) / ann_std
            mon_zscore = (mon - mon_mean) / mon_std

            # Backward-looking Lags (fallback to historical mean if unavailable)
            lag1_ann = float(srows[i-1]['ANNUAL']) if i >= 1 else ann_mean
            lag2_ann = float(srows[i-2]['ANNUAL']) if i >= 2 else ann_mean
            lag3_ann = float(srows[i-3]['ANNUAL']) if i >= 3 else ann_mean
            lag1_mon = float(srows[i-1]['Jun-Sep']) if i >= 1 else mon_mean

            # Inter-annual Momentum / Delta
            annual_momentum = lag1_ann - lag2_ann

            # Backward-looking Rolling Averages
            # Past 3 years
            past3 = [float(srows[j]['ANNUAL']) for j in range(max(0, i-3), i)]
            roll3_mean = sum(past3) / len(past3) if past3 else ann_mean

            # Past 5 years
            past5 = [float(srows[j]['ANNUAL']) for j in range(max(0, i-5), i)]
            roll5_mean = sum(past5) / len(past5) if past5 else ann_mean
            roll5_std = math.sqrt(sum((x - roll5_mean)**2 for x in past5) / len(past5)) if len(past5) > 1 else ann_std

            # Past 10 years drift
            past10 = [float(srows[j]['ANNUAL']) for j in range(max(0, i-10), i)]
            roll10_mean = sum(past10) / len(past10) if past10 else ann_mean
            decadal_drift = roll10_mean - ann_mean

            # Intra-annual & Seasonal Ratios
            winter_pct = (jf / ann) * 100.0 if ann > 0 else 0.0
            pre_monsoon_pct = (mam / ann) * 100.0 if ann > 0 else 0.0
            monsoon_concentration_idx = (mon / ann) * 100.0 if ann > 0 else 0.0
            retreating_monsoon_idx = (ond / ann) * 100.0 if ann > 0 else 0.0

            early_monsoon = jun + jul
            late_monsoon = aug + sep
            early_vs_late_ratio = (early_monsoon / late_monsoon) if late_monsoon > 0 else 1.0
            june_onset_pdn = ((jun - jun_mean) / jun_mean) * 100.0 if jun_mean > 0 else 0.0

            # IMD Drought & Deluge Classification Target
            if ann_pdn >= 20.0:
                imd_category = "Excess (Deluge)"
                is_drought = 0
            elif ann_pdn >= -19.0:
                imd_category = "Normal"
                is_drought = 0
            elif ann_pdn >= -49.0:
                imd_category = "Deficient (Moderate Drought)"
                is_drought = 1
            else:
                imd_category = "Scanty (Severe Drought)"
                is_drought = 1

            # Assemble full record
            featured_row = dict(r)  # Keep all 19 original columns intact
            featured_row.update({
                # Climatological Baselines
                'SUBDIV_NORMAL_ANNUAL': f"{ann_mean:.2f}",
                'SUBDIV_NORMAL_MONSOON': f"{mon_mean:.2f}",
                'CLIMATIC_ZONE': zone,

                # Standardized Anomalies & Departures
                'ANNUAL_PDN': f"{ann_pdn:+.2f}",
                'MONSOON_PDN': f"{mon_pdn:+.2f}",
                'ANNUAL_ZSCORE': f"{ann_zscore:+.3f}",
                'MONSOON_ZSCORE': f"{mon_zscore:+.3f}",

                # Temporal Lags & Momentum
                'LAG1_ANNUAL': f"{lag1_ann:.2f}",
                'LAG2_ANNUAL': f"{lag2_ann:.2f}",
                'LAG3_ANNUAL': f"{lag3_ann:.2f}",
                'LAG1_MONSOON': f"{lag1_mon:.2f}",
                'ANNUAL_MOMENTUM': f"{annual_momentum:+.2f}",

                # Rolling Climatology
                'ROLL3_MEAN_ANNUAL': f"{roll3_mean:.2f}",
                'ROLL5_MEAN_ANNUAL': f"{roll5_mean:.2f}",
                'ROLL5_STD_ANNUAL': f"{roll5_std:.2f}",
                'DECADAL_DRIFT': f"{decadal_drift:+.2f}",

                # Intra-Annual & Seasonal Ratios
                'WINTER_PCT': f"{winter_pct:.2f}",
                'PRE_MONSOON_PCT': f"{pre_monsoon_pct:.2f}",
                'MONSOON_CONCENTRATION_PCT': f"{monsoon_concentration_idx:.2f}",
                'RETREATING_MONSOON_PCT': f"{retreating_monsoon_idx:.2f}",
                'EARLY_VS_LATE_MONSOON_RATIO': f"{early_vs_late_ratio:.3f}",
                'JUNE_ONSET_PDN': f"{june_onset_pdn:+.2f}",

                # Targets
                'IMD_DROUGHT_CATEGORY': imd_category,
                'IS_DROUGHT_YEAR': is_drought
            })

            new_rows.append(featured_row)

    # Sort final rows by SUBDIVISION, YEAR to preserve exact canonical ordering
    new_rows.sort(key=lambda x: (x['SUBDIVISION'], int(x['YEAR'])))

    # Get all field names
    all_fieldnames = list(new_rows[0].keys())

    # Write to both locations (sources for Files & Docs, and cleaned)
    for out_path in [OUTPUT_SOURCES, OUTPUT_CLEANED]:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        print(f"Successfully created: {out_path}")

    print("\n" + "=" * 70)
    print(f"SUCCESS: Feature engineering complete!")
    print(f"Total Rows: {len(new_rows)}")
    print(f"Total Columns: {len(all_fieldnames)} (19 Original + 22 Engineered = 41 Total)")
    print("=" * 70)

    return all_fieldnames, len(new_rows)

if __name__ == "__main__":
    run_feature_engineering()
