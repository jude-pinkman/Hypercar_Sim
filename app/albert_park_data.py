"""
Albert Park Circuit — Sector & Corner Data (2026)
=================================================
Detailed per-sector and per-corner physics data for the
F1 Manager race engine's Albert Park simulation.

Track layout (5.278 km, 16 corners, 2 DRS zones):
  Sector 1 — T1–T6   (start/finish straight + technical first sector)
  Sector 2 — T7–T13  (lake section + DRS zone 1)
  Sector 3 — T14–T16 (back section + DRS zone 2 → finish)

Real 2024 lap record: 1:17.657 (Leclerc) ≈ 77.657 s
Typical race laps:    58

Corner catalogue
----------------
  T1  right  medium  ~75 m/s  braking zone after S/F straight
  T2  left   slow    ~55 m/s  tight entry
  T3  right  medium  ~80 m/s  flows from T2
  T4  right  fast    ~155 m/s light kink
  T5  left   medium  ~95 m/s
  T6  right  slow    ~60 m/s  end of S1 / chicane entry
  T7  left   medium  ~85 m/s
  T8  right  medium  ~90 m/s
  T9  left   slow    ~50 m/s  hairpin
  T10 right  slow    ~55 m/s  hairpin exit
  T11 right  medium  ~110 m/s S2 exit / DRS detection point
  T12 left   fast    ~150 m/s DRS zone 1
  T13 left   medium  ~100 m/s S2/S3 split
  T14 right  fast    ~160 m/s fast right-hander
  T15 right  medium  ~105 m/s penultimate corner
  T16 left   slow    ~70 m/s  final corner → DRS zone 2
"""

from dataclasses import dataclass
from typing import List

# ── speed category weights ────────────────────────────────────────────────────
# Fraction of lap time attributable to each category.
# slow/medium/fast corners have different driver-skill vs car-performance mixes.
CORNER_SPEED_WEIGHT = {
    "slow":   {"driver": 0.70, "car": 0.30},  # slow → mostly driver skill
    "medium": {"driver": 0.50, "car": 0.50},
    "fast":   {"driver": 0.25, "car": 0.75},  # fast → mostly car performance
}


@dataclass
class Corner:
    number: int
    direction: str      # "left" | "right"
    speed_cat: str      # "slow" | "medium" | "fast"
    ref_speed_ms: float # reference cornering speed (m/s)
    sector: int         # 1 | 2 | 3
    drs_detect: bool = False  # DRS detection point immediately before this corner


@dataclass
class Sector:
    number: int         # 1 | 2 | 3
    # Fraction of total lap length in this sector
    length_fraction: float
    # Characteristic of sector — affects overtake probability
    overtake_factor: float
    # DRS zone inside this sector
    has_drs: bool
    # Reference sector time for an elite car on new medium tyres (seconds)
    ref_time_s: float


# ── Albert Park corners ───────────────────────────────────────────────────────

ALBERT_PARK_CORNERS: List[Corner] = [
    Corner(1,  "right",  "medium", 75.0,  1),
    Corner(2,  "left",   "slow",   55.0,  1),
    Corner(3,  "right",  "medium", 80.0,  1),
    Corner(4,  "right",  "fast",   155.0, 1),
    Corner(5,  "left",   "medium", 95.0,  1),
    Corner(6,  "right",  "slow",   60.0,  1),
    Corner(7,  "left",   "medium", 85.0,  2),
    Corner(8,  "right",  "medium", 90.0,  2),
    Corner(9,  "left",   "slow",   50.0,  2, drs_detect=True),  # DRS1 detection
    Corner(10, "right",  "slow",   55.0,  2),
    Corner(11, "right",  "medium", 110.0, 2),
    Corner(12, "left",   "fast",   150.0, 2),
    Corner(13, "left",   "medium", 100.0, 2),
    Corner(14, "right",  "fast",   160.0, 3, drs_detect=True),  # DRS2 detection
    Corner(15, "right",  "medium", 105.0, 3),
    Corner(16, "left",   "slow",   70.0,  3),
]

# ── Albert Park sectors ───────────────────────────────────────────────────────
# Reference times come from Leclerc's 2024 lap (77.657 s) split roughly:
#   S1 ≈ 26.2 s   S2 ≈ 29.8 s   S3 ≈ 21.7 s  (real broadcasts ≈ these)

ALBERT_PARK_SECTORS: List[Sector] = [
    Sector(1, length_fraction=0.337, overtake_factor=0.40, has_drs=False, ref_time_s=26.2),
    Sector(2, length_fraction=0.383, overtake_factor=0.70, has_drs=True,  ref_time_s=29.8),
    Sector(3, length_fraction=0.280, overtake_factor=0.65, has_drs=True,  ref_time_s=21.7),
]

# ── Track grip evolution ─────────────────────────────────────────────────────
# Albert Park is resurfaced regularly but starts with LOW rubber.
# Grip builds through the race as rubber goes down.
# Expressed as lap-time benefit per lap:  lap_time -= GRIP_GAIN_PER_LAP * lap
GRIP_GAIN_PER_LAP   = 0.012   # ~0.7 s total over 58 laps
GRIP_INITIAL_OFFSET = 0.45    # extra penalty on lap 1 (cold/green track)

# ── DRS activation thresholds ────────────────────────────────────────────────
DRS_GAP_THRESHOLD_S = 1.0     # gap ≤ 1 s at detection point → DRS open
DRS_OVERTAKE_BONUS  = 0.14    # added to overtake probability when DRS open
DRS_LAP_TIME_GAIN   = 0.35    # each DRS zone saves ≈ 0.35 s in lap time

# ── Sector time calculation helper ──────────────────────────────────────────

def calc_sector_time(
    sector: Sector,
    base_lap_ref: float,          # driver's reference full-lap time (s)
    driver_skill: float,          # 0-1
    car_performance: float,       # 0-1 (team power/handling avg)
    tyre_age: int,
    tyre_deg_accumulated: float,
    fuel_correction: float,       # negative = lighter car
    weather_delta: float,         # 0 in dry
    grip_correction: float,       # negative = faster grip correction
    sc_active: bool,
    vsc_active: bool,
    drs_active: bool,
    noise_sigma: float = 0.12,
) -> float:
    """
    Compute a single sector time for one car.

    The sector reference time is scaled by the driver's reference lap fraction,
    then adjusted for driver skill, car performance, tyres, fuel, weather, etc.
    """
    import random

    # Base sector time proportional to driver's base lap
    base_ratio   = sector.ref_time_s / sum(s.ref_time_s for s in ALBERT_PARK_SECTORS)
    sector_base  = base_lap_ref * base_ratio

    # Skill weighting per sector type
    # Sector 1 (technical) → driver skill matters more
    # Sector 3 (power lap) → car matters more
    driver_weight = {1: 0.60, 2: 0.52, 3: 0.38}[sector.number]
    car_weight    = 1.0 - driver_weight

    # Skill/performance deltas — each 0.01 of skill ≈ 0.02 s/sector
    skill_delta = (0.92 - driver_skill)   * driver_weight * 4.0
    car_delta   = (0.92 - car_performance) * car_weight   * 3.5

    # Tyre degradation contribution to this sector
    tyre_sector_pen = tyre_deg_accumulated * sector.length_fraction

    # DRS benefit (only if DRS active AND sector has DRS)
    drs_gain = DRS_LAP_TIME_GAIN * sector.length_fraction if (drs_active and sector.has_drs) else 0.0

    # SC/VSC slowdown
    sc_delta = 0.0
    if sc_active:
        sc_delta = 40.0 * sector.length_fraction
    elif vsc_active:
        sc_delta = 15.0 * sector.length_fraction

    # Noise
    noise = random.gauss(0, noise_sigma * sector.length_fraction)

    return max(
        sector_base * 0.96,
        sector_base
        + skill_delta
        + car_delta
        + tyre_sector_pen
        + fuel_correction * sector.length_fraction
        + weather_delta * sector.length_fraction
        + grip_correction * sector.length_fraction
        - drs_gain
        + sc_delta
        + noise
    )
