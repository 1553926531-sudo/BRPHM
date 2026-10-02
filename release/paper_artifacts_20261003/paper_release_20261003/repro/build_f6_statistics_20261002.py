from __future__ import annotations

"""Build F6 statistics with explicit frozen-reference and replay provenance."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon


HERE = Path(__file__).resolve()


def project_root() -> Path:
    """Resolve either the source checkout or the self-contained release tree."""
    candidates = (HERE.parent, *HERE.parents)
    for candidate in candidates:
        if (candidate / "work" / "paper").is_dir():
            return candidate
    for candidate in candidates:
        if (candidate / "review").is_dir() and (candidate / "repro").is_dir():
            return candidate
    raise RuntimeError(f"cannot resolve project root from {HERE}")


ROOT = project_root()
PAPER = ROOT / "work" / "paper" if (ROOT / "work" / "paper").is_dir() else ROOT
REVIEW = PAPER / "review/f6_statistics_20261002"
F5_DIR = PAPER / "review/f5_unit_metrics_20261002"
PAIRED = F5_DIR / "formal_unit_paired_metrics.csv"
CANDIDATE_UNITS = F5_DIR / "formal_unit_metrics.csv"
FOLD = F5_DIR / "formal_metrics_unrounded.json"
F5_LEDGER = F5_DIR / "f5_evidence_ledger_reconciled.json"
SEED_FOLD = PAPER / "review/f6_seed_metrics_20261002/seed_fold_metrics.csv"
SEED_UNITS = PAPER / "review/f6_seed_metrics_20261002/seed_unit_metrics.csv"
SEED_SUMMARY = PAPER / "review/f6_seed_metrics_20261002/seed_metrics_summary.json"
SEEDS = (17, 42, 73)
BOOTSTRAP_REPS = 20000
BOOTSTRAP_SEED = 20261002
ALPHA = 0.05
FAMILY_SIZE = 12
TOLERANCE = 1e-12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def key(row: dict) -> tuple[str, str]:
    return str(row["component"]), str(row["test_orbit"])


def unit_key(row: dict) -> tuple[str, str, str]:
    return str(row["component"]), str(row["test_orbit"]), str(row["unit_id"])


def paired_test(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        raise ValueError("empty paired unit sample")
    nonzero = values[np.abs(values) > 0.0]
    if nonzero.size == 0:
        statistic, p_value = 0.0, 1.0
    else:
        result = wilcoxon(values, alternative="less", zero_method="wilcox", method="auto")
        statistic, p_value = float(result.statistic), float(result.pvalue)
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    return {
        "n_units": int(values.size),
        "mean_delta": mean,
        "median_delta": float(np.median(values)),
        "sd_delta": sd,
        "cohen_dz": mean / sd if sd > 0 else None,
        "wilcoxon_statistic": statistic,
        "wilcoxon_p_less": p_value,
        "wilcoxon_p_bonferroni": min(1.0, p_value * FAMILY_SIZE),
    }


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator) -> list[float]:
    values = np.asarray(values, dtype=np.float64)
    draws = rng.integers(0, values.size, size=(BOOTSTRAP_REPS, values.size))
    means = values[draws].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def candidate_cluster_bootstrap(group: list[dict], rng: np.random.Generator) -> dict:
    windows = np.asarray([int(row["n_windows"]) for row in group], dtype=np.int64)
    rmse = np.asarray([float(row["rmse"]) for row in group], dtype=np.float64)
    mae = np.asarray([float(row["mae"]) for row in group], dtype=np.float64)
    if np.any(windows <= 0):
        raise ValueError("unit with no windows in candidate metrics")
    draws = rng.integers(0, len(group), size=(BOOTSTRAP_REPS, len(group)))
    sampled_windows = windows[draws]
    total_windows = sampled_windows.sum(axis=1)
    boot_rmse = np.sqrt((sampled_windows * np.square(rmse[draws])).sum(axis=1) / total_windows)
    boot_mae = (sampled_windows * mae[draws]).sum(axis=1) / total_windows
    return {
        "n_units": len(group),
        "mean_unit_rmse": float(np.mean(rmse)),
        "median_unit_rmse": float(np.median(rmse)),
        "sd_unit_rmse": float(np.std(rmse, ddof=1)),
        "mean_unit_mae": float(np.mean(mae)),
        "median_unit_mae": float(np.median(mae)),
        "sd_unit_mae": float(np.std(mae, ddof=1)),
        "candidate_rmse_bootstrap_ci95": [float(x) for x in np.quantile(boot_rmse, [0.025, 0.975])],
        "candidate_mae_bootstrap_ci95": [float(x) for x in np.quantile(boot_mae, [0.025, 0.975])],
        "bootstrap_rmse_samples": boot_rmse,
        "bootstrap_mae_samples": boot_mae,
    }


def main() -> int:
    REVIEW.mkdir(parents=True, exist_ok=True)
    required = (PAIRED, CANDIDATE_UNITS, FOLD, F5_LEDGER, SEED_FOLD, SEED_UNITS, SEED_SUMMARY)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("F6 inputs missing: " + ", ".join(missing))

    f5_ledger = json.loads(F5_LEDGER.read_text(encoding="utf-8"))
    if f5_ledger["unit_pairing"]["paired_csv_valid_for_frozen_reference_inference"]:
        raise ValueError("F5 does not classify the paired CSV as diagnostic-only")
    fold_doc = json.loads(FOLD.read_text(encoding="utf-8"))
    seed_doc = json.loads(SEED_SUMMARY.read_text(encoding="utf-8"))
    candidate_rows = read_csv(CANDIDATE_UNITS)
    paired_rows = read_csv(PAIRED)
    seed_fold_rows = read_csv(SEED_FOLD)
    seed_unit_rows = read_csv(SEED_UNITS)

    assert len(candidate_rows) == len(paired_rows) == 443
    assert len(seed_fold_rows) == 18 and len(seed_unit_rows) == int(seed_doc["seed_unit_row_count"])
    candidate_by_unit = {unit_key(row): row for row in candidate_rows}
    paired_by_unit = {unit_key(row): row for row in paired_rows}
    assert len(candidate_by_unit) == len(candidate_rows)
    assert candidate_by_unit.keys() == paired_by_unit.keys()
    for k, candidate in candidate_by_unit.items():
        paired_candidate = paired_by_unit[k]
        assert int(candidate["n_windows"]) == int(paired_candidate["n_windows"])
        for metric in ("rmse", "mae", "bias"):
            assert float(candidate[metric]) == float(paired_candidate[f"candidate_{metric}"])

    fold_rows = {
        key(row): row
        for row in fold_doc["fold_metrics"]
    }
    seed_groups: dict[tuple[str, str], list[dict]] = {}
    for row in seed_fold_rows:
        seed_groups.setdefault(key(row), []).append(row)
    seed_unit_groups: dict[tuple[str, str, int], list[dict]] = {}
    for row in seed_unit_rows:
        seed_unit_groups.setdefault((str(row["component"]), str(row["test_orbit"]), int(row["seed"])), []).append(row)
    assert set(fold_rows) == {
        (component, orbit)
        for component in ("bat", "rwa")
        for orbit in ("LEO500", "LEO550", "LEO700")
    }
    assert set(seed_groups) == set(fold_rows)
    assert all(len(group) == len(SEEDS) for group in seed_groups.values())

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    frozen_folds = []
    replay_folds = []
    seed_sensitivity_folds = []
    for fold_key in sorted(fold_rows):
        component, orbit = fold_key
        fold = fold_rows[fold_key]
        units = [row for row in candidate_rows if key(row) == fold_key]
        replay = [row for row in paired_rows if key(row) == fold_key]
        assert len(units) == int(fold["n_units"])
        assert len(replay) == len(units)
        boot = candidate_cluster_bootstrap(units, rng)
        frozen_rmse = float(fold["reference_rmse"])
        frozen_mae = float(fold["reference_mae"])
        candidate_rmse = float(fold["candidate_rmse"])
        candidate_mae = float(fold["candidate_mae"])
        rmse_delta = candidate_rmse - frozen_rmse
        mae_delta = candidate_mae - frozen_mae
        rmse_boot_delta = boot.pop("bootstrap_rmse_samples") - frozen_rmse
        mae_boot_delta = boot.pop("bootstrap_mae_samples") - frozen_mae
        simultaneous_quantile = 1.0 - ALPHA / FAMILY_SIZE
        rmse_upper = float(np.quantile(rmse_boot_delta, simultaneous_quantile))
        mae_upper = float(np.quantile(mae_boot_delta, simultaneous_quantile))
        frozen_folds.append(
            {
                "component": component,
                "test_orbit": orbit,
                "physical_unit": "cycles" if component == "bat" else "days",
                "n_units": len(units),
                "n_windows": int(fold["n_windows"]),
                "frozen_reference_rmse": frozen_rmse,
                "candidate_rmse": candidate_rmse,
                "delta_rmse": rmse_delta,
                "relative_rmse_change_pct": 100.0 * rmse_delta / frozen_rmse,
                "candidate_rmse_cluster_bootstrap_ci95": boot["candidate_rmse_bootstrap_ci95"],
                "delta_rmse_cluster_bootstrap_ci95_vs_fixed_reference": [
                    float(np.quantile(rmse_boot_delta, 0.025)),
                    float(np.quantile(rmse_boot_delta, 0.975)),
                ],
                "delta_rmse_bonferroni_one_sided_upper_bound": rmse_upper,
                "familywise_nonregression_supported_rmse": rmse_upper <= TOLERANCE,
                "familywise_strict_gain_supported_rmse": rmse_upper < -TOLERANCE,
                "frozen_reference_mae": frozen_mae,
                "candidate_mae": candidate_mae,
                "delta_mae": mae_delta,
                "relative_mae_change_pct": 100.0 * mae_delta / frozen_mae,
                "candidate_mae_cluster_bootstrap_ci95": boot["candidate_mae_bootstrap_ci95"],
                "delta_mae_cluster_bootstrap_ci95_vs_fixed_reference": [
                    float(np.quantile(mae_boot_delta, 0.025)),
                    float(np.quantile(mae_boot_delta, 0.975)),
                ],
                "delta_mae_bonferroni_one_sided_upper_bound": mae_upper,
                "familywise_nonregression_supported_mae": mae_upper <= TOLERANCE,
                "familywise_strict_gain_supported_mae": mae_upper < -TOLERANCE,
                "candidate_unit_distribution": {
                    k: v for k, v in boot.items() if k not in {"candidate_rmse_bootstrap_ci95", "candidate_mae_bootstrap_ci95"}
                },
                "unit_cluster_bootstrap": {
                    "repetitions": BOOTSTRAP_REPS,
                    "rng_seed": BOOTSTRAP_SEED,
                    "sampling_unit": "unit_id; sample n_units with replacement and retain all windows per sampled unit",
                    "window_counts_preserved": True,
                    "reference_treatment": "frozen fold aggregate held fixed; its unit-level sampling variance and paired covariance are unavailable",
                },
            }
        )

        replay_rmse_delta = np.asarray(
            [float(row["candidate_rmse"]) - float(row["reference_rmse"]) for row in replay],
            dtype=np.float64,
        )
        replay_mae_delta = np.asarray(
            [float(row["candidate_mae"]) - float(row["reference_mae"]) for row in replay],
            dtype=np.float64,
        )
        rmse_test = paired_test(replay_rmse_delta)
        mae_test = paired_test(replay_mae_delta)
        rmse_test["bootstrap_ci95_mean_delta"] = bootstrap_mean_ci(replay_rmse_delta, rng)
        mae_test["bootstrap_ci95_mean_delta"] = bootstrap_mean_ci(replay_mae_delta, rng)
        replay_folds.append(
            {
                "component": component,
                "test_orbit": orbit,
                "physical_unit": "cycles" if component == "bat" else "days",
                "comparison": "candidate vs refitted current control replay",
                "rmse": rmse_test,
                "mae": mae_test,
                "fold_delta_vs_frozen_reference_rmse": rmse_delta,
                "fold_delta_vs_frozen_reference_mae": mae_delta,
                "interpretation": "paired unit analysis of a current control replay; not inference against historical frozen-reference predictions",
            }
        )

        seed_rows_for_fold = sorted(seed_groups[fold_key], key=lambda row: int(row["seed"]))
        assert [int(row["seed"]) for row in seed_rows_for_fold] == list(SEEDS)
        seed_rmse = np.asarray([float(row["rmse"]) for row in seed_rows_for_fold])
        seed_mae = np.asarray([float(row["mae"]) for row in seed_rows_for_fold])
        seed_detail = []
        for seed_row in seed_rows_for_fold:
            seed = int(seed_row["seed"])
            unit_rows = seed_unit_groups[(component, orbit, seed)]
            assert len(unit_rows) == int(seed_row["n_units"])
            assert sum(int(row["n_windows"]) for row in unit_rows) == int(seed_row["n_windows"])
            seed_detail.append(
                {
                    "seed": seed,
                    "rmse": float(seed_row["rmse"]),
                    "rmse_delta_vs_frozen_fold_point": float(seed_row["rmse"]) - frozen_rmse,
                    "mae": float(seed_row["mae"]),
                    "mae_delta_vs_frozen_fold_point": float(seed_row["mae"]) - frozen_mae,
                    "unit_rmse_mean": float(np.mean([float(row["rmse"]) for row in unit_rows])),
                    "unit_rmse_sd": float(np.std([float(row["rmse"]) for row in unit_rows], ddof=1)),
                    "unit_mae_mean": float(np.mean([float(row["mae"]) for row in unit_rows])),
                    "unit_mae_sd": float(np.std([float(row["mae"]) for row in unit_rows], ddof=1)),
                }
            )
        seed_sensitivity_folds.append(
            {
                "component": component,
                "test_orbit": orbit,
                "physical_unit": "cycles" if component == "bat" else "days",
                "seed_count": len(SEEDS),
                "seed_rmse_mean": float(seed_rmse.mean()),
                "seed_rmse_sd": float(seed_rmse.std(ddof=1)),
                "seed_rmse_range": [float(seed_rmse.min()), float(seed_rmse.max())],
                "seed_mae_mean": float(seed_mae.mean()),
                "seed_mae_sd": float(seed_mae.std(ddof=1)),
                "seed_mae_range": [float(seed_mae.min()), float(seed_mae.max())],
                "per_seed": seed_detail,
                "interpretation": "descriptive sensitivity only; three fixed seeds are not independent experiment replications",
            }
        )

    output = {
        "schema": "brphm-f6-statistics-reconciled-v2",
        "observed_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "finding": "F6",
        "status": "RECONCILED_DIAGNOSTIC_STATISTICS_REFERENCE_PAIRING_UNAVAILABLE",
        "source_f5_status": f5_ledger["status"],
        "unit_pairing": {
            "frozen_reference_pairing_available": False,
            "replay_csv_role": "DIAGNOSTIC_REPLAY_ONLY",
            "historical_outer_fold_role": "DEVELOPMENT_DIAGNOSTIC_AFTER_F1_CHRONOLOGY_REVIEW",
            "paired_csv_sha256": sha256(PAIRED),
            "candidate_unit_csv_sha256": sha256(CANDIDATE_UNITS),
        },
        "frozen_fold_benchmark": {
            "fold_count": len(frozen_folds),
            "reference_summary_sha256": f5_ledger["reference_binding"]["sha256"],
            "candidate_receipt_sha256": f5_ledger["artifacts"]["candidate_receipt"]["sha256"],
            "unit_cluster_bootstrap": {
                "repetitions": BOOTSTRAP_REPS,
                "seed": BOOTSTRAP_SEED,
                "sampling_unit": "unit_id clusters within each component-orbit fold",
                "window_counts_preserved": True,
                "candidate_metric": "window-weighted RMSE and MAE reconstructed by preserving each sampled unit's complete windows",
                "reference_metric": "hash-bound frozen fold aggregate treated as fixed; no paired unit uncertainty available",
                "familywise_alpha": ALPHA,
                "multiplicity": "Bonferroni over 6 folds x 2 metrics = 12 one-sided upper bounds",
                "one_sided_upper_quantile": 1.0 - ALPHA / FAMILY_SIZE,
                "decision": "upper bound <= 1e-12 supports non-regression conditional on the fixed reference point; upper bound < -1e-12 supports strict gain",
            },
            "folds": frozen_folds,
        },
        "replay_control_sensitivity": {
            "paired_unit_tests_are_diagnostic_only": True,
            "comparison": "candidate vs newly refitted current control; not the historical frozen-reference predictions",
            "bootstrap": {
                "repetitions": BOOTSTRAP_REPS,
                "seed": BOOTSTRAP_SEED,
                "sampling_unit": "paired unit_id within each fold",
                "ci": "percentile 95% CI for equally weighted mean per-unit delta",
            },
            "wilcoxon": {
                "alternative": "candidate minus replay control < 0",
                "zero_method": "wilcox",
                "multiplicity": "Bonferroni over 12 fold x metric tests",
                "family_alpha": ALPHA,
                "adjusted_alpha": ALPHA / FAMILY_SIZE,
            },
            "multiplicity_family_size": FAMILY_SIZE,
            "folds": replay_folds,
        },
        "seed_sensitivity": {
            "seeds": list(SEEDS),
            "seed_count": len(SEEDS),
            "fold_row_count": len(seed_fold_rows),
            "unit_row_count": len(seed_unit_rows),
            "fold_metrics_sha256": sha256(SEED_FOLD),
            "unit_metrics_sha256": sha256(SEED_UNITS),
            "inferential_status": "DESCRIPTIVE_ONLY",
            "aggregation": "published candidate is elementwise median of three seed predictions",
            "folds": seed_sensitivity_folds,
        },
        "limitations": [
            "Historical frozen-reference per-unit predictions were not retained; no frozen-reference paired bootstrap, Wilcoxon, or paired effect size is claimed.",
            "The candidate cluster bootstrap treats the frozen fold aggregate as fixed and does not include reference sampling variance or paired covariance.",
            "The current replay-control paired tests are sensitivity diagnostics for a refitted control and are not substitutes for frozen-reference inference.",
            "The six orbit-component folds are not independent replications; all intervals and tests are fold-specific, with Bonferroni familywise handling across 12 metric comparisons.",
            "Legacy outer folds are development/diagnostic evidence under the F1 chronology resolution, not a fresh untouched population confirmation.",
            "No engineering-relevance threshold was registered; numerical gate passage alone is not practical significance.",
        ],
        "artifacts": {
            "f5_reconciled_ledger": {"path": str(F5_LEDGER), "sha256": sha256(F5_LEDGER)},
            "frozen_fold_metrics": {"path": str(FOLD), "sha256": sha256(FOLD)},
            "candidate_unit_metrics": {"path": str(CANDIDATE_UNITS), "sha256": sha256(CANDIDATE_UNITS)},
            "diagnostic_replay_pairs": {"path": str(PAIRED), "sha256": sha256(PAIRED)},
            "seed_fold_metrics": {"path": str(SEED_FOLD), "sha256": sha256(SEED_FOLD)},
            "seed_unit_metrics": {"path": str(SEED_UNITS), "sha256": sha256(SEED_UNITS)},
            "seed_export_summary": {"path": str(SEED_SUMMARY), "sha256": sha256(SEED_SUMMARY)},
            "statistics_builder": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        },
    }

    output_json = REVIEW / "f6_statistics_reconciled.json"
    output_md = REVIEW / "f6_evidence_ledger_reconciled.md"
    output_json.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# F6 Reconciled Statistical Evidence",
        "",
        "**Audit date:** 2026-10-02 UTC  ",
        f"**Status:** `{output['status']}`",
        "",
        "## Frozen Fold Benchmark",
        "",
        "The exact frozen-reference fold values are hash-bound and compared with candidate unit-cluster bootstrap intervals. The reference fold score is held fixed because its per-unit historical predictions are absent; this is not a paired-reference analysis.",
        "",
        "| Component | Orbit | Units | RMSE delta | RMSE 95% CI | RMSE FWER upper | MAE delta | MAE 95% CI | MAE FWER upper |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in frozen_folds:
        lines.append(
            f"| {row['component'].upper()} | {row['test_orbit']} | {row['n_units']} "
            f"| {row['delta_rmse']:.9g} | {row['delta_rmse_cluster_bootstrap_ci95_vs_fixed_reference'][0]:.9g}, {row['delta_rmse_cluster_bootstrap_ci95_vs_fixed_reference'][1]:.9g} "
            f"| {row['delta_rmse_bonferroni_one_sided_upper_bound']:.9g} "
            f"| {row['delta_mae']:.9g} | {row['delta_mae_cluster_bootstrap_ci95_vs_fixed_reference'][0]:.9g}, {row['delta_mae_cluster_bootstrap_ci95_vs_fixed_reference'][1]:.9g} "
            f"| {row['delta_mae_bonferroni_one_sided_upper_bound']:.9g} |"
        )
    lines.extend(
        [
            "",
            "Units are resampled as clusters with all windows retained, then window-weighted RMSE/MAE are recomputed. Simultaneous one-sided upper bounds use Bonferroni over 12 fold-metric comparisons.",
            "",
            "## Replay Sensitivity",
            "",
            "The paired bootstrap and one-sided Wilcoxon below compare candidate unit errors with a newly refitted current control. The replay is not the frozen historical reference, and these tests are diagnostic only.",
            "",
            "| Component | Orbit | Units | Mean RMSE delta | RMSE CI | Wilcoxon p | Adjusted p | Mean MAE delta | MAE CI | Wilcoxon p | Adjusted p |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in replay_folds:
        rmse, mae = row["rmse"], row["mae"]
        lines.append(
            f"| {row['component'].upper()} | {row['test_orbit']} | {rmse['n_units']} "
            f"| {rmse['mean_delta']:.9g} | {rmse['bootstrap_ci95_mean_delta'][0]:.9g}, {rmse['bootstrap_ci95_mean_delta'][1]:.9g} "
            f"| {rmse['wilcoxon_p_less']:.6g} | {rmse['wilcoxon_p_bonferroni']:.6g} "
            f"| {mae['mean_delta']:.9g} | {mae['bootstrap_ci95_mean_delta'][0]:.9g}, {mae['bootstrap_ci95_mean_delta'][1]:.9g} "
            f"| {mae['wilcoxon_p_less']:.6g} | {mae['wilcoxon_p_bonferroni']:.6g} |"
        )
    lines.extend(
        [
            "",
            "## Seed Sensitivity",
            "",
            "The three fixed seeds are reported descriptively with fold-wise mean, sample SD, and range. They are not treated as independent replications.",
            "",
            "| Component | Orbit | RMSE mean +/- SD | RMSE range | MAE mean +/- SD | MAE range |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in seed_sensitivity_folds:
        lines.append(
            f"| {row['component'].upper()} | {row['test_orbit']} "
            f"| {row['seed_rmse_mean']:.9g} +/- {row['seed_rmse_sd']:.3g} "
            f"| {row['seed_rmse_range'][0]:.9g}, {row['seed_rmse_range'][1]:.9g} "
            f"| {row['seed_mae_mean']:.9g} +/- {row['seed_mae_sd']:.3g} "
            f"| {row['seed_mae_range'][0]:.9g}, {row['seed_mae_range'][1]:.9g} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The deterministic six-fold gate remains separate from statistical and engineering conclusions. The original paired CSV cannot establish frozen-reference unit uncertainty. The candidate-only cluster bootstrap is conditional on the registered orbit sample and a fixed benchmark score; replay-control tests are not substitutes. No practical-significance threshold was pre-registered.",
            "",
            "**Reproduction command:** `python work/paper/repro/build_f6_statistics_20261002.py`",
            "",
        ]
    )
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": output["status"],
                "frozen_folds": len(frozen_folds),
                "replay_folds": len(replay_folds),
                "seed_folds": len(seed_sensitivity_folds),
                "candidate_units": len(candidate_rows),
                "seed_unit_rows": len(seed_unit_rows),
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
