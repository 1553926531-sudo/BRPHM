from __future__ import annotations

"""Reconcile frozen fold metrics, candidate unit metrics, and replay controls."""

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


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
if (ROOT / "work" / "paper").is_dir():
    PAPER = ROOT / "work" / "paper"
else:
    PAPER = ROOT
INPUT = PAPER / "review/f5_unit_metrics_20261002"
REFERENCE = ROOT / "reference_summary_remote.json"
if not REFERENCE.is_file():
    REFERENCE = PAPER / "evidence/reference_summary_remote.json"
UNIT_BUILDER = PAPER / "repro/build_f5_unit_metrics_20261002.py"
TOLERANCE = 1e-12
REAGGREGATION_REL_TOLERANCE = 1e-10
REAGGREGATION_ABS_TOLERANCE = 1e-12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def weighted_unit_metrics(rows: list[dict], metric: str) -> float:
    windows = sum(int(row["n_windows"]) for row in rows)
    if windows <= 0:
        raise ValueError("fold has no windows")
    if metric == "rmse":
        return math.sqrt(
            sum(int(row["n_windows"]) * float(row[metric]) ** 2 for row in rows) / windows
        )
    if metric == "mae":
        return sum(int(row["n_windows"]) * float(row[metric]) for row in rows) / windows
    raise ValueError(f"unsupported metric: {metric}")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    metrics_path = INPUT / "formal_metrics_unrounded.json"
    unit_path = INPUT / "formal_unit_metrics.csv"
    paired_path = INPUT / "formal_unit_paired_metrics.csv"
    receipt_path = INPUT / "frozen_candidate_receipt.json"
    required = (metrics_path, unit_path, paired_path, receipt_path, REFERENCE, UNIT_BUILDER)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("F5 evidence inputs missing: " + ", ".join(missing))

    summary = json.loads(metrics_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    rows = read_csv(unit_path)
    paired = read_csv(paired_path)
    reference_sha = sha256(REFERENCE)
    assert summary["reference_sha256"] == reference_sha
    assert receipt["frozen_reference"]["sha256"] == reference_sha
    assert len(rows) == int(summary["unit_row_count"])
    assert len(paired) == len(rows)

    row_key = lambda row: (row["component"], row["test_orbit"], row["unit_id"])
    unit_by_key = {row_key(row): row for row in rows}
    paired_by_key = {row_key(row): row for row in paired}
    assert len(unit_by_key) == len(rows), "duplicate candidate unit key"
    assert unit_by_key.keys() == paired_by_key.keys()

    expected_folds = {
        (component, orbit)
        for component in ("bat", "rwa")
        for orbit in ("LEO500", "LEO550", "LEO700")
    }
    folds = {(row["component"], row["test_orbit"]): row for row in summary["fold_metrics"]}
    reference_folds = {
        (str(row["component"]), str(row["test_orbit"])): row
        for row in reference["results"]
    }
    candidate_folds = {
        (str(row["component"]), str(row["test_orbit"])): row
        for row in receipt["formal"]["results"]
    }
    assert len(folds) == len(summary["fold_metrics"]) == 6
    assert set(folds) == expected_folds
    assert set(reference_folds) == expected_folds
    assert set(candidate_folds) == expected_folds

    checks = []
    replay_mismatches = 0
    for key in sorted(expected_folds):
        fold = folds[key]
        frozen_fold = reference_folds[key]["metrics"]
        candidate_fold = candidate_folds[key]["metrics"]
        assert float(fold["reference_rmse"]) == float(frozen_fold["rmse"])
        assert float(fold["reference_mae"]) == float(frozen_fold["mae"])
        assert float(fold["candidate_rmse"]) == float(candidate_fold["rmse"])
        assert float(fold["candidate_mae"]) == float(candidate_fold["mae"])

        selected = [row for row in rows if (row["component"], row["test_orbit"]) == key]
        replay_selected = [row for row in paired if (row["component"], row["test_orbit"]) == key]
        assert len(selected) == int(fold["n_units"])
        assert len(replay_selected) == len(selected)
        assert sum(int(row["n_windows"]) for row in selected) == int(fold["n_windows"])

        candidate_rmse = weighted_unit_metrics(selected, "rmse")
        candidate_mae = weighted_unit_metrics(selected, "mae")
        replay_rmse = weighted_unit_metrics(
            [{"n_windows": row["n_windows"], "rmse": row["reference_rmse"]} for row in replay_selected],
            "rmse",
        )
        replay_mae = weighted_unit_metrics(
            [{"n_windows": row["n_windows"], "mae": row["reference_mae"]} for row in replay_selected],
            "mae",
        )
        for observed, expected in (
            (candidate_rmse, float(fold["candidate_rmse"])),
            (candidate_mae, float(fold["candidate_mae"])),
        ):
            assert math.isclose(
                observed,
                expected,
                rel_tol=REAGGREGATION_REL_TOLERANCE,
                abs_tol=REAGGREGATION_ABS_TOLERANCE,
            ), (key, observed, expected)

        delta_rmse = float(fold["candidate_rmse"]) - float(fold["reference_rmse"])
        delta_mae = float(fold["candidate_mae"]) - float(fold["reference_mae"])
        rmse_pass = delta_rmse <= TOLERANCE
        mae_pass = delta_mae <= TOLERANCE
        assert delta_rmse == float(fold["delta_rmse"])
        assert delta_mae == float(fold["delta_mae"])
        assert rmse_pass == bool(fold["rmse_pass"])
        assert mae_pass == bool(fold["mae_pass"])

        replay_rmse_delta = replay_rmse - float(frozen_fold["rmse"])
        replay_mae_delta = replay_mae - float(frozen_fold["mae"])
        replay_matches_frozen = (
            math.isclose(replay_rmse, float(frozen_fold["rmse"]), rel_tol=0.0, abs_tol=TOLERANCE)
            and math.isclose(replay_mae, float(frozen_fold["mae"]), rel_tol=0.0, abs_tol=TOLERANCE)
        )
        replay_mismatches += int(not replay_matches_frozen)
        checks.append(
            {
                "component": key[0],
                "test_orbit": key[1],
                "n_units": len(selected),
                "n_windows": int(fold["n_windows"]),
                "reference_rmse": float(frozen_fold["rmse"]),
                "candidate_rmse": float(fold["candidate_rmse"]),
                "delta_rmse": delta_rmse,
                "rmse_pass": rmse_pass,
                "reference_mae": float(frozen_fold["mae"]),
                "candidate_mae": float(fold["candidate_mae"]),
                "delta_mae": delta_mae,
                "mae_pass": mae_pass,
                "candidate_rmse_from_units": candidate_rmse,
                "candidate_mae_from_units": candidate_mae,
                "replayed_control_rmse_from_units": replay_rmse,
                "replayed_control_mae_from_units": replay_mae,
                "replayed_control_rmse_minus_frozen": replay_rmse_delta,
                "replayed_control_mae_minus_frozen": replay_mae_delta,
                "replayed_control_matches_frozen_at_gate_tolerance": replay_matches_frozen,
            }
        )

    strict_gain = any(
        row["delta_rmse"] < -TOLERANCE or row["delta_mae"] < -TOLERANCE for row in checks
    )
    all_nonregressive = all(row["rmse_pass"] and row["mae_pass"] for row in checks)
    old_json = INPUT / "f5_evidence_ledger.json"
    old_md = INPUT / "f5_evidence_ledger.md"
    artifacts = {
        "frozen_reference_summary": {"path": str(REFERENCE), "sha256": reference_sha},
        "candidate_receipt": {"path": str(receipt_path), "sha256": sha256(receipt_path)},
        "fold_metrics": {"path": str(metrics_path), "sha256": sha256(metrics_path)},
        "candidate_unit_metrics": {"path": str(unit_path), "sha256": sha256(unit_path)},
        "diagnostic_replay_pair_csv": {"path": str(paired_path), "sha256": sha256(paired_path)},
        "unit_metrics_builder": {"path": str(UNIT_BUILDER), "sha256": sha256(UNIT_BUILDER)},
        "reconciliation_script": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
    }
    ledger = {
        "schema": "brphm-f5-precision-reconciliation-v2",
        "observed_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "finding": "F5",
        "status": "AGGREGATE_GATE_VERIFIED_FROZEN_UNIT_PAIRING_INVALID",
        "original": {
            "location": "work/paper/en/main.tex:38,108,112",
            "problem": "Eight-decimal paper values do not audit a 1e-12 gate.",
            "superseded_ledger_sha256": {
                "json": sha256(old_json) if old_json.is_file() else None,
                "markdown": sha256(old_md) if old_md.is_file() else None,
            },
        },
        "reference_binding": {
            "path": str(REFERENCE),
            "sha256": reference_sha,
            "summary_sha256_matches_receipt": summary["reference_sha256"] == reference_sha
            and receipt["frozen_reference"]["sha256"] == reference_sha,
            "all_six_fold_metrics_match_frozen_summary": True,
        },
        "candidate_unit_reaggregation": {
            "all_six_folds_match": True,
            "relative_tolerance": REAGGREGATION_REL_TOLERANCE,
            "absolute_tolerance": REAGGREGATION_ABS_TOLERANCE,
            "aggregation": "window-weighted unit RMSE/MAE reconstruct candidate fold RMSE/MAE",
        },
        "unit_pairing": {
            "frozen_reference_pairing": "NOT_AVAILABLE",
            "replay_csv_role": "DIAGNOSTIC_REPLAY_ONLY",
            "replay_csv_definition": "The reference_* columns are captured from a newly fitted current control in build_f5_unit_metrics_20261002.py; they are not unit errors from the frozen reference prediction artifact.",
            "replay_generator_sha256": sha256(UNIT_BUILDER),
            "replay_reference_fold_mismatches": replay_mismatches,
            "paired_csv_valid_for_frozen_reference_inference": False,
        },
        "aggregation": summary["aggregation"],
        "gate": {
            "tolerance": TOLERANCE,
            "fold_count": len(checks),
            "all_primary_metrics_nonregressive": all_nonregressive,
            "at_least_one_strict_gain": strict_gain,
            "promotion_eligible": all_nonregressive and strict_gain,
            "rule": "all six frozen-reference folds pass RMSE and MAE at tolerance 1e-12 and at least one strict gain",
        },
        "fold_checks": checks,
        "unit_rows": len(rows),
        "artifacts": artifacts,
        "cross_validation": {
            "frozen_reference_hash_binding": "PASS",
            "frozen_reference_fold_values": "PASS: all six values match the hash-bound reference summary",
            "candidate_unit_to_fold_reaggregation": "PASS for all six folds",
            "delta_and_gate_recomputation": "PASS from unrounded frozen-reference and candidate fold values",
            "replayed_control_pair_identity": "FAIL for frozen-reference inference; explicitly marked diagnostic-only",
        },
        "confidence": {
            "aggregate_gate_and_candidate_unit_metrics": "HIGH",
            "frozen_reference_unit_pairing": "INVALID: exact reference predictions or unit metrics were not retained in searched artifacts",
        },
        "remaining_risk": "The existing paired CSV cannot support frozen-reference paired uncertainty. F6 reports it only as a replay sensitivity and separately estimates candidate unit-cluster uncertainty against the fixed hash-bound fold benchmark.",
        "required_modification": "Publish the unrounded fold JSON and candidate unit CSV; do not present the replay control CSV as frozen-reference unit pairs.",
    }

    json_path = INPUT / "f5_evidence_ledger_reconciled.json"
    md_path = INPUT / "f5_evidence_ledger_reconciled.md"
    json_path.write_text(json.dumps(ledger, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    table = "| Component | Orbit | Units | Windows | Frozen RMSE | Candidate RMSE | Delta RMSE | Frozen MAE | Candidate MAE | Delta MAE | Gate |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n"
    for row in checks:
        table += (
            f"| {row['component'].upper()} | {row['test_orbit']} | {row['n_units']} | {row['n_windows']} "
            f"| {row['reference_rmse']:.17g} | {row['candidate_rmse']:.17g} | {row['delta_rmse']:.17g} "
            f"| {row['reference_mae']:.17g} | {row['candidate_mae']:.17g} | {row['delta_mae']:.17g} "
            f"| RMSE {row['rmse_pass']}, MAE {row['mae_pass']} |\n"
        )
    md = f"""# F5 Reconciled Evidence Ledger

**Audit date:** 2026-10-02 UTC  
**Status:** `{ledger['status']}`

## Finding

The old F5 ledger incorrectly treated the unit-level `reference_*` columns as errors from the frozen reference. The builder actually captured a newly fitted control model, while the fold gate used the hash-bound frozen-reference summary. The old paired CSV is retained as a diagnostic replay only. The aggregate gate and candidate unit metrics have now been independently reconciled.

## Location and original text

- **Manuscript:** `work/paper/en/main.tex:38,108,112`
- **Issue:** the table shows eight decimal places for a gate tolerance of `1e-12`.

## Reference, aggregation, and gate

- Frozen summary: `{REFERENCE}`
- SHA-256: `{reference_sha}`
- Gate: `delta = candidate - frozen reference`; each RMSE and MAE delta must be `<= {TOLERANCE:.0e}` on all six folds, with at least one strict gain below `-{TOLERANCE:.0e}`.
- Unit aggregation reconstructs the candidate fold metrics using each unit's window count.

{table}
Gate result: `all_nonregressive={all_nonregressive}`, `strict_gain={strict_gain}`, `promotion_eligible={all_nonregressive and strict_gain}`.

## Pairing provenance correction

`formal_unit_paired_metrics.csv` was built by refitting the control through the current `fit_predict_fixed` implementation. It is not the historical frozen-reference prediction. Its window-weighted fold RMSE/MAE differ from the frozen summary in `{replay_mismatches}` of six folds, so it cannot be used for frozen-reference paired bootstrap or Wilcoxon inference. F6 separates replay sensitivity from uncertainty against the fixed fold benchmark.

## Artifacts and verification

The machine-readable ledger contains full-precision fold values and SHA-256 hashes for the reference summary, candidate receipt, fold JSON, both unit CSVs, and builders. Verification command:

```text
python work/paper/repro/build_f5_precision_ledger.py
```

- Frozen-reference summary hash and fold values: **PASS**.
- Candidate unit-to-fold reconstruction: **PASS**, six of six folds.
- Delta and gate recomputation at full precision: **PASS**.
- Frozen-reference unit pairing: **INVALID in the old paired CSV; marked diagnostic-only**.

## Confidence and remaining risk

Confidence is high for the aggregate gate and candidate unit metrics. Exact frozen-reference unit predictions are not present in the searched receipt bundle, so paired inference against those historical predictions is not claimed. The paper must cite the reconciled JSON and candidate unit CSV and must not label the replay CSV as frozen-reference pairs.
"""
    md_path.write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": ledger["status"],
                "folds": len(checks),
                "units": len(rows),
                "replay_reference_fold_mismatches": replay_mismatches,
                "gate": ledger["gate"]["promotion_eligible"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
