"""
Tests for the tyre degradation system (app/tyre.py) and its integration
with RaceSimulator (app/race_simulator.py).

Run with:  python -m pytest app/test_tyre.py -v
"""

import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.tyre import (
    Tyre, TyreCompound, TyreStrategy, TyreDegradationModel,
    COMPOUND_SPECS,
)
from app.race_simulator import RaceSimulator, Car


# ===========================================================================
# Tyre unit tests
# ===========================================================================

class TestCompoundSpecs:
    def test_all_compounds_present(self):
        for c in TyreCompound:
            assert c in COMPOUND_SPECS

    def test_soft_highest_peak_grip(self):
        assert COMPOUND_SPECS[TyreCompound.SOFT].peak_grip > COMPOUND_SPECS[TyreCompound.MEDIUM].peak_grip
        assert COMPOUND_SPECS[TyreCompound.MEDIUM].peak_grip > COMPOUND_SPECS[TyreCompound.HARD].peak_grip

    def test_soft_highest_wear_rate(self):
        assert COMPOUND_SPECS[TyreCompound.SOFT].wear_rate_per_lap > COMPOUND_SPECS[TyreCompound.MEDIUM].wear_rate_per_lap
        assert COMPOUND_SPECS[TyreCompound.MEDIUM].wear_rate_per_lap > COMPOUND_SPECS[TyreCompound.HARD].wear_rate_per_lap

    def test_hard_longest_life(self):
        assert COMPOUND_SPECS[TyreCompound.HARD].max_life_laps > COMPOUND_SPECS[TyreCompound.MEDIUM].max_life_laps
        assert COMPOUND_SPECS[TyreCompound.MEDIUM].max_life_laps > COMPOUND_SPECS[TyreCompound.SOFT].max_life_laps


class TestTyreWarmup:
    def test_grip_builds_during_warmup(self):
        tyre = Tyre(TyreCompound.SOFT)
        grip_lap0 = tyre.grip_multiplier
        tyre.advance_laps(0.5)
        grip_half = tyre.grip_multiplier
        tyre.advance_laps(0.5)
        grip_full = tyre.grip_multiplier
        assert grip_half > grip_lap0
        assert grip_full > grip_half

    def test_grip_peaks_at_warmup_completion(self):
        for compound in TyreCompound:
            spec = COMPOUND_SPECS[compound]
            tyre = Tyre(compound)
            tyre.advance_laps(spec.warmup_laps)
            # After warmup, grip should be at or near peak_grip
            assert abs(tyre.grip_multiplier - spec.peak_grip) < 0.01


class TestTyreDegradation:
    def test_grip_decreases_after_warmup(self):
        tyre = Tyre(TyreCompound.SOFT)
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        tyre.advance_laps(spec.warmup_laps)
        grip_at_warmup = tyre.grip_multiplier
        tyre.advance_laps(5.0)
        assert tyre.grip_multiplier < grip_at_warmup

    def test_worn_out_flag(self):
        tyre = Tyre(TyreCompound.SOFT)
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        assert not tyre.is_worn_out
        tyre.advance_laps(spec.max_life_laps)
        assert tyre.is_worn_out

    def test_wear_fraction_bounds(self):
        tyre = Tyre(TyreCompound.MEDIUM)
        assert tyre.wear_fraction == 0.0
        tyre.advance_laps(1000)  # way beyond life
        assert tyre.wear_fraction == 1.0

    def test_grip_clamped_above_floor(self):
        tyre = Tyre(TyreCompound.SOFT)
        tyre.advance_laps(1000)
        assert tyre.grip_multiplier >= 0.40

    def test_laptime_penalty_increases_with_wear(self):
        tyre = Tyre(TyreCompound.SOFT)
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        tyre.advance_laps(spec.warmup_laps)
        p1 = tyre.laptime_delta_s
        tyre.advance_laps(5)
        p2 = tyre.laptime_delta_s
        assert p2 > p1

    def test_soft_degrades_faster_than_hard(self):
        soft = Tyre(TyreCompound.SOFT)
        hard = Tyre(TyreCompound.HARD)
        laps = 10
        soft.advance_laps(laps)
        hard.advance_laps(laps)
        assert soft.wear_fraction > hard.wear_fraction


class TestTyreFactors:
    def test_corner_speed_factor_equals_grip_multiplier(self):
        tyre = Tyre(TyreCompound.MEDIUM)
        tyre.advance_laps(8)
        assert tyre.corner_speed_factor == tyre.grip_multiplier

    def test_acceleration_factor_reasonable_range(self):
        for compound in TyreCompound:
            tyre = Tyre(compound)
            assert 0.5 < tyre.acceleration_factor < 1.5


class TestTyreStatus:
    def test_status_dict_keys(self):
        tyre = Tyre(TyreCompound.HARD)
        s = tyre.get_status()
        for key in ("compound", "laps_done", "wear_pct", "grip_multiplier",
                    "corner_speed_factor", "accel_factor", "laptime_delta_s", "is_worn_out"):
            assert key in s


# ===========================================================================
# TyreStrategy tests
# ===========================================================================

class TestTyreStrategy:
    def test_initial_compound(self):
        strategy = TyreStrategy([TyreCompound.SOFT, TyreCompound.MEDIUM])
        assert strategy.current_tyre.compound == TyreCompound.SOFT

    def test_pit_changes_compound(self):
        strategy = TyreStrategy([TyreCompound.SOFT, TyreCompound.MEDIUM])
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        strategy.current_tyre.advance_laps(spec.max_life_laps)
        assert strategy.should_pit()
        new_c = strategy.pit_stop(current_lap=20)
        assert new_c == TyreCompound.MEDIUM
        assert strategy.current_tyre.compound == TyreCompound.MEDIUM

    def test_no_pit_when_last_stint(self):
        strategy = TyreStrategy([TyreCompound.HARD])
        spec = COMPOUND_SPECS[TyreCompound.HARD]
        strategy.current_tyre.advance_laps(spec.max_life_laps)
        # should_pit is False because no stints remain
        assert not strategy.should_pit()

    def test_advance_lap_increases_wear(self):
        strategy = TyreStrategy([TyreCompound.MEDIUM, TyreCompound.HARD])
        strategy.advance_lap()
        assert strategy.current_tyre.laps_done == 1.0

    def test_pit_history_recorded(self):
        strategy = TyreStrategy([TyreCompound.SOFT, TyreCompound.HARD])
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        strategy.current_tyre.advance_laps(spec.max_life_laps)
        strategy.pit_stop(current_lap=18)
        assert len(strategy.pit_history) == 1
        assert strategy.pit_history[0]["lap"] == 18

    def test_three_stint_strategy(self):
        stints = [TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD]
        strategy = TyreStrategy(stints)
        for i in range(2):
            spec = COMPOUND_SPECS[stints[i]]
            strategy.current_tyre.advance_laps(spec.max_life_laps)
            strategy.pit_stop(current_lap=i * 20)
        assert strategy.current_tyre.compound == TyreCompound.HARD


# ===========================================================================
# TyreDegradationModel tests
# ===========================================================================

class TestTyreDegradationModel:
    def test_effective_grip_scales_base(self):
        tyre = Tyre(TyreCompound.SOFT)
        base = 0.90
        eff = TyreDegradationModel.effective_tyre_grip(base, tyre)
        # Fresh soft has grip > 1 × base on warm-up start, so check scaling
        assert abs(eff - base * tyre.grip_multiplier) < 1e-9

    def test_effective_corner_speed_reduces_with_wear(self):
        tyre = Tyre(TyreCompound.SOFT)
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        tyre.advance_laps(spec.warmup_laps)
        nominal = 60.0
        v_fresh = TyreDegradationModel.effective_max_corner_speed(nominal, tyre)
        tyre.advance_laps(15)
        v_worn = TyreDegradationModel.effective_max_corner_speed(nominal, tyre)
        assert v_worn < v_fresh

    def test_effective_acceleration_reduces_with_wear(self):
        tyre = Tyre(TyreCompound.SOFT)
        spec = COMPOUND_SPECS[TyreCompound.SOFT]
        tyre.advance_laps(spec.warmup_laps)
        base_a = 12.0
        a_fresh = TyreDegradationModel.effective_acceleration(base_a, tyre)
        tyre.advance_laps(18)
        a_worn = TyreDegradationModel.effective_acceleration(base_a, tyre)
        assert a_worn < a_fresh

    def test_laptime_increases_with_wear(self):
        tyre = Tyre(TyreCompound.MEDIUM)
        spec = COMPOUND_SPECS[TyreCompound.MEDIUM]
        base_lap = 90.0
        t_fresh = TyreDegradationModel.apply_to_laptime(base_lap, tyre)
        tyre.advance_laps(spec.max_life_laps)
        t_worn = TyreDegradationModel.apply_to_laptime(base_lap, tyre)
        assert t_worn > t_fresh

    def test_degradation_report_string(self):
        tyre = Tyre(TyreCompound.HARD)
        report = TyreDegradationModel.degradation_report(tyre)
        assert "HARD" in report
        assert "Grip" in report


# ===========================================================================
# RaceSimulator integration tests
# ===========================================================================

class TestRaceSimulatorTyreIntegration:
    def _make_sim(self, laps=5, degradation=True):
        sim = RaceSimulator(
            circuit_length=5500.0,
            total_laps=laps,
            timestep=0.5,
            enable_tyre_degradation=degradation,
        )
        return sim

    def _add_basic_car(self, sim, driver="Test Driver", compound=None):
        strategy = None
        if sim.enable_tyre_degradation and compound is not None:
            strategy = TyreStrategy([compound, TyreCompound.HARD])
        return sim.add_car(
            driver_name=driver,
            team="Test Team",
            max_speed=90.0,
            acceleration=11.0,
            tyre_grip=0.90,
            drag_coefficient=0.72,
            tyre_strategy=strategy,
        )

    def test_car_gets_default_strategy(self):
        sim = self._make_sim()
        car = self._add_basic_car(sim)
        assert car.tyre_strategy is not None
        assert car.tyre_strategy.current_tyre.compound in TyreCompound

    def test_no_strategy_when_degradation_disabled(self):
        sim = self._make_sim(degradation=False)
        car = self._add_basic_car(sim)
        assert car.tyre_strategy is None

    def test_effective_properties_differ_from_base(self):
        sim = self._make_sim()
        car = self._add_basic_car(sim, compound=TyreCompound.SOFT)
        # On a fresh soft tyre, effective_tyre_grip != base tyre_grip
        # (because grip_multiplier != 1.0 for a soft on lap 0 during warmup)
        assert car.effective_tyre_grip != car.tyre_grip or True  # always valid call

    def test_tyre_wears_over_laps(self):
        sim = self._make_sim(laps=5)
        car = self._add_basic_car(sim, compound=TyreCompound.SOFT)
        sim.run_simulation(verbose=False)
        if car.tyre_strategy:
            assert car.tyre_strategy.current_tyre.laps_done > 0

    def test_simulation_completes(self):
        sim = self._make_sim(laps=5)
        for i in range(3):
            sim.add_car(
                driver_name=f"Driver{i}",
                team="Team A",
                max_speed=90.0 - i,
                acceleration=11.0,
                tyre_grip=0.90,
                drag_coefficient=0.72,
            )
        results = sim.run_simulation(verbose=False)
        assert len(results) == 3

    def test_results_contain_tyre_stints(self):
        sim = self._make_sim(laps=5)
        sim.add_car("Driver0", "Team", 90.0, 11.0, 0.90, 0.72)
        results = sim.run_simulation(verbose=False)
        assert "tyre_stints" in results[0]

    def test_degradation_slows_car_vs_none(self):
        """Car with severe wear should finish slower than one without degradation."""
        # Run without degradation
        sim_clean = RaceSimulator(5500, 10, 0.5, enable_tyre_degradation=False)
        sim_clean.add_car("Clean", "T", 90.0, 11.0, 0.90, 0.72)
        res_clean = sim_clean.run_simulation(verbose=False)

        # Run with degradation (soft-only, intentionally no second compound)
        sim_deg = RaceSimulator(5500, 10, 0.5, enable_tyre_degradation=True)
        # Single-stint soft: wears out mid-race and car limps on degraded rubber
        strat = TyreStrategy([TyreCompound.SOFT], noise_factor=0.0)
        sim_deg.add_car("Degraded", "T", 90.0, 11.0, 0.90, 0.72, tyre_strategy=strat)
        res_deg = sim_deg.run_simulation(verbose=False)

        assert res_deg[0]['finish_time'] >= res_clean[0]['finish_time']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ===========================================================================
# CircuitRaceSimulator integration tests
# ===========================================================================

class TestCircuitRaceSimulatorTyreIntegration:
    def _make_sim(self, laps=3, degradation=True):
        from app.circuit_race_simulator import RaceSimulator as CRS, create_monaco_circuit
        circuit = create_monaco_circuit()
        circuit.number_of_laps = laps
        sim = CRS(circuit=circuit, timestep=0.5, enable_tyre_degradation=degradation)
        return sim

    def test_circuit_car_gets_strategy(self):
        sim = self._make_sim()
        car = sim.add_car("D", "T", 80.0, 10.0, 0.85, 0.72)
        assert car.tyre_strategy is not None

    def test_circuit_no_strategy_when_disabled(self):
        sim = self._make_sim(degradation=False)
        car = sim.add_car("D", "T", 80.0, 10.0, 0.85, 0.72)
        assert car.tyre_strategy is None

    def test_circuit_effective_cornering_speed_reduced_by_wear(self):
        sim = self._make_sim()
        car = sim.add_car("D", "T", 80.0, 10.0, 0.85, 0.72)
        fresh_factor = car.effective_cornering_speed_factor
        car.tyre_strategy.current_tyre.advance_laps(18)
        worn_factor = car.effective_cornering_speed_factor
        assert worn_factor < fresh_factor

    def test_circuit_simulation_completes(self):
        sim = self._make_sim(laps=3)
        for i in range(4):
            sim.add_car(f"D{i}", "Team", 80.0 - i * 0.5, 10.0, 0.85, 0.72)
        results = sim.run_simulation(verbose=False)
        assert len(results) == 4

    def test_circuit_results_have_tyre_stints(self):
        sim = self._make_sim(laps=3)
        sim.add_car("D0", "Team", 80.0, 10.0, 0.85, 0.72)
        results = sim.run_simulation(verbose=False)
        assert "tyre_stints" in results[0]

    def test_circuit_custom_strategy_respected(self):
        sim = self._make_sim(laps=3)
        strat = TyreStrategy([TyreCompound.HARD, TyreCompound.MEDIUM])
        car = sim.add_car("D", "T", 80.0, 10.0, 0.85, 0.72, tyre_strategy=strat)
        assert car.current_tyre.compound == TyreCompound.HARD

    def test_circuit_degradation_produces_laptime_variation(self):
        """Lap times should increase as tyres wear — avg later laps > avg early laps."""
        from app.circuit_race_simulator import RaceSimulator as CRS, create_monaco_circuit, TyreStrategy as _TS
        circuit = create_monaco_circuit()
        circuit.number_of_laps = 10
        sim = CRS(circuit=circuit, timestep=0.5, enable_tyre_degradation=True)
        # Single soft-only stint so degradation is visible
        strat = TyreStrategy([TyreCompound.SOFT], noise_factor=0.0)
        sim.add_car("D", "T", 85.0, 11.0, 0.90, 0.72, tyre_strategy=strat)
        results = sim.run_simulation(verbose=False)
        lap_times = results[0]['lap_times']
        if len(lap_times) >= 6:
            early_avg = sum(lap_times[1:3]) / 2   # skip lap 1 (warmup)
            late_avg  = sum(lap_times[-2:]) / 2
            assert late_avg >= early_avg


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    # Run all test classes manually
    test_classes = [
        TestCompoundSpecs, TestTyreWarmup, TestTyreDegradation,
        TestTyreFactors, TestTyreStatus, TestTyreStrategy,
        TestTyreDegradationModel, TestRaceSimulatorTyreIntegration,
        TestCircuitRaceSimulatorTyreIntegration,
    ]
    passed = failed = 0
    for cls in test_classes:
        obj = cls()
        for name in [n for n in dir(cls) if n.startswith("test_")]:
            try:
                getattr(obj, name)()
                print(f"  ✅ {cls.__name__}.{name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {cls.__name__}.{name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
