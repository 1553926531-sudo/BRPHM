#!/usr/bin/env python3
"""Development-only raw MAT feasibility probe for the next F1 partition.

The probe deliberately consumes a bounded, deterministic subset of the new
metadata-only census. Every touched unit is diagnostic-only and is excluded
from any later final partition. The transformation is byte-for-byte aligned
with the clean evaluator: sim_loader conversion, RWA daily aggregation,
friction feature, slide windows, window-end RUL labels, and drop-negative.
"""
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


def canon(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()


def probe_one(root: Path, row: dict, config: dict, norm_doc: dict) -> dict:
    import numpy as np
    from src.datasets import labels, preprocess, sim_loader, windows

    component = str(row["product_line"])
    uid = str(row["sample_id"])
    mode = config["resample"]["mode"]
    bin_s = float(config["resample"].get("bin_s", preprocess.SECONDS_PER_DAY)) if mode == "daily_agg" else None
    bases = list(config["resample"].get("base_channels", preprocess.RWA_TARGET_BASE)) if mode == "daily_agg" else []
    channels = list(config["channels"])
    absent = set(config.get("channels_absent_ok") or [])
    want_fric = bool(config["resample"].get("fric_tc", True)) and mode == "daily_agg" and preprocess.FRIC_TC_MEAN in channels
    baseline = None
    if want_fric:
        baseline = ((norm_doc.get("derived") or {}).get("rw") or {}).get("fric_tc", {}).get("baseline_coef")
        if not isinstance(baseline, list) or len(baseline) != 2:
            raise RuntimeError("missing frozen RWA friction baseline")
    L = int(config["window"]["L"])
    stride = int(config["window"]["stride"])
    rmax = float(config["labels"]["rmax"])
    floor = config["labels"].get("rul_floor", "keep")
    raw = Path(str(row["raw_path"]))
    dataset_id = str(config["dataset_id"])
    converted, _, frame = sim_loader.convert_one(
        raw, dataset_id, root / "data/interim" / dataset_id,
        root=root, lenient=False, write=False,
    )
    if converted != uid or frame is None:
        raise RuntimeError(f"identity drift: converted={converted!r} expected={uid!r}")
    source_rows = int(len(frame))
    if mode == "daily_agg":
        frame, _ = preprocess._bin_aggregate_rwa(frame, bin_s, bases, [])
    aggregate_rows = int(len(frame))
    if want_fric:
        frame[preprocess.FRIC_TC_MEAN] = (
            frame["rw.motor_current_a.mean"].to_numpy(np.float64)
            - (float(baseline[0]) + float(baseline[1]) * frame["rw.bearing_temp_c.mean"].to_numpy(np.float64))
        )
    missing = [ch for ch in channels if ch not in frame.columns and ch not in absent]
    if missing:
        raise RuntimeError(f"missing channels: {missing}")
    matrix = np.column_stack([
        np.zeros(len(frame), dtype=np.float64) if ch in absent else frame[ch].to_numpy(np.float64)
        for ch in channels
    ])
    windows_array, ends = windows.slide(matrix, L, stride)
    raw_windows = int(len(windows_array))
    y, _, _ = labels.window_labels(frame["label.rul"].to_numpy(np.float64), frame.get("label.hi"), ends, rmax)
    finite = np.isfinite(y)
    nonnegative = y >= 0.0
    keep = finite.copy()
    if floor == "drop_negative":
        keep &= nonnegative
    return {
        "sample_id": uid,
        "product_line": component,
        "orbit": row["orbit"],
        "raw_sha256": row["sha256"],
        "raw_size": int(row["size"]),
        "source_rows": source_rows,
        "aggregate_rows": aggregate_rows,
        "L": L,
        "stride": stride,
        "raw_windows": raw_windows,
        "finite_label_windows": int(finite.sum()),
        "nonnegative_label_windows": int((finite & nonnegative).sum()),
        "kept_windows": int(keep.sum()),
        "status": "feasible" if int(keep.sum()) > 0 else "zero_windows_after_label_filter",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--census", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--per-cell", type=int, default=5)
    args = ap.parse_args()
    root, census_path, output = args.root.resolve(), args.census.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    census = json.loads(census_path.read_text(encoding="utf-8"))
    rows = list(census.get("rows") or [])
    if not rows:
        raise RuntimeError("census has no rows")
    selected = []
    for component in ("bat", "rwa"):
        for orbit in ("LEO500", "LEO550", "LEO700"):
            cell = [r for r in rows if r["product_line"] == component and r["orbit"] == orbit]
            cell.sort(key=lambda r: (-int(r["size"]), str(r["sample_id"])))
            selected.extend(cell[: args.per_cell])
    import yaml

    configs = {c: yaml.safe_load((root / f"configs/preprocess/{c}_target.yaml").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    norms = {c: json.loads((root / f"data/processed/norm_stats/{c}_target.json").read_text(encoding="utf-8")) for c in ("bat", "rwa")}
    results = []
    for row in selected:
        started = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        try:
            result = probe_one(root, row, configs[row["product_line"]], norms[row["product_line"]])
            result["started_utc"] = started
        except Exception as exc:  # isolate one bad raw unit; continue census
            result = {
                "sample_id": row["sample_id"], "product_line": row["product_line"], "orbit": row["orbit"],
                "raw_sha256": row["sha256"], "raw_size": int(row["size"]), "status": "error",
                "error_type": type(exc).__name__, "error": str(exc),
                "traceback_tail": traceback.format_exc().splitlines()[-5:], "started_utc": started,
            }
        result["completed_utc"] = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        results.append(result)
    document = {
        "schema": "brphm-f1-development-feasibility-probe-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "census_path": str(census_path),
        "census_sha256": sha256(census_path),
        "selection_rule": "largest raw file size per component/orbit cell, sample_id ascending tie-break",
        "per_cell": args.per_cell,
        "semantic_labels_read": True,
        "final_label_access": False,
        "diagnostic_only": True,
        "all_touched_units_excluded_from_future_final_partitions": True,
        "configs": {c: {"path": str(root / f"configs/preprocess/{c}_target.yaml"), "sha256": sha256(root / f"configs/preprocess/{c}_target.yaml")} for c in ("bat", "rwa")},
        "norm_stats": {c: {"path": str(root / f"data/processed/norm_stats/{c}_target.json"), "sha256": sha256(root / f"data/processed/norm_stats/{c}_target.json")} for c in ("bat", "rwa")},
        "results": sorted(results, key=lambda r: (r["product_line"], r["orbit"], r["sample_id"])),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    data = canon(document)
    output.write_bytes(data)
    output.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    digest = hashlib.sha256(data).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(digest + "  " + output.name + "\n", encoding="ascii")
    sidecar.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    summary = {"output": str(output), "sha256": digest, "rows": len(results), "status_counts": {s: sum(r.get("status") == s for r in results) for s in sorted({r.get("status") for r in results})}}
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
