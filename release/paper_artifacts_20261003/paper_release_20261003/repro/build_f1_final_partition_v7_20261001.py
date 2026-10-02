#!/usr/bin/env python3
"""Freeze v7 raw-unit membership using file metadata only; never parse MATs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import stat
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = {
    "bat_main": ("BAT_LEO500_B00_H2_L3_S981", "BAT_LEO550_B00_H2_L3_S982"),
    "bat_s983": ("BAT_LEO700_B30_H2_L3_S983",),
    "rwa": ("RWA_LEO500_B00_H0_L1_S991", "RWA_LEO550_B30_H0_L1_S992", "RWA_LEO700_B60_H0_L1_S993"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_manifest(path: Path) -> tuple[dict[str, dict[str, str]], str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    indexed = {row["sample_id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise RuntimeError(f"duplicate sample IDs in generator manifest: {path}")
    return indexed, sha256(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bat-main", type=Path, required=True, help="v7 S981/S982 tree root")
    parser.add_argument("--bat-s983", type=Path, required=True, help="v7 isolated S983 tree root")
    parser.add_argument("--rwa", type=Path, required=True, help="v7 RWA tree root")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)

    roots = {
        "bat_main": args.bat_main.resolve(),
        "bat_s983": args.bat_s983.resolve(),
        "rwa": args.rwa.resolve(),
    }
    indexed_manifests = {}
    for label, root in roots.items():
        manifest = root / "sim/logs/manifest.csv"
        indexed_manifests[label] = read_manifest(manifest)
        got = set(indexed_manifests[label][0])
        if got != set(EXPECTED[label]):
            raise RuntimeError(f"{label} manifest membership drift: {sorted(got)}")

    files = []
    for label, sample_ids in EXPECTED.items():
        root = roots[label]
        manifest_rows, manifest_hash = indexed_manifests[label]
        component = "rwa" if label == "rwa" else "bat"
        for sample_id in sample_ids:
            row = manifest_rows[sample_id]
            raw = (root / "generated" / component / f"{sample_id}.mat").resolve()
            config = root / "configs_sim" / "sample" / f"{sample_id}.yaml"
            if not raw.is_file() or raw.stat().st_size <= 0:
                raise RuntimeError(f"missing or empty raw file: {sample_id}")
            if not config.is_file():
                raise RuntimeError(f"missing unit configuration: {sample_id}")
            if row.get("out_mat", "").split("/")[-1] != raw.name:
                raise RuntimeError(f"manifest output name drift: {sample_id}")
            files.append({
                "sample_id": sample_id,
                "product_line": component,
                "orbit": row["orbit"],
                "seed": int(row["seed"]),
                "raw_path": str(raw),
                "sha256": sha256(raw),
                "size": raw.stat().st_size,
                "config_path": str(config.resolve()),
                "config_sha256": sha256(config),
                "generator_manifest_path": str((root / "sim/logs/manifest.csv").resolve()),
                "generator_manifest_sha256": manifest_hash,
                "selection_reason": "predeclared_v7_unit_id_and_file_metadata_only_before_final_freeze",
            })

    now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    document = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "created_utc": now,
        "semantic_labels_read": False,
        "selection_inputs": ["predeclared_v7_sample_ids", "file_existence", "file_size", "sha256", "config_yaml_sha256", "generator_manifest_sha256"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "v5_outputs", "v6_failed_partition", "parallel_duplicate_RWA_diagnostics"],
        "source_trees": {label: str(path) for label, path in roots.items()},
        "rows": files,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(document)
    args.output.write_bytes(data)
    args.output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = args.output.with_suffix(args.output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + args.output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(args.output), "sha256": digest, "rows": len(files), "created_utc": now}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
