import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock ModelLoader before importing app
with patch('inference.model_loader.ModelLoader.load') as mock_load:
    # Set the load to succeed
    mock_load.return_value = None
    
    # Import app
    from inference.app import app
    from inference.app import model_loader
    
    # We must patch the is_loaded property and version on the singleton
    model_loader._is_loaded = True
    model_loader._model_version = "v-m0ck3d"
    
    # We patch predict directly on the singleton
    model_loader.predict = MagicMock(return_value=7.5)

client = TestClient(app, base_url="http://localhost")

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "api_request_total" in response.text

def test_predict_endpoint_valid():
    payload = {
        "Patient_ID": "P1000",
        "Age": 55,
        "Gender": "Female",
        "Condition": "Diabetes",
        "Drug_Name": "Metformin",
        "Dosage_mg": 500,
        "Treatment_Duration_days": 30,
        "Side_Effects": "Nausea"
    }

    response = client.post("/predict", json=payload)
    
    assert response.status_code == 200
    assert "Improvement_Score" in response.json()
    assert response.json()["Improvement_Score"] == 7.5

def test_predict_endpoint_invalid_schema():
    payload = {
        "Patient_ID": "P1000",
        "Age": 15, # Invalid age (<18)
        "Gender": "Unknown", # Invalid enum
        "Condition": "Diabetes",
        "Drug_Name": "Metformin",
        "Dosage_mg": 500,
        "Treatment_Duration_days": 30,
        "Side_Effects": "Nausea"
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 422 # Unprocessable Entity validation error

def test_dropdown_values_endpoint():
    response = client.get("/dropdown-values")
    assert response.status_code == 200
