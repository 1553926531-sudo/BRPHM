#!/usr/bin/env python3
"""Freeze a source-only candidate and prepare/seal a fresh LEO600 partition."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ORBIT = "LEO600"
BETAS = (0, 30, 60)
COMPONENTS = ("bat", "rwa")
PER_CELL = 2
FIRST_SERIAL = 940
FIRST_SEED = 891940
BAT_PERIOD_S = 5740
MANIFEST_COLUMNS = (
    "sample_id", "line", "dataset_id", "orbit", "beta_deg", "profile",
    "h_level", "l_level", "doe_cell", "cell_index", "indiv", "serial",
    "seed", "yaml", "out_mat", "gmat_env", "stop_time_s", "est_tf_days",
    "est_wall_bucket", "fault_inject", "fault_time_frac", "queue_order",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def write_new(path: Path, payload: bytes, readonly: bool = True) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
    if readonly:
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return hashlib.sha256(payload).hexdigest()


def load_candidate_wrapper(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("f1_candidate_wrapper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load candidate wrapper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_snapshot(receipt_path: Path, wrapper_path: Path, unseen_orbit: str = ORBIT) -> dict[str, Any]:
    wrapper = load_candidate_wrapper(wrapper_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return wrapper.build_candidate_snapshot(receipt, sha256_file(receipt_path), unseen_orbit)


def select_templates(rows: list[dict[str, str]], excluded_ids: set[str],
                     per_cell: int = PER_CELL) -> list[list[dict[str, str]]]:
    allowed = set(MANIFEST_COLUMNS)
    groups: list[list[dict[str, str]]] = []
    for component in COMPONENTS:
        for beta in BETAS:
            candidates = [
                {key: str(value) for key, value in row.items() if key in allowed}
                for row in rows
                if row.get("line") == component
                and int(row.get("beta_deg", -1)) == beta
                and row.get("sample_id") not in excluded_ids
            ]
            candidates = [row for row in candidates if row.get("yaml")]
            candidates.sort(key=lambda row: hashlib.sha256(
                f"f1-leo600-template-v1\0{component}\0{beta:02d}\0{row['sample_id']}".encode("utf-8")
            ).hexdigest())
            if len(candidates) < per_cell:
                raise ValueError(f"need {per_cell} unexcluded templates for {component}/B{beta:02d}")
            groups.append(candidates[:per_cell])
    return groups


def rewrite_config(text: str, *, sample_id: str, orbit: str, beta_deg: int,
                   seed: int, stop_time_s: int, line: str) -> str:
    if line not in COMPONENTS or orbit != ORBIT:
        raise ValueError("candidate config must bind to the registered component and LEO600")
    values = {
        "sample_id": sample_id,
        "orbit": orbit,
        "beta_deg": str(beta_deg),
        "seed": str(seed),
        "stop_time_max_s" if line == "bat" else "stop_time_s": str(
            (stop_time_s // BAT_PERIOD_S) * BAT_PERIOD_S if line == "bat" else stop_time_s
        ),
    }
    result = text
    for key, value in values.items():
        pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", flags=re.MULTILINE)
        result, count = pattern.subn(f"{key}: {value}", result)
        if count != 1:
            raise ValueError(f"expected one {key} entry, found {count}")
    return result


def make_manifest_row(source: dict[str, str], *, sample_id: str,
                      beta_deg: int, seed: int) -> dict[str, str]:
    parsed = re.fullmatch(r"(BAT|RWA)_LEO600_B(\d{2})_H(\d)_L(\d)_S(\d{3})", sample_id)
    if parsed is None:
        raise ValueError(f"invalid predeclared LEO600 sample id: {sample_id}")
    prefix, beta_text, h_level, l_level, serial_text = parsed.groups()
    component = "bat" if prefix == "BAT" else "rwa"
    if component != source.get("line") or int(beta_text) != beta_deg:
        raise ValueError("sample id, source component and beta do not agree")
    row = {key: str(source.get(key, "")) for key in MANIFEST_COLUMNS}
    serial = int(serial_text)
    row.update({
        "sample_id": sample_id,
        "line": component,
        "dataset_id": f"SIM_{component}",
        "orbit": ORBIT,
        "beta_deg": str(beta_deg),
        "doe_cell": f"{ORBIT}-B{beta_deg:02d}-H{h_level}-L{l_level}",
        "seed": str(seed),
        "yaml": f"configs/sim/sample/{sample_id}.yaml",
        "out_mat": f"data/raw/sim/{component}/{sample_id}.mat",
        "gmat_env": f"sim/gmat/out/env_{ORBIT}_B{beta_deg:02d}.mat",
        "serial": str(serial),
        "queue_order": str(serial - FIRST_SERIAL + 1),
    })
    return row


def parse_excluded_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {row["sample_id"] for row in csv.DictReader(handle) if row.get("sample_id")}


def load_validated_environment_inputs(validation_path: Path, gmat_cache: Path) -> list[dict[str, Any]]:
    validation_path = validation_path.resolve()
    gmat_cache = gmat_cache.resolve()
    document = json.loads(validation_path.read_text(encoding="utf-8"))
    if document.get("schema") != "f1_leo600_import_validation_v3":
        raise ValueError("unexpected GMAT validation manifest schema")
    if document.get("semantic_labels_read") is not False or document.get("final_label_access") is not False:
        raise ValueError("GMAT import validation reports label access")
    results = document.get("results")
    expected_ids = {f"LEO600_B{beta:02d}" for beta in BETAS}
    if not isinstance(results, list) or {row.get("id") for row in results} != expected_ids:
        raise ValueError("GMAT validation must bind B00, B30 and B60 exactly once")
    if len(results) != len(expected_ids):
        raise ValueError("GMAT validation contains duplicate orbit records")

    records = []
    for row in sorted(results, key=lambda item: item["id"]):
        beta = int(row["id"][-2:])
        beta_text = f"{beta:02d}"
        folder = (gmat_cache / f"f1_leo600_b{beta_text.lower()}_20261002").resolve()
        report = Path(row["report_file"]).resolve()
        eclipse = Path(row["eclipse_file"]).resolve()
        imported = Path(row["out_file"]).resolve()
        if report != folder / f"LEO600_B{beta_text}.csv":
            raise ValueError(f"GMAT report path does not bind the registered beta tile: {row['id']}")
        if eclipse != folder / f"LEO600_B{beta_text}_eclipse.txt":
            raise ValueError(f"GMAT eclipse path does not bind the registered beta tile: {row['id']}")
        if not report.is_file() or not eclipse.is_file() or not imported.is_file():
            raise FileNotFoundError(f"validated GMAT inputs or imported environment are missing: {row['id']}")
        checks = row.get("checks")
        expected_checks = [f"[PASS] V{i}" for i in range(1, 9)]
        if row.get("grid_points") != 259201 or not isinstance(checks, list) or len(checks) != 8:
            raise ValueError(f"GMAT validation is incomplete: {row['id']}")
        if any(not check.startswith(prefix) for check, prefix in zip(checks, expected_checks)):
            raise ValueError(f"GMAT validation gate failed: {row['id']}")
        records.append({
            "id": row["id"],
            "beta_deg": beta,
            "report_file": str(report),
            "report_sha256": sha256_file(report),
            "eclipse_file": str(eclipse),
            "eclipse_sha256": sha256_file(eclipse),
            "validated_import_file": str(imported),
            "validated_import_sha256": sha256_file(imported),
            "grid_points": row["grid_points"],
            "event_count": row.get("event_count"),
            "checks": checks,
        })
    return records


def prepare(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    source_tree = args.source_tree.resolve()
    tree = args.tree.resolve()
    output_dir = args.output_dir.resolve()
    if tree.exists() or output_dir.exists():
        raise FileExistsError("LEO600 tree and evidence directory must be new")
    if not source_tree.is_dir():
        raise FileNotFoundError(source_tree)

    with (root / "sim/logs/manifest.csv").open(newline="", encoding="utf-8-sig") as handle:
        source_rows = list(csv.DictReader(handle))
    excluded = parse_excluded_ids(args.exclude_manifest.resolve())
    groups = select_templates(source_rows, excluded, PER_CELL)
    template_rows = [row for group in groups for row in group]

    receipt = args.candidate_receipt.resolve()
    wrapper_path = args.candidate_wrapper.resolve()
    snapshot = build_snapshot(receipt, wrapper_path)
    if any(float(snapshot["components"][c]["selected_route"]["alpha_by_target"][ORBIT]) != 1e-5
           for c in COMPONENTS):
        raise RuntimeError("source-only route does not assign the registered unseen-orbit floor")
    environment_records = load_validated_environment_inputs(
        args.validation_manifest.resolve(), args.gmat_cache.resolve()
    )

    shutil.copytree(source_tree, tree, symlinks=True)
    generated = tree / "generated"
    if generated.exists():
        shutil.rmtree(generated)
    for beta in BETAS:
        beta_text = f"{beta:02d}"
        env_dir = args.gmat_cache.resolve() / f"f1_leo600_b{beta_text.lower()}_20261002"
        input_pairs = ((f"LEO600_B{beta_text}.csv", f"LEO600_B{beta_text}.csv"),
                       (f"LEO600_B{beta_text}_eclipse.txt", f"LEO600_B{beta_text}_eclipse.txt"))
        out_dir = tree / "sim/gmat/out"
        out_dir.mkdir(parents=True, exist_ok=True)
        for source_name, dest_name in input_pairs:
            source_path = env_dir / source_name
            if not source_path.is_file():
                raise FileNotFoundError(source_path)
            shutil.copy2(source_path, out_dir / dest_name)

    config_root = tree / "configs_sim/sample"
    config_root.mkdir(parents=True, exist_ok=True)
    config_link = tree / "configs/sim"
    if config_link.is_symlink() or config_link.is_file():
        config_link.unlink()
    elif config_link.exists():
        shutil.rmtree(config_link)
    config_link.symlink_to(Path("../configs_sim"), target_is_directory=True)

    rows: list[dict[str, str]] = []
    cards: list[dict[str, Any]] = []
    for index, source in enumerate(template_rows):
        beta = int(source["beta_deg"])
        component = source["line"]
        source_id = source["sample_id"]
        match = re.fullmatch(r"(?:BAT|RWA)_LEO\d+_B\d{2}_H(\d)_L(\d)_S\d{3}", source_id)
        if match is None:
            raise ValueError(f"unsupported template sample id: {source_id}")
        h_level, l_level = match.groups()
        serial = FIRST_SERIAL + index
        prefix = "BAT" if component == "bat" else "RWA"
        sample_id = f"{prefix}_{ORBIT}_B{beta:02d}_H{h_level}_L{l_level}_S{serial:03d}"
        seed = FIRST_SEED + index
        source_config = (root / source["yaml"]).resolve()
        if not source_config.is_file():
            raise FileNotFoundError(source_config)
        source_config_bytes = source_config.read_bytes()
        rewritten = rewrite_config(
            source_config_bytes.decode("utf-8"), sample_id=sample_id,
            orbit=ORBIT, beta_deg=beta, seed=seed,
            stop_time_s=int(float(source["stop_time_s"])), line=component,
        ).encode("utf-8")
        config_path = config_root / f"{sample_id}.yaml"
        config_path.write_bytes(rewritten)
        row = make_manifest_row(source, sample_id=sample_id, beta_deg=beta, seed=seed)
        if component == "bat":
            row["stop_time_s"] = str((int(float(source["stop_time_s"])) // BAT_PERIOD_S) * BAT_PERIOD_S)
            row["est_tf_days"] = source["est_tf_days"]
        rows.append(row)
        cards.append({
            "sample_id": sample_id,
            "component": component,
            "orbit": ORBIT,
            "beta_deg": beta,
            "seed": seed,
            "source_sample_id": source_id,
            "source_config_path": str(source_config),
            "source_config_sha256": hashlib.sha256(source_config_bytes).hexdigest(),
            "generated_config_path": str(config_path),
            "generated_config_sha256": sha256_file(config_path),
            "semantic_labels_read": False,
        })

    manifest_path = tree / "sim/logs/manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    card_path = tree / "sim/logs/leo600_source_card_manifest.json"
    write_new(card_path, canonical_bytes({
        "schema": "brphm-f1-leo600-source-card-manifest-v1",
        "semantic_labels_read": False,
        "rows": cards,
    }))

    env_records = []
    for record in environment_records:
        beta = record["beta_deg"]
        for kind, source_key, hash_key, name in (
            ("report", "report_file", "report_sha256", f"LEO600_B{beta:02d}.csv"),
            ("eclipse", "eclipse_file", "eclipse_sha256", f"LEO600_B{beta:02d}_eclipse.txt"),
        ):
            copied = tree / "sim/gmat/out" / name
            env_records.append({
                "kind": kind,
                "source": record[source_key],
                "sha256": record[hash_key],
                "copy": str(copied),
                "copy_sha256": sha256_file(copied),
                "validated_import_file": record["validated_import_file"],
                "validated_import_sha256": record["validated_import_sha256"],
            })

    snapshot_dir = output_dir
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_hash = write_new(snapshot_dir / "candidate_snapshot.json", canonical_bytes(snapshot))
    builder_path = Path(__file__).resolve()
    prereg = {
        "schema": "brphm-f1-leo600-candidate-preregistration-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "candidate_id": snapshot["method_id"],
        "candidate_snapshot": {"path": str(snapshot_dir / "candidate_snapshot.json"), "sha256": snapshot_hash},
        "base_receipt": {"path": str(receipt), "sha256": sha256_file(receipt)},
        "candidate_wrapper": {"path": str(wrapper_path), "sha256": sha256_file(wrapper_path)},
        "base_runner_sha256": sha256_file(wrapper_path.with_name("f1_clean_final_test_20261001_v2.py")),
        "builder_script": {"path": str(builder_path), "sha256": sha256_file(builder_path)},
        "validation_manifest": {
            "path": str(args.validation_manifest.resolve()),
            "sha256": sha256_file(args.validation_manifest.resolve()),
        },
        "visible_information": {
            "old_outer_failure_sequence": [5, 4, 3, 1, 3, 0],
            "old_outer_results_disposition": "development_or_diagnostic_only; outer reuse is acknowledged",
            "known_orbit_clean_retry_performance_failure_visible": True,
            "known_orbit_result_used_for_source_route_ranking": False,
            "historical_floor_origin_independently_preregistered": False,
            "disclosure": "the floor rule is a post-outcome F1 repair choice; this frozen version is being assessed on an untouched orbit",
        },
        "selection_rule": snapshot["source_selection"],
        "partition_protocol": {
            "orbit": ORBIT,
            "betas_deg": list(BETAS),
            "units_per_component_beta": PER_CELL,
            "unit_count": len(rows),
            "template_selection": "minimum SHA256('f1-leo600-template-v1\\0component\\0beta\\0sample_id') among source manifest rows after excluding registered clean-final holdout IDs; configuration metadata only",
            "final_labels_used_for_template_or_route_selection": False,
            "final_label_access_before_freeze": False,
            "semantic_label_access_before_freeze": False,
            "excluded_source_holdout_count": len(excluded),
        },
        "environment_inputs": env_records,
        "execution_contract": {
            "workers": 2,
            "priority": "nice -n 15; ionice -c 3",
            "affinity": "taskset -c 0,1",
            "command": "make_dataset('Line','both','Workers',2,'SimMode','accelerator','Smoke',false,'MaxAttempts',1,'OutRoot',<tree>/generated)",
        },
        "generator_tree": str(tree),
        "candidate_and_units_frozen_before_final_label_access": True,
    }
    prereg_hash = write_new(snapshot_dir / "candidate_preregistration.json", canonical_bytes(prereg))
    preparation = {
        "schema": "brphm-f1-leo600-preparation-manifest-v1",
        "created_utc": prereg["created_utc"],
        "candidate_preregistration_sha256": prereg_hash,
        "generator_tree": str(tree),
        "sim_manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path)},
        "source_card_manifest": {"path": str(card_path), "sha256": sha256_file(card_path)},
        "source_manifest_sha256": sha256_file(root / "sim/logs/manifest.csv"),
        "excluded_holdout_manifest": {
            "path": str(args.exclude_manifest.resolve()),
            "sha256": sha256_file(args.exclude_manifest.resolve()),
        },
        "rows": cards,
        "environment_inputs": env_records,
        "semantic_labels_read": False,
        "final_label_access": False,
        "selection_inputs": ["source manifest configuration metadata", "excluded prior holdout ids", "GMAT environment file hashes", "candidate snapshot hash"],
    }
    prep_hash = write_new(snapshot_dir / "preparation_manifest.json", canonical_bytes(preparation))
    print(json.dumps({
        "status": "prepared",
        "candidate_snapshot_sha256": snapshot_hash,
        "candidate_preregistration_sha256": prereg_hash,
        "preparation_manifest_sha256": prep_hash,
        "generator_tree": str(tree),
        "units": len(rows),
        "semantic_labels_read": False,
        "final_label_access": False,
    }, sort_keys=True))
    return 0


def seal(args: argparse.Namespace) -> int:
    tree = args.tree.resolve()
    evidence_dir = args.evidence_dir.resolve()
    preparation_path = evidence_dir / "preparation_manifest.json"
    preparation = json.loads(preparation_path.read_text(encoding="utf-8"))
    if preparation.get("semantic_labels_read") is not False or preparation.get("final_label_access") is not False:
        raise RuntimeError("preparation manifest reports prior label access")
    card_path = tree / "sim/logs/leo600_source_card_manifest.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    if card.get("semantic_labels_read") is not False:
        raise RuntimeError("source-card manifest reports semantic label access")
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    rows = []
    for record in card.get("rows", []):
        if record.get("semantic_labels_read") is not False or record.get("orbit") != ORBIT:
            raise RuntimeError(f"source card is not eligible: {record.get('sample_id')}")
        sample_id = record["sample_id"]
        component = record["component"]
        raw = tree / "generated" / component / f"{sample_id}.mat"
        if not raw.is_file() or raw.stat().st_size <= 0:
            raise RuntimeError(f"missing generated raw file: {sample_id}")
        rows.append({
            "sample_id": sample_id,
            "product_line": component,
            "orbit": ORBIT,
            "beta_deg": record["beta_deg"],
            "seed": record["seed"],
            "raw_path": str(raw),
            "sha256": sha256_file(raw),
            "size": raw.stat().st_size,
            "config_path": record["generated_config_path"],
            "config_sha256": record["generated_config_sha256"],
            "source_sample_id": record["source_sample_id"],
            "source_config_sha256": record["source_config_sha256"],
            "source_card_manifest_sha256": sha256_file(card_path),
            "selection_reason": "predeclared_hash_ranked_template_and_id; metadata-only raw-file binding",
        })
    counts = {component: sum(row["product_line"] == component for row in rows) for component in COMPONENTS}
    if any(count != PER_CELL * len(BETAS) for count in counts.values()):
        raise RuntimeError(f"unexpected component partition counts: {counts}")
    partition = {
        "schema": "brphm-f1-raw-sim-partition-v1",
        "partition_id": "f1_final_unseen_orbit_leo600_v1_20261002",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "semantic_labels_read": False,
        "final_label_access": False,
        "candidate_preregistration": {
            "path": str(evidence_dir / "candidate_preregistration.json"),
            "sha256": sha256_file(evidence_dir / "candidate_preregistration.json"),
        },
        "preparation_manifest": {"path": str(preparation_path), "sha256": sha256_file(preparation_path)},
        "selection_inputs": ["predeclared unit ids", "source-card and config hashes", "raw-file existence and SHA-256 only"],
        "excluded_assets": ["sealed", "A1", "B1", "canonical", "production", "competition", "all previously label-read partitions"],
        "unit_counts": counts,
        "rows": sorted(rows, key=lambda item: item["sample_id"]),
    }
    payload = canonical_bytes(partition)
    digest = write_new(output, payload)
    sidecar_hash = write_new(output.with_suffix(output.suffix + ".sha256"),
                             f"{digest}  {output.name}\n".encode("ascii"))
    print(json.dumps({"status": "sealed_metadata_only", "manifest": str(output),
                      "sha256": digest, "sidecar_sha256": sidecar_hash,
                      "unit_counts": counts, "semantic_labels_read": False,
                      "final_label_access": False}, sort_keys=True))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prep = subparsers.add_parser("prepare")
    for name in ("root", "source-tree", "tree", "gmat-cache", "exclude-manifest",
                 "validation-manifest",
                 "candidate-receipt", "candidate-wrapper", "output-dir"):
        prep.add_argument(f"--{name}", required=True, type=Path)
    prep.set_defaults(func=prepare)
    seal_parser = subparsers.add_parser("seal")
    for name in ("tree", "evidence-dir", "output"):
        seal_parser.add_argument(f"--{name}", required=True, type=Path)
    seal_parser.set_defaults(func=seal)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
