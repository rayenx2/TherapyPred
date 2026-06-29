import pytest
import pandas as pd
import numpy as np

def test_training_model_instantiation():
    # Test we can instantiate the model based on params
    from sklearn.ensemble import RandomForestRegressor
    
    model_params = {
        "n_estimators": 50,
        "max_depth": 5,
        "min_samples_split": 2,
        "min_samples_leaf": 1
    }
    
    model = RandomForestRegressor(
        n_estimators=model_params["n_estimators"],
        max_depth=model_params["max_depth"],
        min_samples_split=model_params["min_samples_split"],
        min_samples_leaf=model_params["min_samples_leaf"],
        random_state=42
    )
    
    assert model is not None
    assert model.n_estimators == 50

def test_training_fit_predict():
    # Test that a tiny toy dataset can be fit and predicted
    from sklearn.ensemble import RandomForestRegressor
    
    # Dummy data
    X_train = pd.DataFrame({
        "Feature1": np.random.rand(10),
        "Feature2": np.random.rand(10)
    })
    y_train = pd.Series(np.random.rand(10))
    
    X_test = pd.DataFrame({
        "Feature1": np.random.rand(5),
        "Feature2": np.random.rand(5)
    })
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    preds = model.predict(X_test)
    assert len(preds) == 5
    assert not np.isnan(preds).any()
