#!/usr/bin/env python3
"""Freeze and evaluate the registered F1 candidate on an untouched LEO600 partition."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


COMPONENTS = ("bat", "rwa")
REGISTERED_TARGETS = ("LEO500", "LEO550", "LEO700")
GATE_METRICS = ("rmse", "mae")
TOLERANCE = 1e-12
UNSEEN_ALPHA_FLOOR = 1e-5
PREVIOUS_RETRY_RECEIPT_SHA256 = "6539846060867f598732a3a4b7d17a71cca05bb5f54c2e22426d6056c2b39b20"
PREVIOUS_RETRY_METRICS = {
    "bat": {"rmse": 1.6578676802765389, "mae": 1.0855729667557303},
    "rwa": {"rmse": 0.018801855461304577, "mae": 0.01389681839862735},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def select_source_floor_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    source = candidate.get("source_protocol", {})
    directions = source.get("directions")
    expected_directions = [
        "LEO500->LEO550", "LEO500->LEO700",
        "LEO550->LEO500", "LEO550->LEO700",
        "LEO700->LEO500", "LEO700->LEO550",
    ]
    if directions != expected_directions:
        raise ValueError("source route direction order is missing or changed")

    families = source.get("route_catalog", {}).get("alpha_families")
    route_count = source.get("route_catalog", {}).get("route_count")
    if not isinstance(families, list) or not families:
        raise ValueError("source route catalog has no alpha families")
    if not isinstance(route_count, int) or route_count < 1:
        raise ValueError("source route catalog has an invalid route count")

    selected: dict[str, Any] = {}
    selection_counts: dict[str, Any] = {}
    for component in COMPONENTS:
        record = candidate.get("components", {}).get(component, {})
        sweep = record.get("route_sweep")
        if not isinstance(sweep, list) or len(sweep) != route_count:
            raise ValueError(f"{component} route sweep does not match the registered route count")

        seen: set[str] = set()
        gate_pass_count = 0
        eligible: list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]] = []
        for item in sweep:
            route_id = item.get("route_id")
            match = re.fullmatch(r"family(\d+)_mask(\d+)", str(route_id))
            if match is None or route_id in seen:
                raise ValueError(f"{component} route sweep has an invalid or duplicate route id")
            seen.add(route_id)
            family_index, mask = (int(match.group(1)), int(match.group(2)))
            if not 0 <= family_index < len(families) or not 0 <= mask < (1 << len(directions)):
                raise ValueError(f"{component}/{route_id} is outside the registered route catalog")

            family = families[family_index]
            if not isinstance(family, list) or len(family) != 2:
                raise ValueError(f"{component}/{route_id} has a malformed alpha family")
            low, high = (float(value) for value in family)
            if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in (low, high)) or high < low:
                raise ValueError(f"{component}/{route_id} has invalid alpha bounds")
            directed = {
                direction: (high if mask & (1 << index) else low)
                for index, direction in enumerate(directions)
            }
            by_target: dict[str, float] = {}
            for target in REGISTERED_TARGETS:
                incoming = [value for direction, value in directed.items()
                            if direction.endswith(f"->{target}")]
                if len(incoming) != 2:
                    raise ValueError(f"{component}/{route_id} has incomplete source directions for {target}")
                by_target[target] = sum(incoming) / len(incoming)

            gate = item.get("gate", {})
            if not isinstance(gate.get("passes"), bool):
                raise ValueError(f"{component}/{route_id} has no boolean source-gate decision")
            if not gate["passes"]:
                continue
            gate_pass_count += 1
            if any(value < UNSEEN_ALPHA_FLOOR for value in by_target.values()):
                continue

            metrics = tuple(float(gate.get(key, math.nan)) for key in (
                "worst_residual_ks", "mean_rmse", "mean_mae"))
            if not all(math.isfinite(value) for value in metrics):
                raise ValueError(f"{component}/{route_id} has non-finite source-gate tie-break metrics")
            route = {
                "route_id": route_id,
                "family_index": family_index,
                "low_alpha": low,
                "high_alpha": high,
                "mask": mask,
                "alphas": directed,
                "alpha_by_target": by_target,
                "route_semantics": "mean of the two frozen source-to-target directed alphas",
            }
            tie_break = (
                sum(by_target.values()),
                max(by_target.values()),
                *metrics,
                route_id,
            )
            eligible.append((tie_break, route, gate))

        if not eligible:
            raise ValueError(f"no source-gate route meets the alpha floor for {component}")
        eligible.sort(key=lambda item: item[0])
        _, selected[component], selected_gate = eligible[0]
        selection_counts[component] = {
            "registered_route_count": route_count,
            "source_gate_pass_count": gate_pass_count,
            "floor_eligible_count": len(eligible),
            "selected_gate": selected_gate,
            "route_sweep_sha256": hashlib.sha256(canonical_bytes(sweep)).hexdigest(),
        }

    protocol = json.loads(json.dumps(source))
    protocol["uniform_alpha_floor"] = UNSEEN_ALPHA_FLOOR
    protocol["selection"] = (
        "source-gate-only uniform target-orbit alpha floor >= 1e-5 for BAT and RWA; "
        "then minimum total alpha and existing source-only tie-breaks"
    )
    protocol["selection_function"] = "select_route_uniform_floor"

    result: dict[str, Any] = {
        "schema": "brphm-f1-source-only-floor-candidate-v1",
        "method_id": "source_only_temporal_tcn_unit_first_relative_residual_centered_uniform_alpha_floor",
        "execution_complete": True,
        "source_protocol": protocol,
        "components": {},
        "source_selection": {
            "inputs": [
                "source_protocol.directions",
                "source_protocol.route_catalog.alpha_families",
                "components.*.route_sweep[*].route_id",
                "components.*.route_sweep[*].gate",
            ],
            "outer_or_final_metrics_used": False,
            "uniform_alpha_floor": UNSEEN_ALPHA_FLOOR,
            "selection_counts": selection_counts,
        },
    }
    for component in COMPONENTS:
        original = candidate["components"][component]
        result["components"][component] = {
            "input_tensor_sha256": original.get("input_tensor_sha256"),
            "input_shape": original.get("input_shape"),
            "rmax": original.get("rmax"),
            "selected_route": selected[component],
            "source_gate_selection": selection_counts[component],
        }
    return result


def build_candidate_snapshot(candidate: dict[str, Any], base_receipt_sha256: str,
                             unseen_orbit: str) -> dict[str, Any]:
    if len(base_receipt_sha256) != 64 or any(c not in "0123456789abcdef" for c in base_receipt_sha256):
        raise ValueError("base candidate receipt SHA-256 is invalid")
    routes = candidate.get("components", {})
    routes_ready = all(
        isinstance(routes.get(component, {}).get("selected_route", {}).get("alpha_by_target"), dict)
        for component in COMPONENTS
    )
    if "uniform_alpha_floor" not in candidate.get("source_protocol", {}) or not routes_ready:
        candidate = select_source_floor_candidate(candidate)
    floor = float(candidate.get("source_protocol", {}).get("uniform_alpha_floor", math.nan))
    if not math.isfinite(floor) or not 0.0 <= floor <= 1.0:
        raise ValueError("candidate uniform_alpha_floor must be finite and in [0, 1]")
    if floor != UNSEEN_ALPHA_FLOOR:
        raise ValueError("candidate uniform_alpha_floor differs from the registered source-only floor")
    snapshot = json.loads(json.dumps(candidate))
    for component in COMPONENTS:
        route = snapshot.get("components", {}).get(component, {}).get("selected_route")
        if not isinstance(route, dict):
            raise ValueError(f"candidate has no selected route for {component}")
        alpha_by_target = route.get("alpha_by_target")
        if not isinstance(alpha_by_target, dict) or set(alpha_by_target) != set(REGISTERED_TARGETS):
            raise ValueError(f"{component} route must contain exactly the registered targets")
        if unseen_orbit in alpha_by_target:
            raise ValueError(f"unseen target already exists in frozen {component} route")
        for target, value in alpha_by_target.items():
            alpha = float(value)
            if not math.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
                raise ValueError(f"invalid frozen alpha for {component}/{target}")
        alpha_by_target[unseen_orbit] = floor
        route["unseen_target_rule"] = "uniform_alpha_floor_from_frozen_source_protocol"
    snapshot["derivation"] = {
        "schema": "brphm-f1-unseen-orbit-candidate-snapshot-v1",
        "base_candidate_receipt_sha256": base_receipt_sha256,
        "unseen_orbit": unseen_orbit,
        "alpha_rule": "set only the unseen orbit alpha to source_protocol.uniform_alpha_floor; preserve all registered target routes",
        "alpha_value_by_component": {component: floor for component in COMPONENTS},
        "selection_uses_unseen_labels": False,
        "source_selection": snapshot.get("source_selection"),
    }
    return snapshot


def validate_partition(document: dict[str, Any], expected_orbit: str) -> dict[str, int]:
    if document.get("schema") != "brphm-f1-raw-sim-partition-v1":
        raise ValueError("unexpected partition schema")
    if document.get("semantic_labels_read") is not False or document.get("final_label_access") is not False:
        raise ValueError("partition must be metadata-only before freeze")
    rows = document.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("partition has no rows")
    ids: set[str] = set()
    counts = {component: 0 for component in COMPONENTS}
    for row in rows:
        sample_id = str(row.get("sample_id", ""))
        pieces = sample_id.split("_")
        component = row.get("product_line")
        if len(pieces) < 3 or pieces[1] != expected_orbit:
            raise ValueError(f"partition contains a unit outside {expected_orbit}: {sample_id}")
        if component not in COMPONENTS or sample_id in ids:
            raise ValueError(f"invalid component or duplicate sample id: {sample_id}")
        ids.add(sample_id)
        counts[component] += 1
    if any(counts[component] == 0 for component in COMPONENTS):
        raise ValueError(f"partition must contain BAT and RWA units: {counts}")
    return counts


def compare_performance(candidate: dict[str, dict[str, float]],
                        reference: dict[str, dict[str, float]]) -> dict[str, Any]:
    deltas: dict[str, dict[str, float]] = {}
    regressions: list[str] = []
    strict_gain = False
    for component in COMPONENTS:
        if component not in candidate or component not in reference:
            raise ValueError(f"missing component metrics: {component}")
        deltas[component] = {}
        for metric in GATE_METRICS:
            observed = float(candidate[component][metric])
            baseline = float(reference[component][metric])
            if not math.isfinite(observed) or not math.isfinite(baseline):
                raise ValueError(f"non-finite {component}.{metric} metric")
            delta = observed - baseline
            deltas[component][metric] = delta
            if observed > baseline + TOLERANCE:
                regressions.append(f"{component}.{metric}")
            if observed < baseline - TOLERANCE:
                strict_gain = True
    return {
        "passes": not regressions and strict_gain,
        "strict_gain": strict_gain,
        "regressions": sorted(regressions),
        "tolerance": TOLERANCE,
        "deltas_candidate_minus_same_partition_reference": deltas,
        "rule": "both components must be non-inferior on RMSE and MAE to the same-partition projected frozen HGB/MLP reference, with at least one strict gain",
    }


def write_new(path: Path, data: bytes) -> str:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return hashlib.sha256(data).hexdigest()


def load_base_runner() -> Any:
    path = Path(__file__).with_name("f1_clean_final_test_20261001_v2.py")
    spec = importlib.util.spec_from_file_location("f1_clean_final_test_20261001_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base evaluator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_wrapper_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("phase", choices=("freeze", "evaluate"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-receipt", type=Path)
    parser.add_argument("--partition-manifest", type=Path, required=True)
    parser.add_argument("--unseen-orbit", default="LEO600")
    args, remaining = parser.parse_known_args(argv)
    if args.phase == "freeze" and args.candidate_receipt is None:
        parser.error("freeze requires --candidate-receipt")
    return args, remaining


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_freeze(module: Any, args: argparse.Namespace, remaining: list[str]) -> int:
    base_receipt = args.candidate_receipt.resolve()
    partition_path = args.partition_manifest.resolve()
    candidate = load_json(base_receipt)
    partition = load_json(partition_path)
    counts = validate_partition(partition, args.unseen_orbit)
    snapshot = build_candidate_snapshot(candidate, sha256_file(base_receipt), args.unseen_orbit)
    snapshot_path = args.output.resolve().with_name(args.output.name + ".candidate_snapshot.json")
    snapshot_hash = write_new(snapshot_path, canonical_bytes(snapshot))

    original_dependencies = module.dependency_paths

    def dependency_paths(root: Path, candidate_receipt: Path) -> list[Path]:
        paths = original_dependencies(root, candidate_receipt)
        paths.extend([base_receipt, Path(__file__).resolve(), Path(__file__).with_name("f1_clean_final_test_20261001_v2.py"), partition_path])
        unique: dict[str, Path] = {str(path.resolve()): path.resolve() for path in paths}
        if any(not path.is_file() for path in unique.values()):
            missing = [str(path) for path in unique.values() if not path.is_file()]
            raise RuntimeError("missing F1 freeze dependency: " + ", ".join(missing))
        return list(unique.values())

    module.dependency_paths = dependency_paths
    original_write_new = module.write_new

    def write_new_with_visibility(path: Path, value: Any, readonly: bool = True) -> str:
        if path.name == "freeze_manifest.json":
            visible = value.setdefault("visible_information_before_freeze", {})
            visible["prior_clean_retry1"] = {
                "receipt_sha256": PREVIOUS_RETRY_RECEIPT_SHA256,
                "status": "development_diagnostic_performance_gate_failed",
                "metrics": PREVIOUS_RETRY_METRICS,
                "candidate_or_route_selection_input": False,
                "purpose": "records that the failed known-orbit retry was visible and is not claimed as final evidence",
            }
            visible["outer_reuse_disposition"] = "all successive outer-fold outcomes, including 5/4/3/1/3/0, development_or_diagnostic_only"
            visible["new_orbit_alpha_rule"] = snapshot["derivation"]
            value["candidate_snapshot"] = module.file_record(snapshot_path, args.root.resolve())
            value["candidate_snapshot_sha256"] = snapshot_hash
            value["pre_freeze_partition_counts"] = counts
        return original_write_new(path, value, readonly=readonly)

    module.write_new = write_new_with_visibility
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], "freeze", "--root", str(args.root), "--output", str(args.output),
                    "--candidate-receipt", str(snapshot_path), "--partition-manifest", str(partition_path)] + remaining
        return module.main()
    finally:
        sys.argv = original_argv


def run_evaluate(module: Any, args: argparse.Namespace, remaining: list[str]) -> int:
    partition_path = args.partition_manifest.resolve()
    partition = load_json(partition_path)
    counts = validate_partition(partition, args.unseen_orbit)
    output = args.output.resolve()
    freeze_doc = load_json(output / "freeze_manifest.json")
    if freeze_doc.get("candidate", {}).get("selected_routes") is None:
        raise RuntimeError("frozen selected routes are missing")
    for component in COMPONENTS:
        route = freeze_doc["candidate"]["selected_routes"][component]
        if args.unseen_orbit not in route.get("alpha_by_target", {}):
            raise RuntimeError(f"frozen route does not define {args.unseen_orbit} for {component}")
    if freeze_doc.get("final_partition", {}).get("manifest", {}).get("sha256") != sha256_file(partition_path):
        raise RuntimeError("evaluation partition differs from the frozen partition")

    original_evaluate = module.evaluate

    def evaluate_with_same_partition_gate(evaluate_args: argparse.Namespace) -> int:
        status = original_evaluate(evaluate_args)
        receipt_path = output / "final_receipt.json"
        receipt = load_json(receipt_path)
        candidate_metrics = {component: receipt["results"][component]["metrics"] for component in COMPONENTS}
        reference_metrics = {component: receipt["results"][component]["control_only_metrics"] for component in COMPONENTS}
        gate = compare_performance(candidate_metrics, reference_metrics)
        report = {
            "schema": "brphm-f1-same-partition-reference-gate-v1",
            "created_utc": receipt["created_utc"],
            "final_receipt_sha256": sha256_file(receipt_path),
            "freeze_manifest_sha256": sha256_file(output / "freeze_manifest.json"),
            "partition_manifest_sha256": sha256_file(partition_path),
            "partition_unit_counts": counts,
            "comparison": gate,
            "metrics": {
                component: {
                    "candidate_blend": candidate_metrics[component],
                    "same_partition_reference": reference_metrics[component],
                }
                for component in COMPONENTS
            },
            "labels_reloaded_or_model_rerun": False,
        }
        report_path = output / "same_partition_performance_gate.json"
        report_hash = write_new(report_path, canonical_bytes(report))
        module.append_event(output / "events", "same_partition_reference_gate_completed", {
            "performance_gate_sha256": report_hash,
            "final_receipt_sha256": sha256_file(receipt_path),
            "gate_passed": gate["passes"],
            "labels_reloaded_or_model_rerun": False,
        })
        print(json.dumps({"performance_gate": gate, "sha256": report_hash}, ensure_ascii=True))
        return status

    module.evaluate = evaluate_with_same_partition_gate
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], "evaluate", "--root", str(args.root), "--output", str(args.output),
                    "--partition-manifest", str(partition_path)] + remaining
        return module.main()
    finally:
        sys.argv = original_argv


def main(argv: list[str] | None = None) -> int:
    args, remaining = parse_wrapper_args(sys.argv[1:] if argv is None else argv)
    module = load_base_runner()
    if args.phase == "freeze":
        return run_freeze(module, args, remaining)
    return run_evaluate(module, args, remaining)


if __name__ == "__main__":
    raise SystemExit(main())
