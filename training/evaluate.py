"""
Stage 5: Model Evaluation
--------------------------
Evaluates the trained model on the test set.
Computes RMSE, MAE, R² and writes to metrics/scores.json.
"""

import os
import sys
import json
import yaml
import logging
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("evaluate")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load params.yaml: {e}")
        sys.exit(1)


def main():
    logger.info("Starting evaluation...")
    params = load_params()
    
    try:
        processed_dir = params["data"]["processed_dir"]
        model_dir = params["data"]["model_dir"]
        metrics_dir = params["data"]["metrics_dir"]
    except KeyError as e:
        logger.error(f"Missing param: {e}")
        sys.exit(1)

    # --- Load test data ---
    X_test_path = os.path.join(processed_dir, "X_test.csv")
    y_test_path = os.path.join(processed_dir, "y_test.csv")
    model_path = os.path.join(model_dir, "model.joblib")

    for path in [X_test_path, y_test_path, model_path]:
        if not os.path.exists(path):
            logger.error(f"Required file not found: {path}")
            sys.exit(1)

    try:
        X_test = pd.read_csv(X_test_path)
        y_test = pd.read_csv(y_test_path).values.ravel()
        model = joblib.load(model_path)
    except Exception as e:
        logger.error(f"Failed to load data or model: {e}")
        sys.exit(1)

    # --- Predict ---
    try:
        y_pred = model.predict(X_test)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)

    # --- Compute metrics ---
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "test_samples": int(len(y_test)),
    }

    # --- Save metrics ---
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_path = os.path.join(metrics_dir, "scores.json")
    
    try:
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save metrics: {e}")
        sys.exit(1)

    logger.info(f"Evaluation complete:")
    logger.info(f"  Test samples: {metrics['test_samples']}")
    logger.info(f"  RMSE: {metrics['rmse']}")
    logger.info(f"  MAE:  {metrics['mae']}")
    logger.info(f"  R²:   {metrics['r2']}")
    logger.info(f"  Metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
