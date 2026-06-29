"""
Model Loader
-------------
Loads model and preprocessor from disk.
Singleton pattern with version tracking.
"""

import os
import hashlib
import joblib
import logging
import pandas as pd
from typing import Any

logger = logging.getLogger(__name__)


class ModelLoader:
    """Singleton model loader with version tracking."""

    _instance = None
    _model: Any = None
    _preprocessor: Any = None
    _model_version: str = "unknown"
    _is_loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._preprocessor = None
            cls._instance._model_version = "unknown"
            cls._instance._is_loaded = False
        return cls._instance

    def load(
        self,
        model_path: str = "models/model.joblib",
        preprocessor_path: str = "data/processed/preprocessor.joblib",
    ):
        """Load model and preprocessor from disk."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(preprocessor_path):
            raise FileNotFoundError(
                f"Preprocessor file not found: {preprocessor_path}"
            )

        self._model = joblib.load(model_path)
        self._preprocessor = joblib.load(preprocessor_path)

        # Generate version hash from model file
        with open(model_path, "rb") as f:
            model_hash = str(hashlib.sha256(f.read()).hexdigest())[:8]
        self._model_version = f"v-{model_hash}"
        self._is_loaded = True

        logger.info(f"Model loaded: version={self._model_version}")
        logger.info(f"  Model path: {model_path}")
        logger.info(f"  Preprocessor path: {preprocessor_path}")

    @property
    def model(self):
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        return self._model

    @property
    def preprocessor(self):
        if not self._is_loaded:
            raise RuntimeError("Preprocessor not loaded. Call load() first.")
        return self._preprocessor

    @property
    def version(self) -> str:
        return self._model_version

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def predict(self, input_data: dict) -> float:
        """
        Run prediction on a single input.
        Input is a dict matching the CSV schema (minus Patient_ID and Improvement_Score).
        Returns predicted Improvement_Score.
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Create DataFrame from input
        df = pd.DataFrame([input_data])

        # Apply preprocessor
        X = self._preprocessor.transform(df)

        # Predict
        prediction = self._model.predict(X)[0]

        # Clamp to valid range
        prediction = max(0.0, min(10.0, float(prediction)))

        return float(f"{prediction:.2f}")
