"""
Stage 3: Data Preprocessing
----------------------------
- Drops Patient_ID (not a predictive feature)
- One-hot encodes categorical features (Gender, Condition, Drug_Name, Side_Effects)
- Scales numeric features (Age, Dosage_mg, Treatment_Duration_days)
- Splits into train/test sets
- Saves preprocessor pipeline as .joblib for inference reuse
"""

import os
import sys
import yaml
import logging
import pandas as pd


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("preprocess")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load params.yaml: {e}")
        sys.exit(1)


def main():
    logger.info("Starting data preprocessing...")
    params = load_params()
    
    try:
        processed_dir = params["data"]["processed_dir"]
        random_seed = params["random_seed"]
        test_split = params["test_split"]
        features = params["features"]
    except KeyError as e:
        logger.error(f"Missing param: {e}")
        sys.exit(1)

    input_path = os.path.join(processed_dir, "validated.csv")

    # --- Load data ---
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)

    logger.info(f"Preprocessing {len(df)} rows...")

    # --- Separate target and features ---
    target_col = features["target"]
    id_col = features["id_column"]
    numeric_cols = features["numeric"]
    categorical_cols = features["categorical"]

    y = df[target_col].values
    X = df.drop(columns=[target_col, id_col])

    from sklearn.impute import SimpleImputer

    # --- Build preprocessor pipeline ---
    # Add SimpleImputer to prevent catastrophic failure on unexpected NaNs
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]
    )

    # STRICT: handle_unknown='ignore'
    # In production, crashing on a new drug/condition creates downtime.
    # It is usually safer to zero-out the unexpected category's one-hot encodings 
    # than to hard-crash the API. We log these via a separate data drift monitor.
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )

    # --- Split data ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_split, random_state=random_seed
    )

    # --- Fit preprocessor on training data only ---
    try:
        X_train_processed = preprocessor.fit_transform(X_train)
        X_test_processed = preprocessor.transform(X_test)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    # --- Get feature names after transformation ---
    feature_names = (
        numeric_cols
        + list(preprocessor.named_transformers_["cat"]
               .named_steps["onehot"]
               .get_feature_names_out(categorical_cols))
    )

    # --- Save processed data ---
    try:
        pd.DataFrame(X_train_processed, columns=feature_names).to_csv(
            os.path.join(processed_dir, "X_train.csv"), index=False
        )
        pd.DataFrame(X_test_processed, columns=feature_names).to_csv(
            os.path.join(processed_dir, "X_test.csv"), index=False
        )
        pd.DataFrame(y_train, columns=[target_col]).to_csv(
            os.path.join(processed_dir, "y_train.csv"), index=False
        )
        pd.DataFrame(y_test, columns=[target_col]).to_csv(
            os.path.join(processed_dir, "y_test.csv"), index=False
        )

        # --- Save preprocessor ---
        preprocessor_path = os.path.join(processed_dir, "preprocessor.joblib")
        joblib.dump(preprocessor, preprocessor_path)
    except Exception as e:
        logger.error(f"Failed to save processed data/artifacts: {e}")
        sys.exit(1)

    logger.info(f"Preprocessing complete:")
    logger.info(f"  Train set: {X_train_processed.shape[0]} rows, {X_train_processed.shape[1]} features")
    logger.info(f"  Test set: {X_test_processed.shape[0]} rows, {X_test_processed.shape[1]} features")
    logger.info(f"  Feature names: {feature_names}")
    logger.info(f"  Preprocessor saved: {preprocessor_path}")


if __name__ == "__main__":
    main()
