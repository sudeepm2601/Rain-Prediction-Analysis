import csv
import os
from collections import defaultdict

MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
SEASONS = ['Jan-Feb', 'Mar-May', 'Jun-Sep', 'Oct-Dec']
NULL_VARIANTS = {'', 'na', 'nan', 'null', 'none', 'n/a', '?'}

def is_null(val):
    if val is None:
        return True
    return str(val).strip().lower() in NULL_VARIANTS

def clean_datasets(base_dir):
    sources_dir = os.path.join(base_dir, "projects", "rainprediction_codesis", "sources")
    cleaned_dir = os.path.join(base_dir, "projects", "rainprediction_codesis", "cleaned")
    os.makedirs(cleaned_dir, exist_ok=True)
    
    file1_in = os.path.join(sources_dir, "rainfall in india 1901-2015.csv")
    file1_out = os.path.join(cleaned_dir, "rainfall_in_india_1901_2015_cleaned.csv")
    file1_sources_out = os.path.join(sources_dir, "rainfall_in_india_1901_2015_cleaned.csv")
    
    file2_in = os.path.join(sources_dir, "district_wise_rainfall_normal.csv")
    file2_out = os.path.join(cleaned_dir, "district_wise_rainfall_normal_cleaned.csv")
    file2_sources_out = os.path.join(sources_dir, "district_wise_rainfall_normal_cleaned.csv")
    
    print("=" * 70)
    print("STEP 1: CLEANING DATASET 1 (rainfall in india 1901-2015.csv)")
    print("=" * 70)
    
    with open(file1_in, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows1 = list(reader)
        
    print(f"Loaded {len(rows1)} rows from {file1_in}")
    
    # 1. Compute historical monthly mean per subdivision for each month: mu(S, m)
    subdiv_month_vals = defaultdict(lambda: defaultdict(list))
    # Also index row by (subdivision, year) for cross-year neighbour lookups if needed
    subdiv_year_row = {}
    
    for r in rows1:
        sub = r['SUBDIVISION'].strip()
        yr = int(r['YEAR'].strip())
        subdiv_year_row[(sub, yr)] = r
        for m in MONTHS:
            v = r[m].strip()
            if not is_null(v):
                try:
                    subdiv_month_vals[sub][m].append(float(v))
                except ValueError:
                    pass
                    
    subdiv_month_mean = {}
    for sub, m_dict in subdiv_month_vals.items():
        subdiv_month_mean[sub] = {}
        for m, vals in m_dict.items():
            subdiv_month_mean[sub][m] = sum(vals) / len(vals) if vals else 0.0
            
    # 2. Impute missing monthly values and recompute aggregates
    imputed_records = []
    cleaned_rows1 = []
    
    for r in rows1:
        sub = r['SUBDIVISION'].strip()
        yr = int(r['YEAR'].strip())
        new_row = {'SUBDIVISION': sub, 'YEAR': yr}
        
        # Extract monthly floats or None
        row_months = {}
        for m in MONTHS:
            v = r[m].strip()
            if is_null(v):
                row_months[m] = None
            else:
                row_months[m] = float(v)
                
        # Impute if None
        for i, m in enumerate(MONTHS):
            if row_months[m] is None:
                # Component A: Subdivision historical mean for this month
                mu = subdiv_month_mean[sub].get(m, 0.0)
                
                # Component B: Neighbouring months in that year
                neighbours = []
                
                # Left neighbour
                left_val = None
                if i > 0:
                    left_val = row_months[MONTHS[i - 1]]
                else:
                    # Jan's left neighbour is Dec of previous year, if available
                    prev_r = subdiv_year_row.get((sub, yr - 1))
                    if prev_r and not is_null(prev_r.get('DEC')):
                        try:
                            left_val = float(prev_r['DEC'])
                        except ValueError:
                            pass
                if left_val is not None:
                    neighbours.append(left_val)
                    
                # Right neighbour
                right_val = None
                if i < 11:
                    # Look ahead to raw or already checked next month
                    raw_next = r[MONTHS[i + 1]].strip()
                    if not is_null(raw_next):
                        try:
                            right_val = float(raw_next)
                        except ValueError:
                            pass
                else:
                    # Dec's right neighbour is Jan of next year, if available
                    next_r = subdiv_year_row.get((sub, yr + 1))
                    if next_r and not is_null(next_r.get('JAN')):
                        try:
                            right_val = float(next_r['JAN'])
                        except ValueError:
                            pass
                if right_val is not None:
                    neighbours.append(right_val)
                    
                # Fallback if both immediate neighbours were missing: use available neighbour
                if not neighbours:
                    # Search wider in the year
                    valid_in_year = [v for v in row_months.values() if v is not None]
                    if valid_in_year:
                        neighbour_mean = sum(valid_in_year) / len(valid_in_year)
                    else:
                        neighbour_mean = mu
                else:
                    neighbour_mean = sum(neighbours) / len(neighbours)
                    
                # Hybrid imputation: average of historical month mean and neighbouring month mean
                imputed_val = round((mu + neighbour_mean) / 2.0, 2)
                row_months[m] = imputed_val
                
                imputed_records.append({
                    'SUBDIVISION': sub,
                    'YEAR': yr,
                    'MONTH': m,
                    'HISTORICAL_MEAN': round(mu, 2),
                    'NEIGHBOUR_MEAN': round(neighbour_mean, 2),
                    'IMPUTED_VALUE': imputed_val
                })
                
        # Format monthly values to 2 decimal places
        for m in MONTHS:
            new_row[m] = f"{row_months[m]:.2f}"
            
        # Recompute seasonal aggregates for 100% mathematical integrity
        jan_feb = row_months['JAN'] + row_months['FEB']
        mar_may = row_months['MAR'] + row_months['APR'] + row_months['MAY']
        jun_sep = row_months['JUN'] + row_months['JUL'] + row_months['AUG'] + row_months['SEP']
        oct_dec = row_months['OCT'] + row_months['NOV'] + row_months['DEC']
        annual = sum(row_months.values())
        
        new_row['ANNUAL'] = f"{annual:.2f}"
        new_row['Jan-Feb'] = f"{jan_feb:.2f}"
        new_row['Mar-May'] = f"{mar_may:.2f}"
        new_row['Jun-Sep'] = f"{jun_sep:.2f}"
        new_row['Oct-Dec'] = f"{oct_dec:.2f}"
        
        cleaned_rows1.append(new_row)
        
    # Write Cleaned Dataset 1 to cleaned/ and sources/
    for out_path in [file1_out, file1_sources_out]:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows1)
        
    print(f"Successfully cleaned Dataset 1. Imputed {len(imputed_records)} missing month values.")
    print(f"Saved cleaned file to: {file1_out}")
    print(f"Saved cleaned file to: {file1_sources_out} (Files & Docs)")
    
    print("\n" + "=" * 70)
    print("STEP 2: CLEANING DATASET 2 (district_wise_rainfall_normal.csv)")
    print("=" * 70)
    
    with open(file2_in, 'r', encoding='utf-8-sig') as f:
        reader2 = csv.DictReader(f)
        fieldnames2 = reader2.fieldnames
        rows2 = list(reader2)
        
    cleaned_rows2 = []
    for r in rows2:
        # Ignore completely empty rows (like trailing empty lines)
        if not r.get('STATE_UT_NAME') and not r.get('DISTRICT'):
            continue
        new_row = {
            'STATE_UT_NAME': r['STATE_UT_NAME'].strip(),
            'DISTRICT': r['DISTRICT'].strip()
        }
        month_vals = {}
        for m in MONTHS:
            month_vals[m] = float(r[m].strip())
            new_row[m] = f"{month_vals[m]:.1f}"
            
        jan_feb = month_vals['JAN'] + month_vals['FEB']
        mar_may = month_vals['MAR'] + month_vals['APR'] + month_vals['MAY']
        jun_sep = month_vals['JUN'] + month_vals['JUL'] + month_vals['AUG'] + month_vals['SEP']
        oct_dec = month_vals['OCT'] + month_vals['NOV'] + month_vals['DEC']
        annual = sum(month_vals.values())
        
        new_row['ANNUAL'] = f"{annual:.1f}"
        new_row['Jan-Feb'] = f"{jan_feb:.1f}"
        new_row['Mar-May'] = f"{mar_may:.1f}"
        new_row['Jun-Sep'] = f"{jun_sep:.1f}"
        new_row['Oct-Dec'] = f"{oct_dec:.1f}"
        
        cleaned_rows2.append(new_row)
        
    # Write Cleaned Dataset 2 to cleaned/ and sources/
    for out_path in [file2_out, file2_sources_out]:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames2)
            writer.writeheader()
            writer.writerows(cleaned_rows2)
        
    print(f"Successfully cleaned Dataset 2. Processed {len(cleaned_rows2)} district rows.")
    print(f"Saved cleaned file to: {file2_out}")
    print(f"Saved cleaned file to: {file2_sources_out} (Files & Docs)")
    
    return imputed_records, len(cleaned_rows1), len(cleaned_rows2)

if __name__ == "__main__":
    current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # In case run from workspace root:
    if not os.path.exists(os.path.join(current_dir, "projects")):
        current_dir = r"C:\Users\Sudeep M\Documents\Project Antigravity"
    clean_datasets(current_dir)
