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
    output_rows = []
    with (root / "sim" / "logs" / "manifest.csv").open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    selected = []
    for component in ("bat", "rwa"):
        for orbit in ("LEO500", "LEO550", "LEO700"):
            candidates = [row for row in all_rows if row["line"] == component and row["orbit"] == orbit and row["fault_inject"] == "none"]
            candidates.sort(key=lambda row: (float(row["est_tf_days"]), row["sample_id"]), reverse=True)
            selected.append(candidates[0])
    for index, row in enumerate(selected, 1):
        old_id = row["sample_id"]
        new_id = re.sub(r"_S\d{3}$", f"_S{950 + index:03d}", old_id)
        component = row["line"]
        source_yaml = root / row["yaml"]
        target_yaml = gen / "configs_sim" / "sample" / f"{new_id}.yaml"
        text = source_yaml.read_text(encoding="utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {new_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {710000 + index}", text, flags=re.MULTILINE)
        if component == "bat":
            text = re.sub(r"^  bat\.aging_scale: .*?$", "  bat.aging_scale: 20.0", text, flags=re.MULTILINE)
            text = re.sub(r"^stop_time_max_s: .*?$", "stop_time_max_s: 400000", text, flags=re.MULTILINE)
            text = re.sub(r"^est_tf_days: .*?$", "est_tf_days: 2.5", text, flags=re.MULTILINE)
        target_yaml.write_text(text, encoding="utf-8")
        output = dict(row)
        output["sample_id"] = new_id
        output["yaml"] = f"configs/sim/sample/{new_id}.yaml"
        output["out_mat"] = f"data/raw/sim/{component}/{new_id}.mat"
        output["seed"] = str(710000 + index)
        if component == "bat":
            output["stop_time_s"] = "400000"
            output["est_tf_days"] = "2.5"
        output["queue_order"] = str(index)
        output_rows.append(output)
    manifest = gen / "sim" / "logs" / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print([(row["sample_id"], row["line"], row["orbit"], row["stop_time_s"]) for row in output_rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
