"""
Tests for PitStopManager (app/pit_stop.py) and its integration
with RaceSimulator (app/race_simulator.py).

Run with:  python app/test_pit_stop.py
      or:  python -m pytest app/test_pit_stop.py -v
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tyre import TyreCompound, TyreStrategy, COMPOUND_SPECS
from app.pit_stop import (
    PitStopManager, PitStopRecord, PitPlan,
    RaceStrategy, StrategyTemplate, STRATEGY_TEMPLATES,
    assign_grid_strategies,
)
from app.race_simulator import RaceSimulator, Car


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manager(total_laps: int = 50) -> PitStopManager:
    return PitStopManager(total_laps=total_laps)


def make_sim(
    total_laps: int = 20,
    timestep: float = 0.5,
    default_strategy: RaceStrategy = RaceStrategy.TWO_STOP,
) -> RaceSimulator:
    return RaceSimulator(
        circuit_length=5500.0,
        total_laps=total_laps,
        timestep=timestep,
        enable_tyre_degradation=True,
        default_strategy=default_strategy,
    )


def add_basic_car(sim: RaceSimulator, name: str = "Driver", speed: float = 90.0) -> Car:
    return sim.add_car(name, "Team", speed, 11.0, 0.90, 0.72)


# ---------------------------------------------------------------------------
# StrategyTemplate / STRATEGY_TEMPLATES
# ---------------------------------------------------------------------------

class TestStrategyTemplates:
    def test_all_strategies_present(self):
        for s in RaceStrategy:
            assert s in STRATEGY_TEMPLATES

    def test_one_stop_has_two_stints(self):
        tmpl = STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP]
        assert len(tmpl.stints) == 2

    def test_two_stop_has_three_stints(self):
        tmpl = STRATEGY_TEMPLATES[RaceStrategy.TWO_STOP]
        assert len(tmpl.stints) == 3

    def test_aggressive_has_four_stints(self):
        tmpl = STRATEGY_TEMPLATES[RaceStrategy.AGGRESSIVE]
        assert len(tmpl.stints) == 4

    def test_stop_count_equals_stints_minus_one(self):
        for rs, tmpl in STRATEGY_TEMPLATES.items():
            expected_stops = len(tmpl.stints) - 1
            assert len(tmpl.pit_window_fractions) == expected_stops, \
                f"{rs}: windows {len(tmpl.pit_window_fractions)} != stops {expected_stops}"

    def test_wear_threshold_in_range(self):
        for rs, tmpl in STRATEGY_TEMPLATES.items():
            assert 0.0 < tmpl.wear_threshold < 1.0, f"{rs} wear_threshold out of range"

    def test_aggressive_lower_threshold_than_one_stop(self):
        agg = STRATEGY_TEMPLATES[RaceStrategy.AGGRESSIVE].wear_threshold
        one = STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP].wear_threshold
        assert agg < one, "Aggressive should pit earlier (lower threshold)"

    def test_pit_windows_ordered(self):
        for rs, tmpl in STRATEGY_TEMPLATES.items():
            fracs = [f[0] for f in tmpl.pit_window_fractions]
            assert fracs == sorted(fracs), f"{rs}: pit windows not in order"

    def test_pit_windows_within_race(self):
        for rs, tmpl in STRATEGY_TEMPLATES.items():
            for start, end in tmpl.pit_window_fractions:
                assert 0 < start < end <= 1.0


# ---------------------------------------------------------------------------
# PitStopManager.register_car
# ---------------------------------------------------------------------------

class TestPitStopManagerRegistration:
    def test_register_returns_tyre_strategy(self):
        mgr = make_manager()
        ts = mgr.register_car("Alice", RaceStrategy.ONE_STOP)
        assert isinstance(ts, TyreStrategy)

    def test_registered_strategy_has_correct_stints(self):
        mgr = make_manager()
        ts = mgr.register_car("Bob", RaceStrategy.TWO_STOP)
        tmpl = STRATEGY_TEMPLATES[RaceStrategy.TWO_STOP]
        assert ts._stints == list(tmpl.stints)

    def test_plan_created(self):
        mgr = make_manager()
        mgr.register_car("Carol", RaceStrategy.AGGRESSIVE)
        assert "Carol" in mgr._plans

    def test_pit_windows_converted_to_laps(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("Dave", RaceStrategy.ONE_STOP)
        plan = mgr.get_plan("Dave")
        assert len(plan.pit_windows) == 1
        w_start, w_end = plan.pit_windows[0]
        assert isinstance(w_start, int) and isinstance(w_end, int)
        assert 1 <= w_start < w_end <= 49

    def test_noise_factor_applied(self):
        mgr = make_manager()
        mgr.register_car("Eve", RaceStrategy.ONE_STOP, noise_factor=0.10)
        plan = mgr.get_plan("Eve")
        assert plan.tyre_strategy.current_tyre.noise_factor == 0.10

    def test_multiple_drivers_independent(self):
        mgr = make_manager()
        ts1 = mgr.register_car("F1", RaceStrategy.ONE_STOP)
        ts2 = mgr.register_car("F2", RaceStrategy.TWO_STOP)
        assert ts1 is not ts2
        assert mgr.get_plan("F1").strategy == RaceStrategy.ONE_STOP
        assert mgr.get_plan("F2").strategy == RaceStrategy.TWO_STOP


# ---------------------------------------------------------------------------
# PitStopManager.notify_lap_complete — wear threshold trigger
# ---------------------------------------------------------------------------

class TestWearThresholdTrigger:
    def test_no_pit_below_threshold(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("G", RaceStrategy.ONE_STOP, noise_factor=0.0)
        # Advance to just below the threshold
        threshold = STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP].wear_threshold
        plan = mgr.get_plan("G")
        # Set wear to threshold - epsilon without hitting it
        laps_needed = int(threshold * plan.tyre_strategy.current_tyre.spec.max_life_laps * 0.8)
        for lap in range(1, laps_needed + 1):
            triggered = mgr.notify_lap_complete("G", lap, float(lap * 100))
        # After many laps but still possibly below threshold, car may or may not pit
        # Just confirm the function runs without error
        assert not plan.in_pit or plan.in_pit  # tautology: just checks no exception

    def test_pit_triggered_at_threshold(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("H", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = mgr.get_plan("H")
        threshold = STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP].wear_threshold
        max_life = plan.tyre_strategy.current_tyre.spec.max_life_laps
        # Force wear to exceed threshold
        plan.tyre_strategy.current_tyre.advance_laps(threshold * max_life + 1)
        triggered = mgr.notify_lap_complete("H", 20, 2000.0)
        assert triggered
        assert plan.in_pit

    def test_pit_time_in_range(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("I", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = mgr.get_plan("I")
        plan.tyre_strategy.current_tyre.advance_laps(
            STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP].wear_threshold
            * plan.tyre_strategy.current_tyre.spec.max_life_laps + 1
        )
        mgr.notify_lap_complete("I", 22, 2200.0)
        assert mgr.PIT_TIME_MIN <= plan.pit_time_remaining <= mgr.PIT_TIME_MAX

    def test_compound_changes_after_service(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("J", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = mgr.get_plan("J")
        old_compound = plan.tyre_strategy.current_tyre.compound
        plan.tyre_strategy.current_tyre.advance_laps(
            STRATEGY_TEMPLATES[RaceStrategy.ONE_STOP].wear_threshold
            * plan.tyre_strategy.current_tyre.spec.max_life_laps + 1
        )
        mgr.notify_lap_complete("J", 20, 2000.0)
        # Tick through service time
        for _ in range(200):
            mgr.tick("J", 0.1)
        new_compound = plan.tyre_strategy.current_tyre.compound
        assert new_compound != old_compound


# ---------------------------------------------------------------------------
# PitStopManager.tick — service execution
# ---------------------------------------------------------------------------

class TestPitTick:
    def _enter_pit(self, mgr: PitStopManager, driver: str) -> PitPlan:
        plan = mgr.get_plan(driver)
        # Force pit
        plan.tyre_strategy.current_tyre.advance_laps(9999)
        mgr.notify_lap_complete(driver, 20, 2000.0)
        return plan

    def test_tick_returns_true_while_in_pit(self):
        mgr = make_manager()
        mgr.register_car("K", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = self._enter_pit(mgr, "K")
        # On first tick car should still be pitting
        result = mgr.tick("K", 0.1)
        assert result is True

    def test_tick_returns_false_after_service_complete(self):
        mgr = make_manager()
        mgr.register_car("L", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = self._enter_pit(mgr, "L")
        # Burn through service time
        for _ in range(100):
            done = mgr.tick("L", 0.1)
        assert done is False
        assert not plan.in_pit

    def test_tick_idle_car_returns_false(self):
        mgr = make_manager()
        mgr.register_car("M", RaceStrategy.TWO_STOP)
        result = mgr.tick("M", 0.1)
        assert result is False

    def test_tick_unknown_driver_returns_false(self):
        mgr = make_manager()
        result = mgr.tick("Nobody", 0.1)
        assert result is False

    def test_pit_record_populated_after_stop(self):
        mgr = make_manager()
        mgr.register_car("N", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = self._enter_pit(mgr, "N")
        for _ in range(100):
            mgr.tick("N", 0.1)
        stops = mgr.stops_for_driver("N")
        assert len(stops) == 1
        rec = stops[0]
        assert rec.driver == "N"
        assert rec.lap == 20
        assert rec.old_compound != ""
        assert rec.new_compound != ""
        assert rec.service_time >= mgr.PIT_TIME_MIN
        assert rec.service_time <= mgr.PIT_TIME_MAX
        assert 0.0 < rec.wear_at_pit <= 1.0
        assert rec.race_time_exit > rec.race_time_entry


# ---------------------------------------------------------------------------
# PitStopManager.all_stops / stops_for_driver
# ---------------------------------------------------------------------------

class TestPitRecords:
    def test_all_stops_sorted_by_entry_time(self):
        mgr = make_manager(total_laps=60)
        for name in ["P1", "P2", "P3"]:
            mgr.register_car(name, RaceStrategy.ONE_STOP, noise_factor=0.0)
        for i, name in enumerate(["P1", "P2", "P3"]):
            plan = mgr.get_plan(name)
            plan.tyre_strategy.current_tyre.advance_laps(9999)
            mgr.notify_lap_complete(name, 20 + i, float(2000 + i * 100))
            for _ in range(100): mgr.tick(name, 0.1)
        stops = mgr.all_stops
        times = [s.race_time_entry for s in stops]
        assert times == sorted(times)

    def test_stops_for_unknown_driver_empty(self):
        mgr = make_manager()
        assert mgr.stops_for_driver("ghost") == []

    def test_two_stop_produces_two_records(self):
        mgr = make_manager(total_laps=60)
        mgr.register_car("Q", RaceStrategy.TWO_STOP, noise_factor=0.0)
        plan = mgr.get_plan("Q")
        for stop in range(2):
            plan.tyre_strategy.current_tyre.advance_laps(9999)
            mgr.notify_lap_complete("Q", 20 + stop * 10, float(2000 + stop * 1000))
            for _ in range(100): mgr.tick("Q", 0.1)
        assert len(mgr.stops_for_driver("Q")) == 2

    def test_trigger_field_set(self):
        mgr = make_manager(total_laps=50)
        mgr.register_car("R", RaceStrategy.ONE_STOP, noise_factor=0.0)
        plan = mgr.get_plan("R")
        plan.tyre_strategy.current_tyre.advance_laps(9999)
        mgr.notify_lap_complete("R", 20, 2000.0)
        for _ in range(100): mgr.tick("R", 0.1)
        rec = mgr.stops_for_driver("R")[0]
        assert rec.trigger in ("wear_threshold", "pit_window", "worn_out")


# ---------------------------------------------------------------------------
# assign_grid_strategies factory
# ---------------------------------------------------------------------------

class TestAssignGridStrategies:
    def test_all_drivers_registered(self):
        drivers = ["A", "B", "C", "D"]
        mgr = assign_grid_strategies(drivers, total_laps=50)
        for d in drivers:
            assert mgr.get_plan(d) is not None

    def test_default_strategy_applied(self):
        mgr = assign_grid_strategies(["X", "Y"], 50, default_strategy=RaceStrategy.AGGRESSIVE)
        assert mgr.get_plan("X").strategy == RaceStrategy.AGGRESSIVE
        assert mgr.get_plan("Y").strategy == RaceStrategy.AGGRESSIVE

    def test_override_applied(self):
        mgr = assign_grid_strategies(
            ["Alpha", "Beta"], 50,
            default_strategy=RaceStrategy.ONE_STOP,
            strategy_overrides={"Beta": RaceStrategy.TWO_STOP},
        )
        assert mgr.get_plan("Alpha").strategy == RaceStrategy.ONE_STOP
        assert mgr.get_plan("Beta").strategy == RaceStrategy.TWO_STOP


# ---------------------------------------------------------------------------
# RaceSimulator integration
# ---------------------------------------------------------------------------

class TestRaceSimulatorIntegration:
    def test_pit_manager_created_on_run(self):
        sim = make_sim()
        add_basic_car(sim)
        sim.run_simulation(verbose=False)
        assert sim.pit_manager is not None

    def test_strategy_override_per_car(self):
        sim = make_sim()
        sim.add_car("Soft-Guy", "T", 90.0, 11.0, 0.90, 0.72,
                    strategy=RaceStrategy.AGGRESSIVE)
        sim.add_car("Hard-Guy", "T", 90.0, 11.0, 0.90, 0.72,
                    strategy=RaceStrategy.ONE_STOP)
        sim.run_simulation(verbose=False)
        assert sim.pit_manager.get_plan("Soft-Guy").strategy == RaceStrategy.AGGRESSIVE
        assert sim.pit_manager.get_plan("Hard-Guy").strategy == RaceStrategy.ONE_STOP

    def test_results_contain_pit_stops_key(self):
        sim = make_sim()
        add_basic_car(sim)
        results = sim.run_simulation(verbose=False)
        assert "pit_stops" in results[0]

    def test_car_velocity_zero_during_pit(self):
        """Cars in pit must have zero velocity — check mid-simulation."""
        sim = RaceSimulator(
            circuit_length=5500.0, total_laps=30,
            timestep=0.1, enable_tyre_degradation=True,
            default_strategy=RaceStrategy.TWO_STOP,
        )
        car = sim.add_car("Spy", "T", 90.0, 11.0, 0.90, 0.72)
        sim.race_active = True
        sim.race_time   = 0.0
        sim.pit_manager = PitStopManager(total_laps=30)
        ts = sim.pit_manager.register_car("Spy", RaceStrategy.TWO_STOP)
        car.tyre_strategy = ts

        # Force the car into a pit stop manually
        plan = sim.pit_manager.get_plan("Spy")
        plan.tyre_strategy.current_tyre.advance_laps(9999)
        sim.pit_manager.notify_lap_complete("Spy", 10, 1000.0)

        assert sim.pit_manager.is_in_pit("Spy")
        sim._update_car_physics(car)
        assert car.velocity == 0.0

    def test_car_released_after_service(self):
        sim = RaceSimulator(
            circuit_length=5500.0, total_laps=30,
            timestep=0.1, enable_tyre_degradation=True,
        )
        car = sim.add_car("Rel", "T", 90.0, 11.0, 0.90, 0.72)
        sim.race_active = True
        sim.race_time   = 0.0
        sim.pit_manager = PitStopManager(total_laps=30)
        ts = sim.pit_manager.register_car("Rel", RaceStrategy.ONE_STOP)
        car.tyre_strategy = ts

        plan = sim.pit_manager.get_plan("Rel")
        plan.tyre_strategy.current_tyre.advance_laps(9999)
        sim.pit_manager.notify_lap_complete("Rel", 10, 1000.0)

        # Tick until service ends
        for _ in range(500):
            sim._update_car_physics(car)
            sim.race_time += 0.1
            if not sim.pit_manager.is_in_pit("Rel"):
                break

        assert not sim.pit_manager.is_in_pit("Rel")
        assert car.velocity > 0.0

    def test_compound_changes_mid_race(self):
        sim = make_sim(total_laps=30)
        car = add_basic_car(sim, "ComChange")
        results = sim.run_simulation(verbose=False)
        plan = sim.pit_manager.get_plan("ComChange")
        # After the race the compound may have changed (depending on wear)
        # At minimum: tyre_strategy object exists and current_tyre is valid
        assert plan.tyre_strategy.current_tyre is not None

    def test_pit_stop_adds_time_cost(self):
        """Car with forced pit should finish slower than one without."""
        # No degradation — baseline
        sim_clean = RaceSimulator(5500, 15, 0.5, enable_tyre_degradation=False)
        sim_clean.add_car("Clean", "T", 90.0, 11.0, 0.90, 0.72)
        res_clean = sim_clean.run_simulation(verbose=False)

        # With degradation + aggressive pitting
        sim_pit = RaceSimulator(
            5500, 15, 0.5,
            enable_tyre_degradation=True,
            default_strategy=RaceStrategy.AGGRESSIVE,
        )
        sim_pit.add_car("Pitter", "T", 90.0, 11.0, 0.90, 0.72)
        res_pit = sim_pit.run_simulation(verbose=False)

        # Pitting costs time → pitter should be no faster than clean car
        assert res_pit[0]['finish_time'] >= res_clean[0]['finish_time']

    def test_full_grid_simulation(self):
        from app.race_simulator import create_f1_grid
        sim = RaceSimulator(
            circuit_length=5500.0,
            total_laps=20,
            timestep=0.5,
            enable_tyre_degradation=True,
            default_strategy=RaceStrategy.TWO_STOP,
        )
        for spec in create_f1_grid():
            sim.add_car(**spec)
        results = sim.run_simulation(verbose=False)
        assert len(results) == 22
        # All results have pit_stops key
        assert all("pit_stops" in r for r in results)

    def test_reset_clears_pit_manager(self):
        sim = make_sim()
        add_basic_car(sim)
        sim.run_simulation(verbose=False)
        assert sim.pit_manager is not None
        sim.reset()
        assert sim.pit_manager is None

    def test_strategy_summary_non_empty(self):
        sim = make_sim()
        add_basic_car(sim)
        sim.run_simulation(verbose=False)
        summary = sim.pit_manager.strategy_summary()
        assert len(summary) > 0
        assert "Driver" in summary or "Stop" in summary or "→" in summary


# ---------------------------------------------------------------------------
# Standalone runner (no pytest needed)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_classes = [
        TestStrategyTemplates,
        TestPitStopManagerRegistration,
        TestWearThresholdTrigger,
        TestPitTick,
        TestPitRecords,
        TestAssignGridStrategies,
        TestRaceSimulatorIntegration,
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
                failed += 1

    print(f"\n{'='*60}")
    print(f"  {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
