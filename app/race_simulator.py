"""
F1 Race Simulator - Physics Engine for 22-Car Grid
Extends Hypercar_Sim to support full Formula 1 grid racing
"""

import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from app.tyre import (
    Tyre, TyreCompound, TyreStrategy, TyreDegradationModel,
    COMPOUND_SPECS,
)
from app.pit_stop import (
    PitStopManager, RaceStrategy, PitStopRecord,
    assign_grid_strategies, STRATEGY_TEMPLATES,
)
from app.weather import (
    WeatherSystem, WeatherState, WeatherCondition,
    WeatherEffect, WeatherEvent, WEATHER_PARAMS,
)


@dataclass
class Car:
    """Individual car with physics properties and state"""
    driver_name: str
    team: str
    max_speed: float       # m/s
    acceleration: float    # m/s²
    tyre_grip: float       # 0.0-1.0 (base value; degradation scales this)
    drag_coefficient: float

    position: float = 0.0
    velocity: float = 0.0
    lap: int = 0
    finished: bool = False
    finish_time: float = None

    # ── Tyre degradation ─────────────────────────────────────────────────
    tyre_strategy: Optional[TyreStrategy] = field(default=None, repr=False)
    _base_tyre_grip: float = field(default=0.0, init=False, repr=False)

    # ── Pit stop state ───────────────────────────────────────────────────
    # Seconds of pit service remaining; > 0 means car is stationary in box
    pit_stop_remaining: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._base_tyre_grip = self.tyre_grip

    # ------------------------------------------------------------------
    # Degradation-aware property helpers
    # ------------------------------------------------------------------

    @property
    def current_tyre(self) -> Optional[Tyre]:
        return self.tyre_strategy.current_tyre if self.tyre_strategy else None

    @property
    def is_in_pit(self) -> bool:
        return self.pit_stop_remaining > 0.0

    @property
    def effective_tyre_grip(self) -> float:
        """Base grip scaled by current tyre compound & wear."""
        if self.tyre_strategy is None:
            return self.tyre_grip
        return TyreDegradationModel.effective_tyre_grip(
            self._base_tyre_grip, self.tyre_strategy.current_tyre
        )

    @property
    def effective_acceleration(self) -> float:
        """Acceleration scaled by tyre traction availability."""
        if self.tyre_strategy is None:
            return self.acceleration
        return TyreDegradationModel.effective_acceleration(
            self.acceleration, self.tyre_strategy.current_tyre
        )

    @property
    def tyre_laptime_penalty(self) -> float:
        """Extra seconds per lap from tyre degradation."""
        if self.tyre_strategy is None:
            return 0.0
        return self.tyre_strategy.current_tyre.laptime_delta_s


class RaceSimulator:
    """
    Manages race simulation for multiple cars with realistic physics.

    Pit stop decisions are fully delegated to ``PitStopManager``.
    Weather effects are applied every physics step via ``WeatherSystem``.
    """

    def __init__(
        self,
        circuit_length: float = 5500.0,
        total_laps: int = 50,
        timestep: float = 0.1,
        enable_tyre_degradation: bool = True,
        default_strategy: RaceStrategy = RaceStrategy.TWO_STOP,
        weather: Optional[WeatherSystem] = None,
    ):
        self.circuit_length          = circuit_length
        self.total_laps              = total_laps
        self.timestep                = timestep
        self.enable_tyre_degradation = enable_tyre_degradation
        self.default_strategy        = default_strategy

        # Weather: defaults to static dry if not provided
        self.weather: WeatherSystem = (
            weather if weather is not None
            else WeatherSystem.static(total_laps, WeatherCondition.DRY)
        )

        self.cars:         List[Car]   = []
        self.race_time:    float       = 0.0
        self.race_active:  bool        = False
        self.results:      List[Dict]  = []

        self.pit_manager: Optional[PitStopManager] = None
        self._strategy_overrides: Dict[str, RaceStrategy] = {}

        # Lap-level weather log: [(lap, WeatherState.summary())]
        self._weather_log: List[Tuple[int, str]] = []

    # ------------------------------------------------------------------
    # Car registration
    # ------------------------------------------------------------------

    def add_car(
        self,
        driver_name: str,
        team: str,
        max_speed: float,
        acceleration: float,
        tyre_grip: float,
        drag_coefficient: float,
        strategy: RaceStrategy = None,
        tyre_strategy: Optional[TyreStrategy] = None,
    ) -> Car:
        """
        Add a car to the race.

        Parameters
        ----------
        strategy:
            Named RaceStrategy (ONE_STOP / TWO_STOP / AGGRESSIVE).
            If provided, overrides ``default_strategy`` for this car.
            Ignored when ``tyre_strategy`` is passed directly.
        tyre_strategy:
            An already-constructed TyreStrategy.  When supplied the car
            bypasses PitStopManager scheduling and uses legacy worn-out
            detection only.  Useful for testing.
        """
        car = Car(driver_name, team, max_speed, acceleration, tyre_grip, drag_coefficient)

        if self.enable_tyre_degradation:
            if tyre_strategy is not None:
                # Legacy / test path: attach strategy directly
                car.tyre_strategy = tyre_strategy
            else:
                # Pit manager path: record override for later registration
                if strategy is not None:
                    self._strategy_overrides[driver_name] = strategy

        self.cars.append(car)
        return car

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------

    def _calculate_acceleration(self, car: Car) -> float:
        """
        Calculate effective acceleration integrating tyre degradation
        and live weather conditions.

        Composition order (each layer multiplies on top of the previous):
          1. car.effective_tyre_grip   — base grip × tyre wear multiplier
          2. WeatherEffect.effective_grip  — track surface grip reduction
          3. WeatherEffect.effective_acceleration — wet-tarmac traction limit
          4. drag_force subtracted
        """
        ws = self.weather.current_state

        # Grip: tyre degradation first, then weather track-surface factor
        grip_factor  = WeatherEffect.effective_grip(car.effective_tyre_grip, ws)

        # Acceleration: base capability, weather traction limit, then grip
        accel_base   = WeatherEffect.effective_acceleration(car.effective_acceleration, ws)

        # Speed ceiling: weather caps usable top speed
        effective_max_speed = WeatherEffect.effective_max_speed(car.max_speed, ws)

        drag_force   = car.drag_coefficient * (car.velocity ** 2) * 0.001
        speed_ratio  = car.velocity / effective_max_speed if effective_max_speed > 0 else 1.0
        speed_factor = 1.0 - (speed_ratio ** 2)

        effective_accel = accel_base * grip_factor * speed_factor - drag_force
        if car.velocity >= effective_max_speed:
            effective_accel = min(0, effective_accel)
        return effective_accel

    def _update_car_physics(self, car: Car) -> None:
        """Update position and velocity for one timestep, honouring pit stops and weather."""
        if car.finished:
            return

        ws = self.weather.current_state

        # ── Pit stop in progress ─────────────────────────────────────
        if self.pit_manager and self.pit_manager.is_in_pit(car.driver_name):
            still_pitting = self.pit_manager.tick(car.driver_name, self.timestep)
            car.velocity = 0.0
            if not still_pitting:
                car.velocity = 15.0  # pit-exit speed limit (m/s)
            return

        # Legacy path: TyreStrategy attached directly (no manager)
        if car.is_in_pit:
            car.pit_stop_remaining -= self.timestep
            car.velocity = 0.0
            if car.pit_stop_remaining <= 0.0:
                car.pit_stop_remaining = 0.0
                car.velocity = 15.0
            return

        # ── Normal racing physics ────────────────────────────────────
        accel        = self._calculate_acceleration(car)
        car.velocity += accel * self.timestep

        # Effective speed ceiling (weather-aware)
        effective_max = WeatherEffect.effective_max_speed(car.max_speed, ws)
        car.velocity  = max(0.0, min(car.velocity, effective_max))

        # Velocity bleed: tyre degradation penalty + weather lap-time penalty
        if self.enable_tyre_degradation and car.tyre_strategy:
            tyre_bleed    = WeatherEffect.laptime_velocity_bleed(car.tyre_laptime_penalty)
            weather_bleed = WeatherEffect.laptime_velocity_bleed(ws.laptime_penalty_s)
            car.velocity  = max(0.0, car.velocity - tyre_bleed - weather_bleed)

        car.position += car.velocity * self.timestep

        # ── Lap completion ────────────────────────────────────────────
        completed_laps = int(car.position / self.circuit_length)
        if completed_laps > car.lap:
            car.lap = completed_laps

            # Advance weather once per lap (only on first car to cross — handled
            # in simulate_step instead; here we just read current state)
            if self.enable_tyre_degradation:
                wear_mult = ws.wear_multiplier
                if self.pit_manager and car.driver_name in self.pit_manager._plans:
                    self.pit_manager.notify_lap_complete(
                        car.driver_name, car.lap, self.race_time,
                        wear_multiplier=wear_mult,
                    )
                elif car.tyre_strategy:
                    # Legacy path
                    car.tyre_strategy.current_tyre.advance_laps(wear_mult)
                    if car.tyre_strategy.should_pit():
                        car.tyre_strategy.pit_stop(car.lap)

        # ── Race finish ───────────────────────────────────────────────
        if car.lap >= self.total_laps and not car.finished:
            car.finished    = True
            car.finish_time = self.race_time
            self.results.append({
                'position':    len(self.results) + 1,
                'driver':      car.driver_name,
                'team':        car.team,
                'finish_time': car.finish_time,
                'laps':        car.lap,
                'pit_stops':   (
                    self.pit_manager.stops_for_driver(car.driver_name)
                    if self.pit_manager else []
                ),
                'tyre_stints': (
                    car.tyre_strategy.pit_history
                    if car.tyre_strategy else []
                ),
                'weather_conditions': [w for _, w in self._weather_log],
            })

    # ------------------------------------------------------------------
    # Race control
    # ------------------------------------------------------------------

    def get_race_positions(self) -> List[Tuple[int, str, str, int, float]]:
        """Get current race positions sorted by total distance."""
        positions = []
        for car in self.cars:
            distance_in_lap = car.position - (car.lap * self.circuit_length)
            positions.append({
                'car':            car,
                'total_distance': car.position,
                'lap':            car.lap,
                'distance_in_lap': distance_in_lap,
            })
        positions.sort(key=lambda x: x['total_distance'], reverse=True)
        result = []
        for idx, data in enumerate(positions):
            car = data['car']
            result.append((idx + 1, car.driver_name, car.team,
                           data['lap'], data['distance_in_lap']))
        return result

    def simulate_step(self) -> bool:
        """Simulate one timestep for all cars, advancing weather each new lap."""
        if not self.race_active:
            return False

        # Advance weather at the start of each new lap boundary
        # Use the leading car's lap count as the reference lap
        if self.cars:
            leading_lap = max(c.lap for c in self.cars if not c.finished) \
                          if any(not c.finished for c in self.cars) else 0
            last_logged_lap = self._weather_log[-1][0] if self._weather_log else -1
            if leading_lap > last_logged_lap:
                state = self.weather.advance(leading_lap)
                summary = state.summary()
                self._weather_log.append((leading_lap, summary))

        for car in self.cars:
            self._update_car_physics(car)

        self.race_time += self.timestep

        if all(car.finished for car in self.cars):
            self.race_active = False
            return False
        return True

    def run_simulation(
        self,
        verbose: bool = True,
        update_interval: float = 5.0,
    ) -> List[Dict]:
        """
        Run the complete race simulation.

        On first call, a PitStopManager is created and all cars that don't
        already have a manual tyre_strategy are registered with it.
        """
        # ── Bootstrap PitStopManager ──────────────────────────────────
        if self.enable_tyre_degradation:
            self.pit_manager = PitStopManager(total_laps=self.total_laps)
            for car in self.cars:
                if car.tyre_strategy is None:
                    strategy = self._strategy_overrides.get(
                        car.driver_name, self.default_strategy
                    )
                    ts = self.pit_manager.register_car(car.driver_name, strategy)
                    car.tyre_strategy = ts

        self.race_active  = True
        self.race_time    = 0.0
        self.results      = []
        self._weather_log = []

        if verbose:
            ws   = self.weather.current_state
            fore = self.weather.forecast()
            print(f"\n{'='*90}")
            print(f"RACE START — {len(self.cars)} cars | "
                  f"{self.total_laps} laps | "
                  f"{self.circuit_length/1000:.2f} km circuit")
            print(f"\n🌤️  WEATHER: {ws.summary()}")
            if fore:
                print("📅  FORECAST:")
                for ev in fore:
                    params = WEATHER_PARAMS[ev.condition]
                    print(f"     Lap {ev.lap:>3}  →  {params.icon} {params.description}"
                          f"  (transition: {ev.transition_laps} laps)")
            if self.pit_manager:
                print(f"\n📋 PIT STRATEGIES:")
                print(self.pit_manager.strategy_summary())
            print(f"{'='*90}\n")

        last_update = 0.0
        while self.simulate_step():
            if verbose and (self.race_time - last_update) >= update_interval:
                self._print_race_status()
                last_update = self.race_time

        if verbose:
            print(f"\n{'='*90}")
            print("RACE COMPLETE")
            print(f"{'='*90}\n")
            self._print_final_results()

        return self.results

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _print_race_status(self) -> None:
        """Print current race status with tyre, pit, and weather info."""
        positions = self.get_race_positions()
        ws = self.weather.current_state
        params = WEATHER_PARAMS[ws.condition]
        print(f"\n⏱️  Race Time: {self.race_time:.1f}s  |  "
              f"{params.icon} {ws.summary()}")
        print(f"{'Pos':<5} {'Driver':<20} {'Team':<20} "
              f"{'Lap':<5} {'km/h':<8} {'Tyre':<8} {'Wear%':<7} {'Status'}")
        print("─" * 90)
        for i in range(min(5, len(positions))):
            pos, driver, team, lap, _ = positions[i]
            car      = next(c for c in self.cars if c.driver_name == driver)
            speed_kmh = car.velocity * 3.6
            tyre_str  = wear_str = "—"
            status    = "racing"
            if car.current_tyre:
                s        = car.current_tyre.get_status()
                tyre_str = s['compound'].upper()
                wear_str = f"{s['wear_pct']:.0f}%"
            if self.pit_manager and self.pit_manager.is_in_pit(driver):
                plan   = self.pit_manager.get_plan(driver)
                status = f"🔧 PIT {plan.pit_time_remaining:.1f}s"
            print(f"{pos:<5} {driver:<20} {team:<20} "
                  f"{lap:<5} {speed_kmh:<8.1f} {tyre_str:<8} {wear_str:<7} {status}")

    def _print_final_results(self) -> None:
        """Print final race results with pit stop details."""
        print(f"\n🏁 FINAL RESULTS")
        print(f"{'Pos':<5} {'Driver':<20} {'Team':<25} "
              f"{'Time':<14} {'Gap':<10} {'Stops':<6} {'Strategy'}")
        print("═" * 100)

        if not self.results:
            print("No finishers")
            return

        winner_time = self.results[0]['finish_time']
        for result in self.results:
            gap_s    = result['finish_time'] - winner_time
            gap_str  = f"+{gap_s:.2f}s" if gap_s > 0 else "—"
            stops    = result.get('pit_stops', [])
            n_stops  = len(stops)

            # Build compound sequence from pit history
            stints   = result.get('tyre_stints', [])
            if stints:
                strat_str = " → ".join(
                    p['old_compound'].upper() for p in stints
                ) + " → " + stints[-1]['new_compound'].upper()
            elif result.get('pit_stops'):
                strat_str = " → ".join(
                    f"{s.old_compound.upper()}→{s.new_compound.upper()}"
                    for s in stops
                )
            else:
                strat_str = "no stops"

            print(f"{result['position']:<5} {result['driver']:<20} "
                  f"{result['team']:<25} {result['finish_time']:.2f}s    "
                  f"{gap_str:<10} {n_stops:<6} {strat_str}")

        # ── Weather history ───────────────────────────────────────────
        if self._weather_log:
            conditions_seen = {}
            for lap, summary in self._weather_log:
                cond = self.weather.current_state.condition.value
                if summary not in conditions_seen.values():
                    conditions_seen[lap] = summary
            history = self.weather.history
            if history:
                print(f"\n🌤️  WEATHER HISTORY")
                print("─" * 60)
                for lap, cond in history:
                    params = WEATHER_PARAMS[cond]
                    print(f"  Lap {lap:>3}  →  {params.icon} {params.description}")
            all_stops = self.pit_manager.all_stops
            if all_stops:
                print(f"\n🔧 PIT STOP LOG")
                print(f"{'Driver':<22} {'Lap':<5} {'Entry':>10} "
                      f"{'Exit':>10} {'Svc':>6} {'Change':<22} "
                      f"{'Wear%':<7} {'Trigger'}")
                print("─" * 100)
                for s in all_stops:
                    change = f"{s.old_compound.upper()} → {s.new_compound.upper()}"
                    print(f"{s.driver:<22} {s.lap:<5} "
                          f"{s.race_time_entry:>10.1f}s "
                          f"{s.race_time_exit:>10.1f}s "
                          f"{s.service_time:>5.2f}s  "
                          f"{change:<22} "
                          f"{s.wear_at_pit*100:>5.1f}%  "
                          f"{s.trigger}")

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset race state. Re-run ``run_simulation`` to start fresh."""
        self.race_time    = 0.0
        self.race_active  = False
        self.results      = []
        self.pit_manager  = None
        self._weather_log = []
        for car in self.cars:
            car.position           = 0.0
            car.velocity           = 0.0
            car.lap                = 0
            car.finished           = False
            car.finish_time        = None
            car.pit_stop_remaining = 0.0
            car.tyre_strategy      = None


def create_f1_grid() -> List[Dict]:
    """Create a realistic F1 grid with 22 cars"""
    f1_grid = [
        {"driver_name": "Max Verstappen", "team": "Red Bull Racing", "max_speed": 95.0, "acceleration": 12.5, "tyre_grip": 0.95, "drag_coefficient": 0.70},
        {"driver_name": "Sergio Perez", "team": "Red Bull Racing", "max_speed": 94.5, "acceleration": 12.3, "tyre_grip": 0.93, "drag_coefficient": 0.71},
        {"driver_name": "Charles Leclerc", "team": "Ferrari", "max_speed": 94.0, "acceleration": 12.2, "tyre_grip": 0.92, "drag_coefficient": 0.72},
        {"driver_name": "Carlos Sainz", "team": "Ferrari", "max_speed": 93.8, "acceleration": 12.1, "tyre_grip": 0.91, "drag_coefficient": 0.72},
        {"driver_name": "Lewis Hamilton", "team": "Mercedes", "max_speed": 93.5, "acceleration": 12.0, "tyre_grip": 0.91, "drag_coefficient": 0.73},
        {"driver_name": "George Russell", "team": "Mercedes", "max_speed": 93.3, "acceleration": 11.9, "tyre_grip": 0.90, "drag_coefficient": 0.73},
        {"driver_name": "Lando Norris", "team": "McLaren", "max_speed": 92.5, "acceleration": 11.7, "tyre_grip": 0.89, "drag_coefficient": 0.74},
        {"driver_name": "Oscar Piastri", "team": "McLaren", "max_speed": 92.3, "acceleration": 11.6, "tyre_grip": 0.88, "drag_coefficient": 0.74},
        {"driver_name": "Fernando Alonso", "team": "Aston Martin", "max_speed": 91.8, "acceleration": 11.5, "tyre_grip": 0.87, "drag_coefficient": 0.75},
        {"driver_name": "Lance Stroll", "team": "Aston Martin", "max_speed": 91.5, "acceleration": 11.4, "tyre_grip": 0.86, "drag_coefficient": 0.75},
        {"driver_name": "Pierre Gasly", "team": "Alpine", "max_speed": 90.5, "acceleration": 11.2, "tyre_grip": 0.85, "drag_coefficient": 0.76},
        {"driver_name": "Esteban Ocon", "team": "Alpine", "max_speed": 90.3, "acceleration": 11.1, "tyre_grip": 0.84, "drag_coefficient": 0.76},
        {"driver_name": "Alex Albon", "team": "Williams", "max_speed": 89.5, "acceleration": 11.0, "tyre_grip": 0.83, "drag_coefficient": 0.77},
        {"driver_name": "Logan Sargeant", "team": "Williams", "max_speed": 89.0, "acceleration": 10.9, "tyre_grip": 0.82, "drag_coefficient": 0.77},
        {"driver_name": "Valtteri Bottas", "team": "Alfa Romeo", "max_speed": 88.8, "acceleration": 10.8, "tyre_grip": 0.82, "drag_coefficient": 0.78},
        {"driver_name": "Zhou Guanyu", "team": "Alfa Romeo", "max_speed": 88.5, "acceleration": 10.7, "tyre_grip": 0.81, "drag_coefficient": 0.78},
        {"driver_name": "Nico Hulkenberg", "team": "Haas F1 Team", "max_speed": 88.0, "acceleration": 10.6, "tyre_grip": 0.80, "drag_coefficient": 0.79},
        {"driver_name": "Kevin Magnussen", "team": "Haas F1 Team", "max_speed": 87.8, "acceleration": 10.5, "tyre_grip": 0.79, "drag_coefficient": 0.79},
        {"driver_name": "Yuki Tsunoda", "team": "AlphaTauri", "max_speed": 87.5, "acceleration": 10.4, "tyre_grip": 0.79, "drag_coefficient": 0.80},
        {"driver_name": "Daniel Ricciardo", "team": "AlphaTauri", "max_speed": 87.3, "acceleration": 10.3, "tyre_grip": 0.78, "drag_coefficient": 0.80},
        {"driver_name": "Liam Lawson", "team": "Racing Bulls", "max_speed": 87.0, "acceleration": 10.2, "tyre_grip": 0.78, "drag_coefficient": 0.81},
        {"driver_name": "Ayumu Iwasa", "team": "Racing Bulls", "max_speed": 86.8, "acceleration": 10.1, "tyre_grip": 0.77, "drag_coefficient": 0.81},
    ]
    return f1_grid


def main():
    """Run a complete F1 race simulation"""
    simulator = RaceSimulator(circuit_length=5500.0, total_laps=50, timestep=0.1)
    
    f1_grid = create_f1_grid()
    for car_spec in f1_grid:
        simulator.add_car(**car_spec)
    
    print(f"Grid size: {len(simulator.cars)} cars")
    results = simulator.run_simulation(verbose=True, update_interval=10.0)
    
    print(f"\n📊 Race Statistics:")
    print(f"Total race distance: {simulator.circuit_length * simulator.total_laps / 1000:.1f} km")
    print(f"Race duration: {results[-1]['finish_time']:.1f} seconds ({results[-1]['finish_time']/60:.2f} minutes)")
    print(f"Winner: {results[0]['driver']} ({results[0]['team']})")
    print(f"Gap to last place: {results[-1]['finish_time'] - results[0]['finish_time']:.2f} seconds")


if __name__ == "__main__":
    main()
