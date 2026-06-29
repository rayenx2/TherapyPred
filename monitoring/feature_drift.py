"""
monitoring/feature_drift.py
----------------------------
TherapyPred — Feature Distribution Drift Monitor

Monitors input feature distributions at inference time against the training
baseline distribution stored in data/processed/. Flags drift using
configurable thresholds per feature and emits Prometheus-compatible alerts.

Supported drift detectors:
  - Numeric features: Population Stability Index (PSI) + KL divergence
  - Categorical features: Chi-squared frequency shift + JS divergence

Usage:
    # Run standalone drift check against saved baseline
    python monitoring/feature_drift.py

    # Check specific input batch
    python monitoring/feature_drift.py --input-file data/processed/X_test.csv

    # Set custom PSI threshold
    python monitoring/feature_drift.py --psi-threshold 0.15

Author: Rayen Lassoued
        github.com/Hamilas | https://www.linkedin.com/in/lassoued-rayen/
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("feature_drift")


# ── Constants ─────────────────────────────────────────────────────────────────

# PSI thresholds (industry standard)
PSI_LOW      = 0.10   # Minor drift — monitor
PSI_MEDIUM   = 0.20   # Significant drift — investigate
PSI_HIGH     = 0.25   # Major drift — retrain or alert

EPS = 1e-6  # Numerical stability for log operations


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class FeatureDriftResult:
    feature: str
    drift_type: str          # "numeric" or "categorical"
    psi: float               # Population Stability Index
    kl_divergence: float     # KL divergence (numeric) or JS divergence (categorical)
    drift_level: str         # "none" | "minor" | "significant" | "major"
    is_drifted: bool         # True if drift_level >= significant
    baseline_stats: dict = field(default_factory=dict)
    current_stats: dict = field(default_factory=dict)


@dataclass
class DriftReport:
    total_features: int
    drifted_features: int
    drift_rate: float
    results: list[FeatureDriftResult]
    overall_drift: bool
    summary: str


# ── PSI Computation ───────────────────────────────────────────────────────────

def compute_psi_numeric(
    baseline: np.ndarray,
    current: np.ndarray,
    bins: int = 10,
) -> tuple[float, float]:
    """
    Compute PSI and KL divergence for a numeric feature.

    PSI = sum((current_% - baseline_%) * ln(current_% / baseline_%))
    PSI < 0.10  → No significant drift
    PSI < 0.20  → Minor drift
    PSI >= 0.20 → Significant drift (retrain candidate)
    """
    # Use baseline to define bin edges — ensures consistent bucketing
    min_val = min(baseline.min(), current.min())
    max_val = max(baseline.max(), current.max())
    bin_edges = np.linspace(min_val - EPS, max_val + EPS, bins + 1)

    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts,  _ = np.histogram(current,  bins=bin_edges)

    # Convert to proportions with Laplace smoothing to avoid zero-division
    baseline_pct = (baseline_counts + EPS) / (len(baseline) + EPS * bins)
    current_pct  = (current_counts  + EPS) / (len(current)  + EPS * bins)

    psi = float(np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct)))
    kl  = float(np.sum(baseline_pct * np.log(baseline_pct / current_pct)))

    return abs(psi), abs(kl)


def compute_psi_categorical(
    baseline: np.ndarray,
    current: np.ndarray,
) -> tuple[float, float]:
    """
    Compute PSI and Jensen-Shannon divergence for a categorical feature.
    Handles unseen categories in current distribution gracefully.
    """
    all_categories = sorted(set(baseline) | set(current))

    baseline_counts = np.array([np.sum(baseline == c) for c in all_categories], dtype=float)
    current_counts  = np.array([np.sum(current  == c) for c in all_categories], dtype=float)

    baseline_pct = (baseline_counts + EPS) / (len(baseline) + EPS * len(all_categories))
    current_pct  = (current_counts  + EPS) / (len(current)  + EPS * len(all_categories))

    psi = float(np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct)))

    # Jensen-Shannon divergence (symmetric, bounded [0, 1])
    m = (baseline_pct + current_pct) / 2
    js = 0.5 * np.sum(baseline_pct * np.log(baseline_pct / m + EPS)) + \
         0.5 * np.sum(current_pct  * np.log(current_pct  / m + EPS))

    return abs(psi), float(abs(js))


# ── Drift Level Classifier ────────────────────────────────────────────────────

def classify_drift(psi: float, threshold: float) -> tuple[str, bool]:
    """Map PSI value to drift severity label and boolean flag."""
    if psi < PSI_LOW:
        return "none", False
    if psi < PSI_MEDIUM:
        return "minor", False
    if psi < threshold:
        return "significant", True
    return "major", True


# ── Baseline Loader ───────────────────────────────────────────────────────────

def load_baseline(processed_dir: str) -> Optional[pd.DataFrame]:
    """Load training data (X_train) as the reference distribution baseline."""
    path = Path(processed_dir) / "X_train.csv"
    if not path.exists():
        logger.error(
            f"Baseline file not found: {path}. "
            "Run `make run-pipeline` to generate training artifacts."
        )
        return None
    try:
        df = pd.read_csv(path)
        logger.info(f"Baseline loaded: {path} ({len(df)} rows, {len(df.columns)} columns)")
        return df
    except Exception as e:
        logger.error(f"Failed to load baseline: {e}")
        return None


def load_params(params_path: str = "params.yaml") -> dict:
    """Load pipeline parameters."""
    try:
        with open(params_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load params.yaml: {e}")
        return {}


# ── Core Drift Check ──────────────────────────────────────────────────────────

def check_feature_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
    psi_threshold: float = PSI_MEDIUM,
) -> DriftReport:
    """
    Compare current input distribution against baseline for all features.
    Returns a structured DriftReport with per-feature results.
    """
    results: list[FeatureDriftResult] = []

    for feature in numeric_features:
        if feature not in baseline_df.columns or feature not in current_df.columns:
            logger.warning(f"Numeric feature '{feature}' missing in one dataset — skipping")
            continue

        baseline_vals = baseline_df[feature].dropna().values.astype(float)
        current_vals  = current_df[feature].dropna().values.astype(float)

        if len(current_vals) < 10:
            logger.warning(f"Feature '{feature}': too few current samples ({len(current_vals)}) — skipping drift check")
            continue

        psi, kl = compute_psi_numeric(baseline_vals, current_vals)
        level, is_drifted = classify_drift(psi, psi_threshold)

        results.append(FeatureDriftResult(
            feature=feature,
            drift_type="numeric",
            psi=round(psi, 5),
            kl_divergence=round(kl, 5),
            drift_level=level,
            is_drifted=is_drifted,
            baseline_stats={
                "mean":   round(float(baseline_vals.mean()), 3),
                "std":    round(float(baseline_vals.std()),  3),
                "min":    round(float(baseline_vals.min()),  3),
                "max":    round(float(baseline_vals.max()),  3),
                "n":      len(baseline_vals),
            },
            current_stats={
                "mean":   round(float(current_vals.mean()), 3),
                "std":    round(float(current_vals.std()),  3),
                "min":    round(float(current_vals.min()),  3),
                "max":    round(float(current_vals.max()),  3),
                "n":      len(current_vals),
            },
        ))

    # Categorical features — note: preprocess.py one-hot encodes them
    # so we check the original categorical columns if available
    for feature in categorical_features:
        if feature not in baseline_df.columns or feature not in current_df.columns:
            continue

        baseline_vals = baseline_df[feature].dropna().astype(str).values
        current_vals  = current_df[feature].dropna().astype(str).values

        if len(current_vals) < 5:
            logger.warning(f"Feature '{feature}': too few current samples — skipping")
            continue

        psi, js = compute_psi_categorical(baseline_vals, current_vals)
        level, is_drifted = classify_drift(psi, psi_threshold)

        baseline_freq = {
            k: int(v) for k, v in
            zip(*np.unique(baseline_vals, return_counts=True))
        }
        current_freq = {
            k: int(v) for k, v in
            zip(*np.unique(current_vals, return_counts=True))
        }

        results.append(FeatureDriftResult(
            feature=feature,
            drift_type="categorical",
            psi=round(psi, 5),
            kl_divergence=round(js, 5),
            drift_level=level,
            is_drifted=is_drifted,
            baseline_stats={"freq": baseline_freq, "n": len(baseline_vals)},
            current_stats={"freq": current_freq,   "n": len(current_vals)},
        ))

    total_features  = len(results)
    drifted_features = sum(1 for r in results if r.is_drifted)
    drift_rate       = drifted_features / total_features if total_features > 0 else 0.0
    overall_drift    = drift_rate > 0.25  # >25% features drifted → overall alert

    if overall_drift:
        summary = f"DRIFT DETECTED: {drifted_features}/{total_features} features drifted. Consider retraining."
    elif drifted_features > 0:
        summary = f"MINOR DRIFT: {drifted_features}/{total_features} features show minor drift. Monitor closely."
    else:
        summary = f"NO DRIFT: All {total_features} features within expected distribution."

    return DriftReport(
        total_features=total_features,
        drifted_features=drifted_features,
        drift_rate=round(drift_rate, 4),
        results=results,
        overall_drift=overall_drift,
        summary=summary,
    )


# ── Display ───────────────────────────────────────────────────────────────────

def print_drift_report(report: DriftReport) -> None:
    """Print formatted drift report to stdout."""
    sep = "─" * 72
    print(f"\n{sep}")
    print("  TherapyPred — Feature Drift Report")
    print(sep)
    print(f"  {'Feature':<28} {'Type':<12} {'PSI':>7} {'JS/KL':>7} {'Level':<14} {'Drifted'}")
    print(f"  {'─'*28} {'─'*12} {'─'*7} {'─'*7} {'─'*14} {'─'*8}")

    for r in sorted(report.results, key=lambda x: x.psi, reverse=True):
        flag = "YES !" if r.is_drifted else "no"
        level_display = r.drift_level.upper() if r.is_drifted else r.drift_level
        print(
            f"  {r.feature:<28} {r.drift_type:<12} {r.psi:>7.4f} "
            f"{r.kl_divergence:>7.4f} {level_display:<14} {flag}"
        )

    print(sep)
    print(f"\n  {report.summary}")
    print(f"  Drift rate: {report.drift_rate:.1%} ({report.drifted_features}/{report.total_features} features)")
    print(f"\n  PSI Thresholds:")
    print(f"    < {PSI_LOW:.2f}  → No drift")
    print(f"    < {PSI_MEDIUM:.2f}  → Minor drift (monitor)")
    print(f"    >= {PSI_MEDIUM:.2f} → Significant drift (investigate)")
    print(f"    >= {PSI_HIGH:.2f} → Major drift (retrain)")
    print(f"\n{sep}\n")


def save_drift_report(report: DriftReport, output_path: str) -> None:
    """Persist drift report to JSON for CI/CD integration."""
    data = {
        "summary": report.summary,
        "overall_drift": report.overall_drift,
        "drift_rate": report.drift_rate,
        "total_features": report.total_features,
        "drifted_features": report.drifted_features,
        "features": [
            {
                "feature": r.feature,
                "type": r.drift_type,
                "psi": r.psi,
                "kl_divergence": r.kl_divergence,
                "drift_level": r.drift_level,
                "is_drifted": r.is_drifted,
            }
            for r in report.results
        ],
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Drift report saved to: {output_path}")


# ── Entry Point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TherapyPred feature drift monitoring.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitoring/feature_drift.py
  python monitoring/feature_drift.py --input-file data/processed/X_test.csv
  python monitoring/feature_drift.py --psi-threshold 0.15 --save-report monitoring/drift_report.json
        """,
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory with processed data artifacts (default: data/processed)",
    )
    parser.add_argument(
        "--input-file",
        default=None,
        help="CSV file to check for drift against baseline. Defaults to X_test.csv.",
    )
    parser.add_argument(
        "--psi-threshold",
        type=float,
        default=PSI_MEDIUM,
        help=f"PSI threshold for 'drifted' classification (default: {PSI_MEDIUM})",
    )
    parser.add_argument(
        "--save-report",
        default=None,
        help="If set, save JSON drift report to this path.",
    )
    parser.add_argument(
        "--params-file",
        default="params.yaml",
        help="Path to params.yaml (default: params.yaml)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = load_params(args.params_file)

    # Resolve feature lists from params.yaml
    features_cfg     = params.get("features", {})
    numeric_features     = features_cfg.get("numeric", ["Age", "Dosage_mg", "Treatment_Duration_days"])
    categorical_features = features_cfg.get("categorical", ["Gender", "Condition", "Drug_Name", "Side_Effects"])

    # Load baseline (X_train)
    baseline_df = load_baseline(args.processed_dir)
    if baseline_df is None:
        sys.exit(1)

    # Load current input for comparison
    input_path = args.input_file or os.path.join(args.processed_dir, "X_test.csv")
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        current_df = pd.read_csv(input_path)
        logger.info(f"Current input loaded: {input_path} ({len(current_df)} rows)")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)

    # Run drift detection
    logger.info(
        f"Running drift check — {len(numeric_features)} numeric + "
        f"{len(categorical_features)} categorical features"
    )
    report = check_feature_drift(
        baseline_df=baseline_df,
        current_df=current_df,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        psi_threshold=args.psi_threshold,
    )

    print_drift_report(report)

    if args.save_report:
        save_drift_report(report, args.save_report)

    # Exit code: 0 = no drift, 1 = drift detected (for CI/CD pipelines)
    if report.overall_drift:
        logger.warning("Overall drift threshold exceeded. Recommend model retraining.")
        sys.exit(1)


if __name__ == "__main__":
    main()
