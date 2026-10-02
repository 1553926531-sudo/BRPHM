from __future__ import annotations

"""Capture per-seed metrics for the frozen development candidate."""

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
    error = pred - actual
    groups: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        groups.setdefault(str(row["unit_id"]), []).append(i)
    result = []
    for unit_id in sorted(groups):
        idx = np.asarray(groups[unit_id], dtype=int)
        values = error[idx]
        result.append({
            "unit_id": unit_id,
            "n_windows": int(idx.size),
            "rmse": float(np.sqrt(np.mean(values**2))),
            "mae": float(np.mean(np.abs(values))),
            "bias": float(np.mean(values)),
        })
    return result


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
    source = root / "work/rul_next_electrochemical"
    centered_path = source / "temporal_tcn_unit_first_residual_centered_source_gate_20261001.py"
    global_path = source / "temporal_tcn_global_inner_route_source_gate.py"
    fine_path = source / "temporal_tcn_fine_global_inner_route_source_gate.py"
    segmented_path = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/run_segmented_hgb_mlp_source_gate_20260929.py"
    loader_path = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/run_leave_one_orbit_out_generalization_20260825.py"
    centered = load("f6_centered", centered_path)
    implementation = load("f6_global", global_path)
    fine = load("f6_fine", fine_path)
    segmented = load("f6_segmented", segmented_path)
    loader = load("f6_loader", loader_path)
    implementation.ALPHA_CATALOG = fine.FINE_ALPHA_CATALOG
    implementation.ROUTES = implementation.route_catalog()
    base = implementation.base
    relative = centered.r
    frozen_receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    selected_routes = {c: frozen_receipt["components"][c]["selected_route"] for c in base.COMPONENTS}

    captures: dict[str, object] = {}
    original_predict = relative.predict_models_relative

    def capture_predict(models, sequences, rows, center, scale, device_name):
        median = original_predict(models, sequences, rows, center, scale, device_name)
        per_seed = [original_predict([item], sequences, rows, center, scale, device_name) for item in models]
        orbit_set = {base.orbit_of(row) for row in rows}
        if len(orbit_set) == 1:
            captures["valid_per_seed"] = per_seed
        else:
            captures["train_per_seed"] = per_seed
        return median

    relative.predict_models_relative = capture_predict
    base.CONFIG_CURRENT = base.CONFIG
    original_formal = implementation._fit_relative_formal
    implementation._fit_relative_formal = centered.fit_relative_formal_centered
    seed_fold_rows = []
    seed_unit_rows = []
    try:
        data = base.load_data(loader, root)
        for component in base.COMPONENTS:
            candidate = implementation.reference_control_candidate(segmented, component)
            for target_orbit in base.ORBITS:
                outer = np.asarray([base.orbit_of(row) == target_orbit for row in data[component]["rows"]], dtype=bool)
                train = ~outer
                captures.clear()
                # The patched predictor sees train then valid calls inside the formal fit.
                candidate_median = centered.fit_relative_formal_centered(data[component], component, train, outer, args.device)
                # centered.fit_relative_formal_centered has completed both calls; the
                # wrapper stores the second call as valid and the first as train.
                train_per_seed = captures.get("train_per_seed")
                valid_per_seed = captures.get("valid_per_seed")
                if train_per_seed is None or valid_per_seed is None:
                    raise RuntimeError(f"seed capture incomplete for {component}/{target_orbit}: {captures.keys()}")
                control = np.asarray(
                    segmented.fit_predict_fixed(data[component], component, train, outer, candidate, args.device, return_prediction=True)[3],
                    dtype=np.float32,
                )
                train_rows = [data[component]["rows"][i] for i in np.flatnonzero(train)]
                outer_rows = [data[component]["rows"][i] for i in np.flatnonzero(outer)]
                source_y = data[component]["y"][train] / float(data[component]["rmax"])
                # Reconstruct the exact correction from the captured per-seed source predictions.
                train_median = np.median(np.stack(train_per_seed, axis=0), axis=0)
                correction = -float(centered.SHRINK) * float(np.median(train_median.astype(np.float64) - source_y.astype(np.float64)))
                truth = data[component]["y"][outer] / float(data[component]["rmax"])
                alpha = float(selected_routes[component]["alpha_by_target"][target_orbit])
                for seed_index, seed in enumerate(base.SEEDS):
                    seed_candidate = base.project(
                        np.asarray(valid_per_seed[seed_index], dtype=np.float32) + np.float32(correction),
                        outer_rows,
                        base.CONFIG[component]["postprocess"],
                    )
                    prediction = base.project(
                        alpha * seed_candidate + (1.0 - alpha) * control,
                        outer_rows,
                        base.CONFIG[component]["postprocess"],
                    )
                    values = unit_metrics(prediction, truth, float(data[component]["rmax"]), outer_rows)
                    physical_pred = np.clip(np.asarray(prediction, dtype=np.float64), 0.0, 1.0) * float(data[component]["rmax"])
                    physical_truth = np.asarray(truth, dtype=np.float64) * float(data[component]["rmax"])
                    err = physical_pred - physical_truth
                    seed_fold_rows.append({
                        "component": component,
                        "test_orbit": target_orbit,
                        "seed": int(seed),
                        "physical_unit": "cycles" if component == "bat" else "days",
                        "rmse": float(np.sqrt(np.mean(err**2))),
                        "mae": float(np.mean(np.abs(err))),
                        "bias": float(np.mean(err)),
                        "n_windows": int(len(err)),
                        "n_units": int(len(values)),
                    })
                    for row in values:
                        seed_unit_rows.append({"component": component, "test_orbit": target_orbit, "seed": int(seed), **row})
    finally:
        relative.predict_models_relative = original_predict
        implementation._fit_relative_formal = original_formal

    fold_csv = output / "seed_fold_metrics.csv"
    fold_cols = ["component", "test_orbit", "seed", "physical_unit", "rmse", "mae", "bias", "n_windows", "n_units"]
    with fold_csv.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(fold_cols) + "\n")
        for row in seed_fold_rows:
            f.write(",".join(json.dumps(row[c], ensure_ascii=True) for c in fold_cols) + "\n")
    unit_csv = output / "seed_unit_metrics.csv"
    unit_cols = ["component", "test_orbit", "seed", "unit_id", "n_windows", "rmse", "mae", "bias"]
    with unit_csv.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(unit_cols) + "\n")
        for row in seed_unit_rows:
            f.write(",".join(json.dumps(row[c], ensure_ascii=True) for c in unit_cols) + "\n")
    summary = {
        "schema": "brphm-f6-seed-metrics-v1",
        "candidate_receipt_sha256": sha256(args.receipt),
        "reference_sha256": sha256(args.reference),
        "source_code_sha256": {str(p): sha256(p) for p in (centered_path, global_path, fine_path, segmented_path, loader_path)},
        "seeds": list(base.SEEDS),
        "fold_count": 6,
        "seed_fold_row_count": len(seed_fold_rows),
        "seed_unit_row_count": len(seed_unit_rows),
        "fold_csv_sha256": sha256(fold_csv),
        "unit_csv_sha256": sha256(unit_csv),
        "route_frozen_from_receipt": True,
        "outer_used_for_selection": False,
        "status": "COMPLETE_DEVELOPMENT_DIAGNOSTIC_EXPORT",
    }
    (output / "seed_metrics_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "fold_rows": len(seed_fold_rows), "unit_rows": len(seed_unit_rows)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
