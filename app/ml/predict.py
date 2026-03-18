"""
predict.py — FastAPI router for race-winner prediction.

Registers two endpoints onto the existing ``app`` in main.py:

    POST /api/ml/predict
        Accept a race grid (1–22 drivers with all required features),
        return win-probability rankings.

    GET  /api/ml/model-info
        Return training metadata (version, AUC, features, etc.)

    POST /api/ml/predict-from-simulation
        Accept RaceSimulator parameters, build RaceRecord objects
        internally, and return ranked predictions.  Useful for the
        frontend: callers need not pre-compute normalised features.

Model loading is lazy (loaded once on first request, cached globally).
If the model artefacts are absent the endpoints return HTTP 503 with
a clear message.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.ml.schema import (
    RaceRecord,
    ALL_FEATURE_NAMES,
    FEATURE_RANGES,
    CIRCUIT_TYPE_ENCODING,
    WEATHER_ENCODING,
    STRATEGY_ENCODING,
)
from app.ml.schemas_api import (
    DriverFeatures,
    PredictRequest,
    DriverPrediction,
    PredictResponse,
    SimDriverSpec,
    SimPredictRequest,
)

# ---------------------------------------------------------------------------
# Lazy model cache
# ---------------------------------------------------------------------------

_predictor = None   # loaded on first request


def _get_predictor():
    global _predictor
    if _predictor is not None:
        return _predictor
    from app.ml.model import WinnerPredictor
    if not WinnerPredictor.is_trained():
        raise HTTPException(
            status_code=503,
            detail=(
                "Model artefacts not found.  "
                "Run: python -m app.ml.train --races 200"
            ),
        )
    _predictor = WinnerPredictor.load()
    return _predictor


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/ml", tags=["ML Prediction"])


@router.get("/model-info", summary="Return training metadata for the loaded model")
async def model_info() -> Dict[str, Any]:
    """
    Returns metadata about the currently loaded model:
    training date, dataset size, CV ROC-AUC, Brier score,
    top-1 accuracy, and the list of input features.
    """
    predictor = _get_predictor()
    if predictor.meta is None:
        raise HTTPException(status_code=404, detail="Model metadata not found")
    return predictor.meta.to_dict()


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict race winner from pre-computed driver features",
)
async def predict(request: PredictRequest) -> PredictResponse:
    """
    Accepts a full race grid (up to 22 drivers) with pre-computed
    normalised features and returns win-probability rankings.

    All ``*_norm`` features must be normalised relative to the **full
    grid in this race** (not to historical values).  The easiest way
    is to use ``/api/ml/predict-from-simulation`` which does this
    automatically.
    """
    predictor = _get_predictor()

    # Build dummy RaceRecord objects (race_id / finish fields not used)
    records: List[RaceRecord] = []
    for d in request.drivers:
        skill_x_quali  = d.driver_skill * (1.0 - d.qualifying_position / 22.0)
        from app.weather import WEATHER_PARAMS, WeatherCondition
        cond_map = {0: WeatherCondition.DRY,
                    1: WeatherCondition.LIGHT_RAIN,
                    2: WeatherCondition.HEAVY_RAIN}
        grip = WEATHER_PARAMS[cond_map[d.weather_condition]].track_grip_factor
        team_x_weather = d.team_performance * grip

        records.append(RaceRecord(
            race_id               = 0,
            driver_name           = d.driver_name,
            team                  = d.team,
            driver_skill          = d.driver_skill,
            wet_skill             = d.wet_skill,
            team_performance      = d.team_performance,
            car_max_speed_norm    = d.car_max_speed_norm,
            car_acceleration_norm = d.car_acceleration_norm,
            drag_coefficient      = d.drag_coefficient,
            tyre_grip_base        = d.tyre_grip_base,
            qualifying_position   = d.qualifying_position,
            circuit_type          = d.circuit_type,
            weather_condition     = d.weather_condition,
            weather_grip_factor   = d.weather_grip_factor,
            tyre_strategy         = d.tyre_strategy,
            skill_x_quali         = skill_x_quali,
            team_x_weather        = team_x_weather,
            won                   = 0,   # unknown at prediction time
            finish_position       = 0,
            finish_time_s         = 0.0,
        ))

    rankings_raw = predictor.rank_drivers(records)
    rankings = [
        DriverPrediction(
            rank=e["rank"],
            driver=e["driver"],
            team=e["team"],
            win_prob=e["win_prob"],
            features=e["features"],
        )
        for e in rankings_raw
    ]

    return PredictResponse(
        rankings   = rankings,
        model_name = predictor.meta.best_model if predictor.meta else "unknown",
        model_auc  = predictor.meta.cv_roc_auc if predictor.meta else None,
        n_drivers  = len(records),
    )


@router.post(
    "/predict-from-simulation",
    response_model=PredictResponse,
    summary="Predict winner from raw car specs (normalisation done server-side)",
)
async def predict_from_simulation(request: SimPredictRequest) -> PredictResponse:
    """
    Accepts raw car specifications (max_speed, acceleration, tyre_grip, etc.)
    and returns win-probability rankings.

    Feature normalisation is handled server-side by scaling values across
    the submitted grid, so callers do not need to pre-process features.

    This is the recommended endpoint for frontend/integration use.
    """
    predictor = _get_predictor()

    drivers = request.drivers
    n = len(drivers)

    # ── normalise across submitted grid ──────────────────────────────
    from app.ml.dataset import _normalise, _driver_skill_raw, _team_performance_raw

    specs = [
        {
            "driver_name":     d.driver_name,
            "team":            d.team,
            "max_speed":       d.max_speed,
            "acceleration":    d.acceleration,
            "tyre_grip":       d.tyre_grip,
            "drag_coefficient": d.drag_coefficient,
        }
        for d in drivers
    ]

    skill_raws = [_driver_skill_raw(s) for s in specs]
    team_raws  = [_team_performance_raw(s) for s in specs]
    speed_raws = [s["max_speed"] for s in specs]
    accel_raws = [s["acceleration"] for s in specs]

    skill_norm  = _normalise(skill_raws)
    team_norm   = _normalise(team_raws)
    speed_norm  = _normalise(speed_raws)
    accel_norm  = _normalise(accel_raws)

    circ_enc    = CIRCUIT_TYPE_ENCODING[request.circuit_type]
    weather_enc = WEATHER_ENCODING[request.weather_condition]

    from app.weather import WEATHER_PARAMS, WeatherCondition
    cond_obj = WeatherCondition(request.weather_condition)
    weather_grip = WEATHER_PARAMS[cond_obj].track_grip_factor

    records: List[RaceRecord] = []
    for i, d in enumerate(drivers):
        strat_enc      = STRATEGY_ENCODING[d.tyre_strategy]
        skill_x_quali  = skill_norm[i] * (1.0 - d.qualifying_position / n)
        team_x_weather = team_norm[i] * weather_grip

        records.append(RaceRecord(
            race_id               = 0,
            driver_name           = d.driver_name,
            team                  = d.team,
            driver_skill          = round(skill_norm[i], 6),
            wet_skill             = d.wet_skill,
            team_performance      = round(team_norm[i], 6),
            car_max_speed_norm    = round(speed_norm[i], 6),
            car_acceleration_norm = round(accel_norm[i], 6),
            drag_coefficient      = d.drag_coefficient,
            tyre_grip_base        = d.tyre_grip,
            qualifying_position   = d.qualifying_position,
            circuit_type          = circ_enc,
            weather_condition     = weather_enc,
            weather_grip_factor   = round(weather_grip, 4),
            tyre_strategy         = strat_enc,
            skill_x_quali         = round(skill_x_quali, 6),
            team_x_weather        = round(team_x_weather, 6),
            won                   = 0,
            finish_position       = 0,
            finish_time_s         = 0.0,
        ))

    rankings_raw = predictor.rank_drivers(records)
    rankings = [
        DriverPrediction(
            rank=e["rank"],
            driver=e["driver"],
            team=e["team"],
            win_prob=e["win_prob"],
            features=e["features"],
        )
        for e in rankings_raw
    ]

    return PredictResponse(
        rankings   = rankings,
        model_name = predictor.meta.best_model if predictor.meta else "unknown",
        model_auc  = predictor.meta.cv_roc_auc if predictor.meta else None,
        n_drivers  = len(records),
    )
