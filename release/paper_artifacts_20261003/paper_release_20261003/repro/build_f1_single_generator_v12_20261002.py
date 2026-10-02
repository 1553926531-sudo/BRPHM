#!/usr/bin/env python3
"""Build one isolated BAT generator tree with an orbit-aligned stop bound.

The v11 builder passed the nominal BAT stop-time ceiling verbatim.  BAT
simulation requires the actual stop time to be an integer multiple of the
5740-second orbit period, so this builder records both the requested ceiling
and its deterministic floor-aligned effective value.
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


BAT_ORBIT_S = 5740


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    # root source_tree gen line orbit new_id seed source_id stop est
    root, source_tree, gen = map(lambda s: pathlib.Path(s).resolve(), sys.argv[1:4])
    line, orbit, new_id, seed, source_id, stop, est = sys.argv[4:11]
    seed = int(seed)
    requested_stop = int(float(stop))
    if line != "bat":
        raise RuntimeError("v12 builder is restricted to BAT diagnostic units")
    effective_stop = (requested_stop // BAT_ORBIT_S) * BAT_ORBIT_S
    if effective_stop <= 0 or effective_stop % BAT_ORBIT_S:
        raise RuntimeError("invalid orbit-aligned BAT stop time")
    if gen.exists():
        raise FileExistsError(gen)
    shutil.copytree(source_tree, gen, symlinks=True)
    inherited = gen / "generated"
    if inherited.exists():
        shutil.rmtree(inherited)
    configs = gen / "configs"
    configs.mkdir(exist_ok=True)
    link = configs / "sim"
    if link.is_symlink() or link.is_file():
        link.unlink()
    elif link.exists():
        if any(link.iterdir()):
            raise RuntimeError(f"non-empty configs/sim: {link}")
        link.rmdir()
    link.symlink_to(pathlib.Path("../configs_sim"), target_is_directory=True)

    master = root / "sim/logs/manifest.csv"
    rows = list(csv.DictReader(master.open(newline="", encoding="utf-8")))
    by_id = {r["sample_id"]: r for r in rows}
    source = by_id.get(source_id)
    if source is None or source["line"] != line or source["orbit"] != orbit:
        raise RuntimeError(f"source contract drift: {source_id}")
    config_src = root / source["yaml"]
    original = config_src.read_bytes()
    text = original.decode("utf-8")
    text = re.sub(r"^sample_id: .*?$", f"sample_id: {new_id}", text, flags=re.MULTILINE)
    text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
    text = re.sub(r"^stop_time_max_s: .*?$", f"stop_time_max_s: {effective_stop}", text, flags=re.MULTILINE)
    text = re.sub(r"^est_tf_days: .*?$", f"est_tf_days: {est}", text, flags=re.MULTILINE)
    config = gen / "configs_sim/sample" / f"{new_id}.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(text, encoding="utf-8")
    row = dict(source)
    row.update({
        "sample_id": new_id,
        "yaml": f"configs/sim/sample/{new_id}.yaml",
        "out_mat": f"data/raw/sim/{line}/{new_id}.mat",
        "seed": str(seed),
        "stop_time_s": str(effective_stop),
        "est_tf_days": est,
        "queue_order": "1",
    })
    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerow(row)
    card = gen / "sim/logs/single_source_card.json"
    card.write_text(json.dumps({
        "schema": "brphm-f1-single-source-card-v2",
        "semantic_labels_read": False,
        "inherited_generated_removed": True,
        "stop_time_contract": {
            "orbit_period_s": BAT_ORBIT_S,
            "requested_stop_time_max_s": requested_stop,
            "effective_stop_time_max_s": effective_stop,
            "alignment": "floor_to_integer_orbit",
        },
        "row": {
            "sample_id": new_id,
            "line": line,
            "orbit": orbit,
            "seed": seed,
            "source_sample_id": source_id,
            "source_config_path": str(config_src),
            "source_config_sha256": digest(original),
            "generated_config_path": str(config),
            "generated_config_sha256": digest(config.read_bytes()),
        },
    }, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    card.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({
        "generator": str(gen),
        "manifest": str(manifest),
        "sample_id": new_id,
        "requested_stop_time_max_s": requested_stop,
        "effective_stop_time_max_s": effective_stop,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
