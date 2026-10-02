#!/usr/bin/env python3
"""Freeze v8 BAT plus the already generated v7 RWA files by metadata only."""
from __future__ import annotations

import csv
import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


EXPECTED = {
    "bat": (
        ("BAT_LEO500_B00_H2_L3_S984", 780001, "BAT_LEO500_B00_H2_L3_S035"),
        ("BAT_LEO550_B30_H2_L3_S985", 780002, "BAT_LEO550_B30_H2_L3_S180"),
        ("BAT_LEO700_B60_H2_L3_S986", 780003, "BAT_LEO700_B60_H2_L3_S324"),
    ),
    "rwa": (
        ("RWA_LEO500_B00_H0_L1_S991", 760011, None),
        ("RWA_LEO550_B30_H0_L1_S992", 760012, None),
        ("RWA_LEO700_B60_H0_L1_S993", 760013, None),
    ),
}
FORBIDDEN = {
    "BAT_LEO500_B00_H2_L3_S961", "BAT_LEO550_B00_H2_L3_S962", "BAT_LEO700_B30_H2_L3_S963",
    "BAT_LEO500_B00_H2_L3_S981", "BAT_LEO550_B00_H2_L3_S982", "BAT_LEO700_B30_H2_L3_S983",
    "BAT_LEO500_B00_H2_L3_S996", "BAT_LEO550_B00_H2_L3_S997", "BAT_LEO700_B30_H2_L3_S998",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def read_manifest(path: Path) -> tuple[dict[str, dict[str, str]], str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    indexed = {row["sample_id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise RuntimeError(f"duplicate sample IDs: {path}")
    return indexed, sha256(path)


def read_source_cards(path: Path) -> dict[str, dict[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "brphm-f1-v8-source-card-manifest-v1":
        raise RuntimeError(f"source-card schema drift: {path}")
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError(f"source-card rows missing: {path}")
    indexed = {str(row["sample_id"]): row for row in rows}
    if len(indexed) != len(rows):
        raise RuntimeError(f"duplicate source-card IDs: {path}")
    return indexed


def main() -> int:
    bat_root = Path(sys.argv[1]).resolve()
    rwa_root = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    if output.exists():
        raise FileExistsError(output)
    roots = {"bat": bat_root, "rwa": rwa_root}
    files = []
    seed_values = []
    for component, specs in EXPECTED.items():
        root = roots[component]
        indexed, manifest_hash = read_manifest(root / "sim/logs/manifest.csv")
        source_cards = {}
        if component == "bat":
            source_cards = read_source_cards(root / "sim/logs/v8_source_card_manifest.json")
        expected_ids = {item[0] for item in specs}
        if set(indexed) != expected_ids:
            raise RuntimeError(f"manifest membership drift for {component}: {sorted(indexed)}")
        for sample_id, expected_seed, source_id in specs:
            if sample_id in FORBIDDEN:
                raise RuntimeError(f"forbidden repeated ID: {sample_id}")
            row = indexed[sample_id]
            if int(row["seed"]) != expected_seed:
                raise RuntimeError(f"seed drift for {sample_id}")
            if component == "bat":
                card = source_cards.get(sample_id)
                if not card or card.get("source_sample_id") != source_id or int(card.get("seed", -1)) != expected_seed:
                    raise RuntimeError(f"source card drift for {sample_id}")
                source_config = Path(str(card["source_config_path"]))
                generated_config = Path(str(card["generated_config_path"]))
                if sha256(source_config) != card.get("source_config_sha256"):
                    raise RuntimeError(f"source config hash drift for {sample_id}")
                if sha256(generated_config) != card.get("generated_config_sha256"):
                    raise RuntimeError(f"generated config hash drift for {sample_id}")
            raw = (root / "generated" / component / f"{sample_id}.mat").resolve()
            config = root / "configs_sim" / "sample" / f"{sample_id}.yaml"
            if not raw.is_file() or raw.stat().st_size <= 0 or not config.is_file():
                raise RuntimeError(f"missing generated artifact for {sample_id}")
            if row.get("out_mat", "").split("/")[-1] != raw.name:
                raise RuntimeError(f"output name drift for {sample_id}")
            seed_values.append(expected_seed)
            files.append({
                "sample_id": sample_id,
                "product_line": component,
                "orbit": row["orbit"],
                "seed": expected_seed,
                "source_sample_id": source_id,
                "raw_path": str(raw),
                "sha256": sha256(raw),
                "size": raw.stat().st_size,
                "config_path": str(config.resolve()),
                "config_sha256": sha256(config),
                "generator_manifest_path": str((root / "sim/logs/manifest.csv").resolve()),
                "generator_manifest_sha256": manifest_hash,
                "selection_reason": "predeclared_v8_ids_new_seeds_and_file_metadata_only_before_final_freeze",
            })
    if len(seed_values) != len(set(seed_values)):
        raise RuntimeError("seed collision inside v8 partition")
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    document = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "created_utc": now,
        "semantic_labels_read": False,
        "selection_inputs": ["predeclared_v8_sample_ids", "expected_new_seed_values", "file_existence", "file_size", "sha256", "config_yaml_sha256", "generator_manifest_sha256"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "v5_outputs", "v6_failed_partition", "v7_bat_duplicate_seed_outputs"],
        "source_trees": {component: str(path) for component, path in roots.items()},
        "historical_exclusion_ids": sorted(FORBIDDEN),
        "rows": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(document)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(files), "created_utc": now}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
