#!/usr/bin/env python3
"""Build the unprobed v13 F1 partition from six clean generator trees."""
from __future__ import annotations

import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


EXPECTED = (
    ("RWA_LEO500_B00_H0_L1_S919", "rwa", "LEO500", 891919, "RWA_LEO500_B00_H0_L1_S004"),
    ("RWA_LEO550_B30_H0_L1_S920", "rwa", "LEO550", 891920, "RWA_LEO550_B30_H0_L1_S146"),
    ("RWA_LEO700_B60_H0_L1_S921", "rwa", "LEO700", 891921, "RWA_LEO700_B60_H0_L1_S292"),
    ("BAT_LEO500_B60_H2_L3_S930", "bat", "LEO500", 891930, "BAT_LEO500_B60_H2_L3_S106"),
    ("BAT_LEO550_B60_H0_L2_S923", "bat", "LEO550", 891923, "BAT_LEO550_B60_H0_L2_S187"),
    ("BAT_LEO700_B30_H2_L1_S924", "bat", "LEO700", 891924, "BAT_LEO700_B30_H2_L1_S279"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canon(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> int:
    if len(sys.argv) != 9:
        raise SystemExit("usage: build_f1_final_partition_v13_20261002.py ROOT S919 S920 S921 S922 S923 S924 DIAGNOSTIC_PROBE")
    root = Path(sys.argv[1]).resolve()
    trees = {uid: Path(tree).resolve() for (uid, *_), tree in zip(EXPECTED, sys.argv[2:8])}
    probe = Path(sys.argv[8]).resolve()
    output = root / "work/f1_final_partition_v13_20261002/partition_manifest.json"
    if output.exists():
        raise FileExistsError(output)
    probe_doc = json.loads(probe.read_text(encoding="utf-8"))
    if probe_doc.get("schema") != "brphm-f1-development-feasibility-probe-v2" or probe_doc.get("diagnostic_only") is not True or probe_doc.get("all_touched_units_excluded_from_future_final_partitions") is not True:
        raise RuntimeError("diagnostic probe does not prove burn/exclusion")
    rows = []
    for uid, component, orbit, seed, source_uid in EXPECTED:
        tree = trees[uid]
        card_path = tree / "sim/logs/single_source_card.json"
        card_doc = json.loads(card_path.read_text(encoding="utf-8"))
        if card_doc.get("schema") not in {"brphm-f1-single-source-card-v1", "brphm-f1-single-source-card-v2"} or card_doc.get("semantic_labels_read") is not False:
            raise RuntimeError(f"source-card contract drift: {uid}")
        card = card_doc.get("row") or {}
        if card.get("sample_id") != uid or card.get("line") != component or card.get("orbit") != orbit or int(card.get("seed", -1)) != seed or card.get("source_sample_id") != source_uid:
            raise RuntimeError(f"source binding drift: {uid}")
        config = Path(card["generated_config_path"])
        if not config.is_file() or sha256(config) != card.get("generated_config_sha256"):
            raise RuntimeError(f"config hash drift: {uid}")
        raw = tree / "generated" / component / f"{uid}.mat"
        if not raw.is_file() or raw.stat().st_size <= 0:
            raise RuntimeError(f"missing fresh raw output: {uid}")
        rows.append({
            "sample_id": uid, "product_line": component, "orbit": orbit, "seed": seed,
            "raw_path": str(raw), "sha256": sha256(raw), "size": raw.stat().st_size,
            "config_path": str(config), "config_sha256": sha256(config),
            "source_sample_id": source_uid, "source_config_sha256": card.get("source_config_sha256"),
            "source_card_path": str(card_path), "source_card_sha256": sha256(card_path),
            "selection_reason": "predeclared_v13_fresh_id_after_diagnostic_burn; metadata_only",
        })
    doc = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "partition_id": "f1_final_partition_v13_20261002",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "semantic_labels_read": False,
        "final_label_access": False,
        "diagnostic_probe": {"path": str(probe), "sha256": sha256(probe), "burned_unit_count": len(probe_doc.get("results", []))},
        "selection_inputs": ["predeclared_v13_ids", "source_card_schema_and_hash", "config_hash", "raw_file_existence_size_sha256", "diagnostic_probe_burn_hash"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "v8/v9 burned partitions", "all S911-S918 and S928-S929 diagnostic units"],
        "rows": sorted(rows, key=lambda r: r["sample_id"]),
    }
    payload = canon(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(payload).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
