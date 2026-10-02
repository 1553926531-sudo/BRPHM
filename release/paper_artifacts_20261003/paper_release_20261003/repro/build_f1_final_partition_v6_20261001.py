#!/usr/bin/env python3
"""Create the v6 untouched raw partition from file metadata only."""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path

SCHEMA = "brphm-f1-raw-sim-partition-v1"
EXPECTED = {
    "bat": ("BAT_LEO500_B00_H2_L3_S961", "BAT_LEO550_B00_H2_L3_S962", "BAT_LEO700_B30_H2_L3_S963"),
    "rwa": ("RWA_LEO500_B00_H0_L1_S971", "RWA_LEO550_B30_H0_L1_S972", "RWA_LEO700_B60_H0_L1_S973"),
}
FORBIDDEN = {"RWA_LEO500_B00_H1_L3_S024", "BAT_LEO500_B00_H2_L3_S996", "BAT_LEO550_B00_H2_L3_S997", "BAT_LEO700_B30_H2_L3_S998", "BAT_LEO500_B00_H0_L1_S991"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def build(generated: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    rows = []
    for component, ids in EXPECTED.items():
        for sample_id in ids:
            path = (generated / component / f"{sample_id}.mat").resolve()
            if sample_id in FORBIDDEN or not path.is_file():
                raise RuntimeError(f"missing or forbidden generated raw file: {sample_id}")
            size = path.stat().st_size
            if size <= 0:
                raise RuntimeError(f"empty generated raw file: {sample_id}")
            rows.append({
                "sample_id": sample_id,
                "product_line": component,
                "raw_path": str(path),
                "sha256": sha256(path),
                "size": size,
                "selection_reason": "v6_generated_unit_file_metadata_only_before_freeze",
            })
    document = {
        "schema": SCHEMA,
        "created_utc": "2026-10-01T00:00:00Z",
        "semantic_labels_read": False,
        "source": str(generated.resolve()),
        "selection_inputs": ["expected_v6_sample_ids", "raw_file_existence", "raw_file_size", "raw_file_sha256"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "diagnostic_S024", "v5_outputs"],
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(document)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"manifest": str(output), "sha256": digest, "rows": len(rows)}, ensure_ascii=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.generated.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
