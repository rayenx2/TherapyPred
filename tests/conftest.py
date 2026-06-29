import os

# Set dummy model paths before any imports so the loaders don't crash
os.environ["MODEL_PATH"] = "dummy_model.joblib"
os.environ["PREPROCESSOR_PATH"] = "dummy_preprocessor.joblib"
