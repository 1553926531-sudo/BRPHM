#!/usr/bin/env python3
"""Build the fresh v11 mixed generator tree after v10 feasibility probing."""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re
import shutil
import stat
import sys

SPECS = (
    ("rwa", "LEO500", "RWA_LEO500_B00_H0_L1_S911", 891911, "RWA_LEO500_B00_H0_L1_S004", "48950", "0.2659"),
    ("rwa", "LEO550", "RWA_LEO550_B30_H0_L1_S912", 891912, "RWA_LEO550_B30_H0_L1_S146", "49140", "0.2670"),
    ("rwa", "LEO700", "RWA_LEO700_B60_H0_L1_S913", 891913, "RWA_LEO700_B60_H0_L1_S292", "49180", "0.2672"),
    ("bat", "LEO500", "BAT_LEO500_B60_H2_L3_S914", 891914, "BAT_LEO500_B60_H2_L3_S106", "1500000", "9.5"),
    ("bat", "LEO550", "BAT_LEO550_B60_H0_L2_S915", 891915, "BAT_LEO550_B60_H0_L2_S187", "1500000", "9.5"),
    ("bat", "LEO700", "BAT_LEO700_B30_H2_L1_S916", 891916, "BAT_LEO700_B30_H2_L1_S279", "1500000", "9.5"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    root = pathlib.Path(sys.argv[1]).resolve()
    source_tree = pathlib.Path(sys.argv[2]).resolve()
    gen = pathlib.Path(sys.argv[3]).resolve()
    if gen.exists():
        raise FileExistsError(gen)
    shutil.copytree(source_tree, gen, symlinks=True)
    configs = gen / "configs"
    configs.mkdir(exist_ok=True)
    link = configs / "sim"
    if link.is_symlink() or link.is_file():
        link.unlink()
    elif link.exists():
        if any(link.iterdir()):
            raise RuntimeError(f"unexpected non-empty configs/sim path: {link}")
        link.rmdir()
    link.symlink_to(pathlib.Path("../configs_sim"), target_is_directory=True)

    master_path = root / "sim/logs/manifest.csv"
    all_rows = list(csv.DictReader(master_path.open(newline="", encoding="utf-8")))
    by_id = {row["sample_id"]: row for row in all_rows}
    rows, cards = [], []
    for queue, (line, orbit, sample_id, seed, source_id, stop, est) in enumerate(SPECS, 1):
        source = by_id.get(source_id)
        if source is None or source["line"] != line or source["orbit"] != orbit:
            raise RuntimeError(f"source contract drift: {source_id}")
        if sample_id in by_id:
            raise RuntimeError(f"ID collision: {sample_id}")
        source_config = root / source["yaml"]
        original = source_config.read_bytes()
        text = original.decode("utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {sample_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
        if line == "bat":
            text = re.sub(r"^stop_time_max_s: .*?$", f"stop_time_max_s: {stop}", text, flags=re.MULTILINE)
        else:
            text = re.sub(r"^stop_time_s: .*?$", f"stop_time_s: {stop}", text, flags=re.MULTILINE)
        text = re.sub(r"^est_tf_days: .*?$", f"est_tf_days: {est}", text, flags=re.MULTILINE)
        config = gen / "configs_sim/sample" / f"{sample_id}.yaml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(text, encoding="utf-8")
        cards.append({"sample_id": sample_id, "line": line, "orbit": orbit, "seed": seed, "source_sample_id": source_id, "source_config_path": str(source_config), "source_config_sha256": digest(original), "generated_config_path": str(config), "generated_config_sha256": digest(config.read_bytes()), "semantic_labels_read": False})
        row = dict(source)
        row.update({"sample_id": sample_id, "yaml": f"configs/sim/sample/{sample_id}.yaml", "out_mat": f"data/raw/sim/{line}/{sample_id}.mat", "seed": str(seed), "stop_time_s": stop, "est_tf_days": est, "queue_order": str(queue)})
        rows.append(row)
    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    card_path = gen / "sim/logs/v11_source_card_manifest.json"
    card_path.write_text(json.dumps({"schema": "brphm-f1-v11-source-card-manifest-v1", "semantic_labels_read": False, "master_manifest_path": str(master_path), "master_manifest_sha256": digest(master_path.read_bytes()), "rows": cards}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    card_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"generator": str(gen), "manifest": str(manifest), "source_cards": str(card_path), "rows": rows}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
