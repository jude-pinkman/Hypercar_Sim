"""
F1 Manager Race Engine — 2026 Season
=====================================
Full F1 Grand Prix simulation implementing official regulations:

  ✅ 22-car grid, 305km race distance
  ✅ 2-hour maximum race time
  ✅ Formation lap — tyre warm-up, return to grid
  ✅ 5-light start sequence
  ✅ Race start simulation — reaction time, launch skill, L1 position changes
  ✅ Sector-based lap time (3 sectors, Albert Park data)
  ✅ Driver skill + car performance per sector
  ✅ Tyre wear & degradation, compound pace delta
  ✅ Two dry compound rule enforcement
  ✅ Pit stop strategy (20–25s loss, compound change)
  ✅ DRS (within 1s, DRS zones, speed/overtake boost)
  ✅ Track grip evolution (rubber buildup)
  ✅ Yellow flag (no overtaking during SC/VSC)
  ✅ Safety Car + Virtual Safety Car
  ✅ Red flag (rare, restarts with standing start)
  ✅ DNF / mechanical failure
  ✅ Points system top 10 (25-18-15-12-10-8-6-4-2-1) + fastest lap bonus
  ✅ track_position (0.0–1.0) for live map rendering
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Generator
from enum import Enum

from app.f1_data_2026 import (
    F1_DRIVERS_2026, F1_TEAMS_2026, F1_CIRCUITS_2026,
    get_driver_by_id, get_team_by_name, get_circuit_by_id,
    create_f1_2026_grid, CircuitType,
)
from app.albert_park_data import (
    ALBERT_PARK_CORNERS, ALBERT_PARK_SECTORS,
    GRIP_GAIN_PER_LAP, GRIP_INITIAL_OFFSET,
    DRS_GAP_THRESHOLD_S, DRS_OVERTAKE_BONUS, DRS_LAP_TIME_GAIN,
    calc_sector_time,
)


# ============================================================================
# CONSTANTS
# ============================================================================

PIT_STOP_LOSS_SECONDS = 22.0
DNF_BASE_PROBABILITY  = 0.004
MAX_RACE_SECONDS      = 7200.0   # 2-hour rule

POINTS_SYSTEM     = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}
FASTEST_LAP_BONUS = 1

PHASE_FORMATION = "formation"
PHASE_LIGHTS_OUT = "lights_out"
PHASE_RACING = "racing"
PHASE_FINISHED = "finished"


class TyreCompound(Enum):
    SOFT   = "S"
    MEDIUM = "M"
    HARD   = "H"
    INTER  = "I"
    WET    = "W"


COMPOUND_DELTA = {
    # (pace_delta_sec, deg_rate_per_lap, max_life_laps)
    TyreCompound.SOFT:   (-0.8,  0.065, 25),
    TyreCompound.MEDIUM: ( 0.0,  0.040, 38),
    TyreCompound.HARD:   ( 0.5,  0.025, 55),
    TyreCompound.INTER:  ( 1.5,  0.045, 35),
    TyreCompound.WET:    ( 3.5,  0.055, 30),
}

WEATHER_BASE_DELTA = {"dry": 0.0, "damp": 2.5, "wet": 6.0}

# Tyre temperature model — warm tyres give full grip, cold tyres are slower
TYRE_WARM_LAP_BONUS = 0.6   # seconds slower on lap 1 (cold tyres)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CarState:
    driver_id: str
    driver_name: str
    team: str
    number: int
    speed: float
    consistency: float
    wet_weather: float
    racecraft: float
    reliability: float
    pit_efficiency: float
    skill_rating: float
    car_performance: float
    base_lap_time: float

    position: int = 0
    gap_to_leader: float = 0.0
    total_race_time: float = 0.0

    compound: TyreCompound = TyreCompound.MEDIUM
    tyre_age: int = 0
    tyre_deg_accumulated: float = 0.0
    tyre_temp_warm: bool = False    # True after formation lap warming

    # Two-compound rule tracking
    compounds_used: List[str] = field(default_factory=list)

    pit_count: int = 0
    pit_laps: List[int] = field(default_factory=list)

    dnf: bool = False
    dnf_lap: Optional[int] = None
    laps_completed: int = 0

    lap_times: List[float] = field(default_factory=list)
    sector_times: List[List[float]] = field(default_factory=list)

    drs_active: bool = False
    track_position: float = 0.0

    def is_active(self) -> bool:
        return not self.dnf

    def has_used_two_compounds(self) -> bool:
        return len(set(self.compounds_used)) >= 2


@dataclass
class LapSnapshot:
    lap: int
    driver_id: str
    driver_name: str
    team: str
    number: int
    position: int
    lap_time: float
    sector1: float
    sector2: float
    sector3: float
    total_race_time: float
    gap_to_leader: float
    compound: str
    tyre_age: int
    tyre_deg: float
    pit_this_lap: bool
    pit_count: int
    drs_active: bool
    dnf: bool
    track_position: float
    flag: str = "green"
    # Extended telemetry
    speed_kmh: float = 0.0          # estimated top speed this lap (km/h)
    tyre_wear_pct: float = 0.0      # 0-100% tyre wear
    compounds_used: List[str] = field(default_factory=list)
    pit_laps: List[int] = field(default_factory=list)
    best_lap_time: float = 0.0      # personal best so far
    laps_completed: int = 0
    skill_rating: float = 0.0
    car_performance: float = 0.0


@dataclass
class RaceLapData:
    lap: int
    total_laps: int
    circuit_name: str
    weather: str
    sc_active: bool
    vsc_active: bool
    drivers: List[LapSnapshot]
    fastest_lap_driver: Optional[str] = None
    fastest_lap_time: Optional[float] = None
    grip_level: float = 1.0
    phase: str = "racing"
    lights_count: int = 0
    flag: str = "green"    # green | yellow | sc | vsc | red
    red_flag: bool = False


# ============================================================================
# STRATEGY PLANNER  — ensures 2-compound rule
# ============================================================================

def plan_strategy(driver_id: str, total_laps: int, weather: str,
                  circuit_type: CircuitType) -> List[Dict]:
    """
    Plan pit stop strategy. In dry races, ALWAYS includes at least one
    compound change so the two-dry-compound rule is satisfied.
    """
    if weather == "wet":
        return [{"lap": random.randint(15, 25), "compound": TyreCompound.INTER}]
    if weather == "damp":
        return [{"lap": random.randint(10, 20), "compound": TyreCompound.MEDIUM}]

    # Dry — always 2 different compounds
    stops = random.choices([1, 2], weights=[30, 70])[0]

    if stops == 1:
        stop1 = random.randint(int(total_laps * 0.38), int(total_laps * 0.58))
        # Must change to a different compound than starting compound
        # Starting compound is decided later; strategy always offers both options
        next_cmp = random.choice([TyreCompound.MEDIUM, TyreCompound.HARD])
        return [{"lap": stop1, "compound": next_cmp}]
    else:
        stop1 = random.randint(int(total_laps * 0.22), int(total_laps * 0.35))
        stop2 = random.randint(int(total_laps * 0.52), int(total_laps * 0.68))
        return [
            {"lap": stop1, "compound": TyreCompound.MEDIUM},
            {"lap": stop2, "compound": TyreCompound.HARD},
        ]


# ============================================================================
# MAIN ENGINE
# ============================================================================

class F1ManagerEngine:

    def __init__(
        self,
        circuit_id: str,
        weather: str = "dry",
        speed_mult: float = 1.0,
        driver_ids: Optional[List[str]] = None,
    ):
        self.circuit = get_circuit_by_id(circuit_id)
        if self.circuit is None:
            raise ValueError(f"Unknown circuit_id: {circuit_id}")

        self.circuit_id  = circuit_id
        self.weather     = weather
        self.speed_mult  = max(1.0, min(speed_mult, 30.0))
        self.total_laps  = self.circuit.typical_race_laps

        self.use_sector_model = (circuit_id == "AUS")

        # Race flags
        self.sc_active      = False
        self.sc_laps_left   = 0
        self.vsc_active     = False
        self.vsc_laps_left  = 0
        self.yellow_flag    = False   # true during SC/VSC
        self.red_flag_lap   = None    # lap when red flag was thrown
        self.red_flag_active = False

        # Track grip
        self.grip_level = 1.0 - GRIP_INITIAL_OFFSET / 10.0

        # Race time accumulator
        self.race_time_elapsed = 0.0

        # Build grid
        all_specs = create_f1_2026_grid()
        if driver_ids:
            id_set    = set(driver_ids)
            all_specs = [s for s in all_specs if s["driver_id"] in id_set]

        self.cars: List[CarState] = self._build_cars(all_specs)
        self._assign_grid_positions()

        self.lap_history: List[RaceLapData] = []
        self.final_results: List[Dict]      = []

    # ── build ──────────────────────────────────────────────────────────────────

    def _build_cars(self, specs: List[Dict]) -> List[CarState]:
        cars   = []
        circ   = self.circuit
        base_ref = circ.lap_record_seconds

        for spec in specs:
            skill  = spec["skill_rating"]
            offset = 12.0 * (1.0 - skill) + random.uniform(-0.3, 0.3)
            base   = base_ref + 1.5 + offset

            team     = get_team_by_name(spec["team"])
            car_perf = ((team.power + team.handling) / 2.0) if team else 0.85

            strategy = plan_strategy(spec["driver_id"], circ.typical_race_laps,
                                     self.weather, circ.circuit_type)

            if self.weather == "wet":
                start_cmp = TyreCompound.WET
            elif self.weather == "damp":
                start_cmp = TyreCompound.INTER
            else:
                start_cmp = random.choices([TyreCompound.SOFT, TyreCompound.MEDIUM],
                                           weights=[55, 45])[0]

            car = CarState(
                driver_id       = spec["driver_id"],
                driver_name     = spec["driver_name"],
                team            = spec["team"],
                number          = spec["number"],
                speed           = spec["max_speed"],
                consistency     = spec["consistency"],
                wet_weather     = spec["wet_weather"],
                racecraft       = spec["cornering_ability"],
                reliability     = spec["reliability"],
                pit_efficiency  = spec["pit_efficiency"],
                skill_rating    = spec["skill_rating"],
                car_performance = car_perf,
                base_lap_time   = base,
                compound        = start_cmp,
                compounds_used  = [start_cmp.value],
            )
            car._strategy     = strategy       # type: ignore[attr-defined]
            car._strategy_idx = 0              # type: ignore[attr-defined]
            cars.append(car)
        return cars

    def _assign_grid_positions(self):
        """Qualifying-order grid with random variance."""
        scored = [(c, c.skill_rating + random.gauss(0, 0.025)) for c in self.cars]
        scored.sort(key=lambda x: -x[1])
        for i, (car, _) in enumerate(scored):
            car.position = i + 1
            # Grid on pit straight before chequered flag (fraction 0.953 = just before flag)
            car.track_position = round(max(0.88, 0.953 - i * 0.002), 4)

    # ── formation lap tyre warm-up ────────────────────────────────────────────

    def _run_formation_lap(self):
        """
        Simulate the formation lap: tyres warm up, cars return to grid.
        Cold tyres = slower first racing lap. Warm tyres = full grip immediately.
        """
        for car in self.cars:
            # Formation lap warms tyres based on compound and driver skill
            warm_chance = 0.7 + car.skill_rating * 0.25
            car.tyre_temp_warm = random.random() < warm_chance
            # Tyre age doesn't increment (formation lap is neutralised)
            # Reset grid positions
            slot_frac = 0.953 - (car.position - 1) * 0.002
            car.track_position = round(max(0.88, slot_frac), 4)

    # ── race start simulation ─────────────────────────────────────────────────

    def _simulate_race_start(self):
        """
        Simulate the standing start after lights out.
        Each driver has a reaction time based on skill + randomness.
        Positions can be gained/lost in the first lap.
        """
        start_performances = []
        for car in self.cars:
            # Reaction time: skilled drivers react faster
            reaction = random.gauss(0.18, 0.04) - car.skill_rating * 0.05
            reaction = max(0.10, min(0.30, reaction))

            # Launch traction: tyre grip + car acceleration
            _, _, _ = COMPOUND_DELTA[car.compound]
            grip_bonus = 0.1 if car.tyre_temp_warm else 0.0
            launch = car.skill_rating * 0.6 + car.car_performance * 0.4 + grip_bonus
            launch += random.gauss(0, 0.05)

            # Combined start score (lower = better)
            start_score = reaction - launch * 0.3
            start_performances.append((car, start_score))

        # Sort by start score — determines initial L1 order at T1
        start_performances.sort(key=lambda x: x[1])

        # Apply position changes (only realistic swaps — max ±4 places)
        new_positions = {}
        for new_pos, (car, _) in enumerate(start_performances, start=1):
            new_positions[car.driver_id] = new_pos

        for car in self.cars:
            old_pos = car.position
            new_pos = new_positions.get(car.driver_id, old_pos)
            # Cap position change at ±4 (realistic standing start movement)
            capped = max(old_pos - 4, min(old_pos + 4, new_pos))
            car.position = capped

        # Re-sort to ensure no duplicates
        self._reindex_positions()

    def _reindex_positions(self):
        """Ensure positions are 1..N with no gaps."""
        active = sorted([c for c in self.cars if c.is_active()], key=lambda c: c.position)
        for i, car in enumerate(active, start=1):
            car.position = i
        dnfs = [c for c in self.cars if c.dnf]
        for i, car in enumerate(dnfs):
            car.position = len(active) + 1 + i

    # ── grip ──────────────────────────────────────────────────────────────────

    def _update_grip(self, lap: int):
        self.grip_level = min(1.0, self.grip_level + GRIP_GAIN_PER_LAP)

    def _grip_time_correction(self, lap: int) -> float:
        baseline = 1.0 - GRIP_INITIAL_OFFSET / 10.0
        improvement = self.grip_level - baseline
        return -improvement * 6.0

    # ── lap time ──────────────────────────────────────────────────────────────

    def _calc_lap_time(self, car: CarState, lap: int) -> tuple[float, List[float]]:
        compound_pace, deg_rate, _ = COMPOUND_DELTA[car.compound]

        car.tyre_deg_accumulated += deg_rate * (1.0 + car.tyre_age * 0.008)
        tyre_pen = car.tyre_deg_accumulated

        # Cold tyre penalty (lap 1 or immediately after pit)
        cold_pen = TYRE_WARM_LAP_BONUS if (car.tyre_age == 0 and not car.tyre_temp_warm) else 0.0

        fuel_corr  = -(lap - 1) * 0.04
        wx_delta   = WEATHER_BASE_DELTA[self.weather]
        if self.weather != "dry":
            wx_delta *= (1.5 - car.wet_weather)

        grip_corr  = self._grip_time_correction(lap)

        sc_extra = 0.0
        if self.sc_active:    sc_extra = 40.0
        elif self.vsc_active: sc_extra = 15.0

        sigma = 0.3 * (1.5 - car.consistency)

        if self.use_sector_model:
            sector_times = []
            for sector in ALBERT_PARK_SECTORS:
                st = calc_sector_time(
                    sector               = sector,
                    base_lap_ref         = car.base_lap_time,
                    driver_skill         = car.skill_rating,
                    car_performance      = car.car_performance,
                    tyre_age             = car.tyre_age,
                    tyre_deg_accumulated = tyre_pen,
                    fuel_correction      = fuel_corr,
                    weather_delta        = wx_delta,
                    grip_correction      = grip_corr,
                    sc_active            = self.sc_active,
                    vsc_active           = self.vsc_active,
                    drs_active           = car.drs_active,
                    noise_sigma          = sigma,
                )
                st += compound_pace * sector.length_fraction + cold_pen * sector.length_fraction
                sector_times.append(st)
            total = sum(sector_times)
        else:
            noise = random.gauss(0, sigma)
            total = (car.base_lap_time + compound_pace + tyre_pen + cold_pen
                     + fuel_corr + wx_delta + grip_corr + sc_extra + noise)
            total = max(total, car.base_lap_time * 0.97)
            sector_times = [total * 0.337, total * 0.383, total * 0.280]

        return total, sector_times

    # ── two-compound rule enforcement ────────────────────────────────────────

    def _enforce_two_compound_rule(self, car: CarState, lap: int):
        """
        If a car has not used two compounds and is approaching the end of the race
        (within 10 laps), force a pit stop for the second compound.
        """
        remaining = self.total_laps - lap
        if remaining <= 0 or car.has_used_two_compounds():
            return
        # Must pit by lap total_laps - 2 to guarantee rule compliance
        if remaining <= 10 and not car.has_used_two_compounds():
            # Force the pit this lap
            car._strategy.insert(car._strategy_idx, {  # type: ignore[attr-defined]
                "lap": lap,
                "compound": TyreCompound.HARD if car.compound != TyreCompound.HARD
                            else TyreCompound.MEDIUM,
            })

    # ── pit stop ──────────────────────────────────────────────────────────────

    def _should_pit(self, car: CarState, lap: int) -> bool:
        if not car.is_active():
            return False
        # Don't pit under red flag (handled separately)
        strat = car._strategy        # type: ignore[attr-defined]
        idx   = car._strategy_idx    # type: ignore[attr-defined]
        if idx < len(strat) and lap >= strat[idx]["lap"]:
            return True
        _, _, max_life = COMPOUND_DELTA[car.compound]
        if car.tyre_age >= max_life:
            return True
        return False

    def _do_pit_stop(self, car: CarState, lap: int):
        strat = car._strategy        # type: ignore[attr-defined]
        idx   = car._strategy_idx    # type: ignore[attr-defined]

        if idx < len(strat):
            new_compound      = strat[idx]["compound"]
            car._strategy_idx += 1  # type: ignore[attr-defined]
        else:
            # Fallback: use a different compound to satisfy two-compound rule
            if not car.has_used_two_compounds():
                new_compound = (TyreCompound.HARD if car.compound != TyreCompound.HARD
                                else TyreCompound.MEDIUM)
            else:
                new_compound = TyreCompound.HARD

        efficiency_bonus         = (car.pit_efficiency - 0.75) * 4.0
        stop_loss                = PIT_STOP_LOSS_SECONDS - efficiency_bonus + random.gauss(0, 0.5)
        car.compound             = new_compound
        car.tyre_age             = 0
        car.tyre_deg_accumulated = 0.0
        car.tyre_temp_warm       = False   # fresh tyres are cold
        car.pit_count           += 1
        car.pit_laps.append(lap)
        car.compounds_used.append(new_compound.value)
        car.total_race_time     += max(stop_loss, 18.0)

    # ── overtake ──────────────────────────────────────────────────────────────

    def _resolve_overtakes(self, lap: int):
        # NO overtaking under yellow (SC/VSC/red)
        if self.sc_active or self.vsc_active or self.red_flag_active:
            # Update DRS — disabled under yellow
            for car in self.cars:
                car.drs_active = False
            self._reindex_positions()
            return

        active = [c for c in self.cars if c.is_active()]
        active.sort(key=lambda c: c.total_race_time)

        for i in range(len(active) - 1):
            ahead  = active[i]
            behind = active[i + 1]
            gap    = behind.total_race_time - ahead.total_race_time

            if gap > 2.0:
                continue

            skill_delta  = behind.skill_rating - ahead.skill_rating
            drs_bonus    = DRS_OVERTAKE_BONUS if behind.drs_active else 0.0
            street_pen   = -0.15 if self.circuit.circuit_type == CircuitType.STREET else 0.0
            sector_bonus = 0.08 if self.use_sector_model else 0.0

            prob = 0.20 + skill_delta * 1.5 + drs_bonus + street_pen + sector_bonus
            prob = max(0.02, min(prob, 0.60))

            if random.random() < prob:
                swap_gain               = random.uniform(0.05, gap)
                behind.total_race_time -= swap_gain
                behind.drs_active       = False
                active[i], active[i + 1] = active[i + 1], active[i]

        for pos, car in enumerate(active, start=1):
            car.position = pos

        dnf_cars = [c for c in self.cars if c.dnf]
        for i, c in enumerate(dnf_cars):
            c.position = len(active) + 1 + i

        # DRS detection
        for i in range(1, len(active)):
            gap = active[i].total_race_time - active[i - 1].total_race_time
            active[i].drs_active = (
                gap <= DRS_GAP_THRESHOLD_S and self.circuit.drs_zones > 0
                and not self.sc_active and not self.vsc_active
            )

    # ── track position ────────────────────────────────────────────────────────

    def _calc_track_position(self, car: CarState, lap: int) -> float:
        if not car.is_active():
            return 0.0

        active = [c for c in self.cars if c.is_active()]
        active.sort(key=lambda c: c.total_race_time)
        leader = active[0] if active else None

        if leader is None or car is leader:
            return 0.955

        avg_lap_t = car.lap_times[-1] if car.lap_times else car.base_lap_time
        if avg_lap_t <= 0:
            return 0.0

        gap_secs = car.total_race_time - leader.total_race_time
        gap_frac = (gap_secs / avg_lap_t) % 1.0

        pos = (0.955 - gap_frac) % 1.0
        return round(pos, 4)

    # ── safety car / flags ────────────────────────────────────────────────────

    def _update_flags(self, lap: int, any_dnf: bool):
        """Update SC, VSC, and red flag state."""
        # Clear finished flags
        if self.sc_active:
            self.sc_laps_left -= 1
            if self.sc_laps_left <= 0:
                self.sc_active  = False
                self.yellow_flag = False
        elif self.vsc_active:
            self.vsc_laps_left -= 1
            if self.vsc_laps_left <= 0:
                self.vsc_active  = False
                self.yellow_flag = False
        elif self.red_flag_active:
            # Red flag clears after 1 lap (standing restart)
            self.red_flag_active = False
            self.yellow_flag     = False
        else:
            if any_dnf:
                roll = random.random()
                if roll < 0.03:          # 3% chance: red flag
                    self.red_flag_active = True
                    self.yellow_flag     = True
                elif roll < 0.23:        # 20% chance: SC
                    self.sc_active       = True
                    self.sc_laps_left    = random.randint(3, 6)
                    self.yellow_flag     = True
                elif roll < 0.53:        # 30% chance: VSC
                    self.vsc_active      = True
                    self.vsc_laps_left   = random.randint(2, 4)
                    self.yellow_flag     = True
            elif random.random() < 0.012 and lap > 3:
                self.vsc_active      = True
                self.vsc_laps_left   = random.randint(2, 3)
                self.yellow_flag     = True

    def _current_flag(self) -> str:
        if self.red_flag_active: return "red"
        if self.sc_active:       return "sc"
        if self.vsc_active:      return "vsc"
        if self.yellow_flag:     return "yellow"
        return "green"

    # ── DNF ──────────────────────────────────────────────────────────────────

    def _check_dnf(self, car: CarState, lap: int) -> bool:
        if car.dnf:
            return False
        dnf_chance = DNF_BASE_PROBABILITY * (1.5 - car.reliability)
        if random.random() < dnf_chance:
            car.dnf     = True
            car.dnf_lap = lap
            return True
        return False

    # ── snapshot builder ─────────────────────────────────────────────────────

    def _build_snapshots(self, lap: int, pit_this_lap: set,
                         fastest_time: float, fastest_driver, resolved) -> list:
        snapshots = []
        flag = self._current_flag()
        for car in sorted(self.cars, key=lambda c: (c.dnf, c.position)):
            lt = car.lap_times[-1] if car.lap_times else 0.0
            st = car.sector_times[-1] if car.sector_times else [0.0, 0.0, 0.0]

            # Tyre wear: percentage of max life consumed
            _, _, max_life = COMPOUND_DELTA[car.compound]
            tyre_wear_pct = min(100.0, round(car.tyre_age / max_life * 100, 1))

            # Estimated speed: lap length / lap time, converted to km/h
            lap_len_km = self.circuit.lap_length_km if hasattr(self.circuit, 'lap_length_km') else 5.278
            speed_kmh  = round((lap_len_km / lt) * 3600, 1) if lt > 0 else 0.0

            # Personal best lap time
            best_lt = round(min(car.lap_times), 3) if car.lap_times else 0.0

            snapshots.append(LapSnapshot(
                lap=lap, driver_id=car.driver_id, driver_name=car.driver_name,
                team=car.team, number=car.number, position=car.position,
                lap_time=round(lt, 3),
                sector1=round(st[0], 3), sector2=round(st[1], 3), sector3=round(st[2], 3),
                total_race_time=round(car.total_race_time, 3),
                gap_to_leader=round(car.gap_to_leader, 3),
                compound=car.compound.value, tyre_age=car.tyre_age,
                tyre_deg=round(car.tyre_deg_accumulated, 3),
                pit_this_lap=car.driver_id in pit_this_lap,
                pit_count=car.pit_count, drs_active=car.drs_active,
                dnf=car.dnf, track_position=car.track_position,
                flag=flag,
                speed_kmh=speed_kmh,
                tyre_wear_pct=tyre_wear_pct,
                compounds_used=list(car.compounds_used),
                pit_laps=list(car.pit_laps),
                best_lap_time=best_lt,
                laps_completed=car.laps_completed,
                skill_rating=round(car.skill_rating, 3),
                car_performance=round(car.car_performance, 3),
            ))
        return snapshots

    # ── public API ────────────────────────────────────────────────────────────

    def simulate_race(self) -> List[Dict]:
        for _ in self.simulate_race_live():
            pass
        return self.final_results

    def _set_grid_positions(self):
        for car in self.cars:
            slot_frac = 0.953 - (car.position - 1) * 0.002
            car.track_position = round(max(0.88, slot_frac), 4)

    def simulate_race_live(self) -> Generator[RaceLapData, None, None]:
        """
        Full race sequence:
          1. Formation lap (tyres warm up)
          2. Five lights sequence
          3. Lights out → race start simulation
          4. 58 race laps (with 2-hour cutoff)
        """
        total_laps = self.total_laps

        # ── 1. Formation lap ─────────────────────────────────────────────────
        self._run_formation_lap()        # warm tyres, set grid positions
        self._set_grid_positions()
        yield RaceLapData(
            lap=0, total_laps=total_laps,
            circuit_name=self.circuit.name, weather=self.weather,
            sc_active=False, vsc_active=False,
            drivers=self._build_snapshots(0, set(), math.inf, None, False),
            phase=PHASE_FORMATION, grip_level=self.grip_level, flag="green",
        )

        # ── 2. Five lights ───────────────────────────────────────────────────
        for light_n in range(1, 6):
            yield RaceLapData(
                lap=0, total_laps=total_laps,
                circuit_name=self.circuit.name, weather=self.weather,
                sc_active=False, vsc_active=False,
                drivers=self._build_snapshots(0, set(), math.inf, None, False),
                phase=PHASE_LIGHTS_OUT, lights_count=light_n,
                grip_level=self.grip_level, flag="green",
            )

        # ── 3. Race start ────────────────────────────────────────────────────
        self._simulate_race_start()

        # ── 4. Race laps ─────────────────────────────────────────────────────
        for lap in range(1, total_laps + 1):

            # 2-hour rule: if elapsed time exceeds limit, end race
            if self.race_time_elapsed >= MAX_RACE_SECONDS:
                break

            any_dnf      = False
            pit_this_lap = set()
            fastest_time = math.inf
            fastest_driver = None

            # Enforce two-compound rule before deciding pit
            if self.weather == "dry":
                for car in self.cars:
                    if car.is_active():
                        self._enforce_two_compound_rule(car, lap)

            for car in self.cars:
                if not car.is_active():
                    continue
                if self._check_dnf(car, lap):
                    any_dnf = True
                    continue

                if self._should_pit(car, lap):
                    self._do_pit_stop(car, lap)
                    pit_this_lap.add(car.driver_id)

                lt, sector_times = self._calc_lap_time(car, lap)
                car.lap_times.append(lt)
                car.sector_times.append(sector_times)
                car.total_race_time += lt
                car.tyre_age        += 1
                car.laps_completed  += 1

                if lt < fastest_time and not self.sc_active and not self.vsc_active:
                    fastest_time   = lt
                    fastest_driver = car.driver_id

            self._resolve_overtakes(lap)
            self._update_flags(lap, any_dnf)
            self._update_grip(lap)

            # Update race elapsed time (use leader's lap time)
            active_sorted = sorted(
                [c for c in self.cars if c.is_active()],
                key=lambda c: c.total_race_time,
            )
            if active_sorted:
                leader_lt = active_sorted[0].lap_times[-1] if active_sorted[0].lap_times else 78.0
                self.race_time_elapsed += leader_lt

            # Gaps to leader
            leader_time = active_sorted[0].total_race_time if active_sorted else 0.0
            for car in active_sorted:
                car.gap_to_leader = car.total_race_time - leader_time

            # Track positions
            for car in self.cars:
                if car.is_active():
                    car.track_position = self._calc_track_position(car, lap)

            # Build snapshots (reuse the racing loop builder)
            snapshots = self._build_snapshots(lap, pit_this_lap, fastest_time,
                                              fastest_driver, True)

            lap_data = RaceLapData(
                lap=lap, total_laps=total_laps,
                circuit_name=self.circuit.name, weather=self.weather,
                sc_active=self.sc_active, vsc_active=self.vsc_active,
                drivers=snapshots,
                fastest_lap_driver=fastest_driver,
                fastest_lap_time=round(fastest_time, 3) if fastest_driver else None,
                grip_level=round(self.grip_level, 4),
                phase=PHASE_RACING,
                flag=self._current_flag(),
                red_flag=self.red_flag_active,
            )

            self.lap_history.append(lap_data)
            yield lap_data

        self.final_results = self._classify()

    # ── classification ────────────────────────────────────────────────────────

    def _classify(self) -> List[Dict]:
        finished = sorted([c for c in self.cars if not c.dnf],
                          key=lambda c: c.total_race_time)
        dnfs     = sorted([c for c in self.cars if c.dnf],
                          key=lambda c: -(c.dnf_lap or 0))
        all_cars = finished + dnfs

        fastest_time   = math.inf
        fastest_driver = None
        for car in finished:
            if car.lap_times:
                best = min(car.lap_times)
                if best < fastest_time:
                    fastest_time   = best
                    fastest_driver = car.driver_id

        results = []
        for pos, car in enumerate(all_cars, start=1):
            pts = POINTS_SYSTEM.get(pos, 0)
            if car.driver_id == fastest_driver and pos <= 10 and not car.dnf:
                pts += FASTEST_LAP_BONUS

            gap = (car.total_race_time - finished[0].total_race_time
                   if not car.dnf and finished else None)

            results.append({
                "position":      pos,
                "driver_id":     car.driver_id,
                "driver_name":   car.driver_name,
                "team":          car.team,
                "number":        car.number,
                "laps":          car.laps_completed,
                "total_time":    round(car.total_race_time, 3),
                "gap":           round(gap, 3) if gap is not None else None,
                "pit_count":     car.pit_count,
                "pit_laps":      car.pit_laps,
                "compounds_used":list(set(car.compounds_used)),
                "points":        pts,
                "dnf":           car.dnf,
                "dnf_lap":       car.dnf_lap,
                "fastest_lap":   car.driver_id == fastest_driver,
                "best_lap_time": round(min(car.lap_times), 3) if car.lap_times else None,
            })
        return results


# ============================================================================
# CLI helper
# ============================================================================

def quick_race(circuit_id: str = "AUS", weather: str = "dry") -> List[Dict]:
    engine  = F1ManagerEngine(circuit_id=circuit_id, weather=weather)
    results = engine.simulate_race()
    circ    = engine.circuit
    print(f"\n{'='*62}")
    print(f"  {circ.name}  |  {weather.upper()}  |  {engine.total_laps} laps")
    print(f"{'='*62}")
    print(f"  {'POS':<4} {'DRIVER':<24} {'TEAM':<22} {'GAP':>10}  PTS  TYRES")
    print(f"  {'-'*70}")
    for r in results[:10]:
        gap = f"+{r['gap']:.3f}s" if r['gap'] else "LEADER"
        fl  = " ⚡" if r['fastest_lap'] else ""
        cmp = "+".join(r['compounds_used'])
        print(f"  {r['position']:<4} {r['driver_name']:<24} {r['team']:<22} {gap:>10}  {r['points']}{fl}  {cmp}")
    print()
    return results


if __name__ == "__main__":
    quick_race("AUS", "dry")
