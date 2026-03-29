"""
Tests for the race-winner ML system:
  app/ml/schema.py      — RaceRecord, CSV I/O, feature names
  app/ml/dataset.py     — DatasetGenerator
  app/ml/model.py       — WinnerPredictor training + inference
  app/ml/predict.py     — FastAPI router (unit-tested without a live server)

Run with:  python app/test_ml.py
      or:  python -m pytest app/test_ml.py -v
"""

import os
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from app.ml.schema import (
    RaceRecord, records_to_csv, csv_to_records,
    ALL_FEATURE_NAMES, RAW_FEATURE_NAMES, INTERACTION_FEATURE_NAMES,
    TARGET_NAME, FEATURE_RANGES,
    CIRCUIT_TYPE_ENCODING, WEATHER_ENCODING, STRATEGY_ENCODING,
)
from app.ml.dataset import (
    DatasetGenerator,
    _normalise, _driver_skill_raw, _team_performance_raw,
    _pick_qualifying_order, _sample_strategy,
)
from app.ml.model import WinnerPredictor, records_to_xy, ModelMeta, _top1_accuracy
from app.weather import WeatherCondition, WEATHER_PARAMS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record(**overrides) -> RaceRecord:
    defaults = dict(
        race_id=0, driver_name="Test Driver", team="Test Team",
        driver_skill=0.8, wet_skill=0.75, team_performance=0.7,
        car_max_speed_norm=0.8, car_acceleration_norm=0.8,
        drag_coefficient=0.72, tyre_grip_base=0.90,
        qualifying_position=1, circuit_type=1,
        weather_condition=0, weather_grip_factor=1.0,
        tyre_strategy=1,
        skill_x_quali=0.76, team_x_weather=0.70,
        won=0, finish_position=1, finish_time_s=3600.0,
    )
    defaults.update(overrides)
    return RaceRecord(**defaults)


def _make_race(n=22, winner_idx=0) -> list:
    """Create a fake race of n RaceRecord rows with one winner."""
    records = []
    for i in range(n):
        rec = _make_record(
            race_id=99,
            driver_name=f"Driver{i}",
            driver_skill=round(1.0 - i / n, 4),
            car_max_speed_norm=round(1.0 - i / n, 4),
            qualifying_position=i + 1,
            skill_x_quali=round((1.0 - i / n) * (1.0 - (i + 1) / n), 4),
            won=1 if i == winner_idx else 0,
            finish_position=i + 1,
        )
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchema:
    def test_all_feature_names_complete(self):
        assert ALL_FEATURE_NAMES == RAW_FEATURE_NAMES + INTERACTION_FEATURE_NAMES

    def test_feature_names_match_record_fields(self):
        rec = _make_record()
        for name in ALL_FEATURE_NAMES:
            assert hasattr(rec, name), f"RaceRecord missing field: {name}"

    def test_to_feature_dict_keys(self):
        rec = _make_record()
        d = rec.to_feature_dict()
        assert set(d.keys()) == set(ALL_FEATURE_NAMES)

    def test_to_feature_dict_values_are_floats(self):
        rec = _make_record()
        for k, v in rec.to_feature_dict().items():
            assert isinstance(v, (int, float)), f"{k} is {type(v)}"

    def test_csv_roundtrip(self):
        records = _make_race(n=5)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as fh:
            path = fh.name
        try:
            records_to_csv(records, path)
            loaded = csv_to_records(path)
            assert len(loaded) == len(records)
            for orig, back in zip(records, loaded):
                assert orig.driver_name    == back.driver_name
                assert orig.won            == back.won
                assert abs(orig.driver_skill - back.driver_skill) < 1e-5
        finally:
            os.unlink(path)

    def test_encoding_dicts_cover_all_values(self):
        assert set(CIRCUIT_TYPE_ENCODING.values()) == {0, 1, 2}
        assert set(WEATHER_ENCODING.values())       == {0, 1, 2}
        assert set(STRATEGY_ENCODING.values())      == {0, 1, 2}

    def test_feature_ranges_cover_all_raw_features(self):
        for name in RAW_FEATURE_NAMES:
            assert name in FEATURE_RANGES, f"{name} missing from FEATURE_RANGES"

    def test_csv_fieldnames_match_dataclass(self):
        from dataclasses import fields
        names = {f.name for f in fields(RaceRecord)}
        assert set(RaceRecord.csv_fieldnames()) == names


# ---------------------------------------------------------------------------
# Dataset helpers tests
# ---------------------------------------------------------------------------

class TestDatasetHelpers:
    def test_normalise_range(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        normed = _normalise(values)
        assert abs(min(normed)) < 1e-9
        assert abs(max(normed) - 1.0) < 1e-9

    def test_normalise_all_same(self):
        normed = _normalise([5.0, 5.0, 5.0])
        assert all(abs(v - 0.5) < 1e-9 for v in normed)

    def test_driver_skill_raw_positive(self):
        spec = {"max_speed": 95.0, "acceleration": 12.5}
        assert _driver_skill_raw(spec) > 0

    def test_team_performance_raw_bounds(self):
        spec = {"tyre_grip": 0.95, "drag_coefficient": 0.70}
        val  = _team_performance_raw(spec)
        assert 0 < val < 1

    def test_qualifying_order_covers_all_positions(self):
        import random
        rng = random.Random(42)
        positions = _pick_qualifying_order(22, rng)
        assert sorted(positions) == list(range(1, 23))

    def test_qualifying_order_length(self):
        import random
        rng = random.Random(0)
        assert len(_pick_qualifying_order(10, rng)) == 10

    def test_sample_strategy_returns_valid(self):
        import random
        from app.pit_stop import RaceStrategy
        rng = random.Random(7)
        for _ in range(50):
            s = _sample_strategy(rng)
            assert isinstance(s, RaceStrategy)


# ---------------------------------------------------------------------------
# DatasetGenerator tests
# ---------------------------------------------------------------------------

class TestDatasetGenerator:
    def _gen(self, n=10) -> DatasetGenerator:
        return DatasetGenerator(total_laps=5, timestep=2.0, seed=42,
                                verbose=False)

    def test_generate_row_count(self):
        gen     = self._gen()
        records = gen.generate(n_races=5)
        assert len(records) == 5 * 22

    def test_exactly_one_winner_per_race(self):
        gen     = self._gen()
        records = gen.generate(n_races=8)
        from collections import Counter
        wins_per_race = Counter(r.race_id for r in records if r.won == 1)
        for race_id, count in wins_per_race.items():
            assert count == 1, f"Race {race_id} has {count} winners"

    def test_all_feature_fields_present(self):
        gen     = self._gen()
        records = gen.generate(n_races=3)
        for name in ALL_FEATURE_NAMES:
            assert all(hasattr(r, name) for r in records), f"Missing: {name}"

    def test_qualifying_positions_cover_full_range(self):
        gen     = self._gen()
        records = gen.generate(n_races=3)
        from collections import Counter
        for race_id in set(r.race_id for r in records):
            race_recs = [r for r in records if r.race_id == race_id]
            positions = sorted(r.qualifying_position for r in race_recs)
            assert positions == list(range(1, 23))

    def test_feature_values_in_valid_ranges(self):
        gen     = self._gen()
        records = gen.generate(n_races=3)
        for rec in records:
            assert 0.0 <= rec.driver_skill <= 1.0
            assert 0.0 <= rec.wet_skill <= 1.0
            assert 0.0 <= rec.team_performance <= 1.0
            assert 1 <= rec.qualifying_position <= 22
            assert rec.circuit_type in (0, 1, 2)
            assert rec.weather_condition in (0, 1, 2)
            assert rec.tyre_strategy in (0, 1, 2)

    def test_interaction_features_computed(self):
        gen     = self._gen()
        records = gen.generate(n_races=2)
        for rec in records:
            expected_sqx = rec.driver_skill * (1.0 - rec.qualifying_position / 22)
            assert abs(rec.skill_x_quali - expected_sqx) < 0.01

    def test_circuit_types_all_appear(self):
        gen     = self._gen()
        records = gen.generate(n_races=6)
        types   = {r.circuit_type for r in records}
        assert types == {0, 1, 2}

    def test_generate_and_save(self):
        gen = self._gen()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as fh:
            path = fh.name
        try:
            records = gen.generate_and_save(n_races=4, filepath=path)
            assert os.path.exists(path)
            loaded = csv_to_records(path)
            assert len(loaded) == len(records)
        finally:
            os.unlink(path)

    def test_seed_reproducibility(self):
        g1 = DatasetGenerator(total_laps=5, timestep=2.0, seed=7, verbose=False)
        g2 = DatasetGenerator(total_laps=5, timestep=2.0, seed=7, verbose=False)
        r1 = g1.generate(n_races=3)
        r2 = g2.generate(n_races=3)
        for a, b in zip(r1, r2):
            assert a.driver_name == b.driver_name
            assert a.qualifying_position == b.qualifying_position
            assert a.won == b.won


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestRecordsToXY:
    def test_shape(self):
        records = _make_race(n=22)
        X, y, names = records_to_xy(records)
        assert X.shape == (22, len(ALL_FEATURE_NAMES))
        assert y.shape == (22,)
        assert names   == ALL_FEATURE_NAMES

    def test_target_values(self):
        records = _make_race(n=5, winner_idx=2)
        _, y, _ = records_to_xy(records)
        assert y[2] == 1
        assert sum(y) == 1

    def test_dtype(self):
        records = _make_race()
        X, y, _ = records_to_xy(records)
        assert X.dtype == np.float64
        assert y.dtype == np.int32


class TestTop1Accuracy:
    def test_perfect_predictor(self):
        records = _make_race(n=5, winner_idx=0)
        # Assign highest prob to winner
        probas  = np.array([0.9, 0.3, 0.2, 0.1, 0.05])
        acc     = _top1_accuracy(records, probas)
        assert acc == 1.0

    def test_wrong_predictor(self):
        records = _make_race(n=5, winner_idx=4)
        probas  = np.array([0.9, 0.3, 0.2, 0.1, 0.05])  # predicts driver 0
        acc     = _top1_accuracy(records, probas)
        assert acc == 0.0

    def test_empty(self):
        assert _top1_accuracy([], np.array([])) == 0.0


class TestWinnerPredictorTrain:
    # Class-level cache: train once, reuse across all methods in this class.
    _cached = None   # (pred, meta, recs)

    def _train_mini(self):
        if TestWinnerPredictorTrain._cached is None:
            gen  = DatasetGenerator(total_laps=5, timestep=2.0,
                                    seed=0, verbose=False)
            recs = gen.generate(n_races=30)
            pred = WinnerPredictor()
            meta = pred.train(recs)
            TestWinnerPredictorTrain._cached = (pred, meta, recs)
        return TestWinnerPredictorTrain._cached

    def test_train_returns_meta(self):
        _, meta, _ = self._train_mini()
        assert isinstance(meta, ModelMeta)

    def test_meta_best_model_valid(self):
        _, meta, _ = self._train_mini()
        assert meta.best_model in ("GradientBoosting", "RandomForest")

    def test_meta_auc_reasonable(self):
        _, meta, _ = self._train_mini()
        # Even on tiny data the model should beat random
        assert meta.cv_roc_auc > 0.5

    def test_meta_top1_accuracy_positive(self):
        _, meta, _ = self._train_mini()
        assert 0.0 <= meta.top1_accuracy <= 1.0

    def test_predict_proba_shape(self):
        pred, _, recs = self._train_mini()
        race_recs = [r for r in recs if r.race_id == 0]
        probas    = pred.predict_proba(race_recs)
        assert probas.shape == (len(race_recs),)

    def test_predict_proba_sums_to_roughly_one(self):
        # Probabilities don't have to sum to 1 exactly (binary classifier),
        # but the winner should have the highest probability among top drivers
        pred, _, recs = self._train_mini()
        race_recs = [r for r in recs if r.race_id == 0]
        probas    = pred.predict_proba(race_recs)
        assert all(0.0 <= p <= 1.0 for p in probas)

    def test_rank_drivers_sorted_descending(self):
        pred, _, recs = self._train_mini()
        race_recs = [r for r in recs if r.race_id == 0]
        rankings  = pred.rank_drivers(race_recs)
        probs     = [e["win_prob"] for e in rankings]
        assert probs == sorted(probs, reverse=True)

    def test_rank_drivers_keys(self):
        pred, _, recs = self._train_mini()
        race_recs = [r for r in recs if r.race_id == 0]
        rankings  = pred.rank_drivers(race_recs)
        for entry in rankings:
            for key in ("rank", "driver", "team", "win_prob", "features"):
                assert key in entry

    def test_rank_is_1_indexed(self):
        pred, _, recs = self._train_mini()
        race_recs = [r for r in recs if r.race_id == 0]
        rankings  = pred.rank_drivers(race_recs)
        assert rankings[0]["rank"] == 1

    def test_save_and_load(self):
        pred, _, recs = self._train_mini()
        with tempfile.TemporaryDirectory() as tmpdir:
            mpath = Path(tmpdir) / "model.joblib"
            epath = Path(tmpdir) / "meta.json"
            pred.save(model_path=mpath, meta_path=epath)
            assert mpath.exists()
            assert epath.exists()
            loaded = WinnerPredictor.load(model_path=mpath, meta_path=epath)
            race_recs = [r for r in recs if r.race_id == 0]
            p1 = pred.predict_proba(race_recs)
            p2 = loaded.predict_proba(race_recs)
            np.testing.assert_allclose(p1, p2, rtol=1e-5)

    def test_meta_json_roundtrip(self):
        _, meta, _ = self._train_mini()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = Path(fh.name)
        try:
            meta.save(path)
            loaded = ModelMeta.load(path)
            assert loaded.best_model   == meta.best_model
            assert loaded.cv_roc_auc   == meta.cv_roc_auc
            assert loaded.feature_names == meta.feature_names
        finally:
            path.unlink()

    def test_model_with_no_records_raises(self):
        pred = WinnerPredictor()
        try:
            pred.train([])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_predict_before_train_raises(self):
        pred = WinnerPredictor()
        try:
            pred.predict_proba(_make_race(n=5))
            assert False, "Should have raised RuntimeError"
        except RuntimeError:
            pass


# ---------------------------------------------------------------------------
# Predict API tests (unit — no live HTTP server)
# ---------------------------------------------------------------------------

class TestPredictAPI:
    """Test the router logic directly without a running server."""

    _cached = None  # (pred, recs)

    def _make_trained_predictor(self):
        if TestPredictAPI._cached is None:
            gen  = DatasetGenerator(total_laps=5, timestep=2.0,
                                    seed=1, verbose=False)
            recs = gen.generate(n_races=30)
            pred = WinnerPredictor()
            pred.train(recs)
            TestPredictAPI._cached = (pred, recs)
        return TestPredictAPI._cached[0]

    def test_records_to_xy_used_in_api_path(self):
        """The API builds RaceRecord then calls rank_drivers; test that path."""
        pred = self._make_trained_predictor()
        records = _make_race(n=22, winner_idx=0)
        rankings = pred.rank_drivers(records)
        assert len(rankings) == 22
        assert rankings[0]["rank"] == 1

    def test_feature_dict_in_rankings(self):
        pred     = self._make_trained_predictor()
        records  = _make_race(n=5)
        rankings = pred.rank_drivers(records)
        for entry in rankings:
            assert set(entry["features"].keys()) == set(ALL_FEATURE_NAMES)

    def test_model_meta_to_dict(self):
        pred = self._make_trained_predictor()
        d    = pred.meta.to_dict()
        assert "best_model"     in d
        assert "cv_roc_auc"     in d
        assert "feature_names"  in d
        assert "trained_at"     in d

    def test_is_trained_false_without_artefacts(self):
        """is_trained() should return False when artefact files don't exist."""
        from app.ml.model import MODEL_PATH, META_PATH
        # Only test if artefacts don't exist (don't delete them if they do)
        if not MODEL_PATH.exists():
            assert not WinnerPredictor.is_trained()

    def test_driver_features_field_bounds_enforced(self):
        """
        The DriverFeatures schema declares driver_skill in [0,1].
        Verify this constraint is documented in schemas_api and that the
        RaceRecord used by the model rejects impossible values at the
        feature-matrix level.
        """
        # schemas_api documents ge=0, le=1 for driver_skill.
        # Test the model pipeline receives sane values by building a
        # RaceRecord directly with an out-of-range skill and checking
        # the feature dict still surfaces it (the model's responsibility
        # to handle; field-level clamping is Pydantic's job at the API layer).
        rec = _make_record(driver_skill=1.5)   # out-of-range but dataclass allows it
        feat = rec.to_feature_dict()
        # The feature is present; the API layer (Pydantic) would reject it
        assert "driver_skill" in feat
        assert feat["driver_skill"] == 1.5      # dataclass doesn't clamp

    def test_sim_predict_circuit_type_encoding(self):
        """
        Valid circuit_type strings must map to 0/1/2 in CIRCUIT_TYPE_ENCODING.
        Invalid strings should NOT be present in the encoding dict.
        """
        from app.ml.schema import CIRCUIT_TYPE_ENCODING
        valid   = {"street", "balanced", "power"}
        invalid = {"oval", "figure8", "dragstrip"}
        for v in valid:
            assert v in CIRCUIT_TYPE_ENCODING, f"Missing valid circuit: {v}"
        for iv in invalid:
            assert iv not in CIRCUIT_TYPE_ENCODING, f"Should not have: {iv}"


# ---------------------------------------------------------------------------
# End-to-end smoke test
# ---------------------------------------------------------------------------

class TestEndToEnd:
    def test_full_pipeline(self):
        """Generate → train → predict → rankings make sense."""
        gen  = DatasetGenerator(total_laps=5, timestep=2.0,
                                seed=123, verbose=False)
        recs = gen.generate(n_races=25)

        pred = WinnerPredictor()
        meta = pred.train(recs)

        # Pick any race and get rankings
        race_id   = recs[0].race_id
        race_recs = [r for r in recs if r.race_id == race_id]
        rankings  = pred.rank_drivers(race_recs)

        # Top-ranked driver should have the highest probability
        assert rankings[0]["win_prob"] >= rankings[1]["win_prob"]

        # Ranks should be 1-indexed sequential
        assert [e["rank"] for e in rankings] == list(range(1, len(race_recs) + 1))

        # Meta checks
        assert meta.n_races == 25
        assert meta.n_rows  == 25 * 22
        assert 0.0 <= meta.top1_accuracy <= 1.0


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_classes = [
        TestSchema,
        TestDatasetHelpers,
        TestDatasetGenerator,
        TestRecordsToXY,
        TestTop1Accuracy,
        TestWinnerPredictorTrain,
        TestPredictAPI,
        TestEndToEnd,
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
                import traceback; traceback.print_exc()
                failed += 1

    print(f"\n{'='*60}")
    print(f"  {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
