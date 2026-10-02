#!/usr/bin/env python3
"""Create a metadata-only v11 six-unit partition after generation completes."""
from __future__ import annotations

import csv
import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = (
    ("RWA_LEO500_B00_H0_L1_S911", "rwa", "LEO500", 891911),
    ("RWA_LEO550_B30_H0_L1_S912", "rwa", "LEO550", 891912),
    ("RWA_LEO700_B60_H0_L1_S913", "rwa", "LEO700", 891913),
    ("BAT_LEO500_B60_H2_L3_S914", "bat", "LEO500", 891914),
    ("BAT_LEO550_B60_H0_L2_S915", "bat", "LEO550", 891915),
    ("BAT_LEO700_B30_H2_L1_S916", "bat", "LEO700", 891916),
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
    root = Path(sys.argv[1]).resolve()
    gen = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = gen / "sim/logs/manifest.csv"
    cards_path = gen / "sim/logs/v11_source_card_manifest.json"
    rows = {r["sample_id"]: r for r in csv.DictReader(manifest.open(newline="", encoding="utf-8"))}
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    if cards.get("schema") != "brphm-f1-v11-source-card-manifest-v1" or cards.get("semantic_labels_read") is not False:
        raise RuntimeError("source-card contract drift")
    card_index = {r["sample_id"]: r for r in cards.get("rows", [])}
    if set(rows) != {x[0] for x in EXPECTED}:
        raise RuntimeError(f"manifest membership drift: {sorted(rows)}")
    out_rows = []
    seeds = []
    for uid, component, orbit, seed in EXPECTED:
        row = rows[uid]
        if row["line"] != component or row["orbit"] != orbit or int(row["seed"]) != seed:
            raise RuntimeError(f"manifest row drift: {uid}")
        card = card_index.get(uid)
        if not card or int(card.get("seed", -1)) != seed or card.get("line") != component:
            raise RuntimeError(f"source-card drift: {uid}")
        config = gen / "configs_sim/sample" / f"{uid}.yaml"
        raw = gen / "generated" / component / f"{uid}.mat"
        if not config.is_file() or not raw.is_file() or raw.stat().st_size <= 0:
            raise RuntimeError(f"missing artifact: {uid}")
        if sha256(config) != card.get("generated_config_sha256"):
            raise RuntimeError(f"config hash drift: {uid}")
        if row["out_mat"].split("/")[-1] != raw.name:
            raise RuntimeError(f"output name drift: {uid}")
        seeds.append(seed)
        out_rows.append({
            "sample_id": uid, "product_line": component, "orbit": orbit, "seed": seed,
            "source_sample_id": card.get("source_sample_id"), "raw_path": str(raw),
            "sha256": sha256(raw), "size": raw.stat().st_size,
            "config_path": str(config), "config_sha256": sha256(config),
            "generator_manifest_path": str(manifest), "generator_manifest_sha256": sha256(manifest),
            "source_card_manifest_path": str(cards_path), "source_card_manifest_sha256": sha256(cards_path),
            "selection_reason": "predeclared_v11_fresh_ids_and_file_metadata_only_before_final_freeze",
        })
    if len(seeds) != len(set(seeds)):
        raise RuntimeError("seed collision")
    doc = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "semantic_labels_read": False,
        "selection_inputs": ["predeclared_v11_ids", "fresh_seed_values", "file_existence", "file_size", "sha256", "config_yaml_sha256", "generator_manifest_sha256", "source_card_manifest_sha256"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "v8/v9 burned partitions", "v10 diagnostic probe units"],
        "source_tree": str(gen), "rows": sorted(out_rows, key=lambda r: r["sample_id"]),
    }
    data = canon(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(out_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
