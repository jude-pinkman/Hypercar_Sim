"""
schemas_api.py — Pydantic request/response models for the ML prediction API.

This module intentionally depends only on ``pydantic``, NOT on ``fastapi``,
so it can be imported in tests, CLI tools, and client code without a running
web server.

``predict.py`` imports everything from here; tests do the same.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# /api/ml/predict  — pre-computed feature vector path
# ---------------------------------------------------------------------------

class DriverFeatures(BaseModel):
    """
    Feature vector for one driver in the upcoming race.

    All normalised features (``driver_skill``, ``team_performance``, etc.)
    must be in **[0, 1]** and normalised relative to the full grid for this
    race — not to any historical baseline.

    Categorical features are integer-encoded:

    ================  ===  ============
    Field             Val  Meaning
    ================  ===  ============
    circuit_type      0    street (Monaco-like)
    circuit_type      1    balanced (Silverstone-like)
    circuit_type      2    power (Monza-like)
    weather_condition 0    dry
    weather_condition 1    light_rain
    weather_condition 2    heavy_rain
    tyre_strategy     0    one_stop
    tyre_strategy     1    two_stop
    tyre_strategy     2    aggressive
    ================  ===  ============
    """

    driver_name: str = Field(..., description="Full driver name")
    team:        str = Field(..., description="Constructor name")

    # ── driver-level ──────────────────────────────────────────────────
    driver_skill:          float = Field(..., ge=0.0, le=1.0,
        description="Composite speed+accel, normalised [0,1]")
    wet_skill:             float = Field(..., ge=0.0, le=1.0,
        description="Wet-weather relative performance [0,1]")

    # ── car / team-level ──────────────────────────────────────────────
    team_performance:      float = Field(..., ge=0.0, le=1.0,
        description="Constructor package quality, normalised [0,1]")
    car_max_speed_norm:    float = Field(..., ge=0.0, le=1.0,
        description="Top speed normalised across grid [0,1]")
    car_acceleration_norm: float = Field(..., ge=0.0, le=1.0,
        description="Peak acceleration normalised across grid [0,1]")
    drag_coefficient:      float = Field(..., ge=0.50, le=1.00,
        description="Raw drag coefficient")
    tyre_grip_base:        float = Field(..., ge=0.50, le=1.00,
        description="Base tyre grip before degradation")

    # ── race context ──────────────────────────────────────────────────
    qualifying_position:   int   = Field(..., ge=1, le=22,
        description="Grid slot (1 = pole)")
    circuit_type:          int   = Field(..., ge=0, le=2,
        description="0=street  1=balanced  2=power")
    weather_condition:     int   = Field(..., ge=0, le=2,
        description="0=dry  1=light_rain  2=heavy_rain")
    weather_grip_factor:   float = Field(..., ge=0.50, le=1.00,
        description="Numerical track-grip multiplier from WeatherParams")
    tyre_strategy:         int   = Field(..., ge=0, le=2,
        description="0=one_stop  1=two_stop  2=aggressive")


class PredictRequest(BaseModel):
    """Full race grid for the /predict endpoint — 1 to 22 drivers."""
    drivers: List[DriverFeatures] = Field(
        ...,
        min_length=1,
        max_length=22,
        description="List of driver feature vectors (1–22)",
    )


class DriverPrediction(BaseModel):
    """Win-probability prediction for one driver."""
    rank:     int
    driver:   str
    team:     str
    win_prob: float
    features: Dict[str, float]


class PredictResponse(BaseModel):
    """Ranked predictions for a full race grid."""
    model_config = {"protected_namespaces": ()}
    
    rankings:   List[DriverPrediction]
    model_name: str
    model_auc:  Optional[float]
    n_drivers:  int


# ---------------------------------------------------------------------------
# /api/ml/predict-from-simulation  — raw car-spec path
# ---------------------------------------------------------------------------

class SimDriverSpec(BaseModel):
    """
    Minimal car specification for the simulation-based prediction endpoint.

    Feature normalisation is computed server-side across the submitted grid,
    so raw physics values (``max_speed`` in m/s, etc.) are accepted directly.
    """
    driver_name:         str
    team:                str
    max_speed:           float = Field(..., gt=0,
        description="Top speed in m/s")
    acceleration:        float = Field(..., gt=0,
        description="Peak acceleration in m/s²")
    tyre_grip:           float = Field(..., ge=0.5, le=1.0,
        description="Base tyre grip coefficient")
    drag_coefficient:    float = Field(..., ge=0.5, le=1.0,
        description="Aerodynamic drag coefficient")
    qualifying_position: int   = Field(..., ge=1, le=22,
        description="Grid slot (1 = pole)")
    tyre_strategy:       str   = Field(
        "two_stop",
        pattern="^(one_stop|two_stop|aggressive)$",
        description="Pit strategy: one_stop | two_stop | aggressive",
    )
    wet_skill:           float = Field(0.80, ge=0.0, le=1.0,
        description="Wet-weather relative performance [0,1]")


class SimPredictRequest(BaseModel):
    """Race grid in raw simulator terms for /predict-from-simulation."""
    drivers:           List[SimDriverSpec] = Field(
        ..., min_length=1, max_length=22
    )
    circuit_type:      str = Field(
        "balanced",
        pattern="^(street|balanced|power)$",
        description="street | balanced | power",
    )
    weather_condition: str = Field(
        "dry",
        pattern="^(dry|light_rain|heavy_rain)$",
        description="dry | light_rain | heavy_rain",
    )
