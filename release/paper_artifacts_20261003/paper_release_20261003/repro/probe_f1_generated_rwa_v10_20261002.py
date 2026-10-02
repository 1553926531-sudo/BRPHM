#!/usr/bin/env python3
"""Development probe for generated RWA v10 samples; touched files are burned."""
from __future__ import annotations

import csv
import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from probe_f1_raw_window_feasibility_v10_20261002 import probe_one


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    gen = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3]).resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = gen / "sim/logs/manifest.csv"
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))
    configs = {c: yaml.safe_load((root / f"configs/preprocess/{c}_target.yaml").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    norms = {c: json.loads((root / f"data/processed/norm_stats/{c}_target.json").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    results = []
    for row in rows:
        if row["line"] != "rwa":
            continue
        raw = gen / "generated/rwa" / f"{row['sample_id']}.mat"
        item = {"sample_id": row["sample_id"], "product_line": "rwa", "orbit": row["orbit"], "raw_path": str(raw), "sha256": sha256(raw), "size": raw.stat().st_size}
        try:
            result = probe_one(root, item, configs["rwa"], norms["rwa"])
        except Exception as exc:
            result = {"sample_id": row["sample_id"], "product_line": "rwa", "orbit": row["orbit"], "status": "error", "error_type": type(exc).__name__, "error": str(exc)}
        result["generator_manifest_sha256"] = sha256(manifest)
        result["generated_raw_sha256"] = item["sha256"]
        results.append(result)
    doc = {"schema": "brphm-f1-generated-rwa-feasibility-probe-v1", "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"), "generator_manifest": str(manifest), "generator_manifest_sha256": sha256(manifest), "semantic_labels_read": True, "diagnostic_only": True, "all_touched_units_excluded_from_future_final_partitions": True, "results": results}
    data = (json.dumps(doc, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"output": str(output), "sha256": digest, "results": results}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
