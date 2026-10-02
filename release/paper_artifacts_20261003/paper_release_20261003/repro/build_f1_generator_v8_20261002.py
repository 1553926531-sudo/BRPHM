#!/usr/bin/env python3
"""Build the v8 BAT generator tree with new seeds and registered cards."""
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
    ("LEO500", "BAT_LEO500_B00_H2_L3_S984", 780001, "BAT_LEO500_B00_H2_L3_S035"),
    ("LEO550", "BAT_LEO550_B30_H2_L3_S985", 780002, "BAT_LEO550_B30_H2_L3_S180"),
    ("LEO700", "BAT_LEO700_B60_H2_L3_S986", 780003, "BAT_LEO700_B60_H2_L3_S324"),
)


def main() -> int:
    root = pathlib.Path(sys.argv[1]).resolve()
    source = pathlib.Path(sys.argv[2]).resolve()
    gen = pathlib.Path(sys.argv[3]).resolve()
    if gen.exists():
        raise FileExistsError(gen)
    shutil.copytree(source, gen, symlinks=True)

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

    all_rows = list(csv.DictReader((root / "sim/logs/manifest.csv").open(
        newline="", encoding="utf-8")))
    by_id = {row["sample_id"]: row for row in all_rows}
    output_rows = []
    source_cards = []
    for queue, (orbit, sample_id, seed, source_id) in enumerate(SPECS, 1):
        if source_id not in by_id:
            raise RuntimeError(f"registered source card missing: {source_id}")
        source_row = by_id[source_id]
        if (source_row["line"], source_row["orbit"], source_row["fault_inject"]) != ("bat", orbit, "none"):
            raise RuntimeError(f"source card contract drift: {source_id}")
        source_config = root / source_row["yaml"]
        original = source_config.read_bytes()
        text = original.decode("utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {sample_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
        config_path = gen / "configs_sim" / "sample" / f"{sample_id}.yaml"
        config_path.write_text(text, encoding="utf-8")
        source_cards.append({
            "sample_id": sample_id,
            "seed": seed,
            "source_sample_id": source_id,
            "source_config_path": str(source_config.resolve()),
            "source_config_sha256": hashlib.sha256(original).hexdigest(),
            "generated_config_path": str(config_path.resolve()),
            "generated_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        })
        output = dict(source_row)
        output.update({
            "sample_id": sample_id,
            "yaml": f"configs/sim/sample/{sample_id}.yaml",
            "out_mat": f"data/raw/sim/bat/{sample_id}.mat",
            "seed": str(seed),
            "queue_order": str(queue),
        })
        output_rows.append(output)

    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    sidecar = gen / "sim/logs/v8_source_card_manifest.json"
    sidecar.write_text(json.dumps({
        "schema": "brphm-f1-v8-source-card-manifest-v1",
        "semantic_labels_read": False,
        "rows": source_cards,
    }, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print([(row["sample_id"], row["seed"], row["stop_time_s"])
           for row in output_rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
