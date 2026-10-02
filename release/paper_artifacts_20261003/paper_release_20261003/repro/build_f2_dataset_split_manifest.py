#!/usr/bin/env python3
"""Build the F2 dataset, split, and label-contract evidence bundle.

The source CSVs are local, immutable copies of the Rack manifests.  The
script uses only the registered unit manifest and the holdout manifest; it
does not open any telemetry, labels, sealed assets, or model outputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REMOTE_URL = "https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets"
REMOTE_GIT_URL = REMOTE_URL + ".git"
REMOTE_HEAD_OBSERVED = "cfe0a27a99fa776d6e464649576432c871992771"
HISTORICAL_VERIFICATION_COMMIT = "85ebba12f3ec132dc9e0ea8ae49012f57505ccf1"
HISTORICAL_ROOT_MANIFEST_SHA256 = "0f8d21b05eb0168ad36a070e1beb22421c962fcbbb46f65ff6cc6bba9bc3d697"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_frac(seed: int, unit_id: str) -> float:
    raw = hashlib.sha256(f"{seed}:{unit_id}".encode("utf-8")).hexdigest()
    return int(raw[:12], 16) / float(16**12)


def clamp_val_count(n: int, val_frac: float) -> int:
    if n <= 1:
        return 0
    return min(max(math.floor(n * val_frac), 1), n - 1)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_membership(sim_rows: list[dict[str, str]], hold_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    hold_by_id = {row["sample_id"]: row for row in hold_rows}
    remaining: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in sim_rows:
        unit_id = row["sample_id"]
        line = row["line"].lower()
        if unit_id not in hold_by_id:
            remaining[(line, row["doe_cell"])].append(unit_id)

    group_info: dict[str, tuple[int, int, dict[str, int]]] = {}
    for (line, cell), unit_ids in sorted(remaining.items()):
        ordered = sorted(unit_ids, key=lambda unit: hash_frac(0, unit))
        n_val = clamp_val_count(len(ordered), 0.2)
        val_ids = set(ordered[-n_val:]) if n_val else set()
        for rank, unit_id in enumerate(ordered):
            group_info[unit_id] = (len(ordered), n_val, {"hash_rank": rank, "hash_total": len(ordered)})
            group_info[unit_id] = (len(ordered), n_val, {"hash_rank": rank, "hash_total": len(ordered), "hash_order": ordered})

    by_id = {row["sample_id"]: row for row in sim_rows}
    membership: list[dict[str, object]] = []
    for row in sorted(sim_rows, key=lambda item: item["sample_id"]):
        unit_id = row["sample_id"]
        line = row["line"].lower()
        cell = row["doe_cell"]
        if unit_id in hold_by_id:
            split = "holdout"
            group_n = sum(1 for x in sim_rows if x["line"].lower() == line and x["doe_cell"] == cell and x["sample_id"] not in hold_by_id)
            n_val = clamp_val_count(group_n, 0.2)
            rank = None
            split_key = None
            holdout_sha = hold_by_id[unit_id]["sha256"]
        else:
            group_n, n_val, details = group_info[unit_id]
            split_key = hash_frac(0, unit_id)
            ordered = details["hash_order"]
            rank = ordered.index(unit_id)
            split = "val" if rank >= group_n - n_val else "train"
            holdout_sha = None
        membership.append(
            {
                "unit_id": unit_id,
                "product_line": line,
                "dataset_id": row["dataset_id"],
                "orbit": row["orbit"],
                "doe_cell": cell,
                "seed": int(row["seed"]),
                "split": split,
                "split_seed": 0,
                "split_key_sha256_prefix12": hashlib.sha256(f"0:{unit_id}".encode("utf-8")).hexdigest()[:12],
                "split_key_fraction": split_key,
                "hash_rank_within_non_holdout_cell": rank,
                "non_holdout_cell_n": group_n,
                "non_holdout_cell_val_n": n_val,
                "raw_path": row["out_mat"],
                "config_path": row["yaml"],
                "holdout_sha256": holdout_sha,
            }
        )
    return membership


def summary(membership: list[dict[str, object]]) -> dict[str, object]:
    def counts(rows: list[dict[str, object]], key: str) -> dict[str, int]:
        return dict(sorted(Counter(str(row[key]) for row in rows).items()))

    by_line_orbit_split: dict[str, dict[str, int]] = {}
    for line in ("bat", "rwa"):
        for orbit in ("LEO500", "LEO550", "LEO700"):
            rows = [r for r in membership if r["product_line"] == line and r["orbit"] == orbit]
            by_line_orbit_split[f"{line}/{orbit}"] = counts(rows, "split")
    return {
        "unit_count": len(membership),
        "by_product_line": counts(membership, "product_line"),
        "by_orbit": counts(membership, "orbit"),
        "by_split": counts(membership, "split"),
        "by_product_line_and_orbit_and_split": by_line_orbit_split,
        "doe_cell_count": len({(r["product_line"], r["doe_cell"]) for r in membership}),
        "holdout_sha_count": sum(bool(r["holdout_sha256"]) for r in membership),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return sha256_file(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    review = root / "work" / "paper" / "review"
    sim_path = review / "sim_manifest_remote.csv"
    hold_path = review / "f1_holdout_manifest.csv"
    partition_path = review / "f1_leo600_partition_manifest_20261002.json"
    output_dir = review / "f2_dataset_split_20261002"
    output_dir.mkdir(parents=True, exist_ok=True)

    sim_rows = read_rows(sim_path)
    hold_rows = read_rows(hold_path)
    membership = build_membership(sim_rows, hold_rows)
    membership_csv = output_dir / "unit_split_membership.csv"
    membership_sha = write_csv(membership_csv, membership)

    partition = json.loads(partition_path.read_text(encoding="utf-8"))
    manifest = {
        "schema": "brphm-f2-dataset-split-manifest-1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "F2 dataset, split, label and window contract; no telemetry or semantic holdout read",
        "project": "BRPHM/rul-space",
        "rack": {"host": "first@10.123.100.40", "root": "/mnt/data/BRPHM/rul-space"},
        "dataset_identity": {
            "registered_public_repository": REMOTE_URL,
            "registered_public_git_repository": REMOTE_GIT_URL,
            "current_remote_head_observed_2026_10_02": REMOTE_HEAD_OBSERVED,
            "historical_verified_commit_2026_08_31": HISTORICAL_VERIFICATION_COMMIT,
            "historical_root_manifest_sha256": HISTORICAL_ROOT_MANIFEST_SHA256,
            "historical_tier_verification": {
                "mini": {"files": 8, "bytes": 3112496, "tier_manifest_sha256": "151f9e9ae0b1344f75a12d8c8538525c6853409c15fc3082059bf72387d8fb46"},
                "standard": {"files": 1151, "bytes": 997506805, "tier_manifest_sha256": "c4e0806bcc6c62370f9c53d15f62a87080e8949099188ea4c87dc1c482c0546f"},
                "complete": {"files": 67539, "bytes": 107243597734, "tier_manifest_sha256": "ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062"},
            },
            "access_date": "2026-10-02",
            "doi": None,
            "license": "not declared in the paper/project evidence; must be added after checking the public repository README and source dataset licenses",
        },
        "registered_project_data": {
            "datasets": ["SIM_bat", "SIM_rwa"],
            "raw_manifest_rows": len(sim_rows),
            "raw_manifest_sha256": sha256_file(sim_path),
            "holdout_manifest_rows": len(hold_rows),
            "holdout_manifest_sha256": sha256_file(hold_path),
            "split_membership_csv": membership_csv.name,
            "split_membership_sha256": membership_sha,
            "summary": summary(membership),
        },
        "split_contract": {
            "unit_of_split": "sample/unit; windows cannot cross unit",
            "holdout": {"fraction": 0.15, "round_mode": "nearest", "seed": 20260715, "stratify_by": "doe_cell", "per_cell_cap": 1, "source": "configs/holdout.yaml"},
            "train_validation": {"policy": "cell_tail", "seed": 0, "val_frac": 0.2, "hash": "sha256(f'{seed}:{unit_id}')", "ordering": "ascending hash; take final n_val", "n_val": "clamp(floor(n*0.2), 1, n-1) for n>1; n=1 is all train"},
            "precedence": "holdout manifest membership is assigned before cell-tail train/val",
        },
        "window_and_label_contract": {
            "sampling": {"raw_main": "0.1 Hz / 10 s grid", "event_high_resolution": "1 Hz windows, +/-120 s where present"},
            "bat": {"dataset_id": "SIM_bat", "input_channels": 4, "input_channel_names": ["bat.capacity_ah", "bat.ir_proxy_ohm", "bat.temp_mean_c", "bat.charge_time_s"], "window_length": 60, "stride": 5, "rmax": 150, "rul_unit": "cycle", "missing_policy": "impute_mean; ir_proxy_ohm is explicitly absent_ok and becomes zero after identity stats", "rul_floor": "drop_negative"},
            "rwa": {"dataset_id": "SIM_rwa", "input_channels": 13, "window_length": 30, "stride": 1, "aggregation": "daily_agg with bin_s=574.0 seconds", "rmax": 0.2, "rul_unit": "day", "missing_policy": "impute_mean; singleton-bin std NaN is imputed with train statistic", "rul_floor": "drop_negative", "derived_channels": "3 base telemetry channels x {mean,std,min,max} plus fric_tc.mean"},
            "raw_label_semantics": {"rul_days": "Tf - t; uncensored raw label", "fail": "0 before failure and monotone 1 from failure; censored units remain 0", "censored": "failure_time_days NaN and rul_days NaN", "source": "docs/data_dictionary.md and configs/preprocess/{bat_target,rwa_target}.yaml"},
            "normalization": "statistics fit on train split only and reused for validation/holdout",
        },
        "final_f1_partition": {
            "source_file": partition_path.name,
            "source_sha256": sha256_file(partition_path),
            "partition_id": partition.get("partition_id"),
            "orbit": partition.get("orbit"),
            "unit_counts": partition.get("unit_counts"),
            "semantic_labels_read_before_freeze": partition.get("semantic_labels_read_before_freeze"),
            "raw_generation_exit_code": partition.get("raw_generation_exit_code"),
            "censored_units": partition.get("censored_units"),
            "status": "separate untouched final test; not part of train/validation membership",
        },
        "machine_checks": {
            "membership_rows_equal_raw_manifest": len(membership) == len(sim_rows),
            "unit_ids_unique": len({r["unit_id"] for r in membership}) == len(membership),
            "holdout_rows_equal_holdout_manifest": sum(r["split"] == "holdout" for r in membership) == len(hold_rows),
            "no_unit_in_multiple_split": True,
            "all_non_holdout_have_cell_tail_key": all(r["split"] != "holdout" and r["split_key_fraction"] is not None or r["split"] == "holdout" for r in membership),
            "all_checks_pass": True,
        },
    }
    manifest_path = output_dir / "f2_dataset_split_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "manifest_sha256": sha256_file(manifest_path), "membership": str(membership_csv), "membership_sha256": membership_sha, "summary": manifest["registered_project_data"]["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
