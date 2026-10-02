#!/usr/bin/env python3
from __future__ import annotations

import csv
import pathlib


EXPECTED = {
    "RWA_LEO500_B00_H0_L1_S971",
    "RWA_LEO550_B30_H0_L1_S972",
    "RWA_LEO700_B60_H0_L1_S973",
}


def main() -> int:
    tree = pathlib.Path(__import__("sys").argv[1]).resolve()
    manifest = tree / "sim/logs/manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows = [row for row in rows if row["line"] == "rwa"]
    if {row["sample_id"] for row in rows} != EXPECTED:
        raise RuntimeError("RWA-only manifest drift")
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print([(row["sample_id"], row["stop_time_s"]) for row in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
