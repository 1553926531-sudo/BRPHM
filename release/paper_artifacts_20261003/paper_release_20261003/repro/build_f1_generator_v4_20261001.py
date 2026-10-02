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
    rows = []
    with (root / "sim" / "logs" / "manifest.csv").open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    for index, orbit in enumerate(("LEO500", "LEO550", "LEO700"), 1):
        candidates = [row for row in all_rows if row["line"] == "bat" and row["orbit"] == orbit and row["fault_inject"] == "none"]
        candidates.sort(key=lambda row: (float(row["est_tf_days"]), row["sample_id"]), reverse=True)
        row = candidates[0]
        old_id = row["sample_id"]
        new_id = re.sub(r"_S\d{3}$", f"_S{990 + index:03d}", old_id)
        target_yaml = gen / "configs_sim" / "sample" / f"{new_id}.yaml"
        text = (root / row["yaml"]).read_text(encoding="utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {new_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {730000 + index}", text, flags=re.MULTILINE)
        text = re.sub(r"^  bat\.aging_scale: .*?$", "  bat.aging_scale: 2.0", text, flags=re.MULTILINE)
        text = re.sub(r"^stop_time_max_s: .*?$", "stop_time_max_s: 57400", text, flags=re.MULTILINE)
        text = re.sub(r"^est_tf_days: .*?$", "est_tf_days: 0.40", text, flags=re.MULTILINE)
        target_yaml.write_text(text, encoding="utf-8")
        out = dict(row)
        out.update({"sample_id": new_id, "yaml": f"configs/sim/sample/{new_id}.yaml", "out_mat": f"data/raw/sim/bat/{new_id}.mat", "seed": str(730000 + index), "stop_time_s": "57400", "est_tf_days": "0.40", "queue_order": str(index)})
        rows.append(out)
    manifest = gen / "sim" / "logs" / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print([(row["sample_id"], row["orbit"], row["stop_time_s"]) for row in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
