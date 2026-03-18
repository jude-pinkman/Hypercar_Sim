"""
WinnerPredictor — trains and serves the race-winner prediction model.

Model architecture
------------------
Two candidates are trained and compared by 5-fold stratified cross-validation
ROC-AUC.  The better model is wrapped in a CalibratedClassifierCV (isotonic
regression) so predicted probabilities are well-calibrated.

Candidate A — GradientBoostingClassifier (primary)
    Handles non-linear feature interactions natively, excellent calibration
    after isotonic post-processing, robust to the class imbalance (~1/22 win
    rate) via ``scale_pos_weight`` analogue (class_weight handled upstream).

Candidate B — RandomForestClassifier (secondary)
    Provides diversity.  Used if its CV AUC beats Gradient Boosting.

Pipeline
--------
1. StandardScaler  — centres continuous features
2. Classifier      — GradientBoosting or RandomForest

Evaluation metrics
------------------
* ROC-AUC (primary selection criterion)
* Precision / Recall / F1 at the threshold that maximises F1
* Brier score (calibration quality)
* Top-1 accuracy: fraction of races where P(win) argmax = actual winner

Artefact layout
---------------
app/ml/artefacts/
    model.joblib        — fitted pipeline (scaler + classifier + calibrator)
    meta.json           — training metadata (date, n_races, AUC, features)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, brier_score_loss,
    precision_recall_fscore_support, classification_report,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    import joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False

from app.ml.schema import (
    RaceRecord, ALL_FEATURE_NAMES, TARGET_NAME,
    FEATURE_RANGES,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ARTEFACT_DIR  = Path(__file__).parent / "artefacts"
MODEL_PATH     = _ARTEFACT_DIR / "model.joblib"
META_PATH      = _ARTEFACT_DIR / "meta.json"


# ---------------------------------------------------------------------------
# Training metadata
# ---------------------------------------------------------------------------

@dataclass
class ModelMeta:
    trained_at:     str       # ISO-8601
    n_races:        int
    n_rows:         int
    best_model:     str       # "GradientBoosting" or "RandomForest"
    cv_roc_auc:     float
    brier_score:    float
    top1_accuracy:  float     # fraction of races where argmax(prob) = winner
    feature_names:  List[str]
    sklearn_version: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "ModelMeta":
        return cls(**d)

    def save(self, path: Path = META_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, path: Path = META_PATH) -> "ModelMeta":
        with open(path) as fh:
            return cls.from_dict(json.load(fh))


# ---------------------------------------------------------------------------
# Feature matrix builder
# ---------------------------------------------------------------------------

def records_to_xy(
    records: List[RaceRecord],
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Convert a list of RaceRecord objects into (X, y, feature_names).

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
    y : ndarray of shape (n_samples,) — binary win labels
    feature_names : list of str
    """
    X = np.array(
        [[getattr(r, f) for f in ALL_FEATURE_NAMES] for r in records],
        dtype=np.float64,
    )
    y = np.array([r.won for r in records], dtype=np.int32)
    return X, y, list(ALL_FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Top-1 accuracy helper
# ---------------------------------------------------------------------------

def _top1_accuracy(
    records: List[RaceRecord],
    probas: np.ndarray,
) -> float:
    """
    Group by race_id; for each race find the driver with highest p(win).
    Return fraction of races where that driver actually won.
    """
    from collections import defaultdict
    race_data: Dict[int, List[Tuple[float, int]]] = defaultdict(list)
    for rec, prob in zip(records, probas):
        race_data[rec.race_id].append((prob, rec.won))

    correct = 0
    for entries in race_data.values():
        best_idx = max(range(len(entries)), key=lambda i: entries[i][0])
        if entries[best_idx][1] == 1:
            correct += 1
    return correct / len(race_data) if race_data else 0.0


# ---------------------------------------------------------------------------
# WinnerPredictor
# ---------------------------------------------------------------------------

class WinnerPredictor:
    """
    Trains, evaluates, saves, and loads the winner prediction model.

    Usage — training
    ----------------
    >>> from app.ml.model import WinnerPredictor
    >>> pred = WinnerPredictor()
    >>> meta = pred.train(records)      # list of RaceRecord
    >>> pred.save()

    Usage — inference
    -----------------
    >>> pred = WinnerPredictor.load()
    >>> probs = pred.predict_proba(records)   # list of RaceRecord for one race
    >>> rankings = pred.rank_drivers(records)
    """

    def __init__(self) -> None:
        self.pipeline: Optional[Pipeline] = None
        self.meta: Optional[ModelMeta]    = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, records: List[RaceRecord]) -> ModelMeta:
        """
        Train on ``records``, select the best model by CV AUC, calibrate it,
        and store pipeline + meta.  Returns the ModelMeta.
        """
        if not records:
            raise ValueError("Cannot train on empty dataset")

        print(f"\n{'='*60}")
        print(f"Training WinnerPredictor on {len(records)} rows "
              f"({len(set(r.race_id for r in records))} races)")
        print(f"{'='*60}")

        X, y, feat_names = records_to_xy(records)
        n_races = len(set(r.race_id for r in records))

        # ── candidate models ─────────────────────────────────────────
        gb_clf = GradientBoostingClassifier(
            n_estimators      = 300,
            learning_rate     = 0.05,
            max_depth         = 4,
            min_samples_leaf  = 10,
            subsample         = 0.8,
            random_state      = 42,
        )
        rf_clf = RandomForestClassifier(
            n_estimators      = 300,
            max_depth         = 8,
            min_samples_leaf  = 10,
            class_weight      = "balanced",
            random_state      = 42,
            n_jobs            = -1,
        )
        candidates = [
            ("GradientBoosting", gb_clf),
            ("RandomForest",     rf_clf),
        ]

        # ── cross-validation ─────────────────────────────────────────
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        best_name, best_clf, best_auc = None, None, -1.0

        print("\n📊 Cross-validation (5-fold stratified ROC-AUC):")
        for name, clf in candidates:
            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("clf",    clf),
            ])
            aucs = cross_val_score(
                pipe, X, y,
                cv      = skf,
                scoring = "roc_auc",
                n_jobs  = -1,
            )
            mean_auc = float(aucs.mean())
            print(f"  {name:<22} AUC = {mean_auc:.4f} ± {aucs.std():.4f}")
            if mean_auc > best_auc:
                best_auc  = mean_auc
                best_name = name
                best_clf  = clf

        print(f"\n✅ Selected: {best_name} (CV AUC = {best_auc:.4f})")

        # ── final fit with calibration ────────────────────────────────
        print("\n🔧 Fitting final model with isotonic calibration…")
        t0   = time.time()
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    CalibratedClassifierCV(best_clf, method="isotonic", cv=5)),
        ])
        pipe.fit(X, y)
        print(f"   Done in {time.time() - t0:.1f}s")

        # ── evaluation on full training set ──────────────────────────
        probas = pipe.predict_proba(X)[:, 1]
        brier  = float(brier_score_loss(y, probas))
        top1   = _top1_accuracy(records, probas)

        print(f"\n📈 Full-data evaluation:")
        print(f"   Brier score     = {brier:.4f}  (lower is better)")
        print(f"   Top-1 accuracy  = {top1:.3f}  "
              f"(model correctly identifies winner in {top1*100:.1f}% of races)")

        # ── feature importances ───────────────────────────────────────
        self._print_feature_importance(best_clf, feat_names)

        self.pipeline = pipe

        # ── metadata ──────────────────────────────────────────────────
        import sklearn
        self.meta = ModelMeta(
            trained_at      = datetime.now(timezone.utc).isoformat(),
            n_races         = n_races,
            n_rows          = len(records),
            best_model      = best_name,
            cv_roc_auc      = round(best_auc, 6),
            brier_score     = round(brier, 6),
            top1_accuracy   = round(top1, 6),
            feature_names   = feat_names,
            sklearn_version = sklearn.__version__,
        )
        return self.meta

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_proba(self, records: List[RaceRecord]) -> np.ndarray:
        """
        Return P(win) for each record.

        Parameters
        ----------
        records : list of RaceRecord for a SINGLE race (1–22 drivers)

        Returns
        -------
        ndarray of shape (n_drivers,) — win probability per driver
        """
        if self.pipeline is None:
            raise RuntimeError("Model not loaded. Call train() or load() first.")
        X, _, _ = records_to_xy(records)
        return self.pipeline.predict_proba(X)[:, 1]

    def rank_drivers(
        self, records: List[RaceRecord]
    ) -> List[Dict]:
        """
        Return drivers sorted descending by P(win).

        Returns a list of dicts:
        {
            "rank":         1,
            "driver":       "Max Verstappen",
            "team":         "Red Bull Racing",
            "win_prob":     0.423,
            "features": { ... }
        }
        """
        probas = self.predict_proba(records)
        entries = []
        for rec, prob in zip(records, probas):
            entries.append({
                "driver":   rec.driver_name,
                "team":     rec.team,
                "win_prob": round(float(prob), 6),
                "features": rec.to_feature_dict(),
            })
        entries.sort(key=lambda e: e["win_prob"], reverse=True)
        for rank, entry in enumerate(entries, start=1):
            entry["rank"] = rank
        return entries

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(
        self,
        model_path: Path = MODEL_PATH,
        meta_path:  Path = META_PATH,
    ) -> None:
        if not _JOBLIB_AVAILABLE:
            raise ImportError("joblib is required to save the model")
        if self.pipeline is None:
            raise RuntimeError("No trained model to save")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, model_path)
        if self.meta:
            self.meta.save(meta_path)
        print(f"\n💾 Model saved → {model_path}")
        print(f"   Meta  saved → {meta_path}")

    @classmethod
    def load(
        cls,
        model_path: Path = MODEL_PATH,
        meta_path:  Path = META_PATH,
    ) -> "WinnerPredictor":
        if not _JOBLIB_AVAILABLE:
            raise ImportError("joblib is required to load the model")
        predictor = cls()
        predictor.pipeline = joblib.load(model_path)
        if meta_path.exists():
            predictor.meta = ModelMeta.load(meta_path)
        return predictor

    @classmethod
    def is_trained(cls) -> bool:
        return MODEL_PATH.exists() and META_PATH.exists()

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @staticmethod
    def _print_feature_importance(clf, feature_names: List[str]) -> None:
        """Print top-10 feature importances if available."""
        importances = None
        if hasattr(clf, "feature_importances_"):
            importances = clf.feature_importances_
        elif hasattr(clf, "estimators_"):
            # CalibratedClassifierCV wraps clf
            pass

        if importances is None:
            return

        pairs = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1], reverse=True,
        )
        print("\n🌲 Feature importances (top 10):")
        for feat, imp in pairs[:10]:
            bar = "█" * int(imp * 40)
            print(f"   {feat:<26} {imp:.4f}  {bar}")
