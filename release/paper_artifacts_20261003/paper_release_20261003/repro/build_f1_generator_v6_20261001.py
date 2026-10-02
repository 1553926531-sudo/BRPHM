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
    # copytree may materialize the source tree's relative configs link as an
    # empty directory.  The simulator resolves manifest YAMLs through
    # configs/sim, so restore that link explicitly in every fresh tree.
    configs_dir = gen / "configs"
    configs_dir.mkdir(exist_ok=True)
    sim_link = configs_dir / "sim"
    # ``Path.exists()`` follows symlinks, so a stale link to another tree
    # looks present and would silently bypass the intended per-tree config.
    # Remove any link explicitly, and reject a real non-empty directory.
    if sim_link.is_symlink():
        sim_link.unlink()
    elif sim_link.exists():
        if any(sim_link.iterdir()):
            raise RuntimeError(f"unexpected non-empty configs/sim path: {sim_link}")
        sim_link.rmdir()
    sim_link.symlink_to(pathlib.Path("../configs_sim"), target_is_directory=True)
    all_rows = list(csv.DictReader((root / "sim/logs/manifest.csv").open(newline="", encoding="utf-8")))
    rows = []
    # BAT cards need the deliberately accelerated high-aging configuration used
    # by the prior development probe; RWA cards use the longest registered
    # non-injected horizon so the generated raw files contain finite labels.
    specs = [
        ("bat", "LEO500", "S961", 750001),
        ("bat", "LEO550", "S962", 750002),
        ("bat", "LEO700", "S963", 750003),
        ("rwa", "LEO500", "S971", 750011),
        ("rwa", "LEO550", "S972", 750012),
        ("rwa", "LEO700", "S973", 750013),
    ]
    for index, (line, orbit, suffix, seed) in enumerate(specs, 1):
        candidates = [row for row in all_rows if row["line"] == line and row["orbit"] == orbit and row["fault_inject"] == "none"]
        candidates.sort(key=lambda row: (float(row["est_tf_days"]), row["sample_id"]), reverse=(line == "rwa"))
        row = candidates[0]
        new_id = re.sub(r"_S\d{3}$", f"_{suffix}", row["sample_id"])
        stop_time = "401800" if line == "bat" else row["stop_time_s"]
        est_tf_days = "4.65" if line == "bat" else row["est_tf_days"]
        text = (root / row["yaml"]).read_text(encoding="utf-8")
        text = re.sub(r"^sample_id: .*?$", f"sample_id: {new_id}", text, flags=re.MULTILINE)
        text = re.sub(r"^seed: .*?$", f"seed: {seed}", text, flags=re.MULTILINE)
        # Keep the selected registered H2/L3 BAT card's high-aging override;
        # changing it here would make the generator probe a different DOE cell.
        text = re.sub(r"^stop_time_max_s: .*?$", f"stop_time_max_s: {stop_time}", text, flags=re.MULTILINE)
        text = re.sub(r"^est_tf_days: .*?$", f"est_tf_days: {est_tf_days}", text, flags=re.MULTILINE)
        (gen / "configs_sim" / "sample" / f"{new_id}.yaml").write_text(text, encoding="utf-8")
        output = dict(row)
        output.update({
            "sample_id": new_id,
            "yaml": f"configs/sim/sample/{new_id}.yaml",
            "out_mat": f"data/raw/sim/{line}/{new_id}.mat",
            "seed": str(seed),
            "stop_time_s": stop_time,
            "est_tf_days": est_tf_days,
            "queue_order": str(index),
        })
        rows.append(output)
    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print([(row["sample_id"], row["orbit"], row["stop_time_s"]) for row in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
