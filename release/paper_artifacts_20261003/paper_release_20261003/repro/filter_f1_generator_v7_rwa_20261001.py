#!/usr/bin/env python3
from __future__ import annotations
import csv, pathlib, sys
EXPECTED = {"RWA_LEO500_B00_H0_L1_S991", "RWA_LEO550_B30_H0_L1_S992", "RWA_LEO700_B60_H0_L1_S993"}
tree = pathlib.Path(sys.argv[1]).resolve(); path = tree / "sim/logs/manifest.csv"
with path.open(newline="", encoding="utf-8") as handle: rows = [r for r in csv.DictReader(handle) if r["line"] == "rwa"]
if {r["sample_id"] for r in rows} != EXPECTED: raise RuntimeError("RWA v7 manifest drift")
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
print([(r["sample_id"], r["seed"]) for r in rows])
