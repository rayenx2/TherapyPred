"""
Stage 2: Data Validation
------------------------
Validates the ingested CSV against the schema defined in params.yaml.
Checks: column names, data types, categorical value ranges, numeric ranges.
Hard-fails on any schema violation.
"""

import os
import sys
import yaml
import logging
import pandas as pd

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("validate")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load params.yaml: {e}")
        sys.exit(1)


def validate_schema(df, schema):
    """Validate dataframe against schema. Returns list of errors."""
    errors = []

    # --- Check column names ---
    expected_cols = schema["columns"]
    actual_cols = list(df.columns)
    if actual_cols != expected_cols:
        missing = set(expected_cols) - set(actual_cols)
        extra = set(actual_cols) - set(expected_cols)
        if missing:
            errors.append(f"Missing columns: {missing}")
        if extra:
            errors.append(f"Unexpected columns: {extra}")

    # --- Check for nulls ---
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if len(cols_with_nulls) > 0:
        errors.append(f"Columns with null values: {dict(cols_with_nulls)}")

    # --- Check Patient_ID format ---
    if "Patient_ID" in df.columns:
        invalid_ids = df[~df["Patient_ID"].astype(str).str.match(r"^P\d+$")]
        if len(invalid_ids) > 0:
            errors.append(
                f"Invalid Patient_ID format (expected P followed by digits): "
                f"{invalid_ids['Patient_ID'].head(5).tolist()}"
            )

    # --- Check Gender values ---
    if "Gender" in df.columns:
        invalid_genders = set(df["Gender"].unique()) - set(schema["gender_values"])
        if invalid_genders:
            errors.append(f"Invalid Gender values: {invalid_genders}")

    # --- Check Condition values ---
    if "Condition" in df.columns:
        invalid_conditions = set(df["Condition"].unique()) - set(
            schema["condition_values"]
        )
        if invalid_conditions:
            errors.append(f"Invalid Condition values: {invalid_conditions}")

    # --- Check Drug_Name values ---
    if "Drug_Name" in df.columns:
        invalid_drugs = set(df["Drug_Name"].unique()) - set(schema["drug_values"])
        if invalid_drugs:
            errors.append(f"Invalid Drug_Name values: {invalid_drugs}")

    # --- Check Side_Effects values ---
    if "Side_Effects" in df.columns:
        invalid_effects = set(df["Side_Effects"].unique()) - set(
            schema["side_effect_values"]
        )
        if invalid_effects:
            errors.append(f"Invalid Side_Effects values: {invalid_effects}")

    # --- Check Age range ---
    if "Age" in df.columns:
        age_min, age_max = schema["age_range"]
        out_of_range = df[(df["Age"] < age_min) | (df["Age"] > age_max)]
        if len(out_of_range) > 0:
            errors.append(
                f"Age out of range [{age_min}, {age_max}]: "
                f"{out_of_range['Age'].unique().tolist()}"
            )

    # --- Check Dosage_mg values ---
    if "Dosage_mg" in df.columns:
        valid_dosages = schema["dosage_values"]
        invalid_dosages = set(df["Dosage_mg"].unique()) - set(valid_dosages)
        if invalid_dosages:
            errors.append(
                f"Invalid Dosage_mg values (expected {valid_dosages}): {invalid_dosages}"
            )

    # --- Check Treatment_Duration_days range ---
    if "Treatment_Duration_days" in df.columns:
        dur_min, dur_max = schema["duration_range"]
        out_of_range = df[
            (df["Treatment_Duration_days"] < dur_min)
            | (df["Treatment_Duration_days"] > dur_max)
        ]
        if len(out_of_range) > 0:
            errors.append(
                f"Treatment_Duration_days out of range [{dur_min}, {dur_max}]: "
                f"{out_of_range['Treatment_Duration_days'].unique().tolist()}"
            )

    # --- Check Improvement_Score range ---
    if "Improvement_Score" in df.columns:
        score_min, score_max = schema["score_range"]
        out_of_range = df[
            (df["Improvement_Score"] < score_min)
            | (df["Improvement_Score"] > score_max)
        ]
        if len(out_of_range) > 0:
            errors.append(
                f"Improvement_Score out of range [{score_min}, {score_max}]: "
                f"{out_of_range['Improvement_Score'].unique().tolist()}"
            )

    return errors


def main():
    logger.info("Starting data validation...")
    params = load_params()
    processed_dir = params["data"]["processed_dir"]
    schema = params["schema"]

    input_path = os.path.join(processed_dir, "ingested.csv")
    output_path = os.path.join(processed_dir, "validated.csv")

    # --- Load data ---
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)
        
    logger.info(f"Validating {len(df)} rows, {len(df.columns)} columns...")

    # --- Run validation ---
    try:
        errors = validate_schema(df, schema)
    except Exception as e:
        logger.error(f"Validation logic error: {e}")
        sys.exit(1)

    if errors:
        logger.error("VALIDATION FAILED:")
        for i, error in enumerate(errors, 1):
            logger.error(f"  {i}. {error}")
        sys.exit(1)

    # --- Save validated data ---
    try:
        df.to_csv(output_path, index=False)
    except IOError as e:
        logger.error(f"Failed to save validated CSV: {e}")
        sys.exit(1)

    logger.info(f"Validation passed: {len(df)} rows, all schema checks OK")
    logger.info(f"Output: {output_path}")


if __name__ == "__main__":
    main()
