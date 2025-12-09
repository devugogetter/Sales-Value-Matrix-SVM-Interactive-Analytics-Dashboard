import pandas as pd
import pathlib
import sys

def main():
    try:
        file_name = input("Enter the Excel filename (e.g., zip-codes-in-virginia-beach-norfolk-newport-news-va-nc.xlsx): ").strip()
        if not file_name:
            raise ValueError("No filename provided.")

        path = pathlib.Path(file_name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_name}")

        df = pd.read_excel(path, engine="openpyxl")

        if "ZIP Code" not in df.columns:
            raise ValueError("Column 'ZIP Code' not found in the file.")
        
        # df = df.drop_duplicates(subset=["Place Name"])

        zip_codes = df["ZIP Code"].astype(str).tolist()
        formatted = ', '.join(f"'{z}'" for z in zip_codes)
        print("\nZIP Codes:")
        print(formatted)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
