#!/usr/bin/env python3
from __future__ import annotations
import csv
import pathlib
import sys

EXPECTED = {"BAT_LEO700_B30_H2_L3_S983"}
tree = pathlib.Path(sys.argv[1]).resolve()
path = tree / "sim/logs/manifest.csv"
with path.open(newline="", encoding="utf-8") as handle:
    rows = [row for row in csv.DictReader(handle) if row["sample_id"] in EXPECTED]
if {row["sample_id"] for row in rows} != EXPECTED:
    raise RuntimeError("BAT S983 manifest drift")
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print([(row["sample_id"], row["seed"]) for row in rows])
