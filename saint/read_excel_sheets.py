import pandas as pd
import sys
import traceback

file_path = r"C:\Users\DARIO LUBISCO\Downloads\DiccionarioAdministrativo.xls"

try:
    print(f"Reading {file_path}")
    # Read Excel file
    xl = pd.ExcelFile(file_path, engine="xlrd")
    print("Sheets available:", xl.sheet_names)
    
except Exception as e:
    print("Error parsing Excel:", e)
    traceback.print_exc()
    sys.exit(1)
