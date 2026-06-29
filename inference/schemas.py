"""
Pydantic schemas for API request/response validation.
Shared between training validation and inference.
Enforces exact CSV schema — inference hard-fails on schema violations.
"""

import os
import json
import yaml
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- Load Schema from params.yaml ---
# This ensures API validation is always in sync with the data pipeline config.
PARAMS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "params.yaml"
)

_params: dict[str, Any] = {}
_schema: dict[str, Any] = {}
if os.path.exists(PARAMS_PATH):
    try:
        with open(PARAMS_PATH, "r") as f:
            _params = yaml.safe_load(f) or {}
            _schema = _params.get("schema", {})
    except (yaml.YAMLError, IOError):
        pass

# Load valid combinations extract
COMBOS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "valid_combinations.json"
)

VALID_COMBINATIONS = []
if os.path.exists(COMBOS_PATH):
    try:
        with open(COMBOS_PATH, "r") as f:
            VALID_COMBINATIONS = json.load(f)
    except (json.JSONDecodeError, IOError):
        VALID_COMBINATIONS = []


VALID_GENDERS      = _schema.get("gender_values", []) if _schema else []
VALID_CONDITIONS   = _schema.get("condition_values", []) if _schema else []
VALID_DRUGS        = _schema.get("drug_values", []) if _schema else []
VALID_SIDE_EFFECTS = _schema.get("side_effect_values", []) if _schema else []
VALID_DOSAGES      = [float(v) for v in _schema.get("dosage_values", [])] if _schema else []

AGE_RANGE      = _schema.get("age_range", [0, 100]) if _schema else [0, 100]
DURATION_RANGE = _schema.get("duration_range", [1, 365]) if _schema else [1, 365]


class PredictionRequest(BaseModel):
    """Schema for prediction API request. Matches CSV schema exactly."""

    model_config = ConfigDict(extra="ignore")

    Age: int = Field(
        ...,
        ge=AGE_RANGE[0],
        le=AGE_RANGE[1],
        description=f"Patient age in years ({AGE_RANGE[0]}-{AGE_RANGE[1]})",
    )
    Gender: str = Field(
        ...,
        description="Gender as recorded",
    )
    Condition: str = Field(
        ...,
        description="Medical condition",
    )
    Drug_Name: str = Field(
        ...,
        description="Prescribed drug",
    )
    Dosage_mg: float = Field(
        ...,
        description="Dosage in milligrams",
    )
    Treatment_Duration_days: int = Field(
        ...,
        ge=DURATION_RANGE[0],
        le=DURATION_RANGE[1],
        description=f"Duration of treatment in days ({DURATION_RANGE[0]}-{DURATION_RANGE[1]})",
    )
    Side_Effects: str = Field(
        ...,
        description="Reported side effects",
    )

    @field_validator("Gender")
    @classmethod
    def validate_gender(cls, v):
        if v not in VALID_GENDERS:
            raise ValueError(
                f"Invalid Gender: '{v}'. Must be one of: {VALID_GENDERS}"
            )
        return v

    @field_validator("Condition")
    @classmethod
    def validate_condition(cls, v):
        if v not in VALID_CONDITIONS:
            raise ValueError(
                f"Invalid Condition: '{v}'. Must be one of: {VALID_CONDITIONS}"
            )
        return v

    @field_validator("Drug_Name")
    @classmethod
    def validate_drug(cls, v):
        if v not in VALID_DRUGS:
            raise ValueError(
                f"Invalid Drug_Name: '{v}'. Must be one of: {VALID_DRUGS}"
            )
        return v

    @field_validator("Side_Effects")
    @classmethod
    def validate_side_effects(cls, v):
        if v not in VALID_SIDE_EFFECTS:
            raise ValueError(
                f"Invalid Side_Effects: '{v}'. Must be one of: {VALID_SIDE_EFFECTS}"
            )
        return v

    @field_validator("Dosage_mg")
    @classmethod
    def validate_dosage(cls, v):
        if v not in VALID_DOSAGES:
            raise ValueError(
                f"Invalid Dosage_mg: {v}. Must be one of: {VALID_DOSAGES}"
            )
        return v



class PredictionResponse(BaseModel):
    """Schema for prediction API response."""

    model_config = ConfigDict(protected_namespaces=())

    Improvement_Score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Predicted improvement score (0-10 scale)",
    )
    model_version: str = Field(
        ...,
        description="Model version identifier"
    )
    disclaimer: str = Field(
        default=(
            "This system predicts patient treatment outcome scores to support "
            "clinical research, quality analysis, and exploratory analytics. "
            "It does not provide diagnostic or treatment recommendations."
        ),
        description="Non-clinical disclaimer",
    )


class HealthResponse(BaseModel):
    """Schema for health check response."""

    model_config = ConfigDict(protected_namespaces=())

    status: str        = Field(default="healthy")
    model_loaded: bool = Field(default=False)
    model_version: str = Field(default="unknown")


class DropdownValues(BaseModel):
    """Schema for frontend dropdown population."""

    genders: list[str]      = Field(default_factory=lambda: VALID_GENDERS)
    conditions: list[str]   = Field(default_factory=lambda: VALID_CONDITIONS)
    drugs: list[str]        = Field(default_factory=lambda: VALID_DRUGS)
    side_effects: list[str] = Field(default_factory=lambda: VALID_SIDE_EFFECTS)
    dosages: list[float]    = Field(default_factory=lambda: VALID_DOSAGES)
    valid_combinations: list[dict] = Field(default_factory=lambda: VALID_COMBINATIONS)
