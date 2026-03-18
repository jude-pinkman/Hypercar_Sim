"""
DatasetGenerator — produces ground-truth training data by running
RaceSimulator with varied grids, circuits, and weather conditions.

Each call to ``generate(n_races)`` runs n_races simulations and returns
a flat list of RaceRecord objects (22 rows per race).

Randomisation axes
------------------
* qualifying_position  — shuffled each race; top-tier cars cluster near front
                         but a noisy draw is used so the model cannot simply
                         learn "pole wins"
* circuit_type         — cycled across street / balanced / power
* weather              — sampled from WeatherSystem.random_race() so ~40 % of
                         races have changing conditions
* tyre_strategy        — each car is randomly assigned ONE_STOP / TWO_STOP /
                         AGGRESSIVE with realistic probabilities
* wet_skill            — per-driver noise factor so rain reshuffles the field

All heavy simulation is done via the real RaceSimulator so the labels are
fully physics-grounded.
"""

from __future__ import annotations

import random
import time
from typing import List, Optional

from app.race_simulator import RaceSimulator, create_f1_grid
from app.pit_stop import RaceStrategy
from app.weather import WeatherSystem, WeatherCondition, WEATHER_PARAMS
from app.ml.schema import (
    RaceRecord,
    records_to_csv,
    csv_to_records,
    CIRCUIT_TYPE_ENCODING,
    WEATHER_ENCODING,
    STRATEGY_ENCODING,
)


# ---------------------------------------------------------------------------
# Driver / team static metadata (constant across races)
# ---------------------------------------------------------------------------

# Wet-skill ratings: some drivers genuinely handle rain better.
# Scale 0–1 (higher = stronger relative improvement in wet).
WET_SKILL_BASE: dict = {
    "Max Verstappen":   0.95,
    "Sergio Perez":     0.82,
    "Charles Leclerc":  0.85,
    "Carlos Sainz":     0.80,
    "Lewis Hamilton":   0.92,
    "George Russell":   0.84,
    "Lando Norris":     0.87,
    "Oscar Piastri":    0.80,
    "Fernando Alonso":  0.90,
    "Lance Stroll":     0.72,
    "Pierre Gasly":     0.78,
    "Esteban Ocon":     0.75,
    "Alex Albon":       0.76,
    "Logan Sargeant":   0.65,
    "Valtteri Bottas":  0.80,
    "Zhou Guanyu":      0.72,
    "Nico Hulkenberg":  0.75,
    "Kevin Magnussen":  0.74,
    "Yuki Tsunoda":     0.73,
    "Daniel Ricciardo": 0.79,
    "Liam Lawson":      0.71,
    "Ayumu Iwasa":      0.70,
}

# Circuit types cycled deterministically so each type appears equally
_CIRCUIT_CYCLE = ["street", "balanced", "power"]

# Strategy sampling weights: two_stop most common, aggressive rarest
_STRATEGY_WEIGHTS = {
    RaceStrategy.ONE_STOP:   0.30,
    RaceStrategy.TWO_STOP:   0.50,
    RaceStrategy.AGGRESSIVE: 0.20,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise(values: List[float]) -> List[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _driver_skill_raw(spec: dict) -> float:
    """Composite of max_speed + acceleration as a single float."""
    return spec["max_speed"] * 0.6 + spec["acceleration"] * 0.4


def _team_performance_raw(spec: dict) -> float:
    """Composite of tyre_grip (higher better) and drag_coefficient (lower better)."""
    return spec["tyre_grip"] * 0.7 + (1.0 - spec["drag_coefficient"]) * 0.3


def _pick_qualifying_order(n: int, rng: random.Random) -> List[int]:
    """
    Return qualifying positions 1..n for n drivers with realistic noise.

    Better drivers (lower index = higher base speed) cluster near the
    front but are occasionally shuffled by Q3 noise.
    """
    base = list(range(n))
    # Add Gaussian noise scaled to ~2 positions
    noisy = [(i + rng.gauss(0, 2.5), i) for i in base]
    noisy.sort(key=lambda x: x[0])
    positions = [0] * n
    for pos, (_, orig_idx) in enumerate(noisy):
        positions[orig_idx] = pos + 1   # 1-indexed
    return positions


def _sample_strategy(rng: random.Random) -> RaceStrategy:
    choices  = list(_STRATEGY_WEIGHTS.keys())
    weights  = list(_STRATEGY_WEIGHTS.values())
    return rng.choices(choices, weights=weights, k=1)[0]


def _circuit_type_for_race(race_idx: int) -> str:
    return _CIRCUIT_CYCLE[race_idx % len(_CIRCUIT_CYCLE)]


def _build_weather(total_laps: int, rng: random.Random) -> WeatherSystem:
    return WeatherSystem.random_race(
        total_laps=total_laps,
        wet_probability=0.40,
        seed=rng.randint(0, 2**31),
    )


def _dominant_weather(ws: WeatherSystem, total_laps: int) -> WeatherCondition:
    """
    Find the condition that covers the most laps.
    Used to encode a single weather feature per race.
    """
    # Step through all laps and count
    counts: dict = {c: 0 for c in WeatherCondition}
    probe = WeatherSystem(total_laps, ws.condition)
    for ev in ws._events:
        probe.add_event(ev)
    for lap in range(1, total_laps + 1):
        probe.advance(lap)
        counts[probe.condition] += 1
    return max(counts, key=lambda c: counts[c])


# ---------------------------------------------------------------------------
# DatasetGenerator
# ---------------------------------------------------------------------------

class DatasetGenerator:
    """
    Generates training data by running the full race simulation.

    Parameters
    ----------
    total_laps:     Race length (shorter = faster generation).
    timestep:       Simulation timestep (larger = faster, less accurate).
    seed:           Random seed for full reproducibility.
    verbose:        Print progress every ``verbose_every`` races.
    verbose_every:  Frequency of progress prints.
    """

    def __init__(
        self,
        total_laps: int = 20,
        timestep: float = 1.0,
        seed: int = 42,
        verbose: bool = True,
        verbose_every: int = 10,
    ):
        self.total_laps   = total_laps
        self.timestep     = timestep
        self.seed         = seed
        self.verbose      = verbose
        self.verbose_every = verbose_every

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, n_races: int = 200) -> List[RaceRecord]:
        """
        Run ``n_races`` simulations and return all RaceRecord rows.

        With 22 drivers per race this yields ``n_races × 22`` rows.
        """
        rng     = random.Random(self.seed)
        records: List[RaceRecord] = []
        grid    = create_f1_grid()   # canonical 22-car specs

        # Pre-compute normalisation denominators across the whole grid
        skill_raws = [_driver_skill_raw(s) for s in grid]
        team_raws  = [_team_performance_raw(s) for s in grid]
        speed_raws = [s["max_speed"] for s in grid]
        accel_raws = [s["acceleration"] for s in grid]

        skill_norm  = _normalise(skill_raws)
        team_norm   = _normalise(team_raws)
        speed_norm  = _normalise(speed_raws)
        accel_norm  = _normalise(accel_raws)

        t0 = time.time()
        for race_idx in range(n_races):
            if self.verbose and race_idx % self.verbose_every == 0:
                elapsed = time.time() - t0
                print(f"  Race {race_idx:>4}/{n_races}  "
                      f"({elapsed:.1f}s elapsed, "
                      f"{len(records)} rows so far)")

            race_records = self._run_one_race(
                race_idx  = race_idx,
                grid      = grid,
                rng       = rng,
                skill_norm  = skill_norm,
                team_norm   = team_norm,
                speed_norm  = speed_norm,
                accel_norm  = accel_norm,
            )
            records.extend(race_records)

        if self.verbose:
            print(f"  Done — {n_races} races, {len(records)} rows "
                  f"in {time.time() - t0:.1f}s")
        return records

    def generate_and_save(self, n_races: int, filepath: str) -> List[RaceRecord]:
        """Generate and immediately persist to CSV."""
        records = self.generate(n_races)
        records_to_csv(records, filepath)
        if self.verbose:
            print(f"  Saved {len(records)} rows to {filepath}")
        return records

    # ------------------------------------------------------------------
    # Internal: single race
    # ------------------------------------------------------------------

    def _run_one_race(
        self,
        race_idx:   int,
        grid:       list,
        rng:        random.Random,
        skill_norm:  List[float],
        team_norm:   List[float],
        speed_norm:  List[float],
        accel_norm:  List[float],
    ) -> List[RaceRecord]:

        n          = len(grid)
        circuit_t  = _circuit_type_for_race(race_idx)
        weather_ws = _build_weather(self.total_laps, rng)
        strategies = [_sample_strategy(rng) for _ in range(n)]
        quali_pos  = _pick_qualifying_order(n, rng)

        # Dominant weather for encoding
        dom_cond     = _dominant_weather(weather_ws, self.total_laps)
        weather_enc  = WEATHER_ENCODING[dom_cond.value]
        weather_grip = WEATHER_PARAMS[dom_cond].track_grip_factor

        # Apply wet-skill as a max_speed perturbation when it rains
        # (modifies a local copy only)
        wet_factor = 1.0
        if dom_cond != WeatherCondition.DRY:
            wet_factor = 0.95 if dom_cond == WeatherCondition.LIGHT_RAIN else 0.88

        # Build simulator
        sim = RaceSimulator(
            circuit_length       = self._circuit_length(circuit_t),
            total_laps           = self.total_laps,
            timestep             = self.timestep,
            enable_tyre_degradation = True,
            default_strategy     = RaceStrategy.TWO_STOP,
            weather              = weather_ws,
        )

        driver_wet_skills: List[float] = []
        for i, spec in enumerate(grid):
            base_wet = WET_SKILL_BASE.get(spec["driver_name"], 0.75)
            # Add small race-to-race noise
            wet_s = max(0.0, min(1.0, base_wet + rng.gauss(0, 0.03)))
            driver_wet_skills.append(wet_s)

            # Modify speed slightly by wet skill relative to average wet skill
            avg_wet = sum(WET_SKILL_BASE.values()) / len(WET_SKILL_BASE)
            wet_adj = 1.0 + (wet_s - avg_wet) * (1.0 - wet_factor) * 0.5
            effective_speed = spec["max_speed"] * wet_adj

            sim.add_car(
                driver_name     = spec["driver_name"],
                team            = spec["team"],
                max_speed       = effective_speed,
                acceleration    = spec["acceleration"],
                tyre_grip       = spec["tyre_grip"],
                drag_coefficient = spec["drag_coefficient"],
                strategy        = strategies[i],
            )

        # Run (silent)
        results = sim.run_simulation(verbose=False)

        # Build a position lookup: driver → finish_position
        pos_lookup: dict = {r["driver"]: r["position"] for r in results}
        time_lookup: dict = {r["driver"]: r["finish_time"] for r in results}
        winner_name = results[0]["driver"] if results else ""

        records: List[RaceRecord] = []
        for i, spec in enumerate(grid):
            name   = spec["driver_name"]
            q_pos  = quali_pos[i]
            strat  = strategies[i]
            strat_enc = STRATEGY_ENCODING[strat.value]

            # Interaction features
            skill_x_quali  = skill_norm[i] * (1.0 - q_pos / n)
            team_x_weather = team_norm[i]  * weather_grip

            fp = pos_lookup.get(name, n)
            ft = time_lookup.get(name, 0.0)

            records.append(RaceRecord(
                race_id               = race_idx,
                driver_name           = name,
                team                  = spec["team"],
                driver_skill          = round(skill_norm[i], 6),
                wet_skill             = round(driver_wet_skills[i], 6),
                team_performance      = round(team_norm[i], 6),
                car_max_speed_norm    = round(speed_norm[i], 6),
                car_acceleration_norm = round(accel_norm[i], 6),
                drag_coefficient      = round(spec["drag_coefficient"], 4),
                tyre_grip_base        = round(spec["tyre_grip"], 4),
                qualifying_position   = q_pos,
                circuit_type          = CIRCUIT_TYPE_ENCODING[circuit_t],
                weather_condition     = weather_enc,
                weather_grip_factor   = round(weather_grip, 4),
                tyre_strategy         = strat_enc,
                skill_x_quali         = round(skill_x_quali, 6),
                team_x_weather        = round(team_x_weather, 6),
                won                   = 1 if name == winner_name else 0,
                finish_position       = fp,
                finish_time_s         = round(ft, 3),
            ))

        return records

    @staticmethod
    def _circuit_length(circuit_type: str) -> float:
        return {
            "street":   3337.0,   # Monaco-esque
            "balanced": 5891.0,   # Silverstone-esque
            "power":    5793.0,   # Monza-esque
        }[circuit_type]
