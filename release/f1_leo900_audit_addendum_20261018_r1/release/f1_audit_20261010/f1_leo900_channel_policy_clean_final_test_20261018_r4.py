"""Add the frozen impute_mean step to the registered LEO900 execution chain.

The r3 closure verifier and r1 adapter are reused. All r3 dependency-binding
steps are retained here, plus this amendment and its payload-only correction.
Original registered files are never edited. No final-data read occurs at import
or freeze; evaluate retains the original exclusive global access guard.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRATION = HERE / "F1_LEO900_CHANNEL_POLICY_AMENDMENT_20261018R4.json"
FILES = {Path(__file__).name, "leo900_channel_policy_20261018_r4.py"}


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_record(row, base=None):
    path = Path(row["path"])
    if base is not None:
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError("channel-policy amendment path escapes support directory")
        path = base / path
    if (path.is_symlink() or not path.is_file() or path.stat().st_size != row.get("size")
            or hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256")):
        raise RuntimeError(f"channel-policy amendment artifact drift: {path}")
    return path.resolve()


def verify_amendment(root):
    doc = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    if (doc.get("schema") != "brphm-f1-leo900-channel-policy-amendment-v1"
            or doc.get("project_root") != str(root.resolve())
            or any(doc.get(key) is not False for key in (
                "semantic_final_labels_read", "simulation_or_configuration_modified", "candidate_or_route_modified"))):
        raise RuntimeError("channel-policy amendment contract mismatch")
    rows = doc.get("files", [])
    if len(rows) != len(FILES) or {r["path"] for r in rows} != FILES:
        raise RuntimeError("channel-policy amendment executable membership mismatch")
    paths = [verify_record(row, HERE) for row in rows]
    paths.extend(verify_record(row) for row in doc.get("evidence", []))
    parent_path = verify_record(doc["parent_registration"])
    parent_doc = json.loads(parent_path.read_text(encoding="utf-8"))
    # Verify the bytes of the old closure utility before importing its code.
    support = {row["path"]: verify_record(row, parent_path.parent) for row in parent_doc["support_files"]}
    utility_path = support["leo900_dependency_closure_20261018.py"]
    utility = load_file("leo900_r4_original_closure_verifier", utility_path)
    parent = utility.verify_registration(root, parent_path)
    return doc, parent, parent_path, paths


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", type=Path, required=True)
    args, _ = parser.parse_known_args(argv)
    root = args.root.resolve()
    amendment, registration, parent_path, added_paths = verify_amendment(root)
    helper = load_file("leo900_registered_channel_policy_r4", HERE / "leo900_channel_policy_20261018_r4.py")
    previous = load_file("leo900_r4_original_r1_adapter", Path(registration["execution_adapter"]["path"]))
    original_loader = previous.load_base_runner
    diagnostics = {}

    def load_with_closure_and_policy():
        module = original_loader()
        original_dependencies, original_write = module.dependency_paths, module.write_new
        original_builder = module.build_raw_holdout_payload

        def dependencies(project, candidate_receipt):
            verify_amendment(project)
            paths = original_dependencies(project, candidate_receipt)
            paths.extend(project / row["path"] for row in registration["project_files"])
            paths.extend(project / registration[key]["path"] for key in ("base_install_receipt", "scripts_install_receipt"))
            paths.extend(parent_path.parent / row["path"] for row in registration["support_files"])
            paths.extend(Path(row["path"]) for row in registration.get("parent_evidence", []))
            paths.extend([parent_path, REGISTRATION, *added_paths])
            return list({str(path.resolve()): path.resolve() for path in paths}.values())

        def build_payload(project, component, config, norm_doc, manifest_rows, manifest_path):
            helper.validate_policy(config)
            payload = original_builder(project, component, config, norm_doc, manifest_rows, manifest_path)
            corrected = helper.apply_channel_policy(payload, config)
            diagnostics[component] = corrected["channel_policy_audit"]
            return corrected

        def write_with_policy(path, value, readonly=True):
            if path.name == "freeze_manifest.json":
                parent_row = module.file_record(parent_path, root)
                amendment_row = module.file_record(REGISTRATION, root)
                value["dependency_closure_registration"] = parent_row
                value["channel_policy_amendment"] = amendment_row
                visible = value.setdefault("visible_information_before_freeze", {})
                visible["dependency_closure_registration"] = parent_row
                visible["channel_policy_amendment"] = amendment_row
            elif path.name == "final_receipt.json":
                value["channel_policy_amendment"] = module.file_record(REGISTRATION, root)
                value["channel_policy_audit"] = diagnostics
            return original_write(path, value, readonly=readonly)

        module.dependency_paths = dependencies
        module.build_raw_holdout_payload = build_payload
        module.write_new = write_with_policy
        return module

    previous.load_base_runner = load_with_closure_and_policy
    return previous.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
