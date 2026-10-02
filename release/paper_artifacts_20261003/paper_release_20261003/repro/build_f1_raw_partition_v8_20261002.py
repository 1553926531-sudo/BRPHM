#!/usr/bin/env python3
"""Select an untouched registered raw partition without reading MAT semantics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import stat
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

COMPONENTS = ("bat", "rwa")
ORBITS = ("LEO500", "LEO550", "LEO700")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def target_units(root: Path, component: str) -> set[str]:
    import torch

    payload = torch.load(root / "data/processed" / f"{component}_target.pt", map_location="cpu", weights_only=False)
    rows = payload.get("meta", {}).get("index", payload.get("index", []))
    return {str(row["unit_id"]) for row in rows}


def csv_ids(path: Path, key: str) -> set[str]:
    if not path.is_file():
        return set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row[key]) for row in csv.DictReader(handle) if row.get(key)}


def diagnostic_units(root: Path) -> tuple[set[str], list[dict[str, object]]]:
    seen: set[str] = set()
    sources = []
    for manifest in sorted((root / "work").glob("f1_generator_20261001_v*/sim/logs/manifest.csv")):
        ids = csv_ids(manifest, "sample_id")
        seen.update(ids)
        sources.append({"path": str(manifest), "sha256": sha256(manifest), "row_count": len(ids)})
    return seen, sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    holdout_path = root / "data/holdout/holdout_manifest.csv"
    holdout_ids = csv_ids(holdout_path, "sample_id")
    target_by_component = {component: target_units(root, component) for component in COMPONENTS}
    diagnostic_ids, diagnostic_sources = diagnostic_units(root)
    master_path = root / "sim/logs/manifest.csv"
    with master_path.open("r", encoding="utf-8", newline="") as handle:
        master_rows = list(csv.DictReader(handle))
    master_hash = sha256(master_path)
    eligible_rows = []
    available = Counter()
    exclusions = {component: {"target_tensor": 0, "existing_holdout": 0, "diagnostic": 0, "missing_raw": 0, "injected": 0} for component in COMPONENTS}
    for item in master_rows:
        component, sample_id = item.get("line", ""), item.get("sample_id", "")
        if component not in COMPONENTS or item.get("orbit") not in ORBITS:
            continue
        if item.get("fault_inject") != "none":
            exclusions[component]["injected"] += 1
            continue
        if sample_id in target_by_component[component]:
            exclusions[component]["target_tensor"] += 1
            continue
        if sample_id in holdout_ids:
            exclusions[component]["existing_holdout"] += 1
            continue
        if sample_id in diagnostic_ids:
            exclusions[component]["diagnostic"] += 1
            continue
        raw = (root / item["out_mat"]).resolve()
        if not raw.is_file() or raw.stat().st_size <= 0:
            exclusions[component]["missing_raw"] += 1
            continue
        eligible_rows.append({"sample_id": sample_id, "product_line": component, "orbit": item["orbit"], "doe_cell": item.get("doe_cell"), "seed": int(item["seed"]), "raw_path": str(raw), "sha256": sha256(raw), "size": raw.stat().st_size, "master_manifest_path": str(master_path), "master_manifest_sha256": master_hash})
        available[(component, item["orbit"])] += 1
    membership = {f"{component}/{orbit}": available[(component, orbit)] for component in COMPONENTS for orbit in ORBITS}
    if not eligible_rows or any(membership[key] == 0 for key in membership):
        raise RuntimeError(f"empty component/orbit cell: {membership}")
    # Hash-ranked ID-only sampling gives one deterministic unit per cell.
    selected = []
    for component in COMPONENTS:
        for orbit in ORBITS:
            cell = [row for row in eligible_rows if row["product_line"] == component and row["orbit"] == orbit]
            chosen = min(cell, key=lambda row: hashlib.sha256(row["sample_id"].encode("utf-8")).hexdigest())
            selected.append({**chosen, "selection_rank_sha256": hashlib.sha256(chosen["sample_id"].encode("utf-8")).hexdigest(), "selection_reason": "minimum_sha256_of_sample_id_within_component_orbit_cell"})
    document = {"schema": "brphm-f1-raw-sim-partition-v1", "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"), "semantic_labels_read": False, "selection_inputs": ["registered_master_manifest_sample_ids", "target_tensor_unit_ids_only", "existing_holdout_sample_ids", "v1_v7_diagnostic_manifest_ids", "raw_file_existence_size_sha256", "sample_id_sha256_rank_within_component_orbit"], "selection_rule": "one unit per component-orbit cell: minimum SHA-256(sample_id) among eligible registered non-injected raw units", "master_manifest": {"path": str(master_path), "sha256": master_hash}, "existing_holdout_manifest": {"path": str(holdout_path), "sha256": sha256(holdout_path), "excluded_units": len(holdout_ids)}, "target_tensor_unit_counts": {component: len(target_by_component[component]) for component in COMPONENTS}, "diagnostic_manifests": diagnostic_sources, "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "all_v1_v7_generator_outputs"], "exclusions": exclusions, "eligible_candidate_counts": membership, "membership_counts": {f"{component}/{orbit}": 1 for component in COMPONENTS for orbit in ORBITS}, "rows": sorted(selected, key=lambda row: row["sample_id"])}
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(document)
    output.write_bytes(payload)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(selected), "eligible_candidate_counts": membership, "exclusions": exclusions}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
