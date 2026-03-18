"""
Dataset schema for the race-winner prediction model.

Every row in the training dataset represents ONE driver in ONE race.
With a 22-car grid, each simulated race produces 22 rows — exactly one
has ``won = 1``.

Feature taxonomy
----------------
Driver-level features
    driver_skill          Composite of max_speed + acceleration, normalised
                          to [0, 1] across the field.  Higher = faster.
    wet_skill             How well the driver handles rain relative to their
                          dry pace.  Sampled with per-driver noise so that
                          some drivers are "rain masters".

Car / team-level features
    team_performance      Composite of tyre_grip and drag_coefficient,
                          normalised to [0, 1].  Reflects the constructor
                          package independent of the driver.
    car_max_speed_norm    Normalised top speed of the car (m/s → [0,1]).
    car_acceleration_norm Normalised peak acceleration (m/s² → [0,1]).
    drag_coefficient      Raw drag coefficient retained as a linear feature.
    tyre_grip_base        Base tyre-grip rating before degradation.

Race-context features
    qualifying_position   Grid slot 1–22.  1 = pole.  Strongly correlated
                          with win probability but not deterministic.
    circuit_type          Encoded circuit character:
                            0 = street  (tight, Monaco-like)
                            1 = balanced (mixed, Silverstone-like)
                            2 = power    (high-speed, Monza-like)
    weather_condition     Encoded dominant race weather:
                            0 = dry
                            1 = light_rain
                            2 = heavy_rain
    weather_grip_factor   Numerical track-grip multiplier from WeatherParams,
                          so the model sees a continuous representation of
                          conditions rather than only a category.
    tyre_strategy         Encoded pit strategy:
                            0 = one_stop
                            1 = two_stop
                            2 = aggressive

Interaction / derived features (computed by the pipeline)
    skill_x_quali         driver_skill × (1 - qualifying_position/22)
                          — captures "fast driver starting near the front"
    team_x_weather        team_performance × weather_grip_factor
                          — captures "strong car in adverse conditions"

Target
    won                   1 if this driver finished P1, else 0.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, asdict
from typing import List, Dict, Any, Tuple
import csv
import io


# ---------------------------------------------------------------------------
# Feature names — single source of truth consumed by model + API
# ---------------------------------------------------------------------------

#: Raw features produced by DatasetGenerator (before interaction terms)
RAW_FEATURE_NAMES: List[str] = [
    "driver_skill",
    "wet_skill",
    "team_performance",
    "car_max_speed_norm",
    "car_acceleration_norm",
    "drag_coefficient",
    "tyre_grip_base",
    "qualifying_position",
    "circuit_type",
    "weather_condition",
    "weather_grip_factor",
    "tyre_strategy",
]

#: Interaction terms appended by the feature-engineering step
INTERACTION_FEATURE_NAMES: List[str] = [
    "skill_x_quali",
    "team_x_weather",
]

#: Full feature vector consumed by the model
ALL_FEATURE_NAMES: List[str] = RAW_FEATURE_NAMES + INTERACTION_FEATURE_NAMES

TARGET_NAME: str = "won"

#: Categorical feature ranges used for validation
FEATURE_RANGES: Dict[str, Tuple[float, float]] = {
    "driver_skill":          (0.0, 1.0),
    "wet_skill":             (0.0, 1.0),
    "team_performance":      (0.0, 1.0),
    "car_max_speed_norm":    (0.0, 1.0),
    "car_acceleration_norm": (0.0, 1.0),
    "drag_coefficient":      (0.50, 1.00),
    "tyre_grip_base":        (0.50, 1.00),
    "qualifying_position":   (1.0, 22.0),
    "circuit_type":          (0.0, 2.0),
    "weather_condition":     (0.0, 2.0),
    "weather_grip_factor":   (0.5, 1.0),
    "tyre_strategy":         (0.0, 2.0),
}

# Circuit type encoding
CIRCUIT_TYPE_ENCODING: Dict[str, int] = {
    "street":   0,
    "balanced": 1,
    "power":    2,
}

# Weather encoding
WEATHER_ENCODING: Dict[str, int] = {
    "dry":        0,
    "light_rain": 1,
    "heavy_rain": 2,
}

# Strategy encoding
STRATEGY_ENCODING: Dict[str, int] = {
    "one_stop":   0,
    "two_stop":   1,
    "aggressive": 2,
}


# ---------------------------------------------------------------------------
# RaceRecord — one row in the dataset
# ---------------------------------------------------------------------------

@dataclass
class RaceRecord:
    """
    One driver in one simulated race.

    A full race with 22 drivers produces 22 RaceRecord rows.
    Exactly one row per race has ``won = 1``.
    """
    # ── identifiers (not used as model features) ──────────────────────
    race_id:            int     # unique integer per simulated race
    driver_name:        str
    team:               str

    # ── raw features ──────────────────────────────────────────────────
    driver_skill:          float   # [0, 1]
    wet_skill:             float   # [0, 1]
    team_performance:      float   # [0, 1]
    car_max_speed_norm:    float   # [0, 1]
    car_acceleration_norm: float   # [0, 1]
    drag_coefficient:      float
    tyre_grip_base:        float
    qualifying_position:   int     # 1 – 22
    circuit_type:          int     # 0=street  1=balanced  2=power
    weather_condition:     int     # 0=dry  1=light_rain  2=heavy_rain
    weather_grip_factor:   float   # from WeatherParams
    tyre_strategy:         int     # 0=one_stop  1=two_stop  2=aggressive

    # ── interaction features ──────────────────────────────────────────
    skill_x_quali:    float   # driver_skill × (1 - qualifying_position/22)
    team_x_weather:   float   # team_performance × weather_grip_factor

    # ── target ────────────────────────────────────────────────────────
    won: int                  # 1 = winner, 0 = did not win

    # ── simulation truth (kept for analysis, excluded from features) ──
    finish_position:  int     # 1–22 actual finishing position
    finish_time_s:    float   # race clock at finish

    def to_feature_dict(self) -> Dict[str, float]:
        """Return only the model input features as a flat dict."""
        return {k: getattr(self, k) for k in ALL_FEATURE_NAMES}

    def to_csv_row(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def csv_fieldnames(cls) -> List[str]:
        return [f.name for f in fields(cls)]


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def records_to_csv(records: List[RaceRecord], filepath: str) -> None:
    """Write a list of RaceRecord objects to a CSV file."""
    if not records:
        return
    with open(filepath, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RaceRecord.csv_fieldnames())
        writer.writeheader()
        for rec in records:
            writer.writerow(rec.to_csv_row())


def csv_to_records(filepath: str) -> List[RaceRecord]:
    """Load RaceRecord objects from a CSV file."""
    records: List[RaceRecord] = []
    with open(filepath, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            records.append(RaceRecord(
                race_id            = int(row["race_id"]),
                driver_name        = row["driver_name"],
                team               = row["team"],
                driver_skill       = float(row["driver_skill"]),
                wet_skill          = float(row["wet_skill"]),
                team_performance   = float(row["team_performance"]),
                car_max_speed_norm = float(row["car_max_speed_norm"]),
                car_acceleration_norm = float(row["car_acceleration_norm"]),
                drag_coefficient   = float(row["drag_coefficient"]),
                tyre_grip_base     = float(row["tyre_grip_base"]),
                qualifying_position = int(row["qualifying_position"]),
                circuit_type       = int(row["circuit_type"]),
                weather_condition  = int(row["weather_condition"]),
                weather_grip_factor = float(row["weather_grip_factor"]),
                tyre_strategy      = int(row["tyre_strategy"]),
                skill_x_quali      = float(row["skill_x_quali"]),
                team_x_weather     = float(row["team_x_weather"]),
                won                = int(row["won"]),
                finish_position    = int(row["finish_position"]),
                finish_time_s      = float(row["finish_time_s"]),
            ))
    return records
