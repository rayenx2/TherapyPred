import pandas as pd
import json
import os

def extract_valid_combinations():
    # Define paths based on project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_data_path = os.path.join(project_root, "data", "raw", "real_drug_dataset.csv")
    processed_dir = os.path.join(project_root, "data", "processed")
    output_path = os.path.join(processed_dir, "valid_combinations.json")

    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)

    # Read the dataset
    df = pd.read_csv(raw_data_path)

    # Extract required columns and drop duplicates
    combos = df[['Condition', 'Drug_Name', 'Dosage_mg', 'Side_Effects']].drop_duplicates()

    # Convert to a list of dicts for JSON serialization
    combos_list = combos.to_dict(orient='records')

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(combos_list, f, indent=2)

    print(f"Extracted {len(combos_list)} valid combinations and saved to {output_path}")

if __name__ == "__main__":
    extract_valid_combinations()
