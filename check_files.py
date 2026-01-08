import pandas as pd
import sys

def check_file(filepath):
    print(f"\nChecking file: {filepath}")
    
    try:
        if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            df = pd.read_excel(filepath)
            print("File type: Excel")
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            print("File type: CSV")
        else:
            print(f"Unknown file type: {filepath}")
            return
        
        print(f"Columns: {df.columns.tolist()}")
        print(f"Shape: {df.shape}")
        print("\nFirst 3 rows:")
        print(df.head(3))
        print("\nColumn dtypes:")
        print(df.dtypes)
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # Check the files in uploads folder
    import os
    uploads_dir = "web/server/uploads"
    
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        for file in files:
            check_file(os.path.join(uploads_dir, file))
    else:
        print(f"Uploads directory not found: {uploads_dir}")
