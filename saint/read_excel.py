import pandas as pd
import json
import sys

# Since it's an .xls file, we need xlrd
# Let's read all sheets
file_path = r"C:\Users\DARIO LUBISCO\Downloads\DiccionarioAdministrativo.xls"

try:
    # Read Excel file
    xl = pd.ExcelFile(file_path, engine="xlrd")
    
    tables_of_interest = ['SAACXP', 'SAPROV', 'SAIPACXP', 'SAFACT', 'SAPAGCXP']
    
    print("Sheets available:", xl.sheet_names)
    
    # Iterate through sheets to find mentions of these tables
    found_info = {}
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        # Convert to string to easily search
        for table in tables_of_interest:
            # Check if table name is in any string column
            mask = df.astype(str).apply(lambda x: x.str.contains(table, case=False, na=False)).any(axis=1)
            if mask.any():
                if table not in found_info:
                    found_info[table] = []
                # Keep rows where table name is found
                found_info[table].append({
                    "sheet": sheet,
                    "data": df[mask].to_dict('records')
                })
                
    # Save to a temporary json file for easy reading
    output_path = r"C:\source\dict_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(found_info, f, ensure_ascii=False, indent=2)
        
    print(f"Data parsed successfully and saved to {output_path}")

except Exception as e:
    print("Error parsing Excel:", e)
    sys.exit(1)
