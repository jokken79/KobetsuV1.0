"""
Sync Excel factory data to JSON files.
Compares E:\EmpresasFabricas.xlsx with E:\factories/*.json and:
1. Creates missing JSON files
2. Updates existing JSON files with Excel data
"""
import pandas as pd
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = 'E:/EmpresasFabricas.xlsx'
JSON_DIR = 'E:/factories'

def safe_str(val):
    """Convert value to string, handling NaN."""
    if pd.isna(val):
        return ''
    return str(val).strip()

def safe_float(val, default=0.0):
    """Convert value to float, handling NaN."""
    if pd.isna(val):
        return default
    try:
        return float(val)
    except:
        return default

def safe_date(val):
    """Convert value to date string."""
    if pd.isna(val):
        return ''
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')
    return str(val)

def create_factory_json(rows, company, factory):
    """Create a factory JSON structure from Excel rows."""
    # Use first row for company/factory info
    row = rows.iloc[0]

    # Build lines array
    lines = []
    for idx, (_, r) in enumerate(rows.iterrows()):
        line_name = safe_str(r.get('ライン', ''))
        if not line_name:
            line_name = f"ライン{idx+1}"

        line = {
            "line_id": f"Factory-{idx+1}",
            "assignment": {
                "department": safe_str(r.get('配属先', '')),
                "line": line_name,
                "supervisor": {
                    "department": safe_str(r.get('指示命令者部署', '')),
                    "name": safe_str(r.get('指示命令者名', '')),
                    "phone": safe_str(r.get('指示命令者電話', ''))
                }
            },
            "job": {
                "description": safe_str(r.get('仕事内容', '')),
                "description2": safe_str(r.get('仕事内容2', '')),
                "hourly_rate": safe_float(r.get('時給単価', 0))
            }
        }
        lines.append(line)

    # Build full structure
    data = {
        "factory_id": f"{company}_{factory}",
        "client_company": {
            "name": company,
            "address": safe_str(row.get('派遣先住所', '')),
            "phone": safe_str(row.get('派遣先電話', '')),
            "responsible_person": {
                "department": safe_str(row.get('派遣先責任者部署', '')),
                "name": safe_str(row.get('派遣先責任者名', '')),
                "phone": safe_str(row.get('派遣先責任者電話', ''))
            },
            "complaint_handler": {
                "department": safe_str(row.get('派遣先：苦情処理：部署', '')),
                "name": safe_str(row.get('派遣先：苦情処理：名', '')),
                "phone": safe_str(row.get('派遣先：苦情処理：電話', ''))
            }
        },
        "plant": {
            "name": factory,
            "address": safe_str(row.get('工場住所', '')),
            "phone": safe_str(row.get('工場電話', ''))
        },
        "lines": lines,
        "dispatch_company": {
            "responsible_person": {
                "department": safe_str(row.get('派遣元責任者部署', '')),
                "name": safe_str(row.get('派遣元責任者名', '')),
                "phone": safe_str(row.get('派遣元責任者電話', ''))
            },
            "complaint_handler": {
                "department": safe_str(row.get('派遣元：苦情処理：部署', '')),
                "name": safe_str(row.get('派遣元：苦情処理：名', '')),
                "phone": safe_str(row.get('派遣元：苦情処理：電話', ''))
            }
        },
        "schedule": {
            "work_hours": safe_str(row.get('就業時間', '')),
            "break_time": safe_str(row.get('休憩時間', '')),
            "calendar": safe_str(row.get('カレンダー', '')),
            "start_date": safe_date(row.get('就業日', '')),
            "end_date": safe_date(row.get('まで', '')),
            "conflict_date": safe_date(row.get('抵触日', '')),
            "non_work_day_labor": safe_str(row.get('就業日外労働', '')),
            "overtime_labor": safe_str(row.get('時間外労働', '')),
            "time_unit": safe_str(row.get('時間単位', ''))
        },
        "payment": {
            "closing_date": safe_str(row.get('締日', '')),
            "payment_date": safe_str(row.get('支払日', '')),
            "bank_account": safe_str(row.get('振込先', '')),
            "worker_closing_date": safe_str(row.get('作業者締め日', '')),
            "worker_payment_date": safe_str(row.get('作業者支払日', '')),
            "worker_calendar": safe_str(row.get('作業者カレンダー', ''))
        },
        "agreement": {
            "period": safe_date(row.get('当該協定期間', '')),
            "explainer": safe_str(row.get('説明者', ''))
        }
    }

    return data

def main():
    print("=== SYNC EXCEL TO JSON ===")
    print(f"Excel: {EXCEL_PATH}")
    print(f"JSON Dir: {JSON_DIR}")
    print()

    # Read Excel
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    df = df.dropna(subset=['派遣先'], how='all')
    df = df[df['派遣先'].notna()]

    # Clean column names and values
    df['派遣先'] = df['派遣先'].str.strip()
    df['工場名'] = df['工場名'].str.strip()
    df['ライン'] = df['ライン'].fillna('').astype(str).str.strip()

    print(f"Excel rows: {len(df)}")

    # Get existing JSON files
    existing_jsons = {}
    for f in os.listdir(JSON_DIR):
        if f.endswith('.json'):
            existing_jsons[f.replace('.json', '')] = os.path.join(JSON_DIR, f)

    print(f"Existing JSONs: {len(existing_jsons)}")
    print()

    # Group by company and factory
    grouped = df.groupby(['派遣先', '工場名'])

    created = 0
    updated = 0
    skipped = 0

    for (company, factory), group in grouped:
        if pd.isna(factory) or not factory:
            print(f"SKIP: {company} - no factory name")
            skipped += 1
            continue

        json_key = f"{company}_{factory}"
        json_path = os.path.join(JSON_DIR, f"{json_key}.json")

        # Create JSON structure from Excel
        excel_data = create_factory_json(group, company, factory)

        if json_key in existing_jsons:
            # Update existing JSON
            with open(existing_jsons[json_key], 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

            # Update lines from Excel (merge by line name)
            existing_lines = {l['assignment']['line']: l for l in existing_data.get('lines', [])}
            excel_lines = {l['assignment']['line']: l for l in excel_data['lines']}

            # Check if there are differences
            needs_update = False

            # Check company info
            if existing_data.get('client_company', {}).get('name', '').strip() != company:
                needs_update = True

            # Check if lines differ
            for line_name, excel_line in excel_lines.items():
                if line_name not in existing_lines:
                    needs_update = True
                    break
                existing_line = existing_lines[line_name]
                # Compare job description and hourly rate
                if (excel_line['job']['description'] != existing_line['job'].get('description', '') or
                    excel_line['job']['hourly_rate'] != existing_line['job'].get('hourly_rate', 0)):
                    needs_update = True
                    break

            if needs_update:
                # Merge: keep existing lines not in Excel, update matching ones
                merged_lines = []
                processed = set()

                for excel_line in excel_data['lines']:
                    line_name = excel_line['assignment']['line']
                    if line_name in existing_lines:
                        # Update existing with Excel data
                        merged_line = existing_lines[line_name].copy()
                        merged_line['assignment']['department'] = excel_line['assignment']['department']
                        merged_line['assignment']['supervisor'] = excel_line['assignment']['supervisor']
                        merged_line['job']['description'] = excel_line['job']['description']
                        merged_line['job']['hourly_rate'] = excel_line['job']['hourly_rate']
                        merged_lines.append(merged_line)
                    else:
                        # Add new line from Excel
                        merged_lines.append(excel_line)
                    processed.add(line_name)

                # Keep lines from JSON that aren't in Excel
                for line_name, line in existing_lines.items():
                    if line_name not in processed:
                        merged_lines.append(line)

                existing_data['lines'] = merged_lines
                existing_data['client_company']['name'] = company  # Fix any encoding issues

                with open(existing_jsons[json_key], 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                print(f"UPDATED: {json_key} ({len(merged_lines)} lines)")
                updated += 1
            else:
                print(f"OK: {json_key} (no changes)")
        else:
            # Create new JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(excel_data, f, ensure_ascii=False, indent=2)
            print(f"CREATED: {json_key} ({len(excel_data['lines'])} lines)")
            created += 1

    print()
    print("=== SUMMARY ===")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")

if __name__ == '__main__':
    main()
