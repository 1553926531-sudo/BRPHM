#!/usr/bin/env python3
"""Build an isolated RWA-only v6 generator tree for parallel execution."""
from __future__ import annotations

import csv
import pathlib
import shutil
import sys


def main() -> int:
    root = pathlib.Path(sys.argv[1]).resolve()
    source = pathlib.Path(sys.argv[2]).resolve()
    gen = pathlib.Path(sys.argv[3]).resolve()
    if gen.exists():
        raise FileExistsError(gen)
    shutil.copytree(source, gen, symlinks=True)
    configs_dir = gen / "configs"
    configs_dir.mkdir(exist_ok=True)
    sim_link = configs_dir / "sim"
    if sim_link.is_symlink() or sim_link.is_file():
        sim_link.unlink()
    elif sim_link.exists():
        if any(sim_link.iterdir()):
            raise RuntimeError(f"unexpected non-empty configs/sim path: {sim_link}")
        sim_link.rmdir()
    sim_link.symlink_to(pathlib.Path("../configs_sim"), target_is_directory=True)
    manifest = gen / "sim/logs/manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows = [row for row in rows if row["line"] == "rwa"]
    if {row["sample_id"] for row in rows} != {
        "RWA_LEO500_B00_H0_L1_S971",
        "RWA_LEO550_B30_H0_L1_S972",
        "RWA_LEO700_B60_H0_L1_S973",
    }:
        raise RuntimeError("RWA-only manifest drift")
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print([(row["sample_id"], row["stop_time_s"]) for row in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
