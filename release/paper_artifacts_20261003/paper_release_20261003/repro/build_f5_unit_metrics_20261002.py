from __future__ import annotations

"""Replay a frozen development candidate and emit unit-level audit metrics.

This is deliberately separate from the LEO600 clean-final chain.  The route
is read from a pre-existing source receipt and is never selected here.
"""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def unit_metrics(prediction, truth, rmax, rows):
    pred = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, 1.0) * float(rmax)
    actual = np.asarray(truth, dtype=np.float64) * float(rmax)
    err = pred - actual
    groups: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        groups.setdefault(str(row["unit_id"]), []).append(i)
    records = []
    for unit_id in sorted(groups):
        idx = np.asarray(groups[unit_id], dtype=int)
        values = err[idx]
        records.append(
            {
                "unit_id": unit_id,
                "n_windows": int(idx.size),
                "rmse": float(np.sqrt(np.mean(values**2))),
                "mae": float(np.mean(np.abs(values))),
                "bias": float(np.mean(values)),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

    source_dir = root / "work/rul_next_electrochemical"
    centered_path = source_dir / "temporal_tcn_unit_first_residual_centered_source_gate_20261001.py"
    global_path = source_dir / "temporal_tcn_global_inner_route_source_gate.py"
    fine_path = source_dir / "temporal_tcn_fine_global_inner_route_source_gate.py"
    segmented_path = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/run_segmented_hgb_mlp_source_gate_20260929.py"
    loader_path = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/run_leave_one_orbit_out_generalization_20260825.py"

    centered = load("f5_centered", centered_path)
    implementation = load("f5_global", global_path)
    fine = load("f5_fine", fine_path)
    segmented = load("f5_segmented", segmented_path)
    loader = load("f5_loader", loader_path)
    implementation.ALPHA_CATALOG = fine.FINE_ALPHA_CATALOG
    implementation.ROUTES = implementation.route_catalog()
    base = implementation.base

    frozen_receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    selected_routes = {
        component: frozen_receipt["components"][component]["selected_route"]
        for component in base.COMPONENTS
    }

    # Install exactly the promoted model/correction path; route values remain frozen.
    base.CONFIG_CURRENT = base.CONFIG
    base.fit_source_predictions = centered.fit_source_predictions_centered
    original_formal = implementation._fit_relative_formal
    implementation._fit_relative_formal = centered.fit_relative_formal_centered
    captured_units: list[list[dict]] = []
    captured_controls: dict[tuple[str, str], list[dict]] = {}
    original_metrics = base.metrics
    original_fit_predict = segmented.fit_predict_fixed

    def capture_metrics(prediction, truth, rmax, rows):
        observed = original_metrics(prediction, truth, rmax, rows)
        captured_units.append(unit_metrics(prediction, truth, rmax, rows))
        return observed

    def capture_control(*args, **kwargs):
        result = original_fit_predict(*args, **kwargs)
        if kwargs.get("return_prediction", False) or (len(args) >= 7 and args[6] is True):
            data_component, component, valid = args[0], str(args[1]), np.asarray(args[3], dtype=bool)
            valid_rows = [data_component["rows"][i] for i in np.flatnonzero(valid)]
            target_orbits = {base.orbit_of(row) for row in valid_rows}
            if len(target_orbits) != 1:
                raise ValueError("control capture requires one target orbit")
            target_orbit = next(iter(target_orbits))
            prediction = np.asarray(result[3], dtype=np.float32)
            truth = data_component["y"][valid] / float(data_component["rmax"])
            captured_controls[(component, target_orbit)] = unit_metrics(
                prediction, truth, float(data_component["rmax"]), valid_rows
            )
        return result

    base.metrics = capture_metrics
    segmented.fit_predict_fixed = capture_control
    try:
        data = base.load_data(loader, args.root)
        for component in base.COMPONENTS:
            candidate = implementation.reference_control_candidate(segmented, component)
            implementation.formal_results(
                data[component], component, segmented, candidate, selected_routes[component], args.device
            )
    finally:
        base.metrics = original_metrics
        segmented.fit_predict_fixed = original_fit_predict
        implementation._fit_relative_formal = original_formal

    all_rows = []
    # formal_results emits exactly three metric calls per component in ORBITS order.
    for component_index, component in enumerate(base.COMPONENTS):
        for orbit_index, orbit in enumerate(base.ORBITS):
            units = captured_units[component_index * len(base.ORBITS) + orbit_index]
            for row in units:
                all_rows.append({"component": component, "test_orbit": orbit, **row})

    candidate_by_key = {(r["component"], r["test_orbit"], r["unit_id"]): r for r in all_rows}
    paired_rows = []
    for key, candidate_row in sorted(candidate_by_key.items()):
        component, orbit, unit_id = key
        reference_row = next(
            row for row in captured_controls[(component, orbit)] if row["unit_id"] == unit_id
        )
        paired_rows.append(
            {
                "component": component,
                "test_orbit": orbit,
                "unit_id": unit_id,
                "n_windows": int(candidate_row["n_windows"]),
                "candidate_rmse": float(candidate_row["rmse"]),
                "reference_rmse": float(reference_row["rmse"]),
                "delta_rmse": float(candidate_row["rmse"] - reference_row["rmse"]),
                "candidate_mae": float(candidate_row["mae"]),
                "reference_mae": float(reference_row["mae"]),
                "delta_mae": float(candidate_row["mae"] - reference_row["mae"]),
                "candidate_bias": float(candidate_row["bias"]),
                "reference_bias": float(reference_row["bias"]),
            }
        )

    # The formal results are in local scope per component; reconstruct from the
    # unit table and the frozen receipt so this output remains compact and exact.
    unit_csv = output / "formal_unit_metrics.csv"
    columns = ["component", "test_orbit", "unit_id", "n_windows", "rmse", "mae", "bias"]
    with unit_csv.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(columns) + "\n")
        for row in all_rows:
            f.write(",".join(json.dumps(row[c], ensure_ascii=True) for c in columns) + "\n")

    paired_csv = output / "formal_unit_paired_metrics.csv"
    paired_columns = [
        "component", "test_orbit", "unit_id", "n_windows", "candidate_rmse", "reference_rmse", "delta_rmse",
        "candidate_mae", "reference_mae", "delta_mae", "candidate_bias", "reference_bias",
    ]
    with paired_csv.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(paired_columns) + "\n")
        for row in paired_rows:
            f.write(",".join(json.dumps(row[c], ensure_ascii=True) for c in paired_columns) + "\n")

    aggregate = []
    for item in frozen_receipt["formal"]["results"]:
        ref = next(x for x in reference["results"] if x["component"] == item["component"] and x["test_orbit"] == item["test_orbit"])
        aggregate.append(
            {
                "component": item["component"],
                "test_orbit": item["test_orbit"],
                "candidate_rmse": float(item["metrics"]["rmse"]),
                "candidate_mae": float(item["metrics"]["mae"]),
                "reference_rmse": float(ref["metrics"]["rmse"]),
                "reference_mae": float(ref["metrics"]["mae"]),
                "delta_rmse": float(item["metrics"]["rmse"] - ref["metrics"]["rmse"]),
                "delta_mae": float(item["metrics"]["mae"] - ref["metrics"]["mae"]),
                "n_windows": int(item["metrics"]["n_windows"]),
                "n_units": int(item["metrics"]["n_units"]),
                "rmse_pass": bool(item["metrics"]["rmse"] - ref["metrics"]["rmse"] <= base.TOLERANCE),
                "mae_pass": bool(item["metrics"]["mae"] - ref["metrics"]["mae"] <= base.TOLERANCE),
            }
        )
    summary = {
        "schema": "brphm-f5-unit-metrics-v1",
        "candidate_receipt_sha256": sha256(args.receipt),
        "reference_sha256": sha256(args.reference),
        "source_code_sha256": {str(p): sha256(p) for p in (centered_path, global_path, fine_path, segmented_path, loader_path)},
        "route_frozen_from_receipt": True,
        "outer_used_for_selection": False,
        "tolerance": base.TOLERANCE,
        "aggregation": "window-level RMSE/MAE over all outer windows; unit table additionally reports per-unit RMSE/MAE and n_windows",
        "fold_metrics": aggregate,
        "unit_csv_sha256": sha256(unit_csv),
        "paired_unit_csv_sha256": sha256(paired_csv),
        "unit_row_count": len(all_rows),
        "paired_unit_row_count": len(paired_rows),
        "status": "COMPLETE_DEVELOPMENT_DIAGNOSTIC_EXPORT",
    }
    (output / "formal_metrics_unrounded.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "unit_rows": len(all_rows), "unit_csv": str(unit_csv)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
