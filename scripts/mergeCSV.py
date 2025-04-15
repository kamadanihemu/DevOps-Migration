#install below pkg
#pip install openpyxl
#pip install pandas

import pandas as pd
import glob
import os

org = "__org__"
output_file = f"{org}_inventory_report.xlsx"
#get all csv
csv_files = glob.glob('*.csv')

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for file in csv_files:
        try: 
            df = pd.read_csv(file)
            if df.empty:
                
                df = pd.DataFrame({'Message': [f'This file ({file}) is empty.']})
            
            sheet_name = file.split('.')[0]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        except pd.errors.EmptyDataError:
            df = pd.DataFrame({'Message': [f'This file ({file}) contains no data.']})
            sheet_name = file.split('.')[0]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print("CSV Files Merged completed...............")