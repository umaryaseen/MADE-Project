import os
import pandas as pd
import sqlite3
import time
from datasets import load_dataset

# Load JSON dataset from Hugging Face with unlimited retries
def load_json_from_hf(dataset_name, data_dir, delay=5):
    attempt = 1
    while True:
        try:
            print(f"Attempt {attempt} to load dataset...")
            # Attempt to load the dataset
            dataset = load_dataset(dataset_name, split='train')
            df = pd.DataFrame(dataset)  # Convert to a DataFrame
            df.to_json(f"{data_dir}/charging_stations.json", orient='records', lines=True)
            print("Dataset loaded successfully.")
            return df
        except Exception as e:
            print(f"Error loading dataset: {e}")
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            attempt += 1  # Increment attempt count for logging purposes

#function to ensure unique columns
def make_column_names_unique(columns):
    seen = {}
    unique_columns = []
    for col in columns:
        if col not in seen:
            seen[col] = 1
            unique_columns.append(col)
        else:
            new_col = f"{col}_{seen[col]}"
            while new_col in seen:
                seen[col] += 1
                new_col = f"{col}_{seen[col]}"
            seen[col] += 1
            seen[new_col] = 1
            unique_columns.append(new_col)
    return unique_columns

# Helper function to keep only specified keys
def keep_keys_from_metadata(metadata, keys_to_keep):
    return {k: v for k, v in metadata.items() if k in keys_to_keep}


# Transform function to keep only specified keys and replace null values
def transform_data(df, keys_to_keep):
    # Keep only specified keys in the `metadata` column
    if 'metadata' in df.columns:
        df['metadata'] = df['metadata'].apply(lambda x: keep_keys_from_metadata(x, keys_to_keep))

        # Flatten the `metadata` column after filtering to only the specified keys
        metadata_df = pd.json_normalize(df['metadata'])
        metadata_df.columns = [f"metadata_{col}" for col in metadata_df.columns]  # Prefix to avoid naming conflicts
        df = df.drop(columns=['metadata']).join(metadata_df)
    
    # Ensure all column names are unique
    df.columns = make_column_names_unique(df.columns)

    # Custom null value replacements
    replacements = {
        "metadata_name": "Charging point",                  # Replace null with "Charging point" for "name"
        "metadata_capacity": 1,                             # Replace null with 1 for "capacity" (assumed numeric)
    }
    
    # For other text columns, replace null with "not available"
    for col in keys_to_keep:
        prefixed_col = f"metadata_{col}"
        if prefixed_col in df.columns:
            if prefixed_col not in replacements:
                # Replace null with "not available" for text fields
                replacements[prefixed_col] = "not available"
    
    # Apply replacements for null values
    for col, replacement in replacements.items():
        if col in df.columns:
            df[col].fillna(replacement, inplace=True)
    
    # Drop duplicate rows
    df.drop_duplicates(inplace=True)
    
    return df


# Save to SQLite Database
def save_to_sqlite(df, db_path):
    with sqlite3.connect(db_path) as conn:
        # Save the DataFrame to SQLite with each metadata field as a separate column
        df.to_sql("charging_stations", conn, if_exists="replace", index=False)

def main():
    # Define paths
    dataset_name = "cfahlgren1/us-ev-charging-locations"
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "charging_stations.sqlite")

    # Load dataset with retries
    print("Loading dataset from Hugging Face with retry logic...")
    df = load_json_from_hf(dataset_name, data_dir)

    # Check if dataset was loaded successfully
    if df is None:
        print("Failed to load dataset after retries. Exiting pipeline.")
        return  # Exit if the dataset could not be loaded

    # Specify the keys to keep
    keys_to_keep = ["name", "brand", "amenity", "operator", "capacity", "addr:city", "addr:state"]

    # Transform dataset
    print("Transforming dataset...")
    df = transform_data(df, keys_to_keep)
    
    # Save to SQLite
    print(f"Saving transformed data to SQLite at {db_path}...")
    save_to_sqlite(df, db_path)
    print("Pipeline completed successfully.")

# Entry point
if __name__ == "__main__":
    main()
