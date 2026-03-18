#!/usr/bin/env python3
"""
train.py — Standalone CLI training script for the race-winner predictor.

Usage
-----
From the project root:

    # Quick smoke-test (50 races ≈ 1 100 rows)
    python -m app.ml.train --races 50

    # Full training run (500 races ≈ 11 000 rows — recommended)
    python -m app.ml.train --races 500

    # Use a pre-generated CSV instead of re-running the simulator
    python -m app.ml.train --csv path/to/dataset.csv

    # Save generated dataset to CSV alongside training
    python -m app.ml.train --races 200 --save-csv data/race_dataset.csv

Options
-------
--races      N     Number of races to simulate (default: 200)
--laps       N     Laps per race (default: 20; shorter = faster generation)
--timestep   F     Simulator timestep in seconds (default: 1.0)
--csv        PATH  Load existing CSV instead of generating new data
--save-csv   PATH  Also save generated dataset to this path
--seed       N     Random seed (default: 42)
--no-save         Do NOT save the model artefacts after training
--quiet            Suppress verbose simulator output
"""

import argparse
import sys
import os
from pathlib import Path

# ── allow running as `python app/ml/train.py` from repo root ──────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Train the race-winner prediction model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--races",     type=int,   default=200,
                   help="Number of races to simulate")
    p.add_argument("--laps",      type=int,   default=20,
                   help="Laps per race (shorter = faster data generation)")
    p.add_argument("--timestep",  type=float, default=1.0,
                   help="Simulator timestep in seconds")
    p.add_argument("--csv",       type=str,   default=None,
                   help="Load existing CSV instead of generating data")
    p.add_argument("--save-csv",  type=str,   default=None,
                   help="Save generated dataset to this path")
    p.add_argument("--seed",      type=int,   default=42,
                   help="Random seed")
    p.add_argument("--no-save",   action="store_true",
                   help="Do not persist model artefacts")
    p.add_argument("--quiet",     action="store_true",
                   help="Suppress verbose progress output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    from app.ml.dataset import DatasetGenerator
    from app.ml.model   import WinnerPredictor
    from app.ml.schema  import csv_to_records

    print("\n" + "=" * 60)
    print("🏎️  Race Winner Predictor — Training Pipeline")
    print("=" * 60)

    # ── Step 1: Dataset ───────────────────────────────────────────────
    if args.csv:
        print(f"\n📂 Loading dataset from {args.csv}…")
        records = csv_to_records(args.csv)
        print(f"   Loaded {len(records)} rows "
              f"({len(set(r.race_id for r in records))} races)")
    else:
        print(f"\n🚗 Generating dataset: {args.races} races × 22 drivers")
        print(f"   Laps: {args.laps}  |  Timestep: {args.timestep}s  "
              f"|  Seed: {args.seed}")
        gen = DatasetGenerator(
            total_laps   = args.laps,
            timestep     = args.timestep,
            seed         = args.seed,
            verbose      = not args.quiet,
            verbose_every = 20,
        )
        if args.save_csv:
            records = gen.generate_and_save(args.races, args.save_csv)
        else:
            records = gen.generate(args.races)

    # ── Step 2: Sanity check ──────────────────────────────────────────
    n_winners = sum(r.won for r in records)
    n_races   = len(set(r.race_id for r in records))
    print(f"\n✅ Dataset summary:")
    print(f"   Total rows    : {len(records)}")
    print(f"   Races         : {n_races}")
    print(f"   Winners       : {n_winners} ({n_winners/len(records)*100:.1f}%)")
    print(f"   Drivers/race  : {len(records)/n_races:.1f}")

    # Feature distribution spot-check
    from collections import Counter
    conds  = Counter(r.weather_condition  for r in records)
    circs  = Counter(r.circuit_type       for r in records)
    strats = Counter(r.tyre_strategy      for r in records)
    print(f"\n   Weather dist  : {dict(sorted(conds.items()))}")
    print(f"   Circuit dist  : {dict(sorted(circs.items()))}")
    print(f"   Strategy dist : {dict(sorted(strats.items()))}")

    # ── Step 3: Train ─────────────────────────────────────────────────
    predictor = WinnerPredictor()
    meta      = predictor.train(records)

    # ── Step 4: Spot-check predictions ───────────────────────────────
    print(f"\n🔍 Prediction spot-check (first race):")
    first_race_id = records[0].race_id
    first_race    = [r for r in records if r.race_id == first_race_id]
    rankings      = predictor.rank_drivers(first_race)
    actual_winner = next((r.driver_name for r in first_race if r.won), "?")
    print(f"   Actual winner : {actual_winner}")
    print(f"   {'Rank':<5} {'Driver':<22} {'P(win)'}")
    for entry in rankings[:5]:
        mark = " ← winner" if entry["driver"] == actual_winner else ""
        print(f"   {entry['rank']:<5} {entry['driver']:<22} "
              f"{entry['win_prob']:.4f}{mark}")

    # ── Step 5: Save ──────────────────────────────────────────────────
    if not args.no_save:
        predictor.save()
        print(f"\n📦 Training complete.  Model ready for inference.")
        print(f"   → Load with: WinnerPredictor.load()")
        print(f"   → Serve with: uvicorn app.main:app")
    else:
        print(f"\n⚠️  --no-save set: model NOT persisted.")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
