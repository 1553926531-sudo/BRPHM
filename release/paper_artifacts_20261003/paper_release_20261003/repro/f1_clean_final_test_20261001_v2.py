#!/usr/bin/env python3
"""F1 clean-chain freeze and one-time final evaluation.

The freeze phase records the already selected source-only candidate and the
existing holdout files without reading their semantic labels.  The evaluate
phase verifies that immutable record, then reads holdout labels exactly once,
fits only on the registered target train/validation tensors, and writes a
hash-linked receipt.  It never writes canonical, raw, holdout, sealed, A1/B1,
or competition assets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import stat
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


HOLDOUT_COLUMNS = ("sample_id", "product_line", "doe_cell", "seed", "sha256")
COMPONENTS = ("bat", "rwa")
PARTITION_SCHEMA = "brphm-f1-raw-sim-partition-v1"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def write_new(path: Path, value: Any, readonly: bool = True) -> str:
    if path.exists():
        raise RuntimeError(f"refusing to overwrite immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(value) if not isinstance(value, bytes) else value
    path.write_bytes(data)
    if readonly:
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return sha256_bytes(data)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def event_files(events_dir: Path) -> list[Path]:
    return sorted(events_dir.glob("*.json")) if events_dir.exists() else []


def append_event(events_dir: Path, event_type: str, payload: dict[str, Any]) -> tuple[Path, str]:
    events_dir.mkdir(parents=True, exist_ok=True)
    existing = event_files(events_dir)
    previous_hash = sha256_file(existing[-1]) if existing else None
    event = {
        "schema": "brphm-f1-event-v1",
        "sequence": len(existing) + 1,
        "event_type": event_type,
        "created_utc": now_utc(),
        "previous_event_sha256": previous_hash,
        "payload": payload,
    }
    data = canonical_bytes(event)
    digest = sha256_bytes(data)
    path = events_dir / f"{event['sequence']:04d}_{event_type}_{digest[:16]}.json"
    path.write_bytes(data)
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return path, digest


def verify_events(events_dir: Path) -> list[dict[str, Any]]:
    events = []
    previous = None
    for expected_seq, path in enumerate(event_files(events_dir), start=1):
        item = read_json(path)
        if item.get("sequence") != expected_seq:
            raise RuntimeError(f"event sequence gap: {path}")
        if item.get("previous_event_sha256") != previous:
            raise RuntimeError(f"event hash chain mismatch: {path}")
        if not sha256_file(path).startswith(path.stem.rsplit("_", 1)[-1]):
            raise RuntimeError(f"event filename hash mismatch: {path}")
        previous = sha256_file(path)
        events.append(item)
    return events


def parse_holdout(root: Path) -> tuple[Path, list[dict[str, str]]]:
    path = (root / "data/holdout/holdout_manifest.csv").resolve()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != HOLDOUT_COLUMNS:
            raise RuntimeError(f"holdout manifest columns drift: {path}")
        rows = [dict(row) for row in reader]
    if len(rows) != 98 or len({row["sample_id"] for row in rows}) != len(rows):
        raise RuntimeError("expected 98 unique holdout rows")
    for row in rows:
        if row["product_line"] not in COMPONENTS:
            raise RuntimeError(f"invalid product line: {row}")
    return path, rows


def parse_partition_manifest(root: Path, manifest_path: Path) -> tuple[Path, list[dict[str, str]]]:
    path = manifest_path.resolve()
    document = read_json(path)
    if document.get("schema") != PARTITION_SCHEMA:
        raise RuntimeError(f"partition manifest schema drift: {path}")
    rows = document.get("rows")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("partition manifest has no rows")
    seen = set()
    for row in rows:
        required = {"sample_id", "product_line", "raw_path", "sha256"}
        if not required.issubset(row):
            raise RuntimeError(f"partition row missing fields: {row}")
        if row["product_line"] not in COMPONENTS or row["sample_id"] in seen:
            raise RuntimeError(f"invalid or duplicate partition row: {row}")
        seen.add(row["sample_id"])
        raw = Path(row["raw_path"])
        if not raw.is_absolute():
            raw = (root / raw).resolve()
        if not raw.is_file() or sha256_file(raw) != row["sha256"]:
            raise RuntimeError(f"partition raw hash mismatch: {row['sample_id']}")
    counts = {component: sum(row["product_line"] == component for row in rows) for component in COMPONENTS}
    if any(counts[component] < 1 for component in COMPONENTS):
        raise RuntimeError(f"partition must contain both components: {counts}")
    return path, rows


def parse_evaluation_partition(root: Path, manifest_path: Path | None) -> tuple[Path, list[dict[str, str]]]:
    return parse_partition_manifest(root, manifest_path) if manifest_path else parse_holdout(root)


def row_raw_path(root: Path, row: dict[str, str]) -> Path:
    raw_value = row.get("raw_path")
    raw = Path(raw_value) if raw_value else root / "data/holdout" / row["product_line"] / f"{row['sample_id']}.mat"
    if not raw.is_absolute():
        raw = root / raw
    return raw.resolve()


def file_record(path: Path, root: Path) -> dict[str, Any]:
    return {"path": relative(path, root), "sha256": sha256_file(path),
            "size": path.stat().st_size}


def dependency_paths(root: Path, candidate_receipt: Path) -> list[Path]:
    base = root / "work/rul_next_electrochemical"
    segmented = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research"
    names = [
        "temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001.py",
        "temporal_tcn_unit_first_residual_centered_source_gate_20261001.py",
        "temporal_tcn_unit_first_source_gate_20261001.py",
        "temporal_tcn_fine_global_inner_route_source_gate.py",
        "temporal_tcn_global_inner_route_source_gate.py",
        "temporal_tcn_inner_adaptive_route_source_gate.py",
        "temporal_tcn_relative_source_gate.py",
        "temporal_tcn_source_gate.py",
    ]
    paths = [base / name for name in names]
    paths.extend([
        segmented / "run_segmented_hgb_mlp_source_gate_20260929.py",
        segmented / "run_leave_one_orbit_out_generalization_20260825.py",
        segmented / "run_component_blend_refinement_20260824.py",
        candidate_receipt,
        root / "work/augmented_features_isolated_20260929/reference_summary_remote.json",
    ])
    for component in COMPONENTS:
        paths.extend([
            root / f"data/processed/{component}_target.pt",
            root / f"data/processed/norm_stats/{component}_target.json",
            root / f"configs/preprocess/{component}_target.yaml",
        ])
    if any(not path.is_file() for path in paths):
        missing = [str(path) for path in paths if not path.is_file()]
        raise RuntimeError("missing freeze dependency: " + ", ".join(missing))
    return paths


def freeze(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"freeze output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    manifest_path, holdout_rows = parse_evaluation_partition(root, args.partition_manifest)
    candidate_receipt = args.candidate_receipt.resolve()
    candidate = read_json(candidate_receipt)
    selected_routes = {
        component: (candidate.get("components", {}).get(component, {})
                   .get("selected_route"))
        for component in COMPONENTS
    }
    if any(not isinstance(route, dict) for route in selected_routes.values()):
        raise RuntimeError("candidate receipt has no selected route for both components")
    for component, route in list(selected_routes.items()):
        if "alpha_by_target" not in route and isinstance(route.get("alphas"), dict):
            target_alpha = {}
            for target in ("LEO500", "LEO550", "LEO700"):
                incoming = [float(value) for direction, value in route["alphas"].items()
                            if direction.endswith(f"->{target}")]
                if len(incoming) != 2:
                    raise RuntimeError(f"route has incomplete incoming alphas for {component}/{target}")
                target_alpha[target] = float(sum(incoming) / len(incoming))
            selected_routes[component] = {
                **route,
                "alpha_by_target": target_alpha,
                "route_semantics": "mean of the two frozen source-to-target directed alphas",
            }
    raw_records = []
    for row in sorted(holdout_rows, key=lambda item: item["sample_id"]):
        raw = row_raw_path(root, row)
        if not raw.is_file() or sha256_file(raw) != row["sha256"]:
            raise RuntimeError(f"holdout raw hash mismatch: {row['sample_id']}")
        raw_records.append({**row, "file": file_record(raw, root)})
    dependencies = dependency_paths(root, candidate_receipt)
    dependency_records = [file_record(path, root) for path in dependencies]
    old_runner = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/run_leave_one_orbit_out_generalization_20260825.py"
    old_runner_text = old_runner.read_text(encoding="utf-8")
    if "data/holdout" in old_runner_text or "holdout/" in old_runner_text:
        raise RuntimeError("old runner contains a holdout path; clean-chain assertion failed")
    source_scope = {
        "old_candidate_input_paths": [
            "data/processed/bat_target.pt",
            "data/processed/rwa_target.pt",
        ],
        "old_runner_static_holdout_path_check": "pass",
        "old_runner_sha256": sha256_file(old_runner),
        "old_receipt_declared_sealed_holdout_read": candidate.get("sealed_holdout_read"),
        "old_receipt_declared_holdout_used_for_training_or_selection": candidate.get(
            "holdout_used_for_training_or_selection"),
    }
    preflight = {
        "schema": "brphm-f1-clean-final-preflight-v1",
        "created_utc": now_utc(),
        "root": str(root),
        "holdout_manifest": file_record(manifest_path, root),
        "holdout_units": {component: len([r for r in raw_records if r["product_line"] == component])
                          for component in COMPONENTS},
        "raw_holdout_files": raw_records,
        "candidate_receipt": file_record(candidate_receipt, root),
        "candidate_id": candidate.get("method_id"),
        "selected_routes": selected_routes,
        "source_scope": source_scope,
        "dependencies": dependency_records,
        "label_access": {
            "semantic_holdout_label_read_before_freeze": False,
            "raw_file_hash_only_before_freeze": True,
        },
    }
    append_event(output / "events", "preflight_recorded", {
        "preflight_sha256": sha256_bytes(canonical_bytes(preflight)),
        "holdout_label_read": False,
    })
    freeze_doc = {
        "schema": "brphm-f1-clean-final-freeze-v1",
        "decision": "freeze_source_only_candidate_and_run_once_on_new_untouched_raw_partition",
        "created_utc": now_utc(),
        "candidate": {
            "method_id": candidate.get("method_id"),
            "selected_routes": selected_routes,
            "alpha_floor": candidate.get("source_protocol", {}).get("uniform_alpha_floor"),
            "candidate_receipt": file_record(candidate_receipt, root),
        },
        "visible_information_before_freeze": {
            "candidate_receipt_sha256": sha256_file(candidate_receipt),
            "old_outer_results_status": "development_or_diagnostic_only",
            "old_outer_results_not_used_as_final_confirmation": True,
            "source_gate_only_selection": True,
        },
        "final_partition": {
            "manifest": file_record(manifest_path, root),
            "raw_files": raw_records,
            "n_units": {component: len([r for r in raw_records if r["product_line"] == component])
                        for component in COMPONENTS},
        },
        "training": {
            "only_registered_target_tensors": True,
            "holdout_labels_not_in_fit_or_selection": True,
            "tensor_hashes": {
                component: sha256_file(root / f"data/processed/{component}_target.pt")
                for component in COMPONENTS
            },
        },
        "prohibitions": [
            "do_not_read_final_labels_before_freeze_event",
            "do_not_change_candidate_route_after_freeze",
            "do_not_use_final_metrics_for_model_or_paper_decisions",
            "do_not_write_canonical_production_competition_or_sealed_assets",
        ],
        "dependencies": dependency_records,
        "source_scope": source_scope,
    }
    freeze_hash = write_new(output / "freeze_manifest.json", freeze_doc)
    write_new(output / "freeze_manifest.sha256", (freeze_hash + "  freeze_manifest.json\n").encode("ascii"))
    decision = {
        "schema": "brphm-f1-selection-decision-v1",
        "candidate_id": candidate.get("method_id"),
        "selected_routes": selected_routes,
        "decision": "candidate frozen before final label access",
        "visible_inputs": freeze_doc["visible_information_before_freeze"],
        "freeze_manifest_sha256": freeze_hash,
    }
    decision_hash = write_new(output / "selection_decision.json", decision)
    append_event(output / "events", "candidate_frozen", {
        "freeze_manifest_sha256": freeze_hash,
        "selection_decision_sha256": decision_hash,
        "semantic_final_label_read": False,
    })
    print(json.dumps({"status": "frozen", "freeze_manifest_sha256": freeze_hash,
                      "selection_decision_sha256": decision_hash,
                      "output": str(output)}, ensure_ascii=True))
    return 0


def verify_freeze(output: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = output / "freeze_manifest.json"
    sidecar = output / "freeze_manifest.sha256"
    if not manifest_path.is_file() or not sidecar.is_file():
        raise RuntimeError("freeze manifest or sidecar is missing")
    expected = sidecar.read_text(encoding="ascii").split()[0]
    actual = sha256_file(manifest_path)
    if expected != actual:
        raise RuntimeError("freeze manifest hash mismatch")
    decision = read_json(output / "selection_decision.json")
    if decision.get("freeze_manifest_sha256") != actual:
        raise RuntimeError("selection decision is not bound to freeze manifest")
    events = verify_events(output / "events")
    if not any(item.get("event_type") == "candidate_frozen" for item in events):
        raise RuntimeError("candidate_frozen event is missing")
    if any(item.get("event_type") == "final_label_access_started" for item in events):
        raise RuntimeError("final label access has already started; refusing a second run")
    return read_json(manifest_path), events


def import_project_modules(root: Path):
    import importlib

    candidate_dir = root / "work/rul_next_electrochemical"
    segmented_dir = root / "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research"
    sys.path.insert(0, str(candidate_dir))
    sys.path.insert(0, str(segmented_dir))
    centered = importlib.import_module("temporal_tcn_unit_first_residual_centered_source_gate_20261001")
    global_inner = importlib.import_module("temporal_tcn_global_inner_route_source_gate")
    fallback = importlib.import_module("temporal_tcn_orbit_fallback_source_gate")
    segmented = importlib.import_module("run_segmented_hgb_mlp_source_gate_20260929")
    loader = importlib.import_module("run_leave_one_orbit_out_generalization_20260825")
    return centered, global_inner, fallback, segmented, loader


def build_raw_holdout_payload(root: Path, component: str, config: dict[str, Any],
                              norm_doc: dict[str, Any], manifest_rows: list[dict[str, str]],
                              manifest_path: Path) -> dict[str, Any]:
    import numpy as np
    from src.datasets import labels, preprocess, sim_loader, windows

    line = component
    dataset_id = str(config["dataset_id"])
    channels = list(config["channels"])
    absent = set(config.get("channels_absent_ok") or [])
    mode = config["resample"]["mode"]
    bin_s = float(config["resample"].get("bin_s", preprocess.SECONDS_PER_DAY)) if mode == "daily_agg" else None
    bases = list(config["resample"].get("base_channels", preprocess.RWA_TARGET_BASE)) if mode == "daily_agg" else []
    want_fric = bool(config["resample"].get("fric_tc", True)) and mode == "daily_agg" and preprocess.FRIC_TC_MEAN in channels
    baseline = None
    if want_fric:
        baseline = ((norm_doc.get("derived") or {}).get("rw") or {}).get("fric_tc", {}).get("baseline_coef")
        if not isinstance(baseline, list) or len(baseline) != 2:
            raise RuntimeError("frozen RWA friction baseline is missing")
    L = int(config["window"]["L"])
    stride = int(config["window"]["stride"])
    rmax = float(config["labels"]["rmax"])
    floor = config["labels"].get("rul_floor", "keep")
    stats = norm_doc["channels"]
    xs, ys, rows, units = [], [], [], {}
    for item in sorted((row for row in manifest_rows if row["product_line"] == line), key=lambda row: row["sample_id"]):
        uid = item["sample_id"]
        raw_path = row_raw_path(root, item)
        if sha256_file(raw_path) != item["sha256"]:
            raise RuntimeError(f"raw holdout hash drift: {uid}")
        converted, _, frame = sim_loader.convert_one(raw_path, dataset_id, root / "data/interim" / dataset_id,
                                                     root=root, lenient=False, write=False)
        if converted != uid or frame is None:
            raise RuntimeError(f"raw identity drift: {uid}")
        if mode == "daily_agg":
            frame, _ = preprocess._bin_aggregate_rwa(frame, bin_s, bases, [])
        if want_fric:
            frame[preprocess.FRIC_TC_MEAN] = (
                frame["rw.motor_current_a.mean"].to_numpy(np.float64)
                - (float(baseline[0]) + float(baseline[1]) * frame["rw.bearing_temp_c.mean"].to_numpy(np.float64))
            )
        missing = [ch for ch in channels if ch not in frame.columns and ch not in absent]
        if missing:
            raise RuntimeError(f"holdout channels missing for {uid}: {missing}")
        matrix = np.column_stack([
            np.zeros(len(frame), dtype=np.float64) if ch in absent else frame[ch].to_numpy(np.float64)
            for ch in channels
        ])
        windows_array, ends = windows.slide(matrix, L, stride)
        y, _, _ = labels.window_labels(frame["label.rul"].to_numpy(np.float64),
                                        frame.get("label.hi"), ends, rmax)
        keep = np.isfinite(y)
        if floor == "drop_negative":
            keep &= y >= 0.0
        windows_array, ends, y = windows_array[keep], ends[keep], y[keep]
        if not len(windows_array):
            continue
        xs.append(preprocess.normalize(windows_array, channels, stats))
        ys.append(y.astype(np.float32))
        rows.extend(windows.build_index(uid, dataset_id, "tgt", "holdout",
                                         frame["t"].to_numpy(np.float64)[ends]))
        units[uid] = int(len(y))
    if not xs:
        raise RuntimeError(f"zero final windows for {line}")
    x = np.concatenate(xs).astype(np.float32)
    y = np.concatenate(ys).astype(np.float32)
    if len(rows) != len(x):
        raise RuntimeError("final payload row/array mismatch")
    return {"x": x, "y": y, "rows": rows, "rmax": rmax, "channels": channels,
            "units": units, "manifest_path": str(manifest_path)}


def package_versions() -> dict[str, str]:
    values = {}
    for name in ("torch", "numpy", "scipy", "pandas", "pyarrow", "scikit-learn"):
        try:
            values[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pass
    return values


def evaluate(args: argparse.Namespace) -> int:
    import numpy as np
    import torch
    import yaml

    root = args.root.resolve()
    output = args.output.resolve()
    manifest, _ = verify_freeze(output)
    append_event(output / "events", "final_label_access_started", {
        "freeze_manifest_sha256": sha256_file(output / "freeze_manifest.json"),
        "reason": "one-time construction of evaluation-only holdout tensors",
        "candidate_or_route_mutation_allowed": False,
    })
    partition_path, holdout_rows = parse_evaluation_partition(root, args.partition_manifest)
    centered, global_inner, fallback, segmented, loader = import_project_modules(root)
    centered.b.CONFIG_CURRENT = centered.b.CONFIG
    centered.b.fit_source_predictions = centered.fit_source_predictions_centered
    old_data = {component: loader.load_component(root, component) for component in COMPONENTS}
    results = {}
    payloads = {}
    for component in COMPONENTS:
        config_path = root / f"configs/preprocess/{component}_target.yaml"
        norm_path = root / f"data/processed/norm_stats/{component}_target.json"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        norm_doc = read_json(norm_path)
        payload = build_raw_holdout_payload(root, component, config, norm_doc, holdout_rows, partition_path)
        payloads[component] = payload
        old = old_data[component]
        n_old = len(old["rows"])
        n_final = len(payload["rows"])
        combined = {
            "x": np.concatenate([old["x"], payload["x"]], axis=0),
            "y": np.concatenate([old["y"], payload["y"]], axis=0),
            "rows": list(old["rows"]) + list(payload["rows"]),
            "rmax": float(old["rmax"]),
            "path": old["path"],
        }
        if float(payload["rmax"]) != float(old["rmax"]):
            raise RuntimeError(f"rmax drift for {component}")
        train = np.zeros(n_old + n_final, dtype=bool)
        train[:n_old] = True
        valid = ~train
        control_candidate = global_inner.reference_control_candidate(segmented, component)
        candidate_prediction = fallback.fit_tcn_formal(
            combined, component, train, valid, args.device
        )
        control = segmented.fit_predict_fixed(
            combined, component, train, valid, control_candidate, args.device,
            return_prediction=True,
        )[3]
        final_rows = list(payload["rows"])
        route = manifest["candidate"]["selected_routes"][component]
        alpha_by_target = route["alpha_by_target"]
        alpha = np.asarray([
            float(alpha_by_target[str(row["unit_id"]).split("_")[1]]) for row in final_rows
        ], dtype=np.float32)
        blended = alpha * np.asarray(candidate_prediction, dtype=np.float32) + (1.0 - alpha) * np.asarray(control, dtype=np.float32)
        prediction = centered.b.project(blended, final_rows, centered.b.CONFIG[component]["postprocess"])
        metrics = centered.b.metrics(prediction, payload["y"] / float(payload["rmax"]),
                                     float(payload["rmax"]), final_rows)
        control_metrics = centered.b.metrics(control, payload["y"] / float(payload["rmax"]),
                                             float(payload["rmax"]), final_rows)
        candidate_metrics = centered.b.metrics(candidate_prediction, payload["y"] / float(payload["rmax"]),
                                               float(payload["rmax"]), final_rows)
        results[component] = {
            "route": route,
            "n_windows": n_final,
            "n_units": len(payload["units"]),
            "unit_window_counts": payload["units"],
            "metrics": metrics,
            "candidate_only_metrics": candidate_metrics,
            "control_only_metrics": control_metrics,
            "candidate_control_blend": "alpha*unit-first-residual-centered-TCN + (1-alpha)*frozen HGB/MLP control; final unit projection applied once",
        }
        payload_path = output / f"final_{component}_payload.pt"
        torch.save({"x": torch.from_numpy(payload["x"]), "y_rul": torch.from_numpy(payload["y"]),
                    "meta": {"channels": payload["channels"], "rmax": payload["rmax"],
                             "index": payload["rows"], "split": "holdout"}}, payload_path)
        results[component]["payload_path"] = payload_path.name
        results[component]["payload_sha256"] = sha256_file(payload_path)
    final_receipt = {
        "schema": "brphm-f1-clean-final-evaluation-v1",
        "created_utc": now_utc(),
        "freeze_manifest_sha256": sha256_file(output / "freeze_manifest.json"),
        "selection_decision_sha256": sha256_file(output / "selection_decision.json"),
        "evaluation": "exactly_once_after_freeze",
        "label_access_event": "final_label_access_started",
        "candidate_id": manifest["candidate"]["method_id"],
        "outer_reuse_disposition": "all_old_outer_results_development_or_diagnostic_only",
        "training": {
            "data": {component: {"path": f"data/processed/{component}_target.pt",
                                  "sha256": manifest["training"]["tensor_hashes"][component]}
                     for component in COMPONENTS},
            "holdout_used_for_training_or_selection": False,
        },
        "holdout": {
            "manifest_sha256": manifest["final_partition"]["manifest"]["sha256"],
            "units": manifest["final_partition"]["n_units"],
            "raw_files_hash_bound": True,
        },
        "results": results,
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    "packages": package_versions(), "device": args.device},
        "mutation": {"canonical_project_modified": False, "competition_line_modified": False,
                      "sealed_read": False, "a1_b1_read": False, "holdout_written": False},
    }
    receipt_hash = write_new(output / "final_receipt.json", final_receipt)
    append_event(output / "events", "final_evaluation_completed", {
        "final_receipt_sha256": receipt_hash,
        "candidate_route_unchanged": True,
        "final_metrics_used_for_selection": False,
        "final_metrics_used_for_paper_decision": False,
    })
    print(json.dumps({"status": "evaluated", "receipt_sha256": receipt_hash,
                      "results": results}, ensure_ascii=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("--root", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--candidate-receipt", type=Path, required=True)
    freeze_parser.add_argument("--partition-manifest", type=Path, required=True)
    eval_parser = sub.add_parser("evaluate")
    eval_parser.add_argument("--root", type=Path, required=True)
    eval_parser.add_argument("--output", type=Path, required=True)
    eval_parser.add_argument("--partition-manifest", type=Path, required=True)
    eval_parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return freeze(args) if args.phase == "freeze" else evaluate(args)


if __name__ == "__main__":
    raise SystemExit(main())
