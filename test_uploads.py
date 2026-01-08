import pandas as pd
import os

# Check uploads directory
uploads_dir = "web/server/uploads"
if os.path.exists(uploads_dir):
    print("Files in uploads directory:")
    for file in os.listdir(uploads_dir):
        filepath = os.path.join(uploads_dir, file)
        print(f"\n=== {file} ===")
        print(f"Size: {os.path.getsize(filepath)} bytes")
        print(f"Modified: {os.path.getmtime(filepath)}")
        
        # Try to read the file
        try:
            if file.endswith('.xlsx') or file.endswith('.xls'):
                df = pd.read_excel(filepath)
                print(f"Type: Excel")
            elif file.endswith('.csv'):
                df = pd.read_csv(filepath)
                print(f"Type: CSV")
            else:
                print(f"Type: Unknown")
                continue
                
            print(f"Columns: {df.columns.tolist()}")
            print(f"Shape: {df.shape}")
            if len(df) > 0:
                print("First row:")
                print(df.iloc[0])
        except Exception as e:
            print(f"Error reading file: {e}")
else:
    print(f"Uploads directory not found: {uploads_dir}")
