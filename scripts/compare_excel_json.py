"""Compare Excel and JSON factory data."""
import pandas as pd
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read Excel
df = pd.read_excel('E:/EmpresasFabricas.xlsx', engine='openpyxl')
df = df.dropna(subset=['派遣先'], how='all')
df = df[df['派遣先'].notna()]

# Read all JSONs
json_dir = 'E:/factories'
json_files = [f for f in os.listdir(json_dir) if f.endswith('.json') and f != 'factory_id_mapping.json']

print('=== FINAL COMPARISON: EXCEL vs JSON ===')
print()

# Build Excel lookup
excel_data = {}
for _, row in df.iterrows():
    company = str(row['派遣先']).strip() if pd.notna(row['派遣先']) else ''
    factory = str(row['工場名']).strip() if pd.notna(row['工場名']) else ''
    line = str(row['ライン']).strip() if pd.notna(row['ライン']) else ''
    key = f'{company}|{factory}|{line}'
    excel_data[key] = row

# Build JSON lookup
json_data = {}
for jf in json_files:
    try:
        with open(os.path.join(json_dir, jf), 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            data = data[0] if data else {}

        company = data.get('client_company', {}).get('name', '').strip()
        factory = data.get('plant', {}).get('name', '').strip()
        for line_obj in data.get('lines', []):
            line_name = line_obj.get('assignment', {}).get('line', '').strip()
            key = f'{company}|{factory}|{line_name}'
            json_data[key] = {
                'file': jf,
                'data': data,
                'line': line_obj
            }
    except Exception as e:
        print(f'Error reading {jf}: {e}')

print(f'Excel entries: {len(excel_data)}')
print(f'JSON entries: {len(json_data)}')
print()

# Find differences
only_excel = set(excel_data.keys()) - set(json_data.keys())
only_json = set(json_data.keys()) - set(excel_data.keys())
matched = set(excel_data.keys()) & set(json_data.keys())

print(f'Matched: {len(matched)}')
print(f'Only in Excel: {len(only_excel)}')
print(f'Only in JSON: {len(only_json)}')
print()

if only_excel:
    print('=== STILL MISSING IN JSON ===')
    for k in sorted(only_excel):
        parts = k.split('|')
        print(f'  {parts[0]} | {parts[1]} | {parts[2]}')
    print()

if only_json:
    print('=== EXTRA IN JSON (not in Excel) ===')
    for k in sorted(only_json)[:20]:
        parts = k.split('|')
        jd = json_data[k]
        print(f'  {parts[0]} | {parts[1]} | {parts[2]}')
    if len(only_json) > 20:
        print(f'  ... and {len(only_json) - 20} more')
