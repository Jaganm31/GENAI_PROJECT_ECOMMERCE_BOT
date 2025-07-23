from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv
import urllib.parse
import numpy as np # <-- Added import for numpy

# ✅ Load environment variables
load_dotenv(dotenv_path='./.env')

# ✅ Fetch DB credentials
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# ✅ Encode password
encoded_password = urllib.parse.quote(DB_PASSWORD)

# ✅ SQLAlchemy engine
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}")

# ✅ Mapping: CSV → Table
file_table_map = {
    "../../datasets/Product-Level Total Sales and Metrics (mapped).csv": "total_sales",
    "../../datasets/Product-Level Ad Sales and Metrics (mapped).csv": "ad_sales",
    "../../datasets/Product-Level Eligibility Table (mapped).csv": "eligibility"
}

# --- NEW: Preprocessing Function ---
def preprocess_df(df, table_name):
    """
    Performs data cleaning and type conversion based on table name.
    """
    print(f"⚙️ Preprocessing data for `{table_name}`...")

    # 1. Standardize column names (already in your original code, kept here for encapsulation)
    df.columns = [col.strip().replace(" ", "_").lower() for col in df.columns]

    # 2. General Data Type Conversions and Cleaning
    for col in df.columns:
        # Attempt to convert to numeric, handling common non-numeric characters
        try:
            # If column is an object (string) type, try cleaning and converting
            if df[col].dtype == 'object':
                # Remove currency symbols, commas, spaces, and handle percentages (e.g., '50%' -> '50')
                cleaned_series = df[col].astype(str).str.replace(r'[₹$,% ]', '', regex=True)
                # Convert to numeric, coercing errors to NaN
                df[col] = pd.to_numeric(cleaned_series, errors='coerce')
            # If not an object type, a direct to_numeric might still be useful (e.g., converting bools to 0/1)
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # After numeric conversion, fill any newly created NaNs (from errors='coerce')
            if df[col].isnull().any() and pd.api.types.is_numeric_dtype(df[col]):
                print(f"   - Warning: Column '{col}' in '{table_name}' had non-numeric values converted to NaN. Filling with 0.")
                df[col] = df[col].fillna(0)

        except Exception:
            # If numeric conversion fails for any reason, leave column as is (e.g., truly text column)
            pass

        # Attempt to convert to datetime for columns that might be dates
        # This runs after numeric conversion, so if a column is purely numeric (like '20230101'),
        # it might stay numeric unless explicitly handled. For 'YYYY-MM-DD' strings, this is key.
        if df[col].dtype == 'object': # Only try if it's still an object/string type
            try:
                # Infer datetime format for robustness, errors='coerce' turns invalid dates to NaT
                df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
            except Exception:
                pass # Silently ignore if datetime conversion fails

    # 3. Table-specific preprocessing rules
    # This is where you can add custom logic for each dataset
    if table_name == "total_sales":
        # Ensure 'item_id' is always treated as a string/categorical, even if it looks numeric
        if 'item_id' in df.columns:
            df['item_id'] = df['item_id'].astype(str)
        # Example: If 'date' column exists, ensure it's datetime and handle NaTs
        if 'date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['date']):
            # Fill NaT (Not a Time) values if any, e.g., with a default date or by dropping rows
            df['date'] = df['date'].fillna(pd.Timestamp('1900-01-01')) # Example fill
        # Add other specific rules for total_sales table

    elif table_name == "ad_sales":
        # Ensure 'item_id' is always treated as a string/categorical
        if 'item_id' in df.columns:
            df['item_id'] = df['item_id'].astype(str)
        # Example: Handle missing 'ad_spend' or 'ad_sales'
        if 'ad_spend' in df.columns:
            df['ad_spend'] = df['ad_spend'].fillna(0)
        if 'ad_sales' in df.columns:
            df['ad_sales'] = df['ad_sales'].fillna(0)
        # Add other specific rules for ad_sales table

    elif table_name == "eligibility":
        # Ensure 'item_id' is always treated as a string/categorical
        if 'item_id' in df.columns:
            df['item_id'] = df['item_id'].astype(str)
        # Ensure 'eligibility_datetime_utc' is datetime
        if 'eligibility_datetime_utc' in df.columns:
             df['eligibility_datetime_utc'] = pd.to_datetime(df['eligibility_datetime_utc'], errors='coerce', infer_datetime_format=True)
             df['eligibility_datetime_utc'] = df['eligibility_datetime_utc'].fillna(pd.Timestamp('1900-01-01'))
        # Example: Convert 'eligibility' column (e.g., 'True'/'False' strings) to boolean or int
        if 'eligibility' in df.columns and df['eligibility'].dtype == 'object':
            df['eligibility'] = df['eligibility'].astype(str).str.lower().map({'true': 1, 'false': 0, 'yes': 1, 'no': 0, 'eligible': 1, 'not eligible': 0}).fillna(0).astype(int)
        # Add other specific rules for eligibility table

    # 4. Remove duplicate rows (good general practice after cleaning)
    df.drop_duplicates(inplace=True)

    print(f"✅ Preprocessing for `{table_name}` complete. DataFrame info after preprocessing:")
    df.info() # Print info to see dtypes and non-null counts
    print("-" * 50)
    return df

# ✅ Upload function
def load_and_upload(csv_path, table_name):
    """
    Loads a CSV, preprocesses it, and uploads it to the specified database table.
    """
    try:
        print(f"📥 Loading: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8')

        # --- Apply preprocessing to the DataFrame ---
        df = preprocess_df(df, table_name)

        # Upload to SQL database
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        print(f"✅ Uploaded to `{table_name}`\n")
    except Exception as e:
        print(f"❌ Error uploading `{table_name}`: {e}\n")

# ✅ Process each file
for path, table in file_table_map.items():
    if os.path.exists(path):
        load_and_upload(path, table)
    else:
        print(f"❌ File not found: {path}")
