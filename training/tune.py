"""
Hyperparameter Tuning
---------------------
Grid search over RandomForest hyperparameters.
Reports best parameters and cross-validation scores.
This is run manually, not as part of the DVC pipeline.

Usage:
    python training/tune.py
"""

import os
import sys
import yaml
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer, mean_squared_error

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("tune")


def load_params():
    """Load pipeline parameters from params.yaml."""
    try:
        with open("params.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("params.yaml not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing params.yaml: {e}")
        sys.exit(1)


def rmse_scorer(y_true, y_pred):
    """Custom RMSE scorer for GridSearchCV.
    Returns negative RMSE so GridSearchCV can maximize the score."""
    return -np.sqrt(mean_squared_error(y_true, y_pred))


def main():
    params = load_params()

    try:
        processed_dir = params["data"]["processed_dir"]
        random_seed = params["random_seed"]
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

    logger.info(f"Tuning on {X_train.shape[0]} samples, {X_train.shape[1]} features...")

    # Prevent CPU starvation in containerized environments.
    n_jobs = int(os.environ.get("N_JOBS", 1))
    logger.info(f"Using n_jobs={n_jobs}")

    # --- Define parameter grids ---
    rf_param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [10, 15, 20, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }

    scorer = make_scorer(rmse_scorer, greater_is_better=True)

    # --- RandomForest Grid Search ---
    logger.info("--- RandomForest Grid Search ---")
    rf = RandomForestRegressor(random_state=random_seed, n_jobs=n_jobs)
    rf_search = GridSearchCV(
        rf, rf_param_grid, cv=5, scoring=scorer, n_jobs=n_jobs, verbose=1
    )

    try:
        rf_search.fit(X_train, y_train)
    except Exception as e:
        logger.error(f"RandomForest grid search failed: {e}")
        sys.exit(1)

    logger.info(f"Best RF RMSE: {-rf_search.best_score_:.4f}")
    logger.info(f"Best RF params: {rf_search.best_params_}")
    logger.info("Update params.yaml with new values.")


if __name__ == "__main__":
    main()
