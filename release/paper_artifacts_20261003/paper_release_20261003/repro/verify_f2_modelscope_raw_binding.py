#!/usr/bin/env python3
"""Compare registered train/validation source-file hashes to ModelScope manifests.

The script reads only Git manifest blobs locally and hashes the corresponding
non-holdout MAT and Parquet files on Rack. It never downloads payloads or
inspects MAT/Parquet contents.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HISTORICAL_COMMIT = "85ebba12f3ec132dc9e0ea8ae49012f57505ccf1"
CURRENT_COMMIT = "cfe0a27a99fa776d6e464649576432c871992771"
EXPECTED_TIER_TREE = "f0b07bea4a1d2eb9286b26f7c91f34b951391da3"
EXPECTED_TIER_MANIFEST_SHA256 = "ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062"
EXPECTED_TIER_MANIFEST_BLOB = "5fbb843ed576b746c547250a0e9a4cd4546ed7f1"
TIER_MANIFEST_PATH = "BRPHM_RUL_complete/MANIFEST.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def run(command: list[str], *, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command!r}\n"
            f"{completed.stderr.decode('utf-8', errors='replace')}"
        )
    return completed.stdout


def git_text(git_dir: Path, *args: str) -> str:
    return run(["git", "-C", str(git_dir), *args]).decode("ascii").strip()


def read_public_manifest(git_dir: Path, commit: str) -> tuple[bytes, list[dict[str, object]]]:
    raw = run(["git", "-C", str(git_dir), "show", f"{commit}:{TIER_MANIFEST_PATH}"])
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("files"), list):
        raise ValueError(f"unexpected manifest schema at {commit}")
    records = []
    for row in parsed["files"]:
        layer = row.get("layer")
        path = str(row.get("path", ""))
        expected_suffix = ".mat" if layer == "raw" else ".parquet" if layer == "interim" else None
        if (
            row.get("source_family") in {"SIM_bat", "SIM_rwa"}
            and expected_suffix is not None
            and path.endswith(expected_suffix)
        ):
            records.append(row)
    return raw, records


def read_registered_train_val(membership_path: Path) -> list[dict[str, str]]:
    with membership_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["split"] in {"train", "val"}]
    if any(row["split"] == "holdout" for row in selected):
        raise AssertionError("holdout row entered train/validation set")
    ids = [row["unit_id"] for row in selected]
    if len(ids) != len(set(ids)):
        raise AssertionError("duplicate unit ID in train/validation membership")
    return selected


def sha_id_set(rows: list[dict[str, str]]) -> str:
    ids = sorted(row["unit_id"] for row in rows)
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def parse_sha256sum(stdout: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in stdout.decode("utf-8").splitlines():
        digest, sep, path = line.partition("  ")
        if not sep or not HEX64.fullmatch(digest):
            raise ValueError(f"unexpected sha256sum output: {line!r}")
        result[path] = digest
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-dir", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--ssh-key", type=Path, required=True)
    parser.add_argument("--rack-host", default="first@10.123.100.40")
    parser.add_argument("--rack-root", default="/mnt/data/BRPHM/rul-space")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 100:
        parser.error("--batch-size must be between 1 and 100")

    revisions = {
        "historical_verified": HISTORICAL_COMMIT,
        "current_head_at_2026_10_02_access": CURRENT_COMMIT,
    }
    manifest_rows: dict[str, dict[str, dict[str, dict[str, object]]]] = {}
    manifest_metadata: dict[str, dict[str, object]] = {}
    for label, commit in revisions.items():
        tree = git_text(args.git_dir, "rev-parse", f"{commit}:BRPHM_RUL_complete")
        blob = git_text(args.git_dir, "rev-parse", f"{commit}:{TIER_MANIFEST_PATH}")
        raw, records = read_public_manifest(args.git_dir, commit)
        digest = hashlib.sha256(raw).hexdigest()
        if tree != EXPECTED_TIER_TREE:
            raise AssertionError(f"unexpected complete-tier tree at {commit}: {tree}")
        if blob != EXPECTED_TIER_MANIFEST_BLOB:
            raise AssertionError(f"unexpected complete-tier manifest blob at {commit}: {blob}")
        if digest != EXPECTED_TIER_MANIFEST_SHA256:
            raise AssertionError(f"unexpected complete-tier manifest digest at {commit}: {digest}")
        by_id: dict[str, dict[str, dict[str, object]]] = {}
        for row in records:
            path = str(row["path"])
            layer = str(row["layer"])
            unit_id = Path(path).stem
            if layer == "interim":
                if not unit_id.startswith("unit_"):
                    raise AssertionError(f"unexpected SIM interim path: {path}")
                unit_id = unit_id.removeprefix("unit_")
            if not HEX64.fullmatch(str(row.get("sha256", ""))):
                raise AssertionError(f"invalid public SHA-256 for {path}")
            if layer in by_id.setdefault(unit_id, {}):
                raise AssertionError(f"duplicate public SIM {layer} unit ID: {unit_id}")
            by_id[unit_id][layer] = row
        manifest_rows[label] = by_id
        raw_records = [row for row in records if row.get("layer") == "raw"]
        interim_records = [row for row in records if row.get("layer") == "interim"]
        manifest_metadata[label] = {
            "commit": commit,
            "complete_tier_tree_oid": tree,
            "complete_tier_manifest_blob_oid": blob,
            "complete_tier_manifest_bytes": len(raw),
            "complete_tier_manifest_sha256": digest,
            "sim_raw_mat_count": len(raw_records),
            "sim_interim_parquet_count": len(interim_records),
            "sim_bat_raw_mat_count": sum(row.get("source_family") == "SIM_bat" for row in raw_records),
            "sim_rwa_raw_mat_count": sum(row.get("source_family") == "SIM_rwa" for row in raw_records),
            "sim_bat_interim_parquet_count": sum(row.get("source_family") == "SIM_bat" for row in interim_records),
            "sim_rwa_interim_parquet_count": sum(row.get("source_family") == "SIM_rwa" for row in interim_records),
        }

    historical = manifest_rows["historical_verified"]
    current = manifest_rows["current_head_at_2026_10_02_access"]
    if historical != current:
        raise AssertionError("the selected SIM raw manifest records differ across pinned revisions")

    registered = read_registered_train_val(args.membership)
    public_ids = {unit_id for unit_id, layers in historical.items() if "raw" in layers}
    registered_ids = {row["unit_id"] for row in registered}
    if public_ids != registered_ids:
        raise AssertionError(
            f"public SIM ID mismatch: missing={len(registered_ids - public_ids)}, "
            f"extra={len(public_ids - registered_ids)}"
        )

    expected_files: dict[str, dict[str, object]] = {}
    unit_rows: dict[str, dict[str, object]] = {}
    for row in registered:
        unit_id = row["unit_id"]
        line = row["product_line"].lower()
        family = "SIM_bat" if line == "bat" else "SIM_rwa"
        public_layers = historical[unit_id]
        expected_paths = {
            "raw": f"raw/sim/{line}/{unit_id}.mat",
            "interim": f"interim/SIM_{line}/unit_{unit_id}.parquet",
        }
        for layer, expected_path in expected_paths.items():
            public = public_layers.get(layer)
            if public is None:
                raise AssertionError(f"public {layer} record missing for {unit_id}")
            if public.get("source_family") != family or public.get("path") != expected_path:
                raise AssertionError(f"public {layer} path/family mismatch for {unit_id}")
            rack_relative = (
                f"data/raw/sim/{line}/{unit_id}.mat"
                if layer == "raw"
                else f"data/interim/SIM_{line}/unit_{unit_id}.parquet"
            )
            expected_files[f"{layer}:{unit_id}"] = {
                "unit_id": unit_id,
                "layer": layer,
                "rack_path": f"{args.rack_root}/{rack_relative}",
                "public_path": expected_path,
                "public_bytes": int(public["bytes"]),
                "public_sha256": str(public["sha256"]),
            }
        unit_rows[unit_id] = {
            "unit_id": unit_id,
            "product_line": line,
            "dataset_id": row["dataset_id"],
            "orbit": row["orbit"],
            "split": row["split"],
        }

    ssh_prefix = [
        "ssh",
        "-i",
        str(args.ssh_key),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        args.rack_host,
    ]
    actual_hashes: dict[str, str] = {}
    commands: list[str] = []
    file_keys = sorted(expected_files)
    for start in range(0, len(file_keys), args.batch_size):
        batch_keys = file_keys[start : start + args.batch_size]
        batch_paths = {key: str(expected_files[key]["rack_path"]) for key in batch_keys}
        remote_argv = "sha256sum -- " + " ".join(shlex.quote(batch_paths[key]) for key in batch_keys)
        commands.append(" ".join(shlex.quote(part) for part in ssh_prefix) + " " + shlex.quote(remote_argv))
        output = run([*ssh_prefix, remote_argv])
        path_hashes = parse_sha256sum(output)
        expected_paths = set(batch_paths.values())
        if set(path_hashes) != expected_paths:
            raise AssertionError(
                f"Rack returned a different path set: missing={len(expected_paths - set(path_hashes))}, "
                f"extra={len(set(path_hashes) - expected_paths)}"
            )
        for key, path in batch_paths.items():
            actual_hashes[key] = path_hashes[path]

    mismatch: list[dict[str, str]] = []
    for key, expected in expected_files.items():
        actual = actual_hashes[key]
        layer = str(expected["layer"])
        unit_id = str(expected["unit_id"])
        match = actual == expected["public_sha256"]
        unit_rows[unit_id][f"{layer}_binding"] = {
            "public_manifest_path": expected["public_path"],
            "public_bytes": expected["public_bytes"],
            "public_sha256": expected["public_sha256"],
            "rack_path": expected["rack_path"],
            "rack_sha256": actual,
            "sha256_match": match,
        }
        if not match:
            mismatch.append(
                {
                    "unit_id": unit_id,
                    "layer": layer,
                    "public_sha256": str(expected["public_sha256"]),
                    "rack_sha256": actual,
                }
            )

    local_membership_sha = hashlib.sha256(args.membership.read_bytes()).hexdigest()
    report = {
        "schema": "brphm-f2-modelscope-source-hash-binding-v1",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "hash-only comparison of registered train/validation SIM raw MAT and interim Parquet files; no file content parsed; holdout files excluded",
        "dataset_url": "https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets",
        "git_url": "https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets.git",
        "versions": manifest_metadata,
        "local_metadata": {
            "membership_path": str(args.membership.resolve()),
            "membership_sha256": local_membership_sha,
            "train_val_unit_count": len(registered),
            "train_val_id_set_sha256": sha_id_set(registered),
            "public_ids_equal_train_val_ids": True,
            "holdout_files_hashed": 0,
        },
        "rack": {
            "host": args.rack_host,
            "project_root": args.rack_root,
            "hashed_file_count": len(actual_hashes),
            "hashed_raw_mat_count": sum(key.startswith("raw:") for key in actual_hashes),
            "hashed_interim_parquet_count": sum(key.startswith("interim:") for key in actual_hashes),
            "ssh_key_identity": str(args.ssh_key),
            "commands": commands,
        },
        "result": {
            "unit_count": len(unit_rows),
            "file_count": len(actual_hashes),
            "sha256_matches": len(actual_hashes) - len(mismatch),
            "mismatch_count": len(mismatch),
            "all_train_val_hashes_match": not mismatch and len(unit_rows) == 550 and len(actual_hashes) == 1100,
            "mismatches": mismatch,
        },
        "records": [unit_rows[unit_id] for unit_id in sorted(unit_rows)],
        "interpretation": {
            "source_record_binding": "verified if all_train_val_hashes_match is true; both published raw MAT and published interim Parquet files are bound per unit",
            "processed_tensor_byte_binding": "not established by this source-file hash comparison; requires a deterministic preprocessing receipt tying the interim hashes and code/configuration to the formal tensor hashes",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "output_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                "unit_count": report["result"]["unit_count"],
                "file_count": report["result"]["file_count"],
                "sha256_matches": report["result"]["sha256_matches"],
                "mismatch_count": report["result"]["mismatch_count"],
                "all_train_val_hashes_match": report["result"]["all_train_val_hashes_match"],
                "holdout_files_hashed": report["local_metadata"]["holdout_files_hashed"],
            },
            indent=2,
        )
    )
    return 0 if report["result"]["all_train_val_hashes_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
