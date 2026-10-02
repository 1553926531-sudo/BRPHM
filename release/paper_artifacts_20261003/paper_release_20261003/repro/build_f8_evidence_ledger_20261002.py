from __future__ import annotations

"""Build hash-linked F8 source-gate and reused-fold diagnostic tables."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "work/paper/review/f8_source_gate_20261002"
RECEIPTS = ROOT / "work/paper/repro/receipts"
SUMMARY = ROOT / "work/paper/evidence/evidence_summary.json"
REPORT = ROOT.parents[1] / "2026-10-01/ni-d/outputs/IEEE_Review_Report_English.md"
TOLERANCE = 1e-12
METHOD_FILES = (
    "temporal_tcn_unit_first_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_l1_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_l1_worst_direction_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_rwa_leo550_floor_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001_remote.json",
    "temporal_gru_source_gate_20261001_remote.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def artifact(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size}


def main() -> int:
    REVIEW.mkdir(parents=True, exist_ok=True)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary_methods = {item["receipt"]: item for item in summary["methods"]}
    method_rows: list[dict] = []
    fold_rows: list[dict] = []
    source_rows: list[dict] = []
    source_receipts = {}

    for filename in METHOD_FILES:
        path = RECEIPTS / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        source_receipts[filename] = receipt
        method_summary = summary_methods.get(filename)
        if method_summary is None:
            raise ValueError(f"evidence summary does not include {filename}")
        eligible = bool(receipt.get("formal_eligible"))
        formal_results = (receipt.get("formal") or {}).get("results", [])
        formal_gate = (receipt.get("formal") or {}).get("promotion_gate")
        if eligible and (len(formal_results) != 6 or not formal_gate):
            raise ValueError(f"eligible candidate has incomplete formal matrix: {filename}")
        if not eligible and formal_results:
            raise ValueError(f"ineligible candidate unexpectedly has formal results: {filename}")

        computed_failures = 0
        for result in formal_results:
            metric = result["metrics"]
            reference = result["reference_metrics"]
            delta_rmse = float(metric["rmse"]) - float(reference["rmse"])
            delta_mae = float(metric["mae"]) - float(reference["mae"])
            failed = [
                name for name, delta in (("rmse", delta_rmse), ("mae", delta_mae))
                if delta > TOLERANCE
            ]
            computed_failures += int(bool(failed))
            fold_rows.append(
                {
                    "candidate": receipt["method_id"],
                    "receipt": filename,
                    "formal_eligible": True,
                    "component": result["component"],
                    "test_orbit": result["test_orbit"],
                    "n_units": metric["n_units"],
                    "n_windows": metric["n_windows"],
                    "reference_rmse": format(float(reference["rmse"]), ".17g"),
                    "candidate_rmse": format(float(metric["rmse"]), ".17g"),
                    "delta_rmse": format(delta_rmse, ".17g"),
                    "rmse_pass_at_1e-12": delta_rmse <= TOLERANCE,
                    "reference_mae": format(float(reference["mae"]), ".17g"),
                    "candidate_mae": format(float(metric["mae"]), ".17g"),
                    "delta_mae": format(delta_mae, ".17g"),
                    "mae_pass_at_1e-12": delta_mae <= TOLERANCE,
                    "failed_metrics": ";".join(failed),
                }
            )

        expected_failures = method_summary.get("promotion_failure_count") if eligible else None
        if eligible and computed_failures != int(expected_failures):
            raise ValueError(f"failure-count mismatch for {filename}: {computed_failures} != {expected_failures}")
        method_rows.append(
            {
                "candidate": receipt["method_id"],
                "receipt": filename,
                "source_gate_bat": receipt["components"]["bat"]["gate"]["passes"],
                "source_gate_rwa": receipt["components"]["rwa"]["gate"]["passes"],
                "formal_eligible": eligible,
                "formal_folds_observed": len(formal_results),
                "formal_fold_denominator": 6 if eligible else 0,
                "diagnostic_failure_folds": computed_failures if eligible else None,
                "diagnostic_failure_denominator": 6 if eligible else None,
                "summary_failure_count_match": eligible and computed_failures == int(expected_failures),
                "interpretation": "reused outer folds; development/diagnostic only" if eligible else "source gate failed; no formal evaluation",
            }
        )

        for component in ("bat", "rwa"):
            component_record = receipt["components"][component]
            controls = component_record.get("controls", {})
            records = component_record.get("records", [])
            by_direction = {row["direction"]: row for row in records if "direction" in row}
            by_pair = {row["orbit_pair"]: row for row in records if "orbit_pair" in row}
            for direction, row in sorted(by_direction.items()):
                metric = row["metrics"]
                control = controls[direction]
                delta_rmse = float(metric["rmse"]) - float(control["rmse"])
                delta_mae = float(metric["mae"]) - float(control["mae"])
                source_rows.append(
                    {
                        "candidate": receipt["method_id"], "receipt": filename,
                        "component": component, "comparison": "directed_transfer",
                        "direction_or_pair": direction,
                        "n_units_left_or_target": metric["n_units"],
                        "n_windows_left_or_target": metric["n_windows"],
                        "n_units_right": "", "n_windows_right": "",
                        "candidate_rmse_or_ks": format(float(metric["rmse"]), ".17g"),
                        "control_rmse_or_ks": format(float(control["rmse"]), ".17g"),
                        "delta_rmse_or_ks": format(delta_rmse, ".17g"),
                        "candidate_mae": format(float(metric["mae"]), ".17g"),
                        "control_mae": format(float(control["mae"]), ".17g"),
                        "delta_mae": format(delta_mae, ".17g"),
                        "rmse_or_ks_pass_at_1e-12": delta_rmse <= TOLERANCE,
                        "mae_pass_at_1e-12": delta_mae <= TOLERANCE,
                        "p_value": "",
                    }
                )
            for pair, row in sorted(by_pair.items()):
                left, right = pair.split("<->")
                left_direction = by_direction[f"{left}->{right}"]["metrics"]
                right_direction = by_direction[f"{right}->{left}"]["metrics"]
                candidate_ks = float(row["residual_ks"])
                control_ks = float(controls[pair]["residual_ks"])
                delta_ks = candidate_ks - control_ks
                source_rows.append(
                    {
                        "candidate": receipt["method_id"], "receipt": filename,
                        "component": component, "comparison": "residual_ks",
                        "direction_or_pair": pair,
                        "n_units_left_or_target": left_direction["n_units"],
                        "n_windows_left_or_target": left_direction["n_windows"],
                        "n_units_right": right_direction["n_units"],
                        "n_windows_right": right_direction["n_windows"],
                        "candidate_rmse_or_ks": format(candidate_ks, ".17g"),
                        "control_rmse_or_ks": format(control_ks, ".17g"),
                        "delta_rmse_or_ks": format(delta_ks, ".17g"),
                        "candidate_mae": "", "control_mae": "", "delta_mae": "",
                        "rmse_or_ks_pass_at_1e-12": delta_ks <= TOLERANCE,
                        "mae_pass_at_1e-12": "not_applicable",
                        "p_value": "not stored in original receipt; residual-level replay pending",
                    }
                )

    fold_fields = [
        "candidate", "receipt", "formal_eligible", "component", "test_orbit", "n_units", "n_windows",
        "reference_rmse", "candidate_rmse", "delta_rmse", "rmse_pass_at_1e-12",
        "reference_mae", "candidate_mae", "delta_mae", "mae_pass_at_1e-12", "failed_metrics",
    ]
    source_fields = [
        "candidate", "receipt", "component", "comparison", "direction_or_pair",
        "n_units_left_or_target", "n_windows_left_or_target", "n_units_right", "n_windows_right",
        "candidate_rmse_or_ks", "control_rmse_or_ks", "delta_rmse_or_ks",
        "candidate_mae", "control_mae", "delta_mae", "rmse_or_ks_pass_at_1e-12",
        "mae_pass_at_1e-12", "p_value",
    ]
    write_csv(REVIEW / "candidate_fold_matrix.csv", fold_rows, fold_fields)
    write_csv(REVIEW / "source_gate_matrix.csv", source_rows, source_fields)

    inputs = [SUMMARY, REPORT, ROOT / "work/paper/generate_figures.py"]
    inputs.extend(RECEIPTS / name for name in METHOD_FILES)
    input_hashes = {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): sha256(path) for path in inputs}
    final_receipt = source_receipts[METHOD_FILES[5]]
    ledger = {
        "schema": "brphm-f8-source-gate-diagnostic-ledger-v1",
        "finding": "F8",
        "audit_date": datetime.now(timezone.utc).isoformat(),
        "status": "RECEIPT_MATRIX_RECONCILED_CLUSTER_INFERENCE_PENDING",
        "location": {
            "review_report": str(REPORT),
            "manuscript_source": "work/paper/en/main.tex:72-91 and Fig. 2 source work/paper/generate_figures.py",
        },
        "original_text": {
            "table": "A dash means formal was not eligible.",
            "figure": "The reused-fold candidate progression is shown under a fixed six-fold promotion gate; the GRU value was sourced from promotion_failure_count=0.",
        },
        "problem": "The six successive candidate receipts contain reused outer outcomes and are development/diagnostic evidence. GRU failed both source gates and has no formal folds; encoding its absent failure count as 0 falsely equated ineligibility with zero failures. The source receipts store KS statistics but not residual vectors, KS p-values, or cluster uncertainty.",
        "correction": "The figure now marks the old folds development/diagnostic only and renders GRU as ineligible without a numeric bar. The machine-readable matrices include all six eligible candidates x six folds (36 rows) and all candidate source directions/pairs. Unit-cluster resampling is pending the isolated residual replay.",
        "thresholds": {
            "formal_fold_gate": "candidate metric - frozen reference metric <= 1e-12 for RMSE and MAE on each of six folds",
            "source_gate": "candidate RMSE/MAE/KS <= frozen-control value + 1e-12 for every required comparison; at least one strict error gain below -1e-12",
            "multiplicity": "The deterministic gates are conjunctions, not p-value tests. Multiplicity-adjusted statistical inference is not present in the original receipts; a six-comparison cluster-aware analysis is being computed separately and will be labeled exploratory because routes were chosen on the same source-validation data.",
        },
        "counts": {
            "eligible_candidates": 6,
            "fold_matrix_rows": len(fold_rows),
            "folds_per_eligible_candidate": 6,
            "formal_ineligible_candidates": 1,
            "source_gate_rows": len(source_rows),
            "historical_failure_counts": {row["candidate"]: row["diagnostic_failure_folds"] for row in method_rows if row["formal_eligible"]},
            "gru": {"source_gate_bat": False, "source_gate_rwa": False, "formal_eligible": False, "formal_folds": 0, "diagnostic_failure_count": None},
        },
        "methods": method_rows,
        "original_source_gate_receipt": {
            "method_id": final_receipt["method_id"],
            "sha256": sha256(RECEIPTS / METHOD_FILES[5]),
            "source_protocol": final_receipt["source_protocol"],
            "selected_routes": {component: final_receipt["components"][component]["selected_route"] for component in ("bat", "rwa")},
            "input_tensor_hashes": {component: final_receipt["components"][component]["input_tensor_sha256"] for component in ("bat", "rwa")},
        },
        "artifacts": input_hashes,
        "commands": [
            "python work/paper/repro/build_f8_evidence_ledger_20261002.py",
            "python work/paper/repro/export_f8_source_residuals_20261002.py --root /mnt/data/BRPHM/rul-space --data-root /mnt/data/BRPHM/rul-space --receipt <hash-bound frozen receipt> --output <isolated f8_source_residuals.json>",
        ],
        "cross_validation": [
            "Per-fold failure counts are recomputed from full-precision receipt metrics and the 1e-12 tolerance, then compared with evidence_summary.json.",
            "Each direction's candidate metrics and each KS statistic are paired with the frozen-control values in the same receipt.",
            "GRU eligibility is checked in both the receipt and evidence_summary; no missing formal result is coerced to zero.",
            "F1 closeout independently classifies all old outer outcomes as development/diagnostic only.",
        ],
        "confidence": "high for receipt completeness, fold denominator, failure counts, source direction metrics, thresholds, and GRU ineligibility; medium for source residual inferential uncertainty until replay cross-check completes",
        "remaining_risk": "The historical candidate sequence used the same outer folds during development. These matrices do not restore confirmatory status. Window-level KS p-values would violate independence assumptions because windows overlap and cluster within units; only unit-cluster results may support uncertainty, and source-route selection makes them exploratory.",
        "status_detail": "The historical results may be described as development/diagnostic evidence only. The separate F1 LEO600 test is not part of this F8 matrix and its result remains under its own preregistration constraints.",
    }
    json_path = REVIEW / "f8_evidence_ledger.json"
    json_path.write_text(json.dumps(ledger, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    md = f"""# F8 Evidence Ledger: Source Gate, GRU Eligibility, and Ablation Matrix

**Audit date:** {ledger['audit_date']}  
**Status:** `{ledger['status']}`  
**Finding fields:** location, original text, problem, correction, evidence, source, date, hash, command, result, cross-check, confidence, remaining risk, status.

## Finding Record

- **Location:** IEEE review report F8; `work/paper/en/main.tex:72-91`; chart generator `work/paper/generate_figures.py`.
- **Original:** The paper reports a six-fold candidate progression and marks GRU with `--`; the generator interpreted the GRU receipt's absent formal failure count as numeric `0`.
- **Problem:** all six historical candidates reused the same outer folds while changing the route/model based on successive results. Those outcomes are development/diagnostic evidence, not six independent confirmatory evaluations. GRU fails both source gates and has no formal denominator. Its zero-valued metadata must never appear as zero failures. Original source-gate receipts include six directed metrics and three KS statistics but omit residual arrays and p-values.
- **Correction made:** the active figure generator now labels the six-fold sequence as development/diagnostic, prints a `k/6` denominator, and labels GRU `ineligible` with no numeric count. PDF figures now embed CID TrueType fonts. Paper body text remains pending the complete evidence pass.

## Recomputed Denominators and Failure Matrix

`candidate_fold_matrix.csv` contains {len(fold_rows)} rows: six eligible candidates times six component-orbit folds. Its columns include unit/window counts, full-precision reference and candidate RMSE/MAE, deltas, per-metric gate booleans at `1e-12`, and failed metrics. `source_gate_matrix.csv` contains {len(source_rows)} rows across all seven receipts, both components, six directed transfers and three residual pairs.

| Candidate sequence | Diagnostic folds with a regression | Denominator | Formal status |
|---|---:|---:|---|
"""
    for row in method_rows:
        fail = "N/A" if row["diagnostic_failure_folds"] is None else str(row["diagnostic_failure_folds"])
        denom = "0 (ineligible)" if not row["formal_eligible"] else "6"
        md += f"| `{row['candidate']}` | {fail} | {denom} | {row['interpretation']} |\n"
    md += f"""
## Source Gate Metrics

All six directions are keyed as source orbit → validation orbit; window and unit counts are the validation sample sizes. The three KS pairs compare residuals from the reciprocal directed transfers. The receipt gate tolerance is `1e-12`; it rejects any RMSE, MAE, or KS regression over tolerance and requires at least one strict RMSE/MAE improvement. The CSV records each full-precision value and candidate-minus-control delta.

The original receipt contains KS statistics only. Its current p-value fields are explicitly marked as absent; the separate source-only replay is exporting per-unit residual vectors so candidate-vs-control KS-distance uncertainty can be computed with unit clusters. IID-window KS p-values will be shown only as non-inferential reference values. Any cluster test remains exploratory because the route was selected on the same source-validation information.

## Controlled Ablations

The retained sequence changes one declared factor at each adjacent step: residual centering; SmoothL1-to-L1 loss; route tie-break; RWA-specific alpha floor; uniform alpha floor. `candidate_fold_matrix.csv` provides the full six-fold metric matrix for each historical variant. Because the same outer folds informed the sequence, these are diagnostic ablations. Seed-level and unit-cluster uncertainty is available only for the final receipt in the current evidence tree; equivalent unit prediction exports for the earlier variants are not present. Do not claim independent ablation confirmation or statistical superiority from the progression chart.

## Evidence and Reproduction

- **Primary evidence:** the seven hash-bound source-gate/formal receipts and `work/paper/evidence/evidence_summary.json`.
- **Independent source:** F1 closeout ledger, which classifies all `5,4,3,1,3,0` outer-fold outcomes as development/diagnostic.
- **Commands:** `python work/paper/repro/build_f8_evidence_ledger_20261002.py`; per-unit replay command is recorded in `f8_evidence_ledger.json`.
- **Verification:** the builder asserts six complete folds for every eligible receipt, recomputes each failure count, matches all counts to the summary, and asserts that the ineligible GRU has no formal rows.
- **Source hashes:** see the `artifacts` object in `f8_evidence_ledger.json`; receipt full hashes are included there.
- **Result:** the historical fold/source metrics and GRU eligibility reconcile. The generated figure no longer depicts ineligibility as zero. Cluster-aware residual uncertainty is pending successful replay and reconciliation against the saved receipts.
- **Cross-check:** receipt metrics versus recomputation; per-direction candidate/control values from each same receipt; GRU source gate versus null formal; F1 disposition versus the supplied review report.
- **Confidence:** high for denominators, gate computations, and GRU status; medium for inferential uncertainty pending residual replay.
- **Remaining risk:** temporal overlap invalidates IID-window inference; source-gate route selection induces selection bias. Historical six-fold outcomes cannot be promoted back to final-test evidence.
- **Status:** `RECEIPT_MATRIX_RECONCILED_CLUSTER_INFERENCE_PENDING`.
"""
    md_path = REVIEW / "f8_evidence_ledger.md"
    md_path.write_text(md, encoding="utf-8")

    outputs = [json_path, md_path, REVIEW / "candidate_fold_matrix.csv", REVIEW / "source_gate_matrix.csv"]
    manifest = {"schema": "brphm-f8-artifact-checksums-v1", "generated_utc": ledger["audit_date"], "artifacts": [artifact(path) for path in outputs]}
    (REVIEW / "artifact_manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "review_dir": str(REVIEW), "fold_rows": len(fold_rows), "source_rows": len(source_rows)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
