import os
import pandas as pd

directory_path = os.getcwd()
project_name = "__project__"


for filename in os.listdir(directory_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory_path, filename)
        
        df = pd.read_csv(file_path)
        if 'teamproject' in df.columns:
            filtered_df = df[df['teamproject'] == project_name]
            filtered_df.to_csv(file_path, index=False)
            print(f"Filtered {filename} and saved the updated file.")
