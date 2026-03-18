"""
PitStopManager — Pit stop scheduling, execution, and strategy templates.

Responsibilities
----------------
* Define the three named race strategies (ONE_STOP, TWO_STOP, AGGRESSIVE)
  and build the per-car TyreStrategy stint lists from them.
* Decide *when* a car should pit (wear-threshold trigger OR pre-planned lap
  window, whichever comes first).
* Execute the pit stop: freeze the car for a realistic 2–3 s service time,
  swap the tyre compound via TyreStrategy, and record a PitStopRecord.
* Expose a clean query API so RaceSimulator can ask
  "should this car pit right now?" without caring about the details.

Integration points
------------------
* `PitStopManager` is instantiated once per RaceSimulator and owns a
  `_plans: Dict[str, PitPlan]` keyed on driver name.
* Each plan holds the TyreStrategy for that car plus the scheduled pit
  windows (lap ranges) for each planned stop.
* RaceSimulator calls `manager.notify_lap_complete(car, lap, race_time)` once
  per car per completed lap and `manager.tick(car, dt)` every physics step.
  The manager sets `car.pit_stop_remaining` when service is in progress so
  the physics engine knows to freeze the car.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.tyre import TyreCompound, TyreStrategy, COMPOUND_SPECS


# ---------------------------------------------------------------------------
# Strategy templates
# ---------------------------------------------------------------------------

class RaceStrategy(Enum):
    """Named strategy templates for a full race."""
    ONE_STOP   = "one_stop"    # 1 pit stop, durable compounds
    TWO_STOP   = "two_stop"    # 2 pit stops, balanced compounds
    AGGRESSIVE = "aggressive"  # 3 pit stops, prioritise peak grip


@dataclass(frozen=True)
class StrategyTemplate:
    """
    Blueprint for a named strategy.

    Attributes
    ----------
    name:
        Human-readable label.
    stints:
        Ordered list of tyre compounds to run.  len(stints) - 1 == number of
        pit stops.
    wear_threshold:
        Fraction of tyre life at which the car *must* pit even if the planned
        lap window hasn't arrived yet.  Range 0–1; e.g. 0.85 = pit at 85 %
        wear regardless of the schedule.
    pit_window_fraction:
        (start_frac, end_frac) of total race laps forming the ideal pit
        window for each intermediate stop.  One tuple per planned stop.
        e.g. [(0.30, 0.45)] means the single stop should happen between
        30 % and 45 % of total race distance.
    """
    name: str
    stints: List[TyreCompound]
    wear_threshold: float
    pit_window_fractions: List[Tuple[float, float]]  # one per planned stop


STRATEGY_TEMPLATES: Dict[RaceStrategy, StrategyTemplate] = {
    RaceStrategy.ONE_STOP: StrategyTemplate(
        name                = "One-Stop",
        stints              = [TyreCompound.MEDIUM, TyreCompound.HARD],
        wear_threshold      = 0.88,
        pit_window_fractions= [(0.40, 0.60)],   # pit roughly mid-race
    ),
    RaceStrategy.TWO_STOP: StrategyTemplate(
        name                = "Two-Stop",
        stints              = [TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD],
        wear_threshold      = 0.80,
        pit_window_fractions= [(0.28, 0.38), (0.58, 0.70)],
    ),
    RaceStrategy.AGGRESSIVE: StrategyTemplate(
        name                = "Aggressive",
        stints              = [TyreCompound.SOFT, TyreCompound.SOFT,
                               TyreCompound.MEDIUM, TyreCompound.SOFT],
        wear_threshold      = 0.70,   # pits early, prioritising peak grip
        pit_window_fractions= [(0.20, 0.30), (0.45, 0.55), (0.72, 0.82)],
    ),
}


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------

@dataclass
class PitStopRecord:
    """Immutable record of a completed pit stop."""
    driver:          str
    lap:             int
    race_time_entry: float          # race clock when car entered pits (s)
    race_time_exit:  float          # race clock when car rejoined track (s)
    service_time:    float          # actual time spent stationary (s)
    old_compound:    str
    new_compound:    str
    trigger:         str            # "wear_threshold" | "pit_window" | "worn_out"
    wear_at_pit:     float          # tyre wear fraction when pitting


@dataclass
class PitPlan:
    """Per-car pit plan managed internally by PitStopManager."""
    driver:           str
    strategy:         RaceStrategy
    tyre_strategy:    TyreStrategy
    wear_threshold:   float
    # Scheduled pit windows as absolute lap numbers – set when race starts
    pit_windows:      List[Tuple[int, int]] = field(default_factory=list)
    # Which stop index we're targeting next (0-based)
    next_stop_index:  int = 0
    # Is the car currently in the pits?
    in_pit:           bool = False
    # Seconds of service time remaining
    pit_time_remaining: float = 0.0
    # History of completed stops for this car
    stops:            List[PitStopRecord] = field(default_factory=list)
    # Race time at which the current pit stop started
    pit_entry_time:   float = 0.0


# ---------------------------------------------------------------------------
# PitStopManager
# ---------------------------------------------------------------------------

class PitStopManager:
    """
    Central authority for all pit stop decisions and execution.

    Lifecycle
    ---------
    1. Create: ``mgr = PitStopManager(total_laps)``
    2. Register each car before the race starts:
       ``mgr.register_car(driver_name, strategy)``
       → returns the TyreStrategy to attach to the Car.
    3. Each lap boundary → ``mgr.notify_lap_complete(car, lap, race_time)``
    4. Each physics step  → ``mgr.tick(car, dt)``
       → returns True while car is still in the pits (velocity should be 0).
    5. After the race     → ``mgr.all_stops`` for the full log.
    """

    #: Service time is drawn from U[min, max] seconds.
    PIT_TIME_MIN: float = 2.0
    PIT_TIME_MAX: float = 3.0

    def __init__(self, total_laps: int, noise_factor_range: float = 0.05):
        """
        Parameters
        ----------
        total_laps:
            Total race distance in laps.  Used to convert pit_window_fractions
            into concrete lap numbers.
        noise_factor_range:
            Maximum ± noise on tyre wear rate per car.
        """
        self.total_laps = total_laps
        self.noise_factor_range = noise_factor_range
        self._plans: Dict[str, PitPlan] = {}

    # ------------------------------------------------------------------
    # Setup API
    # ------------------------------------------------------------------

    def register_car(
        self,
        driver_name: str,
        strategy: RaceStrategy = RaceStrategy.ONE_STOP,
        noise_factor: Optional[float] = None,
    ) -> TyreStrategy:
        """
        Register a car with a named strategy.

        Returns the TyreStrategy that should be attached to the Car object.
        The caller must assign it: ``car.tyre_strategy = manager.register_car(…)``
        """
        template = STRATEGY_TEMPLATES[strategy]
        if noise_factor is None:
            noise_factor = random.uniform(
                -self.noise_factor_range, self.noise_factor_range
            )

        tyre_strat = TyreStrategy(
            stints=list(template.stints),
            noise_factor=noise_factor,
        )

        # Convert fraction-based windows to concrete lap numbers.
        windows: List[Tuple[int, int]] = []
        for start_frac, end_frac in template.pit_window_fractions:
            w_start = max(1, int(start_frac * self.total_laps))
            w_end   = min(self.total_laps - 1, int(end_frac * self.total_laps))
            windows.append((w_start, w_end))

        plan = PitPlan(
            driver           = driver_name,
            strategy         = strategy,
            tyre_strategy    = tyre_strat,
            wear_threshold   = template.wear_threshold,
            pit_windows      = windows,
        )
        self._plans[driver_name] = plan
        return tyre_strat

    # ------------------------------------------------------------------
    # Per-lap decision API
    # ------------------------------------------------------------------

    def notify_lap_complete(
        self,
        driver_name: str,
        lap: int,
        race_time: float,
        wear_multiplier: float = 1.0,
    ) -> bool:
        """
        Called once per car per completed lap.

        Advances tyre wear (scaled by ``wear_multiplier`` from the weather
        system) and evaluates whether to trigger a pit stop.

        Returns True if a pit stop has been *scheduled* for this lap boundary
        (the actual service begins on the next physics tick via ``tick()``).
        """
        plan = self._plans.get(driver_name)
        if plan is None or plan.in_pit:
            return False

        # Advance tyre wear for the lap just completed — weather-scaled.
        plan.tyre_strategy.current_tyre.advance_laps(wear_multiplier)

        tyre       = plan.tyre_strategy.current_tyre
        wear       = tyre.wear_fraction
        stop_idx   = plan.next_stop_index
        more_stops = stop_idx < len(plan.pit_windows)

        if not more_stops:
            # All planned stops done; only pit if truly worn out.
            if tyre.is_worn_out and plan.tyre_strategy.stints_remaining > 0:
                self._initiate_pit(plan, lap, race_time, trigger="worn_out")
                return True
            return False

        window_start, window_end = plan.pit_windows[stop_idx]

        # Trigger conditions (any one is sufficient):
        #   A. Wear exceeded threshold
        #   B. Inside the pit window
        #   C. Past the end of the window (forced stop — we overran)
        trigger: Optional[str] = None
        if wear >= plan.wear_threshold:
            trigger = "wear_threshold"
        elif window_start <= lap <= window_end:
            # Inside the window — pit if wear is meaningful (> 30 %)
            # to avoid pitting on brand-new tyres due to a wide window
            if wear > 0.30:
                trigger = "pit_window"
        elif lap > window_end:
            # Overran the window — pit immediately
            trigger = "pit_window"

        if trigger:
            self._initiate_pit(plan, lap, race_time, trigger=trigger)
            return True

        return False

    # ------------------------------------------------------------------
    # Per-tick execution API
    # ------------------------------------------------------------------

    def tick(self, driver_name: str, dt: float) -> bool:
        """
        Advance the pit stop clock by ``dt`` seconds.

        Returns True while the car is still being serviced (caller should
        hold velocity at 0).  Returns False once service is complete.

        When service ends, the tyre compound is swapped via TyreStrategy.
        """
        plan = self._plans.get(driver_name)
        if plan is None or not plan.in_pit:
            return False

        plan.pit_time_remaining -= dt

        if plan.pit_time_remaining <= 0.0:
            self._complete_pit(plan)
            return False  # car may rejoin track this tick

        return True  # still in pits

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_in_pit(self, driver_name: str) -> bool:
        """True while the car is stationary in the pit box."""
        plan = self._plans.get(driver_name)
        return plan.in_pit if plan else False

    def get_plan(self, driver_name: str) -> Optional[PitPlan]:
        return self._plans.get(driver_name)

    def get_tyre_strategy(self, driver_name: str) -> Optional[TyreStrategy]:
        plan = self._plans.get(driver_name)
        return plan.tyre_strategy if plan else None

    @property
    def all_stops(self) -> List[PitStopRecord]:
        """All completed pit stops across every car, sorted by race time."""
        stops: List[PitStopRecord] = []
        for plan in self._plans.values():
            stops.extend(plan.stops)
        return sorted(stops, key=lambda s: s.race_time_entry)

    def strategy_summary(self) -> str:
        """One-line summary of each car's strategy for race start output."""
        lines = []
        for driver, plan in self._plans.items():
            tmpl = STRATEGY_TEMPLATES[plan.strategy]
            compound_str = " → ".join(c.value.upper() for c in tmpl.stints)
            windows_str  = ", ".join(
                f"L{w[0]}–{w[1]}" for w in plan.pit_windows
            )
            lines.append(
                f"  {driver:<22} [{tmpl.name:<12}]  {compound_str:<30}  "
                f"windows: {windows_str}"
            )
        return "\n".join(lines)

    def stops_for_driver(self, driver_name: str) -> List[PitStopRecord]:
        plan = self._plans.get(driver_name)
        return plan.stops if plan else []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initiate_pit(
        self,
        plan: PitPlan,
        lap: int,
        race_time: float,
        trigger: str,
    ) -> None:
        """Mark car as entering pits; service time is drawn randomly."""
        service_time = random.uniform(self.PIT_TIME_MIN, self.PIT_TIME_MAX)
        plan.in_pit             = True
        plan.pit_time_remaining = service_time
        plan.pit_entry_time     = race_time
        # Store partial record; will be completed in _complete_pit
        plan.stops.append(
            PitStopRecord(
                driver          = plan.driver,
                lap             = lap,
                race_time_entry = race_time,
                race_time_exit  = 0.0,           # filled on exit
                service_time    = service_time,
                old_compound    = plan.tyre_strategy.current_tyre.compound.value,
                new_compound    = "",             # filled on exit
                trigger         = trigger,
                wear_at_pit     = plan.tyre_strategy.current_tyre.wear_fraction,
            )
        )

    def _complete_pit(self, plan: PitPlan) -> None:
        """Swap tyres and mark car as returned to track."""
        lap_of_stop = plan.stops[-1].lap

        # Perform compound swap via TyreStrategy
        old_compound = plan.tyre_strategy.current_tyre.compound.value
        new_compound_enum = plan.tyre_strategy.pit_stop(current_lap=lap_of_stop)

        if new_compound_enum is None:
            # No more compounds — shouldn't normally happen; just release car
            new_compound_str = old_compound
        else:
            new_compound_str = new_compound_enum.value

        # Update the partial record
        record = plan.stops[-1]
        exit_time = record.race_time_entry + record.service_time
        # Replace with completed record (frozen dataclass workaround: rebuild)
        plan.stops[-1] = PitStopRecord(
            driver          = record.driver,
            lap             = record.lap,
            race_time_entry = record.race_time_entry,
            race_time_exit  = exit_time,
            service_time    = record.service_time,
            old_compound    = record.old_compound,
            new_compound    = new_compound_str,
            trigger         = record.trigger,
            wear_at_pit     = record.wear_at_pit,
        )

        plan.in_pit             = False
        plan.pit_time_remaining = 0.0
        plan.next_stop_index   += 1


# ---------------------------------------------------------------------------
# Convenience factory: build a PitStopManager for a full F1 grid
# ---------------------------------------------------------------------------

def assign_grid_strategies(
    drivers: List[str],
    total_laps: int,
    default_strategy: RaceStrategy = RaceStrategy.TWO_STOP,
    strategy_overrides: Optional[Dict[str, RaceStrategy]] = None,
) -> PitStopManager:
    """
    Create a PitStopManager and register all drivers in one call.

    Parameters
    ----------
    drivers:
        List of driver names in grid order.
    total_laps:
        Total race laps.
    default_strategy:
        Strategy applied to every driver not in ``strategy_overrides``.
    strategy_overrides:
        Optional dict mapping driver names to a specific RaceStrategy.

    Returns
    -------
    PitStopManager with all drivers registered.
    """
    manager = PitStopManager(total_laps=total_laps)
    overrides = strategy_overrides or {}

    for driver in drivers:
        strategy = overrides.get(driver, default_strategy)
        manager.register_car(driver, strategy)

    return manager
