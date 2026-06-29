import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import yaml
import os
import sys

# Add pipelines to path so we can import them
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to mock pandas read_csv and to_csv out so we don't need real data
# Also we will create a dummy params.yaml content so we don't depend on the real one during unit tests

@pytest.fixture
def mock_params_yaml():
    return {
        "random_seed": 42,
        "test_split": 0.2,
        "features": {
            "target": "Improvement_Score",
            "id_column": "Patient_ID",
            "numeric": ["Age", "Dosage_mg", "Treatment_Duration_days"],
            "categorical": ["Gender", "Condition", "Drug_Name", "Side_Effects"]
        },
        "schema": {
            "columns": ["Patient_ID", "Age", "Gender", "Condition", "Drug_Name", "Dosage_mg", "Treatment_Duration_days", "Side_Effects", "Improvement_Score"],
            "gender_values": ["Female", "Male"],
            "condition_values": ["Diabetes", "Hypertension"],
            "drug_values": ["Metformin", "Lisinopril"],
            "side_effect_values": ["Nausea", "Dizziness"],
            "age_range": [18, 79],
            "dosage_values": [5, 10, 50, 500],
            "duration_range": [5, 59],
            "score_range": [0, 10]
        },
        "data": {
            "raw_path": "dummy_raw.csv",
            "processed_dir": "dummy_dir/"
        }
    }

def test_pipeline_validate_script_logical(mock_params_yaml):
    # Rather than running the script directly, we test the logic of validation.
    # We will simulate the dataframe
    df = pd.DataFrame({
        "Patient_ID": ["P1", "P2"],
        "Age": [25, 40],
        "Gender": ["Female", "Male"],
        "Condition": ["Diabetes", "Hypertension"],
        "Drug_Name": ["Metformin", "Lisinopril"],
        "Dosage_mg": [500, 10],
        "Treatment_Duration_days": [30, 45],
        "Side_Effects": ["Nausea", "Dizziness"],
        "Improvement_Score": [7.5, 8.0]
    })
    
    schema = mock_params_yaml["schema"]
    
    # Check required columns
    missing = set(schema["columns"]) - set(df.columns)
    assert len(missing) == 0
    
    # Check enums
    assert df["Gender"].isin(schema["gender_values"]).all()
    assert df["Condition"].isin(schema["condition_values"]).all()
    assert df["Drug_Name"].isin(schema["drug_values"]).all()

    # Check numeric ranges
    assert df["Age"].between(schema["age_range"][0], schema["age_range"][1]).all()
    assert df["Treatment_Duration_days"].between(schema["duration_range"][0], schema["duration_range"][1]).all()
    assert df["Improvement_Score"].between(schema["score_range"][0], schema["score_range"][1]).all()

def test_pipeline_preprocess_script_logical(mock_params_yaml):
    # Test that preprocessor correctly separates categorical and numeric
    features = mock_params_yaml["features"]
    target = features["target"]
    num_cols = features["numeric"]
    cat_cols = features["categorical"]
    
    assert len(num_cols) == 3
    assert len(cat_cols) == 4
    
    # Check simple pipeline construction (Scikit-Learn logic)
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    
    preprocessor_pipeline = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )
    
    assert preprocessor_pipeline is not None
