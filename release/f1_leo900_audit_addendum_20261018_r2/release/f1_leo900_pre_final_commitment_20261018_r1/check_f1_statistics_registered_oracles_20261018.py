"""Compare the F1 postprocessor to frozen code using artificial arrays only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import f1_lossless_gate_statistics_20261018 as analysis


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def check(metrics_code, gate_code):
    original_metrics = load_module("f1_registered_metric_oracle", metrics_code)
    original_gate = load_module("f1_registered_gate_oracle", gate_code)
    rng = np.random.default_rng(20261018)
    metric_cases = []
    for dtype in (np.float32, np.float64):
        for rmax in (.2, 1., 1000.):
            for count in (1, 7, 73):
                prediction = rng.uniform(-.4, 1.4, count).astype(dtype)
                truth = rng.uniform(0., 1., count).astype(dtype)
                rows = [{"unit_id": f"SYNTHETIC_{index % 4}", "t_end": count - index}
                        for index in range(count)]
                got = analysis.recompute_metrics(prediction, truth, rmax, rows)
                expected = original_metrics.metrics(prediction, truth, rmax, rows)
                if got != expected:
                    raise AssertionError(f"metric mismatch: {dtype}/{rmax}/{count}: {got} != {expected}")
                metric_cases.append({"dtype": np.dtype(dtype).name, "rmax": rmax, "n_rows": count})

    pairs = []
    for count in range(100):
        reference = {c: {m: float(rng.uniform(0., 1000.)) for m in ("rmse", "mae")}
                     for c in analysis.COMPONENTS}
        candidate = {c: {m: float(reference[c][m] + rng.normal(0., 1.)) for m in ("rmse", "mae")}
                     for c in analysis.COMPONENTS}
        pairs.append((f"random_{count}", candidate, reference))
    for baseline in (0., 1e-6, 1., 1000.):
        for sign in (-1, 1):
            threshold = baseline + sign * 1e-12
            for location, observed in (("below", np.nextafter(threshold, -np.inf)),
                                       ("equal", threshold),
                                       ("above", np.nextafter(threshold, np.inf))):
                reference = {c: {m: baseline for m in ("rmse", "mae")} for c in analysis.COMPONENTS}
                candidate = {c: dict(values) for c, values in reference.items()}
                candidate["bat"]["rmse"] = float(observed)
                candidate["rwa"]["mae"] = float(max(0., baseline - 1.))
                pairs.append((f"boundary_{baseline}_{sign}_{location}", candidate, reference))
    for label, candidate, reference in pairs:
        got = analysis.gate_decision(candidate, reference)
        expected = original_gate.compare_performance(candidate, reference)
        if any(value != expected[key] for key, value in got.items()):
            raise AssertionError(f"gate mismatch: {label}: {got} != {expected}")
    return {"schema": "brphm-f1-statistics-frozen-code-crosscheck-v1", "status": "PASS",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "metrics_code": record(metrics_code), "gate_code": record(gate_code),
            "analysis_code": record(Path(analysis.__file__)), "check_code": record(Path(__file__)),
            "metric_cases": metric_cases, "gate_case_count": len(pairs),
            "metric_equality": "exact equality of every original metric field",
            "gate_equality": "exact equality of every recomputed comparison field",
            "inputs": "artificial arrays only; clipped/out-of-range predictions and float boundary cases",
            "semantic_final_labels_read": False, "tensors_or_mat_loaded": False,
            "candidate_or_route_modified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-code", required=True, type=Path)
    parser.add_argument("--gate-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = check(args.metrics_code, args.gate_code)
    with args.output.open("xb") as handle:
        handle.write(analysis.canonical_bytes(result))
    print(json.dumps({"status": "PASS", "metric_cases": len(result["metric_cases"]),
                      "gate_cases": result["gate_case_count"], "record": record(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
