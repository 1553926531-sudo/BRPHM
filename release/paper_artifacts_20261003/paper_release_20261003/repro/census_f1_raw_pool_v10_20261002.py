#!/usr/bin/env python3
"""Metadata-only census for the next F1 raw candidate pool.

This script intentionally reads registered CSV manifests and target/holdout unit
IDs only. It does not open any raw MAT payload and therefore cannot determine
window feasibility. Feasibility is handled by a separate development probe.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import stat
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

COMPONENTS = ("bat", "rwa")
ORBITS = ("LEO500", "LEO550", "LEO700")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canon(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def csv_ids(path: Path, key: str) -> set[str]:
    if not path.is_file():
        return set()
    with path.open("r", encoding="utf-8", newline="") as f:
        return {str(row[key]) for row in csv.DictReader(f) if row.get(key)}


def target_units(root: Path, component: str) -> set[str]:
    import torch

    path = root / "data/processed" / f"{component}_target.pt"
    payload = torch.load(path, map_location="cpu", weights_only=False)
    rows = payload.get("meta", {}).get("index", payload.get("index", []))
    return {str(row["unit_id"]) for row in rows}


def diagnostic_units(root: Path) -> tuple[set[str], list[dict[str, object]]]:
    seen: set[str] = set()
    sources: list[dict[str, object]] = []
    for path in sorted((root / "work").glob("f1_generator_*/sim/logs/manifest.csv")):
        ids = csv_ids(path, "sample_id")
        seen.update(ids)
        sources.append({"path": str(path), "sha256": sha256(path), "row_count": len(ids)})
    # Burned or previously frozen raw partitions are excluded even when their
    # rows came from the registered master manifest rather than a generator
    # tree (the v9 attempt used this path).
    prior_paths = sorted((root / "work").glob("f1_final_partition_*/partition_manifest.json"))
    prior_paths += sorted((root / "work").glob("f1_raw_candidate_manifest*.json"))
    prior_paths += sorted((root / "work").glob("f1_feasibility_probe*.json"))
    # Freeze manifests are intentionally not globbed here: the historical
    # retry1 clean chain points at the registered holdout itself, and treating
    # every freeze manifest as a burned raw pool would incorrectly remove the
    # entire eligible master pool. Explicit partition/raw-candidate manifests
    # above are the burned-unit exclusion sources.
    for path in prior_paths:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = (doc.get("rows") or doc.get("results") or
                doc.get("final_partition", {}).get("raw_files") or [])
        ids = {str(row.get("sample_id")) for row in rows if row.get("sample_id")}
        seen.update(ids)
        sources.append({"path": str(path), "sha256": sha256(path), "row_count": len(ids), "kind": "prior_partition_or_freeze"})
    return seen, sources


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--include-fault-injected", action="store_true",
                    help="include registered non-none fault_inject rows; default preserves the earlier no-injection census")
    args = ap.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(output)

    master = root / "sim/logs/manifest.csv"
    holdout = root / "data/holdout/holdout_manifest.csv"
    holdout_ids = csv_ids(holdout, "sample_id")
    target = {c: target_units(root, c) for c in COMPONENTS}
    diagnostics, diagnostic_sources = diagnostic_units(root)
    with master.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    exclusions = {c: Counter() for c in COMPONENTS}
    eligible: list[dict[str, object]] = []
    for row in rows:
        component = row.get("line", "")
        orbit = row.get("orbit", "")
        sample_id = row.get("sample_id", "")
        if component not in COMPONENTS or orbit not in ORBITS:
            continue
        if not args.include_fault_injected and row.get("fault_inject") != "none":
            exclusions[component]["injected"] += 1
            continue
        if sample_id in target[component]:
            exclusions[component]["target_tensor"] += 1
            continue
        if sample_id in holdout_ids:
            exclusions[component]["existing_holdout"] += 1
            continue
        if sample_id in diagnostics:
            exclusions[component]["diagnostic_or_generator"] += 1
            continue
        raw = (root / row["out_mat"]).resolve()
        if not raw.is_file() or raw.stat().st_size <= 0:
            exclusions[component]["missing_raw"] += 1
            continue
        eligible.append({
            "sample_id": sample_id,
            "product_line": component,
            "orbit": orbit,
            "doe_cell": row.get("doe_cell"),
            "seed": int(row["seed"]),
            "stop_time_s": row.get("stop_time_s"),
            "est_tf_days": row.get("est_tf_days"),
            "fault_inject": row.get("fault_inject"),
            "fault_time_frac": row.get("fault_time_frac"),
            "raw_path": str(raw),
            "size": raw.stat().st_size,
            "sha256": sha256(raw),
            "master_manifest_path": str(master),
            "master_manifest_sha256": sha256(master),
        })

    counts = {f"{c}/{o}": sum(r["product_line"] == c and r["orbit"] == o for r in eligible)
              for c in COMPONENTS for o in ORBITS}
    if any(v == 0 for v in counts.values()):
        raise RuntimeError(f"empty component/orbit cell: {counts}")
    document = {
        "schema": "brphm-f1-raw-pool-census-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "semantic_labels_read": False,
        "raw_semantics_read": False,
        "selection_rule": "metadata-only eligibility census; no unit selected or frozen",
        "include_fault_injected": bool(args.include_fault_injected),
        "master_manifest": {"path": str(master), "sha256": sha256(master), "row_count": len(rows)},
        "holdout_manifest": {"path": str(holdout), "sha256": sha256(holdout), "excluded_units": len(holdout_ids)},
        "target_tensor_unit_counts": {c: len(target[c]) for c in COMPONENTS},
        "diagnostic_sources": diagnostic_sources,
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "all prior generator outputs", "v8/v9 burned units"],
        "exclusions": {c: dict(sorted(exclusions[c].items())) for c in COMPONENTS},
        "eligible_candidate_counts": counts,
        "rows": sorted(eligible, key=lambda r: (r["product_line"], r["orbit"], r["sample_id"])),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    data = canon(document)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(json.dumps({"output": str(output), "sha256": digest, "eligible_candidate_counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
