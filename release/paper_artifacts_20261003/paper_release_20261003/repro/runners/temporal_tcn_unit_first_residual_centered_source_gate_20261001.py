from __future__ import annotations

"""Unit-first relative TCN with source-fit residual centering.

The residual correction is fitted only from the source orbit's own predicted
windows, then frozen for every cross-orbit validation or outer fold.
"""

import json
from pathlib import Path

import numpy as np

import temporal_tcn_unit_first_source_gate_20261001 as unit_first


fine = unit_first.fine
g = fine.implementation
b = g.base
r = g.relative
SHRINK = 0.25


def _fit_centered(sequences, targets, rows, cfg, seed, device_name, valid_sequences, valid_rows):
    source = np.asarray(sequences, dtype=np.float32)
    target = np.asarray(valid_sequences, dtype=np.float32)
    y = np.asarray(targets, dtype=np.float32).reshape(-1)
    center = source.mean(axis=(0, 1), dtype=np.float64).astype(np.float32)
    scale = np.maximum(source.std(axis=(0, 1), dtype=np.float64), 1e-6).astype(np.float32)
    normalized = ((source - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
    normalized_valid = ((target - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
    models = [
        r.fit_model_relative(normalized, y, rows, b.CONFIG_CURRENT, seed, device_name)
        for seed in b.SEEDS
    ]
    source_raw = r.predict_models_relative(models, source, rows, center, scale, device_name)
    correction = -float(SHRINK) * float(np.median(source_raw.astype(np.float64) - y.astype(np.float64)))
    valid_raw = r.predict_models_relative(models, target, valid_rows, center, scale, device_name)
    return valid_raw + np.float32(correction), {"correction": correction, "source_prediction_median_residual": float(-correction / SHRINK)}


def fit_source_predictions_centered(data: dict, component: str, device_name: str):
    cfg = b.CONFIG_CURRENT[component]
    rows = data["rows"]
    predictions: dict[str, np.ndarray] = {}
    diagnostics: dict[str, object] = {"source_fits": {}, "shrink": SHRINK}
    for train_orbit in b.ORBITS:
        train_mask = np.asarray([b.orbit_of(row) == train_orbit for row in rows], dtype=bool)
        train_rows = [rows[index] for index in np.flatnonzero(train_mask)]
        source_x = data["x"][train_mask]
        source_y = data["y"][train_mask] / float(data["rmax"])
        center = source_x.mean(axis=(0, 1), dtype=np.float64).astype(np.float32)
        scale = np.maximum(source_x.std(axis=(0, 1), dtype=np.float64), 1e-6).astype(np.float32)
        normalized = ((source_x - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
        models = [r.fit_model_relative(normalized, source_y, train_rows, cfg, seed, device_name) for seed in b.SEEDS]
        train_raw = r.predict_models_relative(models, source_x, train_rows, center, scale, device_name)
        correction = -float(SHRINK) * float(np.median(train_raw.astype(np.float64) - source_y.astype(np.float64)))
        diagnostics["source_fits"][train_orbit] = {
            "train_windows": int(train_mask.sum()),
            "train_units": len({str(row["unit_id"]) for row in train_rows}),
            "correction": correction,
            "shrink": SHRINK,
        }
        for valid_orbit in b.ORBITS:
            if valid_orbit == train_orbit:
                continue
            valid_mask = np.asarray([b.orbit_of(row) == valid_orbit for row in rows], dtype=bool)
            valid_rows = [rows[index] for index in np.flatnonzero(valid_mask)]
            raw = r.predict_models_relative(models, data["x"][valid_mask], valid_rows, center, scale, device_name)
            predictions[f"{train_orbit}->{valid_orbit}"] = b.project(raw + np.float32(correction), valid_rows, cfg["postprocess"])
    return predictions, diagnostics


def fit_relative_formal_centered(data: dict, component: str, train: np.ndarray, valid: np.ndarray, device_name: str):
    rows = data["rows"]
    train_rows = [rows[index] for index in np.flatnonzero(train)]
    valid_rows = [rows[index] for index in np.flatnonzero(valid)]
    source_x = data["x"][train]
    source_y = data["y"][train] / float(data["rmax"])
    center = source_x.mean(axis=(0, 1), dtype=np.float64).astype(np.float32)
    scale = np.maximum(source_x.std(axis=(0, 1), dtype=np.float64), 1e-6).astype(np.float32)
    normalized = ((source_x - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
    models = [r.fit_model_relative(normalized, source_y, train_rows, b.CONFIG_CURRENT[component], seed, device_name) for seed in b.SEEDS]
    train_raw = r.predict_models_relative(models, source_x, train_rows, center, scale, device_name)
    correction = -float(SHRINK) * float(np.median(train_raw.astype(np.float64) - source_y.astype(np.float64)))
    valid_raw = r.predict_models_relative(models, data["x"][valid], valid_rows, center, scale, device_name)
    return b.project(valid_raw + np.float32(correction), valid_rows, b.CONFIG_CURRENT[component]["postprocess"])


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    b.CONFIG_CURRENT = b.CONFIG
    b.fit_source_predictions = fit_source_predictions_centered
    original_formal = g._fit_relative_formal
    g._fit_relative_formal = fit_relative_formal_centered
    try:
        receipt = fine.run(args)
    finally:
        g._fit_relative_formal = original_formal
    receipt["schema"] = "brphm-temporal-tcn-unit-first-residual-centered-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_tcn_unit_first_relative_residual_centered"
    receipt["source_protocol"]["input_representation"] = "source-standardized telemetry with per-unit earliest-window baseline-relative trajectories"
    receipt["source_protocol"]["residual_correction"] = "negative SHRINK times the median source-fit residual, SHRINK=0.25; fit only on each training source orbit"
    receipt["outer_selection_independent"] = True
    for component in receipt["components"].values():
        if component.get("selected_candidate_id") is not None:
            component["selected_candidate_id"] = receipt["method_id"]
    args.output.joinpath("receipt.json").write_text(json.dumps(receipt, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str((args.output / "receipt.json").resolve()), "formal_eligible": receipt["formal_eligible"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
