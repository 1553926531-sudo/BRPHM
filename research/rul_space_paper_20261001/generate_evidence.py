from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT_DIR = ROOT / "work" / "rul_next_electrochemical"
OUT = Path(__file__).resolve().parent / "evidence"


def load(name: str) -> dict:
    return json.loads((RECEIPT_DIR / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


FINAL = "temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001_remote.json"
KEY_RECEIPTS = [
    "temporal_tcn_unit_first_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_l1_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_l1_worst_direction_source_gate_20261001_remote.json",
    "temporal_tcn_unit_first_residual_centered_rwa_leo550_floor_source_gate_20261001_remote.json",
    FINAL,
    "temporal_gru_source_gate_20261001_remote.json",
]


def method_row(name: str, payload: dict) -> dict:
    formal = payload.get("formal") or {}
    gate = formal.get("promotion_gate") or {}
    failures = gate.get("failures") or []
    return {
        "receipt": name,
        "method_id": payload.get("method_id"),
        "schema": payload.get("schema"),
        "execution_complete": payload.get("execution_complete"),
        "formal_eligible": payload.get("formal_eligible"),
        "bat_source_gate": bool(payload.get("components", {}).get("bat", {}).get("gate", {}).get("passes")),
        "rwa_source_gate": bool(payload.get("components", {}).get("rwa", {}).get("gate", {}).get("passes")),
        "promotion_eligible": gate.get("promotion_eligible"),
        "promotion_failure_count": len(failures),
        "next_action": payload.get("next_action"),
    }


def formal_rows(payload: dict) -> list[dict]:
    rows = []
    formal = payload.get("formal") or {}
    for item in formal.get("results") or []:
        delta = item.get("delta_vs_reference") or {}
        cfg = item.get("configuration") or {}
        rows.append(
            {
                "method_id": payload.get("method_id"),
                "component": item.get("component"),
                "test_orbit": item.get("test_orbit"),
                "rmse": item.get("metrics", {}).get("rmse"),
                "mae": item.get("metrics", {}).get("mae"),
                "rmse_delta": delta.get("rmse"),
                "mae_delta": delta.get("mae"),
                "route_id": cfg.get("route_id"),
                "outer_test_used_for_selection": item.get("outer_test_used_for_selection"),
                "outer_evaluated_once": item.get("outer_evaluated_once"),
            }
        )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    loaded = {name: load(name) for name in KEY_RECEIPTS if (RECEIPT_DIR / name).is_file()}
    final = loaded[FINAL]
    reference = json.loads((ROOT / "reference_summary_remote.json").read_text(encoding="utf-8"))
    methods = [method_row(name, payload) for name, payload in loaded.items()]
    folds = formal_rows(final)
    provenance = {
        key: final.get(key)
        for key in (
            "canonical_data_modified",
            "competition_line_modified",
            "sealed_holdout_read",
            "a1_b1_source_heldout_read",
            "holdout_used_for_training_or_selection",
            "outer_test_used_for_selection",
            "outer_evaluated_once",
            "population_generalization_verified",
        )
    }
    evidence = {
        "generated_from": {name: sha256(RECEIPT_DIR / name) for name in loaded},
        "frozen_reference_sha256": final.get("frozen_reference", {}).get("sha256"),
        "reference_results": reference.get("results", []),
        "methods": methods,
        "final_formal_folds": folds,
        "final_provenance": provenance,
        "final_source_protocol": final.get("source_protocol"),
        "final_route_by_component": {
            component: {
                "route_id": next(
                    (row["route_id"] for row in folds if row["component"] == component), None
                ),
                "selected_candidate_id": final.get("components", {}).get(component, {}).get("selected_candidate_id"),
            }
            for component in ("bat", "rwa")
        },
    }
    (OUT / "evidence_summary.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (OUT / "formal_folds.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(folds[0]))
        writer.writeheader()
        writer.writerows(folds)
    with (OUT / "method_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(methods[0]))
        writer.writeheader()
        writer.writerows(methods)
    print(json.dumps({"methods": len(methods), "formal_folds": len(folds), "promotion": final["formal"]["promotion_gate"]["promotion_eligible"]}))


if __name__ == "__main__":
    main()
