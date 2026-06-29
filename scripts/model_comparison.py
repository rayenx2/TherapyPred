"""
scripts/model_comparison.py
----------------------------
TherapyPred — Model Comparison and Champion Selection

Loads metrics from metrics/ directory, compares multiple model runs by RMSE,
MAE, and R² score, outputs a ranked comparison table, and identifies the
champion model (lowest RMSE). Supports multiple metric files named
scores_*.json or scores.json.

Usage:
    python scripts/model_comparison.py
    python scripts/model_comparison.py --metrics-dir metrics/ --champion-threshold 0.35

Author: Rayen Lassoued
        github.com/Hamilas | https://www.linkedin.com/in/lassoued-rayen/
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("model_comparison")


# ── Data Classes ──────────────────────────────────────────────────────────────

class ModelMetrics:
    """Holds metrics for one model version."""

    def __init__(
        self,
        version: str,
        rmse: float,
        mae: float,
        r2: float,
        source_file: str,
        extra: Optional[dict] = None,
    ):
        if rmse < 0:
            raise ValueError(f"RMSE must be non-negative, got {rmse}")
        if mae < 0:
            raise ValueError(f"MAE must be non-negative, got {mae}")
        self.version = version
        self.rmse = rmse
        self.mae = mae
        self.r2 = r2
        self.source_file = source_file
        self.extra = extra or {}

    def __repr__(self) -> str:
        return (
            f"ModelMetrics(version={self.version!r}, "
            f"rmse={self.rmse:.4f}, mae={self.mae:.4f}, r2={self.r2:.4f})"
        )


# ── Loader ────────────────────────────────────────────────────────────────────

def load_metrics_from_dir(metrics_dir: str) -> list[ModelMetrics]:
    """
    Scan metrics_dir for JSON files containing model evaluation scores.

    Accepts two layouts:
      1. Flat: {"RMSE": 0.312, "MAE": 0.241, "R2": 0.893}
      2. Nested: {"metrics": {"RMSE": 0.312, "MAE": 0.241, "R2": 0.893}}

    File naming:
      - scores.json           → version derived from file mtime
      - scores_v1.json        → version "v1"
      - scores_a3f8c2.json    → version "a3f8c2"
    """
    dir_path = Path(metrics_dir)
    if not dir_path.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        sys.exit(1)

    json_files = sorted(dir_path.glob("scores*.json"))
    if not json_files:
        logger.warning(f"No scores*.json files found in {metrics_dir}")
        return []

    results = []
    for fpath in json_files:
        try:
            with open(fpath) as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Skipping {fpath.name}: {e}")
            continue

        # Support nested layout
        data = raw.get("metrics", raw)

        # Extract metrics — accept both upper and lower key spellings
        rmse = data.get("RMSE") or data.get("rmse")
        mae  = data.get("MAE")  or data.get("mae")
        r2   = data.get("R2")   or data.get("r2") or data.get("R_squared")

        if rmse is None or mae is None or r2 is None:
            logger.warning(
                f"Skipping {fpath.name}: missing RMSE/MAE/R2 keys. Keys found: {list(data.keys())}"
            )
            continue

        # Derive version from filename
        stem = fpath.stem  # e.g. "scores_v1" or "scores"
        version = stem.replace("scores_", "").replace("scores", "") or "latest"
        if version == "latest":
            mtime = int(fpath.stat().st_mtime)
            version = f"v-{mtime % 0xFFFFFF:06x}"

        try:
            metrics = ModelMetrics(
                version=version,
                rmse=float(rmse),
                mae=float(mae),
                r2=float(r2),
                source_file=str(fpath),
                extra={k: v for k, v in data.items() if k not in ("RMSE", "rmse", "MAE", "mae", "R2", "r2")},
            )
            results.append(metrics)
        except ValueError as e:
            logger.warning(f"Skipping {fpath.name}: invalid metric value — {e}")

    return results


# ── Comparison ────────────────────────────────────────────────────────────────

def rank_models(models: list[ModelMetrics]) -> list[ModelMetrics]:
    """Sort models by RMSE ascending (lower = better)."""
    return sorted(models, key=lambda m: m.rmse)


def identify_champion(models: list[ModelMetrics], champion_threshold: float) -> Optional[ModelMetrics]:
    """
    Select champion: lowest RMSE that also meets the threshold.
    Returns None if no model meets the threshold.
    """
    ranked = rank_models(models)
    for m in ranked:
        if m.rmse <= champion_threshold:
            return m
    # Fall back to best available even if above threshold
    if ranked:
        logger.warning(
            f"No model meets RMSE threshold {champion_threshold}. "
            f"Selecting best available: {ranked[0].version} (RMSE={ranked[0].rmse:.4f})"
        )
        return ranked[0]
    return None


# ── Display ───────────────────────────────────────────────────────────────────

def print_comparison_table(models: list[ModelMetrics], champion: Optional[ModelMetrics]) -> None:
    """Print a formatted comparison table to stdout."""
    ranked = rank_models(models)
    sep = "─" * 72

    print(f"\n{sep}")
    print("  TherapyPred — Model Comparison Report")
    print(f"  Models evaluated: {len(ranked)}")
    print(sep)
    print(f"  {'Version':<14}  {'RMSE':>8}  {'MAE':>8}  {'R²':>8}  {'Rank':>5}  {'Status':<12}")
    print(f"  {'─'*14}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*5}  {'─'*12}")

    for rank, m in enumerate(ranked, start=1):
        is_champ = champion and m.version == champion.version
        status = "CHAMPION" if is_champ else "Candidate"
        marker = " *" if is_champ else "  "
        print(
            f"{marker} {m.version:<14}  {m.rmse:>8.4f}  {m.mae:>8.4f}  {m.r2:>8.4f}  "
            f"{rank:>5}  {status:<12}"
        )

    print(sep)

    if champion:
        print(f"\n  Champion Model: {champion.version}")
        print(f"    RMSE : {champion.rmse:.4f}  (lower is better)")
        print(f"    MAE  : {champion.mae:.4f}  (lower is better)")
        print(f"    R²   : {champion.r2:.4f}  (higher is better, max 1.0)")
        print(f"    File : {champion.source_file}")
        if champion.extra:
            for k, v in champion.extra.items():
                print(f"    {k:<5}: {v}")
    else:
        print("\n  No champion identified — no models available.")

    print(f"\n{sep}\n")


def save_champion_record(champion: ModelMetrics, output_path: str) -> None:
    """Persist champion selection to JSON for downstream CI/CD gating."""
    record = {
        "champion": {
            "version": champion.version,
            "rmse":    champion.rmse,
            "mae":     champion.mae,
            "r2":      champion.r2,
            "source":  champion.source_file,
        }
    }
    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)
    logger.info(f"Champion record saved to: {output_path}")


# ── Entry Point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare TherapyPred model versions and select champion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/model_comparison.py
  python scripts/model_comparison.py --metrics-dir metrics/ --champion-threshold 0.40
  python scripts/model_comparison.py --save-champion metrics/champion.json
        """,
    )
    parser.add_argument(
        "--metrics-dir",
        default="metrics",
        help="Directory containing scores*.json files (default: metrics/)",
    )
    parser.add_argument(
        "--champion-threshold",
        type=float,
        default=0.40,
        help="Maximum RMSE for champion eligibility (default: 0.40)",
    )
    parser.add_argument(
        "--save-champion",
        default=None,
        help="If set, save champion record to this JSON path (e.g. metrics/champion.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info(f"Scanning metrics directory: {args.metrics_dir}")
    models = load_metrics_from_dir(args.metrics_dir)

    if not models:
        logger.error("No valid model metrics found. Run `make run-pipeline` first to generate metrics/scores.json.")
        sys.exit(1)

    logger.info(f"Loaded {len(models)} model metric file(s)")

    champion = identify_champion(models, champion_threshold=args.champion_threshold)
    print_comparison_table(models, champion)

    if args.save_champion and champion:
        save_champion_record(champion, args.save_champion)

    if champion is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
