#!/usr/bin/env python3
"""Read labels once for a diagnostic partition and burn every touched unit."""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import traceback
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def probe_one(root: Path, row: dict, config: dict, norm: dict) -> dict:
    import numpy as np
    from src.datasets import labels, preprocess, sim_loader, windows

    component = str(row["product_line"])
    raw = Path(row["raw_path"]).resolve()
    uid = str(row["sample_id"])
    if sha256(raw) != row["sha256"]:
        raise RuntimeError("raw hash drift")
    mode = config["resample"]["mode"]
    bin_s = float(config["resample"].get("bin_s", preprocess.SECONDS_PER_DAY)) if mode == "daily_agg" else None
    bases = list(config["resample"].get("base_channels", preprocess.RWA_TARGET_BASE)) if mode == "daily_agg" else []
    channels = list(config["channels"])
    absent = set(config.get("channels_absent_ok") or [])
    want_fric = bool(config["resample"].get("fric_tc", True)) and mode == "daily_agg" and preprocess.FRIC_TC_MEAN in channels
    baseline = ((norm.get("derived") or {}).get("rw") or {}).get("fric_tc", {}).get("baseline_coef")
    if want_fric and (not isinstance(baseline, list) or len(baseline) != 2):
        raise RuntimeError("missing frozen RWA friction baseline")
    converted, _, frame = sim_loader.convert_one(raw, str(config["dataset_id"]), root / "data/interim" / str(config["dataset_id"]), root=root, lenient=False, write=False)
    if converted != uid or frame is None:
        raise RuntimeError(f"identity drift: {converted!r} != {uid!r}")
    source_rows = int(len(frame))
    if mode == "daily_agg":
        frame, _ = preprocess._bin_aggregate_rwa(frame, bin_s, bases, [])
    aggregate_rows = int(len(frame))
    if want_fric:
        frame[preprocess.FRIC_TC_MEAN] = frame["rw.motor_current_a.mean"].to_numpy(np.float64) - (float(baseline[0]) + float(baseline[1]) * frame["rw.bearing_temp_c.mean"].to_numpy(np.float64))
    missing = [ch for ch in channels if ch not in frame.columns and ch not in absent]
    if missing:
        raise RuntimeError(f"missing channels: {missing}")
    matrix = np.column_stack([np.zeros(len(frame), dtype=np.float64) if ch in absent else frame[ch].to_numpy(np.float64) for ch in channels])
    _, ends = windows.slide(matrix, int(config["window"]["L"]), int(config["window"]["stride"]))
    y, _, _ = labels.window_labels(frame["label.rul"].to_numpy(np.float64), frame.get("label.hi"), ends, float(config["labels"]["rmax"]))
    finite = np.isfinite(y)
    nonnegative = y >= 0.0
    keep = finite & (nonnegative if config["labels"].get("rul_floor", "keep") == "drop_negative" else True)
    return {
        "sample_id": uid,
        "product_line": component,
        "orbit": row["orbit"],
        "raw_sha256": row["sha256"],
        "raw_size": int(row["size"]),
        "source_rows": source_rows,
        "aggregate_rows": aggregate_rows,
        "window_L": int(config["window"]["L"]),
        "window_stride": int(config["window"]["stride"]),
        "raw_windows": int(len(y)),
        "finite_label_windows": int(finite.sum()),
        "nonnegative_label_windows": int((finite & nonnegative).sum()),
        "kept_windows": int(keep.sum()),
        "status": "feasible" if int(keep.sum()) > 0 else "zero_windows_after_label_filter",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--partition-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    manifest_path = args.partition_manifest.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "brphm-f1-raw-sim-partition-v1" or manifest.get("semantic_labels_read") is not False:
        raise RuntimeError("partition manifest is not metadata-only")
    import yaml
    configs = {c: yaml.safe_load((root / f"configs/preprocess/{c}_target.yaml").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    norms = {c: json.loads((root / f"data/processed/norm_stats/{c}_target.json").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    results = []
    for row in manifest["rows"]:
        started = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        try:
            result = probe_one(root, row, configs[row["product_line"]], norms[row["product_line"]])
            result["started_utc"] = started
        except Exception as exc:
            result = {"sample_id": row["sample_id"], "product_line": row["product_line"], "orbit": row["orbit"], "raw_sha256": row["sha256"], "raw_size": int(row["size"]), "status": "error", "error_type": type(exc).__name__, "error": str(exc), "traceback_tail": traceback.format_exc().splitlines()[-5:], "started_utc": started}
        result["completed_utc"] = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        results.append(result)
    doc = {
        "schema": "brphm-f1-development-feasibility-probe-v2",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "partition_manifest": str(manifest_path),
        "partition_manifest_sha256": sha256(manifest_path),
        "semantic_labels_read": True,
        "final_label_access": False,
        "diagnostic_only": True,
        "all_touched_units_excluded_from_future_final_partitions": True,
        "configs": {c: {"path": str(root / f"configs/preprocess/{c}_target.yaml"), "sha256": sha256(root / f"configs/preprocess/{c}_target.yaml")} for c in ("bat", "rwa")},
        "norm_stats": {c: {"path": str(root / f"data/processed/norm_stats/{c}_target.json"), "sha256": sha256(root / f"data/processed/norm_stats/{c}_target.json")} for c in ("bat", "rwa")},
        "results": sorted(results, key=lambda r: r["sample_id"]),
    }
    payload = canonical(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(payload).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "sha256": digest, "rows": len(results), "status_counts": {s: sum(r.get("status") == s for r in results) for s in sorted({r.get("status") for r in results})}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
