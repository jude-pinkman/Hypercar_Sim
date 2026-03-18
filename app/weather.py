"""
WeatherSystem — Dynamic weather for the race simulator.

Architecture
------------
WeatherCondition   Enum of track states: DRY, LIGHT_RAIN, HEAVY_RAIN.

WeatherParams      Frozen dataclass of physics multipliers for one condition.
                   Consulted every physics step; values deliberately separate
                   from TyreDegradationModel so the two systems compose cleanly:

                       effective_grip = base_grip
                                        × tyre.grip_multiplier      (wear)
                                        × weather.track_grip_factor  (surface)

WeatherEvent       A scheduled condition change at a given lap.

WeatherState       Mutable snapshot that the simulator reads each step.
                   Updated by WeatherSystem.advance() every lap.

WeatherSystem      The live engine.  Holds the event schedule, interpolates
                   smoothly across a configurable transition window, and
                   exposes the current WeatherState to the simulator.

Integration points
------------------
RaceSimulator._calculate_acceleration
    → multiplies grip_factor by weather.current_state.track_grip_factor
    → multiplies max_speed  by weather.current_state.max_speed_factor

RaceSimulator._update_car_physics
    → adds weather.current_state.laptime_penalty_s * bleed to velocity

PitStopManager.notify_lap_complete
    → receives wear_multiplier from weather so rain accelerates tyre wear
      through the existing per-lap advance_laps path

RaceSimulator.run_simulation
    → calls weather.advance(lap) at every lap boundary
    → passes weather.current_state.wear_multiplier into pit manager
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Conditions and their physics parameters
# ---------------------------------------------------------------------------

class WeatherCondition(Enum):
    DRY         = "dry"
    LIGHT_RAIN  = "light_rain"
    HEAVY_RAIN  = "heavy_rain"


@dataclass(frozen=True)
class WeatherParams:
    """
    Physics multipliers for a single weather condition.

    Attributes
    ----------
    condition
        The WeatherCondition this spec describes.
    track_grip_factor
        Multiplier on every car's effective tyre grip (after tyre degradation).
        1.0 = dry tarmac; <1.0 = slippery surface.
    wear_multiplier
        Multiplier on tyre wear-per-lap.  Rain cools tyres and cuts wear
        (light rain) OR hydroplaning stresses them (heavy rain on slicks).
    laptime_penalty_s
        Extra seconds lost per lap due to reduced speed in corners and
        straights.  Applied as a continuous velocity bleed each physics step.
    max_speed_factor
        Fraction of nominal top speed achievable.  Heavy rain limits aero
        downforce exploitation and reduces safe straight-line speed.
    acceleration_factor
        Additional multiplier on traction-limited acceleration.  Wet track
        limits wheelspin headroom independent of compound grip.
    description
        Human-readable label for console output.
    """
    condition:          WeatherCondition
    track_grip_factor:  float   # applied after tyre degradation
    wear_multiplier:    float   # scales advance_laps() per lap
    laptime_penalty_s:  float   # extra seconds/lap (velocity bleed source)
    max_speed_factor:   float   # fraction of car.max_speed usable
    acceleration_factor: float  # additional traction limit
    description:        str
    icon:               str


# Canonical specs — values tuned to be physically meaningful but not
# so severe that they break the existing simulation balance.
WEATHER_PARAMS: Dict[WeatherCondition, WeatherParams] = {
    WeatherCondition.DRY: WeatherParams(
        condition           = WeatherCondition.DRY,
        track_grip_factor   = 1.00,
        wear_multiplier     = 1.00,
        laptime_penalty_s   = 0.00,
        max_speed_factor    = 1.00,
        acceleration_factor = 1.00,
        description         = "Dry",
        icon                = "☀️",
    ),
    WeatherCondition.LIGHT_RAIN: WeatherParams(
        condition           = WeatherCondition.LIGHT_RAIN,
        track_grip_factor   = 0.82,  # −18 % surface grip
        wear_multiplier     = 0.80,  # cooler track → 20 % less wear
        laptime_penalty_s   = 4.50,  # ~4.5 s slower per lap
        max_speed_factor    = 0.93,  # −7 % top speed
        acceleration_factor = 0.88,  # −12 % traction-limited accel
        description         = "Light Rain",
        icon                = "🌦️",
    ),
    WeatherCondition.HEAVY_RAIN: WeatherParams(
        condition           = WeatherCondition.HEAVY_RAIN,
        track_grip_factor   = 0.60,  # −40 % surface grip
        wear_multiplier     = 1.25,  # aquaplaning stresses slick tyres
        laptime_penalty_s   = 12.00, # ~12 s slower per lap
        max_speed_factor    = 0.82,  # −18 % top speed
        acceleration_factor = 0.70,  # −30 % traction-limited accel
        description         = "Heavy Rain",
        icon                = "⛈️",
    ),
}


# ---------------------------------------------------------------------------
# Event schedule
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeatherEvent:
    """
    A scheduled change in weather condition.

    Parameters
    ----------
    lap
        Race lap at which the new condition takes effect (1-based).
    condition
        The new WeatherCondition that begins at this lap.
    transition_laps
        Number of laps over which the transition is smoothed.  A value of 2
        means the shift from old→new parameters is linear over 2 laps.
        Set to 0 for an instantaneous change (e.g. safety-car conditions).
    """
    lap:             int
    condition:       WeatherCondition
    transition_laps: int = 2


# ---------------------------------------------------------------------------
# Live state
# ---------------------------------------------------------------------------

@dataclass
class WeatherState:
    """
    Snapshot of current track conditions consulted by the simulator.

    All float fields are computed by WeatherSystem.advance() via linear
    interpolation between old and new WeatherParams during a transition.
    """
    condition:          WeatherCondition = WeatherCondition.DRY
    track_grip_factor:  float = 1.00
    wear_multiplier:    float = 1.00
    laptime_penalty_s:  float = 0.00
    max_speed_factor:   float = 1.00
    acceleration_factor: float = 1.00
    # Transition bookkeeping (not consumed by physics)
    transitioning:      bool  = False
    transition_progress: float = 1.00   # 0.0 = just started, 1.0 = complete

    def apply(self, params: WeatherParams) -> None:
        """Snap all physics fields directly from a WeatherParams spec."""
        self.condition          = params.condition
        self.track_grip_factor  = params.track_grip_factor
        self.wear_multiplier    = params.wear_multiplier
        self.laptime_penalty_s  = params.laptime_penalty_s
        self.max_speed_factor   = params.max_speed_factor
        self.acceleration_factor = params.acceleration_factor
        self.transitioning      = False
        self.transition_progress = 1.00

    def interpolate(
        self,
        old: WeatherParams,
        new: WeatherParams,
        progress: float,        # 0.0 → 1.0
    ) -> None:
        """Linearly blend all physics fields between two conditions."""
        t = max(0.0, min(1.0, progress))
        self.condition          = new.condition if t >= 0.5 else old.condition
        self.track_grip_factor  = old.track_grip_factor  + t * (new.track_grip_factor  - old.track_grip_factor)
        self.wear_multiplier    = old.wear_multiplier    + t * (new.wear_multiplier    - old.wear_multiplier)
        self.laptime_penalty_s  = old.laptime_penalty_s  + t * (new.laptime_penalty_s  - old.laptime_penalty_s)
        self.max_speed_factor   = old.max_speed_factor   + t * (new.max_speed_factor   - old.max_speed_factor)
        self.acceleration_factor = old.acceleration_factor + t * (new.acceleration_factor - old.acceleration_factor)
        self.transitioning      = (t < 1.0)
        self.transition_progress = t

    def summary(self) -> str:
        """One-line status string for console output."""
        params = WEATHER_PARAMS[self.condition]
        trans  = f" [transitioning {self.transition_progress*100:.0f}%]" if self.transitioning else ""
        return (
            f"{params.icon} {params.description}{trans}  "
            f"grip×{self.track_grip_factor:.2f}  "
            f"wear×{self.wear_multiplier:.2f}  "
            f"Δlap+{self.laptime_penalty_s:.1f}s  "
            f"vmax×{self.max_speed_factor:.2f}"
        )


# ---------------------------------------------------------------------------
# WeatherSystem
# ---------------------------------------------------------------------------

class WeatherSystem:
    """
    Drives dynamic weather throughout a race.

    Usage
    -----
    >>> ws = WeatherSystem(total_laps=50, initial_condition=WeatherCondition.DRY)
    >>> ws.add_event(WeatherEvent(lap=15, condition=WeatherCondition.LIGHT_RAIN))
    >>> ws.add_event(WeatherEvent(lap=30, condition=WeatherCondition.HEAVY_RAIN))
    >>> ws.add_event(WeatherEvent(lap=40, condition=WeatherCondition.DRY, transition_laps=4))

    Each lap call ws.advance(current_lap) — the simulator reads
    ws.current_state for that lap's physics multipliers.
    """

    def __init__(
        self,
        total_laps: int,
        initial_condition: WeatherCondition = WeatherCondition.DRY,
    ):
        self.total_laps       = total_laps
        self._events:  List[WeatherEvent] = []
        self._history: List[Tuple[int, WeatherCondition]] = []  # (lap, condition)

        self.current_state = WeatherState()
        self.current_state.apply(WEATHER_PARAMS[initial_condition])
        self._current_condition = initial_condition
        self._prev_params       = WEATHER_PARAMS[initial_condition]
        self._next_event_idx    = 0
        self._in_transition     = False
        self._transition_start_lap: int  = 0
        self._transition_laps:      int  = 0
        self._transition_old:  WeatherParams = WEATHER_PARAMS[initial_condition]
        self._transition_new:  WeatherParams = WEATHER_PARAMS[initial_condition]

    # ------------------------------------------------------------------
    # Schedule API
    # ------------------------------------------------------------------

    def add_event(self, event: WeatherEvent) -> "WeatherSystem":
        """
        Schedule a weather change.  Events are sorted by lap automatically.
        Returns self to allow method chaining.
        """
        self._events.append(event)
        self._events.sort(key=lambda e: e.lap)
        return self

    def clear_events(self) -> None:
        self._events.clear()
        self._next_event_idx = 0

    # ------------------------------------------------------------------
    # Per-lap advance
    # ------------------------------------------------------------------

    def advance(self, lap: int) -> WeatherState:
        """
        Called once per completed lap.  Updates current_state.

        Returns the (possibly interpolated) WeatherState for this lap.
        """
        # Check whether a new event fires on this lap
        while (
            self._next_event_idx < len(self._events)
            and self._events[self._next_event_idx].lap <= lap
        ):
            ev = self._events[self._next_event_idx]
            self._next_event_idx += 1

            if ev.condition == self._current_condition:
                continue  # no-op

            old_params = WEATHER_PARAMS[self._current_condition]
            new_params = WEATHER_PARAMS[ev.condition]

            if ev.transition_laps <= 0:
                # Instantaneous
                self.current_state.apply(new_params)
                self._current_condition = ev.condition
                self._prev_params       = new_params
                self._in_transition     = False
                self._history.append((lap, ev.condition))
            else:
                # Begin smooth transition
                self._in_transition          = True
                self._transition_start_lap   = lap
                self._transition_laps        = ev.transition_laps
                self._transition_old         = old_params
                self._transition_new         = new_params
                self._current_condition      = ev.condition
                self._history.append((lap, ev.condition))

        # Advance any ongoing transition
        if self._in_transition:
            elapsed  = lap - self._transition_start_lap
            progress = elapsed / self._transition_laps if self._transition_laps > 0 else 1.0
            if progress >= 1.0:
                self.current_state.apply(self._transition_new)
                self._in_transition = False
            else:
                self.current_state.interpolate(
                    self._transition_old, self._transition_new, progress
                )

        return self.current_state

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @property
    def condition(self) -> WeatherCondition:
        return self._current_condition

    @property
    def history(self) -> List[Tuple[int, WeatherCondition]]:
        """List of (lap, condition) at which each transition was triggered."""
        return list(self._history)

    def forecast(self) -> List[WeatherEvent]:
        """Remaining (not yet fired) scheduled events."""
        return self._events[self._next_event_idx:]

    def is_wet(self) -> bool:
        return self._current_condition != WeatherCondition.DRY

    def is_dry(self) -> bool:
        return self._current_condition == WeatherCondition.DRY

    # ------------------------------------------------------------------
    # Factory presets
    # ------------------------------------------------------------------

    @classmethod
    def static(
        cls,
        total_laps: int,
        condition: WeatherCondition = WeatherCondition.DRY,
    ) -> "WeatherSystem":
        """Create a weather system with no changes throughout the race."""
        return cls(total_laps=total_laps, initial_condition=condition)

    @classmethod
    def dry_to_wet(
        cls,
        total_laps: int,
        rain_start_lap: Optional[int] = None,
        rain_condition: WeatherCondition = WeatherCondition.LIGHT_RAIN,
        transition_laps: int = 3,
    ) -> "WeatherSystem":
        """
        Race starts dry, rain begins at ``rain_start_lap``
        (defaults to 40 % through the race).
        """
        if rain_start_lap is None:
            rain_start_lap = max(1, int(total_laps * 0.40))
        ws = cls(total_laps=total_laps, initial_condition=WeatherCondition.DRY)
        ws.add_event(WeatherEvent(
            lap=rain_start_lap,
            condition=rain_condition,
            transition_laps=transition_laps,
        ))
        return ws

    @classmethod
    def wet_to_dry(
        cls,
        total_laps: int,
        dry_start_lap: Optional[int] = None,
        initial_rain: WeatherCondition = WeatherCondition.LIGHT_RAIN,
        transition_laps: int = 3,
    ) -> "WeatherSystem":
        """Race starts wet, track dries from ``dry_start_lap``."""
        if dry_start_lap is None:
            dry_start_lap = max(1, int(total_laps * 0.45))
        ws = cls(total_laps=total_laps, initial_condition=initial_rain)
        ws.add_event(WeatherEvent(
            lap=dry_start_lap,
            condition=WeatherCondition.DRY,
            transition_laps=transition_laps,
        ))
        return ws

    @classmethod
    def mixed_conditions(
        cls,
        total_laps: int,
        seed: Optional[int] = None,
    ) -> "WeatherSystem":
        """
        Generates a realistic-feeling mixed-conditions race:
          Dry → Light Rain → Heavy Rain → Dry
        with randomly jittered transition laps.
        """
        rng = random.Random(seed)
        ws  = cls(total_laps=total_laps, initial_condition=WeatherCondition.DRY)

        lap_light = max(2,  int(total_laps * rng.uniform(0.20, 0.35)))
        lap_heavy = max(lap_light + 3, int(total_laps * rng.uniform(0.45, 0.58)))
        lap_clear = max(lap_heavy + 3, int(total_laps * rng.uniform(0.68, 0.82)))

        ws.add_event(WeatherEvent(lap_light, WeatherCondition.LIGHT_RAIN, transition_laps=2))
        ws.add_event(WeatherEvent(lap_heavy, WeatherCondition.HEAVY_RAIN, transition_laps=2))
        if lap_clear < total_laps - 2:
            ws.add_event(WeatherEvent(lap_clear, WeatherCondition.DRY, transition_laps=3))

        return ws

    @classmethod
    def random_race(
        cls,
        total_laps: int,
        wet_probability: float = 0.40,
        seed: Optional[int] = None,
    ) -> "WeatherSystem":
        """
        Returns either a fully dry race or mixed conditions based on
        ``wet_probability``.  Useful for Monte-Carlo simulations.
        """
        rng = random.Random(seed)
        if rng.random() < wet_probability:
            return cls.mixed_conditions(total_laps=total_laps, seed=seed)
        return cls.static(total_laps=total_laps, condition=WeatherCondition.DRY)


# ---------------------------------------------------------------------------
# WeatherEffect — stateless helper applied in physics calculations
# ---------------------------------------------------------------------------

class WeatherEffect:
    """
    Stateless methods that apply WeatherState multipliers to car physics.

    These are called from RaceSimulator; keeping them here makes the
    weather<→physics contract explicit and testable in isolation.
    """

    @staticmethod
    def effective_grip(base_grip: float, state: WeatherState) -> float:
        """Track-surface grip reduction on top of tyre degradation."""
        return base_grip * state.track_grip_factor

    @staticmethod
    def effective_max_speed(car_max_speed: float, state: WeatherState) -> float:
        """Cap achievable speed in wet conditions."""
        return car_max_speed * state.max_speed_factor

    @staticmethod
    def effective_acceleration(base_accel: float, state: WeatherState) -> float:
        """Additional traction limit from wet tarmac."""
        return base_accel * state.acceleration_factor

    @staticmethod
    def effective_wear_laps(laps: float, state: WeatherState) -> float:
        """Scale lap-count for tyre wear by weather wear multiplier."""
        return laps * state.wear_multiplier

    @staticmethod
    def laptime_velocity_bleed(
        laptime_penalty_s: float,
        bleed_scale: float = 0.002,
    ) -> float:
        """
        Convert a lap-time penalty into a per-step velocity reduction.

        The same mechanism used for tyre degradation bleed; both are
        additive in ``_update_car_physics``.
        """
        return laptime_penalty_s * bleed_scale
