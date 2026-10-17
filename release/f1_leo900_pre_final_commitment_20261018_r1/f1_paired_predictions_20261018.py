"""Lossless, row-bound prediction artifacts from the original evaluation pass."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def write_paired_predictions(output: Path, component: str, rows: list[dict], *,
                             truth_rul, rmax: float, candidate, control, alpha,
                             blended, projected, payload_sha256: str,
                             seed_raw_predictions=None, seeds=None) -> dict:
    if component not in {"bat", "rwa"} or not rows:
        raise ValueError("a component and non-empty row layout are required")
    if not np.isfinite(rmax) or rmax <= 0:
        raise ValueError("rmax must be finite and positive")
    if len(payload_sha256) != 64 or any(c not in "0123456789abcdef" for c in payload_sha256):
        raise ValueError("invalid payload SHA-256")
    arrays = {"truth_rul": np.asarray(truth_rul), "candidate": np.asarray(candidate),
              "control": np.asarray(control), "alpha": np.asarray(alpha),
              "blended_before_final_projection": np.asarray(blended),
              "projected": np.asarray(projected)}
    for name, values in arrays.items():
        if values.ndim != 1 or len(values) != len(rows) or not np.isfinite(values).all():
            raise ValueError(f"{name} must be finite and align with the row layout")
        if values.dtype.kind != "f":
            raise ValueError(f"{name} must retain its floating point dtype")
    if np.any(arrays["alpha"] < 0) or np.any(arrays["alpha"] > 1):
        raise ValueError("alpha must be in [0, 1]")
    if any(not row.get("unit_id") for row in rows):
        raise ValueError("every prediction row must identify its unit")
    arrays["truth_relative"] = arrays["truth_rul"] / float(rmax)
    if seed_raw_predictions is not None:
        if seeds is None:
            raise ValueError("seed identities are required with seed predictions")
        seed_values = np.asarray(seed_raw_predictions)
        if (seed_values.ndim != 2 or seed_values.shape != (len(seeds), len(rows))
                or not np.isfinite(seed_values).all() or seed_values.dtype.kind != "f"):
            raise ValueError("seed predictions must be [seed, row] and finite")
        arrays["seed_raw_predictions"] = seed_values
    rows_bytes = canonical_bytes(rows)
    output = Path(output)
    arrays_path = output / f"final_{component}_paired_predictions.npz"
    layout_path = output / f"final_{component}_paired_predictions.json"
    if arrays_path.exists() or layout_path.exists():
        raise FileExistsError("refusing to replace paired predictions")
    output.mkdir(parents=True, exist_ok=True)
    with arrays_path.open("xb") as handle:
        np.savez_compressed(handle, **arrays)
    arrays_hash = hashlib.sha256(arrays_path.read_bytes()).hexdigest()
    layout = {"schema": "brphm-f1-original-pass-paired-predictions-v1", "component": component,
              "rows": rows, "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(),
              "arrays_path": arrays_path.name, "arrays_sha256": arrays_hash,
              "payload_sha256": payload_sha256, "rmax": float(rmax),
              "array_dtypes": {name: str(values.dtype) for name, values in arrays.items()},
              "array_shapes": {name: list(values.shape) for name, values in arrays.items()},
              "prediction_units": "normalized RUL; truth_rul uses the payload physical RUL unit",
              "seeds": None if seeds is None else list(seeds),
              "seed_prediction_semantics": "raw constituents of the fitted ensemble before residual centering or projection; not independent ensemble reruns",
              "row_order": "original evaluation order; no sorting or resampling",
              "provenance": "captured during the single frozen evaluation; no model rerun"}
    layout_bytes = canonical_bytes(layout)
    with layout_path.open("xb") as handle:
        handle.write(layout_bytes)
    return {"arrays_path": arrays_path.name, "arrays_sha256": arrays_hash,
            "layout_path": layout_path.name, "layout_sha256": hashlib.sha256(layout_bytes).hexdigest(),
            "n_rows": len(rows), "rows_sha256": layout["rows_sha256"]}
