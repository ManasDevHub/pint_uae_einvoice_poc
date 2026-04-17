import pandas as pd
import json
import os

def extract():
    file_path = r'C:\Users\patil\Downloads\PINT_AE_QA_TestCases_v2.xlsx'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Reading {file_path}...")
    # Skip preamble rows
    df = pd.read_excel(file_path, skiprows=2)
    
    rules = []
    # Columns based on d8552c90 check:
    # 'SL.NO', 'Module', 'Field / Component', 'Test Case ID', 'Test Type', 
    # 'Scenario Description', 'Test Data / Input', 'Expected Result', 
    # 'Business Rule', 'Priority', 'Phase', 'Status'
    
    for _, row in df.iterrows():
        if pd.isna(row['Test Case ID']):
            continue
            
        rule = {
            'id': str(row['Test Case ID']),
            'segment': str(row['Module']),
            'field': str(row['Field / Component']),
            'type': str(row['Test Type']),
            'description': str(row['Scenario Description']),
            'input': str(row['Test Data / Input']),
            'expected': str(row['Expected Result']),
            'rule_ref': str(row['Business Rule']),
            'priority': str(row['Priority'])
        }
        rules.append(rule)
    
    output_dir = 'data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'sandbox_rules.json')
    with open(output_path, 'w') as f:
        json.dump(rules, f, indent=2)
    
    print(f"Successfully extracted {len(rules)} rules to {output_path}")

if __name__ == "__main__":
    extract()
