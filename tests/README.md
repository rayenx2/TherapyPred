# 🧪 Automated Test Suite

<div align="center">

![Testing](https://img.shields.io/badge/Framework-Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-Unit_Tests-green?style=for-the-badge)

**Deterministic unit and integration testing boundaries for the MLOps pipeline and backend services.**

[⬅️ Back to Root](../README.md)

</div>

---

## 1. Executive Overview

### Purpose
The `tests/` module encapsulates all automated testing routines asserting the behavioral correctness of the Inference API, Data Pipelines, and Model Training logic. 

### Business & Technical Problems Solved
- **Business**: Ensures system upgrades (dependency bumps, new features) do not regress established clinical logic or cause silent failures in production inference.
- **Technical**: Provides a mocked execution environment avoiding expensive API calls, heavy disk I/O, or massive RAM consumption during standard CI/CD linting phases.

---

## 2. System Context & Architecture

### Testing Strategy
The test suite utilizes the `pytest` framework, organized by isolation domains:
- **API Tests (`test_inference.py`)**: Focuses on HTTP request/response validation, Pydantic guardrails, and Prometheus metric incrementation using FastAPI's `TestClient`.
- **Pipeline Tests (`test_pipelines.py`)**: Focuses on schema transformations, train/test split consistency, and data validation boundaries using `unittest.mock` to sandbox the environment.
- **Training Tests (`test_training.py`)**: Asserts the Random Forest math logic executes correctly on arbitrary synthetic arrays and outputs `.joblib` objects without encountering `NaN` state errors.

---

## 3. Component-Level Design

### Core Test Files

1. **`tests/test_inference.py`**
   - **Responsibility**: Mocks `ModelLoader` to verify `/predict` endpoint zero-trust inputs. Asserts HTTP 422 Unprocessable Entity responses for clinically invalid combinations (e.g., impossible dosages).
2. **`tests/test_pipelines.py`**
   - **Responsibility**: Validates that incoming CSV columns correctly map to `params.yaml` boundaries. Ensures the `ColumnTransformer` (Scalers/Encoders) correctly instantiates.
3. **`tests/test_training.py`**
   - **Responsibility**: Verifies the Scikit-Learn `.fit()` parameters pass cleanly and that `NaN` predictions are fundamentally impossible under standard configurations.

---

## 4. Execution Flow

Testing is triggered sequentially.
1. `pytest` crawls the `tests/` directory discovering all functions prefixed with `test_*`.
2. Mocking decorators (`@patch`) intercept complex external operations (like loading actual 50MB models).
3. Test matrices execute in-memory across the respective modules (`inference`, `pipelines`, `training`).

---

## 5. Security Architecture

- **Mocked Persistence**: Tests strictly use Python's `unittest.mock.patch` to intercept disk reads (`open()`) and model loads (`joblib.load()`). Actual model files or real sensitive data are never loaded into the testing memory footprint, neutralizing risk if test logs are exposed.

---

## 6. Performance & Scalability

- All tests operate purely in-memory. Execution time for the entire suite is universally under 2.0 seconds locally.

---

## 7. Configuration & Environment Variables

*(Not applicable directly. Tests utilize internal mock data dictionaries rather than resolving `.env` strings).*

---

## 8. Development Guide

### Running Tests Locally

```bash
# Execute the entire suite with verbosity
pytest tests/ -v

# Run a specific domain file
pytest tests/test_inference.py -v

# Run tests and generate a coverage report (requires pytest-cov)
pytest tests/ --cov=./ --cov-report=html
```

---

## 9. Future Improvements

- **End-to-End (E2E) Testing**: Currently missing Browser tests (Playwright/Cypress) to validate the visual rendering on the vanilla JS `frontend/` component.
- **CI/CD Integration**: Hook the test module actively into the GitHub Action pipeline ensuring all PR branches return a green build status before mergeability is allowed.
