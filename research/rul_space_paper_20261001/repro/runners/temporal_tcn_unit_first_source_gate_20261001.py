from __future__ import annotations

"""Unit-first relative trajectory TCN, isolated source-gate/formal runner."""

import json
from pathlib import Path

import numpy as np
import torch

import temporal_tcn_fine_global_inner_route_source_gate as fine

g = fine.implementation
b = g.base
r = g.relative
_fit_model_base = b.fit_model


def _unit_baselines(values: np.ndarray, rows: list[dict]) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    if values.ndim != 3 or len(rows) != len(values):
        raise ValueError("values and rows must align")
    first: dict[str, tuple[float, int]] = {}
    for index, row in enumerate(rows):
        key = str(row["unit_id"])
        t_end = float(row.get("t_end", index))
        if key not in first or t_end < first[key][0]:
            first[key] = (t_end, index)
    baseline = np.empty((len(rows), values.shape[2]), dtype=np.float32)
    for index, row in enumerate(rows):
        baseline[index] = values[first[str(row["unit_id"])][1], 0, :]
    return baseline


def append_unit_first(values: np.ndarray, rows: list[dict]) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    if not np.isfinite(values).all():
        raise ValueError("values must be finite")
    baseline = _unit_baselines(values, rows)
    return np.concatenate((values, values - baseline[:, None, :]), axis=2).astype(np.float32)


def fit_model_unit_first(sequences, targets, rows, cfg, seed, device_name):
    return _fit_model_base(append_unit_first(sequences, rows), targets, rows, cfg, seed, device_name)


def predict_models_unit_first(models, sequences, rows, center, scale, device_name):
    normalized = ((np.asarray(sequences, dtype=np.float32) - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
    values = torch.from_numpy(np.transpose(append_unit_first(normalized, rows), (0, 2, 1)))
    outputs = []
    device = torch.device(device_name)
    for model, tmax in models:
        with torch.no_grad():
            outputs.append(model(values.to(device), torch.from_numpy(b._age(rows, tmax)).to(device)).cpu().numpy())
    return np.median(np.stack(outputs, axis=0), axis=0).astype(np.float32)


r.fit_model_relative = fit_model_unit_first
r.predict_models_relative = predict_models_unit_first


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    receipt = fine.run(args)
    receipt["schema"] = "brphm-temporal-tcn-unit-first-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_tcn_unit_first_relative"
    receipt["source_protocol"]["input_representation"] = (
        "source-standardized telemetry concatenated with per-unit earliest-window baseline-relative trajectories"
    )
    receipt["outer_selection_independent"] = True
    for component in receipt["components"].values():
        if component.get("selected_candidate_id") is not None:
            component["selected_candidate_id"] = receipt["method_id"]
    args.output.joinpath("receipt.json").write_text(json.dumps(receipt, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str((args.output / "receipt.json").resolve()), "formal_eligible": receipt["formal_eligible"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
