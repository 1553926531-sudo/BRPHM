#!/usr/bin/env python3
from __future__ import annotations

import csv
import pathlib
import re
import shutil
import sys

import torch


def main() -> int:
    root = pathlib.Path(sys.argv[1]).resolve()
    gen = pathlib.Path(sys.argv[2]).resolve()
    if gen.exists():
        raise FileExistsError(gen)
    gen.mkdir(parents=True)
    shutil.copytree(root / "sim", gen / "sim", symlinks=True)
    shutil.copytree(root / "configs" / "sim", gen / "configs_sim", symlinks=True)
    (gen / "configs").mkdir()
    (gen / "configs" / "sim").symlink_to(gen / "configs_sim", target_is_directory=True)
    (gen / "src").symlink_to(root / "src", target_is_directory=True)
    (gen / "data").symlink_to(root / "data", target_is_directory=True)

    with (root / "sim" / "logs" / "manifest.csv").open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    target = {}
    for component in ("bat", "rwa"):
        payload = torch.load(root / "data" / "processed" / f"{component}_target.pt", map_location="cpu", weights_only=False)
        target[component] = {row["unit_id"] for row in payload["meta"]["index"]}

    chosen = []
    for component in ("bat", "rwa"):
        for orbit in ("LEO500", "LEO550", "LEO700"):
            candidates = [
                row for row in all_rows
                if row["line"] == component
                and row["orbit"] == orbit
                and row["sample_id"] in target[component]
                and row["fault_inject"] == "none"
            ]
            candidates.sort(key=lambda row: (float(row["est_tf_days"]), row["sample_id"]), reverse=True)
            chosen.extend(candidates[:2])
    if len(chosen) != 12:
        raise RuntimeError(f"expected 12 source cards, got {len(chosen)}")

    output_rows = []
    for index, row in enumerate(chosen, 1):
        old_id = row["sample_id"]
        new_id = re.sub(r"_S\d{3}$", f"_S{900 + index:03d}", old_id)
        component = row["line"]
        source_yaml = root / row["yaml"]
        target_yaml = gen / "configs_sim" / "sample" / f"{new_id}.yaml"
        text = source_yaml.read_text(encoding="utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {new_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {700000 + index}", text, flags=re.MULTILINE)
        target_yaml.write_text(text, encoding="utf-8")
        output = dict(row)
        output["sample_id"] = new_id
        output["yaml"] = f"configs/sim/sample/{new_id}.yaml"
        output["out_mat"] = f"data/raw/sim/{component}/{new_id}.mat"
        output["seed"] = str(700000 + index)
        output["queue_order"] = str(index)
        output_rows.append(output)

    manifest = gen / "sim" / "logs" / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print({"chosen": [(row["sample_id"], row["line"], row["orbit"], row["est_tf_days"]) for row in chosen], "manifest": str(manifest)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
