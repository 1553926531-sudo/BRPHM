#!/usr/bin/env python3
from __future__ import annotations

import csv
import pathlib
import re
import shutil
import sys


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
            raise RuntimeError(f"non-empty configs/sim: {link}")
        link.rmdir()
    link.symlink_to(pathlib.Path("../configs_sim"), target_is_directory=True)
    all_rows = list(csv.DictReader((root / "sim/logs/manifest.csv").open(newline="", encoding="utf-8")))
    specs = [
        ("bat", "LEO500", "S981", 740001),
        ("bat", "LEO550", "S982", 740002),
        ("bat", "LEO700", "S983", 740003),
        ("rwa", "LEO500", "S991", 760011),
        ("rwa", "LEO550", "S992", 760012),
        ("rwa", "LEO700", "S993", 760013),
    ]
    output_rows = []
    for queue, (line, orbit, suffix, seed) in enumerate(specs, 1):
        candidates = [row for row in all_rows if row["line"] == line and row["orbit"] == orbit and row["fault_inject"] == "none"]
        candidates.sort(key=lambda row: (float(row["est_tf_days"]), row["sample_id"]), reverse=(line == "rwa"))
        row = candidates[0]
        sample_id = re.sub(r"_S\d{3}$", f"_{suffix}", row["sample_id"])
        stop = "401800" if line == "bat" else row["stop_time_s"]
        est = "4.65" if line == "bat" else row["est_tf_days"]
        text = (root / row["yaml"]).read_text(encoding="utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {sample_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
        text = re.sub(r"^stop_time_max_s: .*?$", f"stop_time_max_s: {stop}", text, flags=re.MULTILINE)
        text = re.sub(r"^est_tf_days: .*?$", f"est_tf_days: {est}", text, flags=re.MULTILINE)
        (gen / "configs_sim" / "sample" / f"{sample_id}.yaml").write_text(text, encoding="utf-8")
        out = dict(row)
        out.update(sample_id=sample_id, yaml=f"configs/sim/sample/{sample_id}.yaml",
                   out_mat=f"data/raw/sim/{line}/{sample_id}.mat", seed=str(seed),
                   stop_time_s=stop, est_tf_days=est, queue_order=str(queue))
        output_rows.append(out)
    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print([(row["sample_id"], row["seed"], row["stop_time_s"]) for row in output_rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
