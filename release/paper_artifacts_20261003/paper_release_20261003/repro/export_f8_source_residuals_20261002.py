from __future__ import annotations

"""Rebuild source-validation residuals for the frozen F8 candidate only.

This intentionally stops before any formal/outer routine. Inputs are the
registered train/validation tensors; target windows are grouped by unit so all
later resampling can preserve within-unit dependence.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import socket
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


SOURCE_REL = Path("work/rul_next_electrochemical")
SEGMENTED_REL = Path("work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def grouped_residuals(rows: list[dict], mask: np.ndarray, values: np.ndarray) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    valid_rows = [rows[index] for index in np.flatnonzero(mask)]
    if len(valid_rows) != len(values):
        raise ValueError("residual vector does not align with validation rows")
    for row, value in zip(valid_rows, values):
        grouped[str(row["unit_id"])].append(float(value))
    return dict(sorted(grouped.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source_dir = root / SOURCE_REL
    sys.path.insert(0, str(source_dir))

    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

    import temporal_tcn_global_inner_route_source_gate as route_impl
    import temporal_tcn_unit_first_residual_centered_source_gate_20261001 as centered
    import temporal_tcn_unit_first_source_gate_20261001  # installs relative-input hooks

    base = route_impl.base
    receipt_path = args.receipt.resolve()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("formal_eligible") is not True:
        raise ValueError("the frozen source-gate receipt is not eligible")

    segmented_path = root / SEGMENTED_REL / "run_segmented_hgb_mlp_source_gate_20260929.py"
    loader_path = root / SEGMENTED_REL / "run_leave_one_orbit_out_generalization_20260825.py"
    segmented = base.load_module("f8_segmented_control", segmented_path)
    loader = base.load_module("f8_registered_loader", loader_path)
    data_by_component = base.load_data(loader, args.data_root.resolve())

    base.CONFIG_CURRENT = base.CONFIG
    base.fit_source_predictions = centered.fit_source_predictions_centered
    result = {
        "schema": "brphm-f8-source-residual-replay-v1",
        "method_id": receipt["method_id"],
        "receipt_sha256": sha256(receipt_path),
        "created_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "scipy": importlib.metadata.version("scipy"),
        "thread_limits": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "scope": "Registered train/validation source transfers only; no formal or outer evaluation function is called.",
        "formal_evaluation_called": False,
        "sealed_a1_b1_accessed": False,
        "components": {},
        "source_hashes": {},
    }

    tracked_paths = [
        source_dir / "temporal_tcn_source_gate.py",
        source_dir / "temporal_tcn_relative_source_gate.py",
        source_dir / "temporal_tcn_inner_adaptive_route_source_gate.py",
        source_dir / "temporal_tcn_global_inner_route_source_gate.py",
        source_dir / "temporal_tcn_fine_global_inner_route_source_gate.py",
        source_dir / "temporal_tcn_unit_first_source_gate_20261001.py",
        source_dir / "temporal_tcn_unit_first_residual_centered_source_gate_20261001.py",
        root / SEGMENTED_REL / "run_segmented_hgb_mlp_source_gate_20260929.py",
        root / SEGMENTED_REL / "run_leave_one_orbit_out_generalization_20260825.py",
        args.data_root.resolve() / "data/processed/bat_target.pt",
        args.data_root.resolve() / "data/processed/rwa_target.pt",
    ]
    result["source_hashes"] = {
        str(path.relative_to(root)) if path.is_relative_to(root) else str(path): sha256(path)
        for path in tracked_paths
    }

    for component in base.COMPONENTS:
        data = data_by_component[component]
        old_candidate = segmented.CANDIDATES[component]
        frozen_candidate = route_impl.reference_control_candidate(segmented, component)
        segmented.CANDIDATES[component] = frozen_candidate
        try:
            control_metrics, control_residuals, control_diagnostics, control_predictions = base.frozen_controls(
                segmented, data, component, "cpu", include_predictions=True
            )
        finally:
            segmented.CANDIDATES[component] = old_candidate

        candidate_predictions, candidate_diagnostics = base.fit_source_predictions(data, component, "cpu")
        route = receipt["components"][component]["selected_route"]
        candidate_blend = route_impl.blend_predictions(
            data,
            component,
            candidate_predictions,
            control_predictions,
            route,
        )
        records, candidate_residuals = base.source_records(
            data, component, candidate_blend, control_metrics
        )

        directions: dict[str, dict] = {}
        rows = data["rows"]
        for direction in base.EXPECTED_DIRECTIONS:
            _, valid = base.transfer_masks(rows, *direction.split("->"))
            valid_rows = [rows[index] for index in np.flatnonzero(valid)]
            directions[direction] = {
                "n_windows": int(valid.sum()),
                "n_units": len({str(row["unit_id"]) for row in valid_rows}),
                "candidate_residuals_by_unit": grouped_residuals(rows, valid, candidate_residuals[direction]),
                "control_residuals_by_unit": grouped_residuals(rows, valid, control_residuals[direction]),
            }

        stored_records = receipt["components"][component]["records"]
        stored_by_key = {
            item.get("direction", item.get("orbit_pair")): item for item in stored_records
        }
        replay_by_key = {
            item.get("direction", item.get("orbit_pair")): item for item in records
        }
        metric_replay = {}
        for key, replay in replay_by_key.items():
            stored = stored_by_key[key]
            if "direction" in replay:
                metric_replay[key] = {
                    metric: {
                        "stored": float(stored["metrics"][metric]),
                        "replayed": float(replay["metrics"][metric]),
                        "delta": float(replay["metrics"][metric]) - float(stored["metrics"][metric]),
                    }
                    for metric in ("rmse", "mae")
                }
            else:
                metric_replay[key] = {
                    "stored": float(stored["residual_ks"]),
                    "replayed": float(replay["residual_ks"]),
                    "delta": float(replay["residual_ks"]) - float(stored["residual_ks"]),
                }

        result["components"][component] = {
            "input_tensor_sha256": sha256(Path(data["path"])),
            "input_shape": list(data["x"].shape),
            "selected_route": route,
            "frozen_control_candidate": frozen_candidate,
            "control_fit_diagnostics": control_diagnostics,
            "candidate_fit_diagnostics": candidate_diagnostics,
            "metric_replay": metric_replay,
            "directions": directions,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str(args.output), "formal_evaluation_called": False}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
