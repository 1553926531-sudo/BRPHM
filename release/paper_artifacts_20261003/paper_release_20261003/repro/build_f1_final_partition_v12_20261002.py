#!/usr/bin/env python3
"""Build the v12 F1 partition from separate, hash-bound generator trees.

This is metadata-only: it hashes files and validates pre-registered cards. It
never opens a MAT payload semantically, and it refuses burned or stale IDs.
"""
from __future__ import annotations

import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


EXPECTED = (
    ("RWA_LEO500_B00_H0_L1_S911", "rwa", "LEO500", 891911, "mixed"),
    ("RWA_LEO550_B30_H0_L1_S912", "rwa", "LEO550", 891912, "mixed"),
    ("RWA_LEO700_B60_H0_L1_S913", "rwa", "LEO700", 891913, "mixed"),
    ("BAT_LEO500_B60_H2_L3_S929", "bat", "LEO500", 891929, "s929"),
    ("BAT_LEO550_B60_H0_L2_S917", "bat", "LEO550", 891917, "s917"),
    ("BAT_LEO700_B30_H2_L1_S928", "bat", "LEO700", 891928, "s928"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canon(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_card(tree: Path, source: str) -> tuple[dict, Path]:
    if source == "mixed":
        path = tree / "sim/logs/v11_source_card_manifest.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != "brphm-f1-v11-source-card-manifest-v1" or doc.get("semantic_labels_read") is not False:
            raise RuntimeError("mixed source-card contract drift")
        return {r["sample_id"]: r for r in doc.get("rows", [])}, path
    path = tree / "sim/logs/single_source_card.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") not in {"brphm-f1-single-source-card-v1", "brphm-f1-single-source-card-v2"} or doc.get("semantic_labels_read") is not False:
        raise RuntimeError(f"single source-card contract drift: {path}")
    row = dict(doc.get("row") or {})
    return {row["sample_id"]: row}, path


def main() -> int:
    if len(sys.argv) != 7:
        raise SystemExit("usage: build_f1_final_partition_v12_20261002.py ROOT MIXED_TREE S917_TREE S928_TREE S929_TREE OUTPUT")
    root, mixed, s917, s928, s929 = (Path(x).resolve() for x in sys.argv[1:6])
    output = Path(sys.argv[6]).resolve()
    if output.exists():
        raise FileExistsError(output)
    trees = {"mixed": mixed, "s917": s917, "s928": s928, "s929": s929}
    card_cache = {name: load_card(tree, name) for name, tree in trees.items()}
    rows = []
    for uid, component, orbit, seed, source in EXPECTED:
        tree = trees[source]
        cards, card_path = card_cache[source]
        card = cards.get(uid)
        if not card:
            raise RuntimeError(f"missing source card: {uid}")
        if card.get("line", card.get("row", {}).get("line")) != component:
            raise RuntimeError(f"component drift: {uid}")
        if card.get("orbit", card.get("row", {}).get("orbit")) != orbit:
            raise RuntimeError(f"orbit drift: {uid}")
        actual_seed = card.get("seed", card.get("row", {}).get("seed"))
        if int(actual_seed) != seed:
            raise RuntimeError(f"seed drift: {uid}")
        config_path = Path(card.get("generated_config_path", card.get("row", {}).get("generated_config_path", "")))
        if not config_path.is_file() or sha256(config_path) != card.get("generated_config_sha256", card.get("row", {}).get("generated_config_sha256")):
            raise RuntimeError(f"config hash drift: {uid}")
        raw = tree / "generated" / component / f"{uid}.mat"
        if not raw.is_file() or raw.stat().st_size <= 0:
            raise RuntimeError(f"missing fresh raw output: {uid}")
        rows.append({
            "sample_id": uid,
            "product_line": component,
            "orbit": orbit,
            "seed": seed,
            "raw_path": str(raw),
            "sha256": sha256(raw),
            "size": raw.stat().st_size,
            "config_path": str(config_path),
            "config_sha256": sha256(config_path),
            "source_sample_id": card.get("source_sample_id", card.get("row", {}).get("source_sample_id")),
            "source_config_sha256": card.get("source_config_sha256", card.get("row", {}).get("source_config_sha256")),
            "source_card_path": str(card_path),
            "source_card_sha256": sha256(card_path),
            "selection_reason": "predeclared_v12_id_and_hash_bound_source_card; metadata_only",
        })
    if len({r["sample_id"] for r in rows}) != len(EXPECTED):
        raise RuntimeError("duplicate sample IDs")
    doc = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "partition_id": "f1_final_partition_v12_20261002",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "semantic_labels_read": False,
        "final_label_access": False,
        "selection_inputs": ["predeclared_v12_unit_ids", "source_card_schema", "source_card_hash", "config_hash", "raw_file_existence_size_sha256"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "v8/v9 burned partitions", "v10 diagnostic units", "aborted S915/S916 trees"],
        "rows": sorted(rows, key=lambda r: r["sample_id"]),
    }
    payload = canon(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
