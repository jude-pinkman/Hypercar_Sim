"""
Tests for WeatherSystem (app/weather.py) and its integration
with RaceSimulator (app/race_simulator.py).

Run with:  python app/test_weather.py
      or:  python -m pytest app/test_weather.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.weather import (
    WeatherCondition, WeatherParams, WeatherState,
    WeatherEvent, WeatherSystem, WeatherEffect,
    WEATHER_PARAMS,
)
from app.race_simulator import RaceSimulator, Car
from app.pit_stop import RaceStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_sim(
    total_laps: int = 20,
    timestep: float = 0.5,
    weather: WeatherSystem = None,
) -> RaceSimulator:
    return RaceSimulator(
        circuit_length=5500.0,
        total_laps=total_laps,
        timestep=timestep,
        enable_tyre_degradation=True,
        default_strategy=RaceStrategy.TWO_STOP,
        weather=weather,
    )


def add_car(sim, name="Driver", speed=90.0):
    return sim.add_car(name, "Team", speed, 11.0, 0.90, 0.72)


# ---------------------------------------------------------------------------
# WeatherParams / WEATHER_PARAMS
# ---------------------------------------------------------------------------

class TestWeatherParams:
    def test_all_conditions_have_specs(self):
        for cond in WeatherCondition:
            assert cond in WEATHER_PARAMS

    def test_dry_is_neutral(self):
        p = WEATHER_PARAMS[WeatherCondition.DRY]
        assert p.track_grip_factor   == 1.00
        assert p.wear_multiplier     == 1.00
        assert p.laptime_penalty_s   == 0.00
        assert p.max_speed_factor    == 1.00
        assert p.acceleration_factor == 1.00

    def test_grip_ordering(self):
        dry   = WEATHER_PARAMS[WeatherCondition.DRY].track_grip_factor
        light = WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN].track_grip_factor
        heavy = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].track_grip_factor
        assert dry > light > heavy

    def test_laptime_penalty_ordering(self):
        dry   = WEATHER_PARAMS[WeatherCondition.DRY].laptime_penalty_s
        light = WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN].laptime_penalty_s
        heavy = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].laptime_penalty_s
        assert dry < light < heavy

    def test_max_speed_ordering(self):
        dry   = WEATHER_PARAMS[WeatherCondition.DRY].max_speed_factor
        light = WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN].max_speed_factor
        heavy = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].max_speed_factor
        assert dry >= light >= heavy

    def test_acceleration_ordering(self):
        dry   = WEATHER_PARAMS[WeatherCondition.DRY].acceleration_factor
        light = WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN].acceleration_factor
        heavy = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].acceleration_factor
        assert dry > light > heavy

    def test_all_multipliers_positive(self):
        for cond, p in WEATHER_PARAMS.items():
            assert p.track_grip_factor   > 0, cond
            assert p.wear_multiplier     > 0, cond
            assert p.laptime_penalty_s   >= 0, cond
            assert p.max_speed_factor    > 0, cond
            assert p.acceleration_factor > 0, cond

    def test_icons_present(self):
        for cond, p in WEATHER_PARAMS.items():
            assert len(p.icon) > 0, f"{cond} has no icon"


# ---------------------------------------------------------------------------
# WeatherState
# ---------------------------------------------------------------------------

class TestWeatherState:
    def test_apply_copies_all_fields(self):
        state  = WeatherState()
        params = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN]
        state.apply(params)
        assert state.condition         == params.condition
        assert state.track_grip_factor == params.track_grip_factor
        assert state.wear_multiplier   == params.wear_multiplier
        assert state.laptime_penalty_s == params.laptime_penalty_s
        assert state.max_speed_factor  == params.max_speed_factor
        assert not state.transitioning
        assert state.transition_progress == 1.0

    def test_interpolate_midpoint(self):
        state  = WeatherState()
        old    = WEATHER_PARAMS[WeatherCondition.DRY]
        new    = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN]
        state.interpolate(old, new, 0.5)
        assert abs(state.track_grip_factor - (old.track_grip_factor + new.track_grip_factor) / 2) < 1e-6
        assert abs(state.laptime_penalty_s - (old.laptime_penalty_s + new.laptime_penalty_s) / 2) < 1e-6
        assert state.transitioning

    def test_interpolate_at_zero_equals_old(self):
        state = WeatherState()
        old   = WEATHER_PARAMS[WeatherCondition.DRY]
        new   = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN]
        state.interpolate(old, new, 0.0)
        assert abs(state.track_grip_factor - old.track_grip_factor) < 1e-6

    def test_interpolate_at_one_equals_new(self):
        state = WeatherState()
        old   = WEATHER_PARAMS[WeatherCondition.DRY]
        new   = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN]
        state.interpolate(old, new, 1.0)
        assert abs(state.track_grip_factor - new.track_grip_factor) < 1e-6
        assert not state.transitioning

    def test_summary_string_non_empty(self):
        state = WeatherState()
        state.apply(WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN])
        assert len(state.summary()) > 0
        assert "Rain" in state.summary()


# ---------------------------------------------------------------------------
# WeatherSystem — basic lifecycle
# ---------------------------------------------------------------------------

class TestWeatherSystemBasic:
    def test_initial_condition_applied(self):
        ws = WeatherSystem(50, WeatherCondition.HEAVY_RAIN)
        assert ws.condition == WeatherCondition.HEAVY_RAIN
        assert ws.current_state.track_grip_factor == WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].track_grip_factor

    def test_static_never_changes(self):
        ws = WeatherSystem.static(50, WeatherCondition.DRY)
        for lap in range(1, 51):
            ws.advance(lap)
        assert ws.condition == WeatherCondition.DRY

    def test_add_event_fires_at_correct_lap(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=10, condition=WeatherCondition.LIGHT_RAIN, transition_laps=0))
        for lap in range(1, 10):
            ws.advance(lap)
        assert ws.condition == WeatherCondition.DRY
        ws.advance(10)
        assert ws.condition == WeatherCondition.LIGHT_RAIN

    def test_instantaneous_transition(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=5, condition=WeatherCondition.HEAVY_RAIN, transition_laps=0))
        ws.advance(5)
        assert ws.current_state.track_grip_factor == WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].track_grip_factor
        assert not ws.current_state.transitioning

    def test_smooth_transition_interpolates(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=10, condition=WeatherCondition.HEAVY_RAIN, transition_laps=4))
        ws.advance(10)   # transition begins
        ws.advance(11)   # 25 % through
        ws.advance(12)   # 50 % through
        # During transition, grip should be between dry and heavy-rain values
        dry_grip   = WEATHER_PARAMS[WeatherCondition.DRY].track_grip_factor
        heavy_grip = WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].track_grip_factor
        assert heavy_grip < ws.current_state.track_grip_factor < dry_grip

    def test_transition_completes_after_window(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=10, condition=WeatherCondition.HEAVY_RAIN, transition_laps=3))
        for lap in range(10, 15):
            ws.advance(lap)
        # Should have reached heavy rain fully
        assert abs(ws.current_state.track_grip_factor - WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN].track_grip_factor) < 1e-6
        assert not ws.current_state.transitioning

    def test_multiple_events_fire_in_sequence(self):
        ws = WeatherSystem(60, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=10, condition=WeatherCondition.LIGHT_RAIN, transition_laps=0))
        ws.add_event(WeatherEvent(lap=30, condition=WeatherCondition.HEAVY_RAIN, transition_laps=0))
        ws.add_event(WeatherEvent(lap=50, condition=WeatherCondition.DRY, transition_laps=0))
        ws.advance(10)
        assert ws.condition == WeatherCondition.LIGHT_RAIN
        ws.advance(30)
        assert ws.condition == WeatherCondition.HEAVY_RAIN
        ws.advance(50)
        assert ws.condition == WeatherCondition.DRY

    def test_history_records_transitions(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=15, condition=WeatherCondition.LIGHT_RAIN, transition_laps=0))
        ws.add_event(WeatherEvent(lap=30, condition=WeatherCondition.HEAVY_RAIN, transition_laps=0))
        for lap in range(1, 40):
            ws.advance(lap)
        assert len(ws.history) == 2
        assert ws.history[0] == (15, WeatherCondition.LIGHT_RAIN)
        assert ws.history[1] == (30, WeatherCondition.HEAVY_RAIN)

    def test_forecast_shrinks_as_events_fire(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=10, condition=WeatherCondition.LIGHT_RAIN, transition_laps=0))
        ws.add_event(WeatherEvent(lap=30, condition=WeatherCondition.HEAVY_RAIN, transition_laps=0))
        assert len(ws.forecast()) == 2
        ws.advance(10)
        assert len(ws.forecast()) == 1
        ws.advance(30)
        assert len(ws.forecast()) == 0

    def test_is_wet_is_dry(self):
        ws = WeatherSystem(50, WeatherCondition.DRY)
        assert ws.is_dry()
        assert not ws.is_wet()
        ws.add_event(WeatherEvent(lap=1, condition=WeatherCondition.LIGHT_RAIN, transition_laps=0))
        ws.advance(1)
        assert ws.is_wet()
        assert not ws.is_dry()


# ---------------------------------------------------------------------------
# WeatherSystem — factory presets
# ---------------------------------------------------------------------------

class TestWeatherSystemFactories:
    def test_dry_to_wet_starts_dry(self):
        ws = WeatherSystem.dry_to_wet(50, rain_start_lap=20)
        assert ws.condition == WeatherCondition.DRY

    def test_dry_to_wet_becomes_wet(self):
        ws = WeatherSystem.dry_to_wet(50, rain_start_lap=5, transition_laps=0)
        ws.advance(5)
        assert ws.is_wet()

    def test_wet_to_dry_starts_wet(self):
        ws = WeatherSystem.wet_to_dry(50)
        assert ws.is_wet()

    def test_wet_to_dry_becomes_dry(self):
        ws = WeatherSystem.wet_to_dry(50, dry_start_lap=5, transition_laps=0)
        ws.advance(5)
        assert ws.is_dry()

    def test_mixed_conditions_has_multiple_events(self):
        ws = WeatherSystem.mixed_conditions(50, seed=42)
        assert len(ws._events) >= 2

    def test_random_race_is_deterministic_with_seed(self):
        ws1 = WeatherSystem.random_race(50, seed=99)
        ws2 = WeatherSystem.random_race(50, seed=99)
        assert ws1.condition == ws2.condition
        assert len(ws1._events) == len(ws2._events)

    def test_static_heavy_rain_full_race(self):
        ws = WeatherSystem.static(50, WeatherCondition.HEAVY_RAIN)
        for lap in range(1, 51):
            ws.advance(lap)
        assert ws.condition == WeatherCondition.HEAVY_RAIN


# ---------------------------------------------------------------------------
# WeatherEffect — static methods
# ---------------------------------------------------------------------------

class TestWeatherEffect:
    def _heavy_state(self):
        s = WeatherState()
        s.apply(WEATHER_PARAMS[WeatherCondition.HEAVY_RAIN])
        return s

    def _dry_state(self):
        s = WeatherState()
        s.apply(WEATHER_PARAMS[WeatherCondition.DRY])
        return s

    def test_effective_grip_reduced_in_rain(self):
        dry   = self._dry_state()
        heavy = self._heavy_state()
        grip  = 0.90
        assert WeatherEffect.effective_grip(grip, heavy) < WeatherEffect.effective_grip(grip, dry)

    def test_effective_grip_dry_unchanged(self):
        state = self._dry_state()
        assert WeatherEffect.effective_grip(0.90, state) == 0.90

    def test_effective_max_speed_reduced_in_rain(self):
        dry   = self._dry_state()
        heavy = self._heavy_state()
        assert WeatherEffect.effective_max_speed(100, heavy) < WeatherEffect.effective_max_speed(100, dry)

    def test_effective_acceleration_reduced_in_rain(self):
        heavy = self._heavy_state()
        dry   = self._dry_state()
        assert WeatherEffect.effective_acceleration(12.0, heavy) < WeatherEffect.effective_acceleration(12.0, dry)

    def test_effective_wear_laps_heavy_rain_increases(self):
        heavy = self._heavy_state()
        assert WeatherEffect.effective_wear_laps(1.0, heavy) > 1.0

    def test_effective_wear_laps_light_rain_decreases(self):
        state = WeatherState()
        state.apply(WEATHER_PARAMS[WeatherCondition.LIGHT_RAIN])
        assert WeatherEffect.effective_wear_laps(1.0, state) < 1.0

    def test_laptime_velocity_bleed_scales_correctly(self):
        penalty = 10.0
        bleed   = WeatherEffect.laptime_velocity_bleed(penalty, bleed_scale=0.002)
        assert abs(bleed - 0.02) < 1e-9

    def test_laptime_velocity_bleed_zero_for_dry(self):
        dry   = self._dry_state()
        bleed = WeatherEffect.laptime_velocity_bleed(dry.laptime_penalty_s)
        assert bleed == 0.0


# ---------------------------------------------------------------------------
# RaceSimulator integration
# ---------------------------------------------------------------------------

class TestRaceSimulatorWeatherIntegration:
    def test_default_weather_is_dry(self):
        sim = make_sim()
        assert sim.weather.condition == WeatherCondition.DRY

    def test_custom_weather_accepted(self):
        ws  = WeatherSystem.static(20, WeatherCondition.LIGHT_RAIN)
        sim = make_sim(weather=ws)
        assert sim.weather.condition == WeatherCondition.LIGHT_RAIN

    def test_heavy_rain_slows_cars(self):
        # Dry race
        sim_dry = make_sim(weather=WeatherSystem.static(15, WeatherCondition.DRY))
        add_car(sim_dry, "Dry")
        res_dry = sim_dry.run_simulation(verbose=False)

        # Heavy rain race, same car
        sim_wet = make_sim(weather=WeatherSystem.static(15, WeatherCondition.HEAVY_RAIN))
        add_car(sim_wet, "Wet")
        res_wet = sim_wet.run_simulation(verbose=False)

        assert res_wet[0]['finish_time'] > res_dry[0]['finish_time']

    def test_light_rain_slower_than_dry_faster_than_heavy(self):
        def finish_time(cond):
            ws  = WeatherSystem.static(15, cond)
            sim = make_sim(weather=ws)
            add_car(sim)
            return sim.run_simulation(verbose=False)[0]['finish_time']

        t_dry   = finish_time(WeatherCondition.DRY)
        t_light = finish_time(WeatherCondition.LIGHT_RAIN)
        t_heavy = finish_time(WeatherCondition.HEAVY_RAIN)
        assert t_dry < t_light < t_heavy

    def test_results_include_weather_conditions(self):
        ws  = WeatherSystem.dry_to_wet(20, rain_start_lap=5, transition_laps=0)
        sim = make_sim(weather=ws)
        add_car(sim)
        results = sim.run_simulation(verbose=False)
        assert 'weather_conditions' in results[0]

    def test_weather_log_populated_after_race(self):
        sim = make_sim()
        add_car(sim)
        sim.run_simulation(verbose=False)
        assert len(sim._weather_log) > 0

    def test_weather_history_recorded_on_transition(self):
        ws = WeatherSystem(20, WeatherCondition.DRY)
        ws.add_event(WeatherEvent(lap=5, condition=WeatherCondition.HEAVY_RAIN, transition_laps=0))
        sim = make_sim(weather=ws)
        add_car(sim)
        sim.run_simulation(verbose=False)
        assert len(sim.weather.history) >= 1
        assert sim.weather.history[0][1] == WeatherCondition.HEAVY_RAIN

    def test_reset_clears_weather_log(self):
        sim = make_sim()
        add_car(sim)
        sim.run_simulation(verbose=False)
        sim.reset()
        assert sim._weather_log == []

    def test_simulation_completes_in_all_conditions(self):
        for cond in WeatherCondition:
            ws  = WeatherSystem.static(10, cond)
            sim = make_sim(total_laps=10, weather=ws)
            for i in range(3):
                sim.add_car(f"D{i}", "T", 90.0 - i, 11.0, 0.90, 0.72)
            results = sim.run_simulation(verbose=False)
            assert len(results) == 3, f"Failed for condition {cond}"

    def test_mixed_conditions_race_completes(self):
        ws  = WeatherSystem.mixed_conditions(20, seed=7)
        sim = make_sim(total_laps=20, weather=ws)
        for i in range(5):
            sim.add_car(f"D{i}", "T", 90.0 - i, 11.0, 0.90, 0.72)
        results = sim.run_simulation(verbose=False)
        assert len(results) == 5

    def test_wear_multiplier_reaches_pit_manager(self):
        """Heavy rain should accelerate tyre wear → cars pit earlier."""
        def avg_first_pit_lap(cond):
            ws  = WeatherSystem.static(30, cond)
            sim = RaceSimulator(
                circuit_length=5500.0, total_laps=30, timestep=0.5,
                enable_tyre_degradation=True,
                default_strategy=RaceStrategy.ONE_STOP,
                weather=ws,
            )
            sim.add_car("D", "T", 90.0, 11.0, 0.90, 0.72)
            sim.run_simulation(verbose=False)
            stops = sim.pit_manager.stops_for_driver("D")
            return stops[0].lap if stops else 999

        lap_dry   = avg_first_pit_lap(WeatherCondition.DRY)
        lap_heavy = avg_first_pit_lap(WeatherCondition.HEAVY_RAIN)
        # Heavy rain accelerates wear → first pit comes no later than dry
        assert lap_heavy <= lap_dry

    def test_full_grid_mixed_weather(self):
        from app.race_simulator import create_f1_grid
        ws  = WeatherSystem.mixed_conditions(20, seed=42)
        sim = RaceSimulator(
            circuit_length=5500.0, total_laps=20, timestep=0.5,
            enable_tyre_degradation=True,
            default_strategy=RaceStrategy.TWO_STOP,
            weather=ws,
        )
        for spec in create_f1_grid():
            sim.add_car(**spec)
        results = sim.run_simulation(verbose=False)
        assert len(results) == 22
        assert all("weather_conditions" in r for r in results)


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_classes = [
        TestWeatherParams,
        TestWeatherState,
        TestWeatherSystemBasic,
        TestWeatherSystemFactories,
        TestWeatherEffect,
        TestRaceSimulatorWeatherIntegration,
    ]
    passed = failed = 0
    for cls in test_classes:
        print(f"\n── {cls.__name__} ──")
        obj = cls()
        for name in sorted(n for n in dir(cls) if n.startswith("test_")):
            try:
                getattr(obj, name)()
                print(f"  ✅ {name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

    print(f"\n{'='*60}")
    print(f"  {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
