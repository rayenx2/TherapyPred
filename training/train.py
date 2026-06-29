"""
Stage 4: Model Training
------------------------
Trains a RandomForestRegressor on preprocessed data.
Uses fixed random seed for reproducibility.
Saves model artifact and logs feature importances.
"""

import os
import sys
import yaml
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("train")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load params.yaml: {e}")
        sys.exit(1)


def main():
    logger.info("Starting model training...")
    params = load_params()
    
    try:
        processed_dir = params["data"]["processed_dir"]
        model_dir = params["data"]["model_dir"]
        random_seed = params["random_seed"]
        model_params = params["model"]
    except KeyError as e:
        logger.error(f"Missing param: {e}")
        sys.exit(1)

    # --- Load training data ---
    X_train_path = os.path.join(processed_dir, "X_train.csv")
    y_train_path = os.path.join(processed_dir, "y_train.csv")

    if not os.path.exists(X_train_path) or not os.path.exists(y_train_path):
        logger.error("Training data not found. Run preprocessing first.")
        sys.exit(1)

    try:
        X_train = pd.read_csv(X_train_path)
        y_train = pd.read_csv(y_train_path).values.ravel()
    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        sys.exit(1)

    logger.info(f"Training on {X_train.shape[0]} samples, {X_train.shape[1]} features...")

    # --- Train model ---
    try:
        # STRICT: Resource Safety.
        # Prevent CPU starvation in containerized environments.
        # Default to 1 if not specified. k8s/docker can override via env var.
        n_jobs = int(os.environ.get("N_JOBS", 1))

        logger.info(f"Training RandomForestRegressor (n_jobs={n_jobs})...")
        model = RandomForestRegressor(
            n_estimators=params["model"]["n_estimators"],
            max_depth=params["model"]["max_depth"],
            min_samples_split=params["model"]["min_samples_split"],
            min_samples_leaf=params["model"]["min_samples_leaf"],
            random_state=params["random_seed"],
            n_jobs=n_jobs,
        )

        model.fit(X_train, y_train)
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        sys.exit(1)

    # --- Log feature importances ---
    feature_names = list(X_train.columns)
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]

    logger.info("Top 10 Feature Importances:")
    for i in range(min(10, len(sorted_idx))):
        idx = sorted_idx[i]
        logger.info(f"  {feature_names[idx]}: {importances[idx]:.4f}")

    # --- Save model ---
    try:
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "model.joblib")
        joblib.dump(model, model_path)
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        sys.exit(1)

    logger.info(f"Training complete:")
    logger.info(f"  Model: RandomForestRegressor")
    logger.info(f"  n_estimators: {model_params['n_estimators']}")
    logger.info(f"  max_depth: {model_params['max_depth']}")
    logger.info(f"  Model saved: {model_path}")


if __name__ == "__main__":
    main()
