#!/usr/bin/env python3
"""Build a second untouched raw-unit partition without reading MAT semantics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import stat
from pathlib import Path

SCHEMA = "brphm-f1-raw-sim-partition-v1"
COMPONENTS = ("bat", "rwa")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def target_units(root: Path, component: str) -> set[str]:
    import torch

    payload = torch.load(root / "data/processed" / f"{component}_target.pt", map_location="cpu", weights_only=False)
    rows = payload.get("meta", {}).get("index", payload.get("index", []))
    return {str(row["unit_id"]) for row in rows}


def holdout_units(root: Path, component: str) -> set[str]:
    with (root / "data/holdout/holdout_manifest.csv").open("r", encoding="utf-8", newline="") as handle:
        return {
            row["sample_id"]
            for row in csv.DictReader(handle)
            if row["product_line"] == component
        }


def build(root: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    rows = []
    exclusions = {}
    for component in COMPONENTS:
        raw_root = root / "data/raw/sim" / component
        raw_files = sorted(raw_root.glob("*.mat"))
        raw_ids = {path.stem for path in raw_files}
        target = target_units(root, component)
        holdout = holdout_units(root, component)
        overlap = (raw_ids & target) | (raw_ids & holdout)
        selected = sorted(raw_ids - target - holdout)
        if not selected:
            raise RuntimeError(f"empty untouched raw partition for {component}")
        exclusions[component] = {
            "raw_count": len(raw_ids),
            "target_unit_count": len(target),
            "existing_holdout_unit_count": len(holdout),
            "selected_count": len(selected),
            "raw_overlap_with_target_or_holdout": sorted(overlap),
        }
        for sample_id in selected:
            path = raw_root / f"{sample_id}.mat"
            rows.append({
                "sample_id": sample_id,
                "product_line": component,
                "raw_path": str(path.resolve()),
                "sha256": sha256(path),
                "selection_reason": "raw_sim_unit_absent_from_target_tensor_and_existing_holdout",
            })
    document = {
        "schema": SCHEMA,
        "created_utc": "2026-10-01T00:00:00Z",
        "root": str(root.resolve()),
        "semantic_labels_read": False,
        "selection_inputs": [
            "raw_sim_filenames",
            "raw_sim_file_sha256",
            "processed_target_unit_ids",
            "existing_holdout_manifest_unit_ids",
        ],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition"],
        "exclusions": exclusions,
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(document)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(hashlib.sha256(data).hexdigest() + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": hashlib.sha256(data).hexdigest(), "rows": len(rows), "exclusions": exclusions}, ensure_ascii=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
