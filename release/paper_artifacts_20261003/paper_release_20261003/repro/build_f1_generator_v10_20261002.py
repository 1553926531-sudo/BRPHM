#!/usr/bin/env python3
"""Build an isolated mixed RWA/BAT generator tree with fresh IDs and seeds.

Only registered YAML configuration text and the master manifest are read.
No raw MAT payload or semantic label is read during this build step.
"""
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
    # line, orbit, new id, seed, source id, stop override, est override
    ("rwa", "LEO500", "RWA_LEO500_B00_H0_L1_S901", 890901, "RWA_LEO500_B00_H0_L1_S004", "48950", "0.2659"),
    ("rwa", "LEO550", "RWA_LEO550_B30_H0_L1_S902", 890902, "RWA_LEO550_B30_H0_L1_S146", "49140", "0.2670"),
    ("rwa", "LEO700", "RWA_LEO700_B60_H0_L1_S903", 890903, "RWA_LEO700_B60_H0_L1_S292", "49180", "0.2672"),
    ("bat", "LEO500", "BAT_LEO500_B60_H2_L3_S904", 890904, "BAT_LEO500_B60_H2_L3_S106", "1500000", "9.5"),
    ("bat", "LEO550", "BAT_LEO550_B60_H0_L2_S905", 890905, "BAT_LEO550_B60_H0_L2_S187", "1500000", "9.5"),
    ("bat", "LEO700", "BAT_LEO700_B30_H2_L1_S906", 890906, "BAT_LEO700_B30_H2_L1_S279", "1500000", "9.5"),
)


def sha256_bytes(data: bytes) -> str:
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
    if len(by_id) != len(all_rows):
        raise RuntimeError("master manifest has duplicate sample IDs")
    output_rows = []
    cards = []
    for queue, (line, orbit, sample_id, seed, source_id, stop, est) in enumerate(SPECS, 1):
        if sample_id in by_id:
            raise RuntimeError(f"new ID collides with registered master: {sample_id}")
        source_row = by_id.get(source_id)
        if source_row is None or source_row["line"] != line or source_row["orbit"] != orbit:
            raise RuntimeError(f"source contract drift: {source_id}")
        source_config = root / source_row["yaml"]
        original = source_config.read_bytes()
        text = original.decode("utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {sample_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
        if line == "bat":
            text = re.sub(r"^stop_time_max_s: .*?$", f"stop_time_max_s: {stop}", text, flags=re.MULTILINE)
        else:
            text = re.sub(r"^stop_time_s: .*?$", f"stop_time_s: {stop}", text, flags=re.MULTILINE)
        text = re.sub(r"^est_tf_days: .*?$", f"est_tf_days: {est}", text, flags=re.MULTILINE)
        config_path = gen / "configs_sim" / "sample" / f"{sample_id}.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(text, encoding="utf-8")
        cards.append({
            "sample_id": sample_id, "line": line, "orbit": orbit, "seed": seed,
            "source_sample_id": source_id,
            "source_config_path": str(source_config), "source_config_sha256": sha256_bytes(original),
            "generated_config_path": str(config_path), "generated_config_sha256": sha256_bytes(config_path.read_bytes()),
            "semantic_labels_read": False,
        })
        output = dict(source_row)
        output.update({
            "sample_id": sample_id, "yaml": f"configs/sim/sample/{sample_id}.yaml",
            "out_mat": f"data/raw/sim/{line}/{sample_id}.mat", "seed": str(seed),
            "stop_time_s": stop, "est_tf_days": est, "queue_order": str(queue),
        })
        output_rows.append(output)

    manifest = gen / "sim/logs/manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    card_path = gen / "sim/logs/v10_source_card_manifest.json"
    card_doc = {"schema": "brphm-f1-v10-source-card-manifest-v1", "semantic_labels_read": False,
                "master_manifest_path": str(master_path), "master_manifest_sha256": sha256_bytes(master_path.read_bytes()),
                "rows": cards}
    card_path.write_text(json.dumps(card_doc, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    card_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"generator": str(gen), "manifest": str(manifest), "source_cards": str(card_path), "rows": output_rows}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
