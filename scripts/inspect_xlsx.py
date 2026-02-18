"""Inspect xlsx files in data/ and print structure and sample rows."""
import os
import sys

try:
    import pandas as pd
except ImportError:
    print("pip install pandas openpyxl")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FILES = [
    "Damage Skills (Update 38_39_40).xlsx",
    "Harpooner's Wading Kilt Cheat Sheet.xlsx",
    "Standalone Damage Modifiers Calculator (ESO).xlsx",
]

def main():
    for filename in FILES:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            print(f"Skip (not found): {filename}\n")
            continue
        print("=" * 60, filename, "=" * 60)
        xl = pd.ExcelFile(path)
        print("Sheet names:", xl.sheet_names)
        for name in xl.sheet_names:
            df = pd.read_excel(path, sheet_name=name, header=None)
            print(f"\n--- Sheet: {name} (shape {df.shape}) ---")
            pd.set_option("display.max_columns", 24)
            pd.set_option("display.width", 240)
            pd.set_option("display.max_rows", 50)
            print(df.head(45).to_string())
        print("\n")

if __name__ == "__main__":
    main()
