"""Continue the fixed LEO900 experiment after normal simulation completion.

The CLI exposes only the registered Rack paths. Tests exercise the controller
with disposable subprocesses. This program never controls MATLAB, reads a MAT
variable, selects a model, retries a failed stage, or removes existing evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path("/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1")
PYTHON = "/mnt/data/BRPHM/rul-space/.venv-fm/bin/python"
SUPPORT = RUN / "final_continuation_support_20261018_r1"
PROTOCOL = SUPPORT / "F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json"
R4 = RUN / "channel_policy_support_20261018_r4a"
R4_ENTRY = R4 / "f1_leo900_channel_policy_clean_final_test_20261018_r4.py"
R4_REGISTRATION = R4 / "F1_LEO900_CHANNEL_POLICY_AMENDMENT_20261018R4.json"
R4_SHA256 = "8c38fde2466d76f2ae58c8bc9a7f3f390ee1728cfc7b6a00b5066d83fd0dd261"
SEALER = RUN / "metadata_sealer_support_20261018_r1/leo900_metadata_sealer_20261018.py"
ANALYSIS = RUN / "statistics_support_20261018_r1"
ANALYSIS_PROTOCOL = ANALYSIS / "F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json"
ANALYSIS_SHA256 = "754326c717669f23f82d8cf044d87333772f21fe82a8b389a169389771506da1"
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
STAGE_NAMES = ("seal", "freeze", "evaluate", "statistics")
COUNTS = {"bat": 48, "rwa": 48}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def exists(path):
    return Path(path).exists() or Path(path).is_symlink()


def regular_file(path):
    path = Path(path)
    redirected = any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
                     for part in (path, *path.parents))
    if not path.is_absolute() or ".." in path.parts or redirected or not path.is_file():
        raise RuntimeError(f"unsafe or missing regular file: {path}")
    return path


def digest(path):
    path = regular_file(path)
    before = path.stat()
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    after = path.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise RuntimeError(f"input changed while hashing: {path}")
    return value.hexdigest()


def record(path):
    return {"path": str(path), "sha256": digest(path), "size": Path(path).stat().st_size}


def read_json(path):
    return json.loads(regular_file(path).read_text(encoding="utf-8"))


def serializable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    return value


def write_new(path, document):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(serializable(document), handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    if os.name == "posix":
        Path(path).chmod(0o444)
    return record(path)


def fixed_plan(inputs):
    """The sole production command sequence; it has no CLI path overrides."""
    seal = RUN / "metadata_seal_execution_20261018_r1"
    formal = RUN / "formal_output_execution_r1"
    statistics = RUN / "formal_statistics_20261018_r1"
    partition = seal / "partition_manifest.json"
    project = RUN / "evaluation_project_execution_r1"
    return {
        "run_root": RUN, "runtime": RUN / "final_continuation_runtime_20261018_r1",
        "guard": RUN / "leo900_final_label_access_guard.json", "inputs": dict(inputs),
        "fresh_outputs": [seal, formal, formal.with_name(formal.name + ".candidate_snapshot.json"), statistics],
        "stages": [
            {"name": "seal", "command": [PYTHON, "-B", str(SEALER), "--run-root", str(RUN), "--output", str(seal)]},
            {"name": "freeze", "command": [PYTHON, "-B", str(R4_ENTRY), "freeze", "--root", str(project),
                "--output", str(formal), "--candidate-receipt", str(RUN / "evidence/formal_candidate_receipt.json"),
                "--partition-manifest", str(partition)]},
            {"name": "evaluate", "command": [PYTHON, "-B", str(R4_ENTRY), "evaluate", "--root", str(project),
                "--output", str(formal), "--partition-manifest", str(partition), "--device", "cpu"]},
            {"name": "statistics", "command": [PYTHON, "-B", str(ANALYSIS / "f1_lossless_gate_statistics_20261018.py"),
                "--result", str(formal), "--output", str(statistics), "--bootstrap-reps", "20000",
                "--bootstrap-seed", "20261018"]},
        ],
        "artifacts": {"seal": seal / "seal_receipt.json", "freeze": formal / "freeze_manifest.json",
            "evaluate": formal / "same_partition_performance_gate.json", "final_receipt": formal / "final_receipt.json",
            "statistics": statistics / "statistics_receipt.json"},
        "production": True,
    }


def verify_inputs(plan):
    if not plan["inputs"]:
        raise RuntimeError("empty input hash registry")
    for path, expected in plan["inputs"].items():
        if digest(Path(path)) != expected:
            raise RuntimeError(f"input hash drift: {path}")
    if plan["production"]:
        if digest(R4_REGISTRATION) != R4_SHA256 or digest(ANALYSIS_PROTOCOL) != ANALYSIS_SHA256:
            raise RuntimeError("registered R4 or statistical protocol drift")
        spec = importlib.util.spec_from_file_location("leo900_continuation_r4_verifier", R4_ENTRY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.verify_amendment(RUN / "evaluation_project_execution_r1")


def resource_status(plan):
    if not plan["production"]:
        return {"ready": True, "synthetic_only": True}
    affinity = sorted(os.sched_getaffinity(0))
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if affinity != [4] or nice < 15 or any(os.environ.get(key) != "1" for key in THREAD_VARS):
        raise RuntimeError("controller requires CPU4, nice>=15, and one numerical thread")
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, value = line.split(":", 1)
        if name == "MemAvailable":
            mem[name] = int(value.split()[0]) * 1024
    free = shutil.disk_usage(RUN).free
    return {"ready": mem.get("MemAvailable", 0) >= 8 * 1024**3 and free >= 8 * 1024**3,
            "mem_available_bytes": mem.get("MemAvailable", 0), "disk_free_bytes": free,
            "minimum_available_memory_and_disk_bytes": 8 * 1024**3,
            "cpu_affinity": affinity, "nice": nice, "numeric_threads": {key: os.environ[key] for key in THREAD_VARS}}


def simulation_status(plan):
    logs = Path(plan["run_root"]) / "simulation_logs"
    start = regular_file(logs / "start_utc.txt").read_text(encoding="utf-8").strip()
    if plan["production"] and start != "2026-10-17T11:01:20Z":
        raise RuntimeError("simulation start differs from the registered run")
    end, exit_path = logs / "end_utc.txt", logs / "exit_status.txt"
    if exists(exit_path):
        exit_text = regular_file(exit_path).read_text(encoding="utf-8").strip()
        if exit_text and exit_text != "0":
            raise RuntimeError(f"simulation exit status is not zero: {exit_text}")
    else:
        exit_text = ""
    complete = exists(end) and bool(regular_file(end).read_text(encoding="utf-8").strip()) and exit_text == "0"
    return {"complete": complete, "start_utc": start,
            "end_utc": regular_file(end).read_text(encoding="utf-8").strip() if exists(end) else None,
            "exit_status": exit_text or None}


def preflight(plan, *, own_runtime=False):
    """Read only registered inputs and completion metadata, without MAT decoding."""
    if tuple(stage["name"] for stage in plan["stages"]) != STAGE_NAMES:
        raise RuntimeError("stage order differs from seal/freeze/evaluate/statistics")
    for stage in plan["stages"]:
        if not isinstance(stage["command"], list) or not stage["command"] or not all(isinstance(x, str) for x in stage["command"]):
            raise RuntimeError("subprocess command must be a nonempty string argument list")
    if not own_runtime and exists(plan["runtime"]):
        raise FileExistsError(f"controller runtime already exists: {plan['runtime']}")
    if exists(plan["guard"]):
        raise RuntimeError("final label access guard already exists")
    for path in plan["fresh_outputs"]:
        if exists(path):
            raise FileExistsError(f"preserve existing output: {path}")
    verify_inputs(plan)
    simulation = simulation_status(plan)
    resources = resource_status(plan)
    state = ("WAITING_FOR_SIMULATION" if not simulation["complete"] else
             "READY_TO_SEAL" if resources["ready"] else "WAITING_FOR_RESOURCES")
    return {"state": state, "observed_utc": utc_now(), "simulation": simulation, "resources": resources,
            "final_stages_invoked": False, "semantic_final_labels_read": False}


def validate_artifact(plan, stage, gate_passes):
    path = Path(plan["artifacts"][stage])
    document = read_json(path)
    if stage == "seal" and (document.get("status") != "PASS" or document.get("unit_counts") != COUNTS):
        raise RuntimeError("metadata seal did not confirm BAT48/RWA48")
    if stage == "freeze" and document.get("final_partition", {}).get("n_units") != COUNTS:
        raise RuntimeError("freeze did not bind BAT48/RWA48")
    records = [record(path)]
    if stage == "evaluate":
        gate_passes = document.get("comparison", {}).get("passes")
        if type(gate_passes) is not bool or not exists(plan["guard"]):
            raise RuntimeError("evaluation receipt or global single-access guard incomplete")
        read_json(plan["artifacts"]["final_receipt"])
        records.extend(record(plan["artifacts"][key]) for key in ("final_receipt",))
        records.append(record(plan["guard"]))
    if stage == "statistics" and (document.get("status") != "PASS" or document.get("gate_passes") is not gate_passes):
        raise RuntimeError("statistics reconstruction failed or gate differs from original")
    return gate_passes, records


def run_controller(plan, *, wait_fn=time.sleep):
    initial = preflight(plan)
    runtime = Path(plan["runtime"])
    runtime.mkdir(exist_ok=False)
    events = runtime / "events"
    events.mkdir(exist_ok=False)
    sequence, previous_hash = 0, None
    completed, immutable_outputs = [], []
    started, gate_passes = utc_now(), None

    def event(kind, payload):
        nonlocal sequence, previous_hash
        sequence += 1
        row = {"sequence": sequence, "previous_event_sha256": previous_hash,
               "created_utc": utc_now(), "event_type": kind, "payload": payload}
        previous_hash = write_new(events / f"{sequence:04d}_{kind}.json", row)["sha256"]

    def check_completed_outputs():
        for row in immutable_outputs:
            if digest(row["path"]) != row["sha256"]:
                raise RuntimeError(f"completed stage evidence drift: {row['path']}")

    try:
        write_new(runtime / "controller_plan.json", plan)
        event("controller_started", {"pid": os.getpid(), "plan": record(runtime / "controller_plan.json"),
                                     "initial_preflight": initial})
        last_state = None
        while True:
            current = preflight(plan, own_runtime=True)
            if current["state"] != last_state:
                event("preflight_state", current)
                last_state = current["state"]
            if current["state"] == "READY_TO_SEAL":
                break
            wait_fn(60)
        for stage in plan["stages"]:
            name = stage["name"]
            verify_inputs(plan)
            check_completed_outputs()
            if name != "statistics" and exists(plan["guard"]):
                raise RuntimeError("unexpected prior final-label claim; no automatic retry")
            waiting = False
            while True:
                resources = resource_status(plan)
                if resources["ready"]:
                    if waiting:
                        event("resources_ready", {"stage": name, "resources": resources})
                    break
                if not waiting:
                    event("waiting_for_resources", {"stage": name, "resources": resources})
                    waiting = True
                wait_fn(60)
                verify_inputs(plan)
                check_completed_outputs()
            row = {"name": name, "command": stage["command"], "started_utc": utc_now(), "resources": resources}
            completed.append(row)
            out_path, err_path = runtime / (name + ".stdout.log"), runtime / (name + ".stderr.log")
            with out_path.open("xb") as stdout, err_path.open("xb") as stderr:
                child = subprocess.Popen(stage["command"], cwd=plan["run_root"], stdout=stdout, stderr=stderr,
                                         stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                row["pid"] = child.pid
                event("stage_started", row)
                while True:
                    try:
                        row["exit_code"] = child.wait(timeout=60)
                        break
                    except subprocess.TimeoutExpired:
                        pass
            row.update(ended_utc=utc_now(), stdout=record(out_path), stderr=record(err_path))
            event("stage_exited", row)
            if row["exit_code"]:
                raise RuntimeError(f"{name} exited with exit code {row['exit_code']}; automatic retries prohibited")
            gate_passes, artifacts = validate_artifact(plan, name, gate_passes)
            row["artifacts"] = artifacts
            immutable_outputs.extend(artifacts)
            event("stage_artifacts_verified", {"stage": name, "artifacts": artifacts})
        verify_inputs(plan)
        check_completed_outputs()
        terminal = {"schema": "brphm-f1-final-continuation-terminal-v1",
                    "state": "EVALUATION_AND_STATISTICS_COMPLETED", "started_utc": started,
                    "ended_utc": utc_now(), "formal_gate_passes": gate_passes, "stages": completed,
                    "note": "Execution and reconstruction completed. This is not a declaration of scientific success or F1/goal closure."}
        event("controller_completed", terminal)
    except BaseException as exc:
        terminal = {"schema": "brphm-f1-final-continuation-terminal-v1", "state": "ERROR",
                    "started_utc": started, "ended_utc": utc_now(), "formal_gate_passes": gate_passes,
                    "error_type": type(exc).__name__, "error": str(exc), "stages": completed,
                    "automatic_retry_permitted": False, "existing_evidence_preserved": True}
        event("controller_error", terminal)
        terminal["last_event_sha256"] = previous_hash
        write_new(runtime / "controller_terminal.json", terminal)
        raise
    terminal["last_event_sha256"] = previous_hash
    write_new(runtime / "controller_terminal.json", terminal)
    return terminal


def production_plan(protocol_sha256):
    if os.name != "posix" or Path(__file__).resolve().parent != SUPPORT or sys.executable != PYTHON:
        raise RuntimeError("production CLI is restricted to its registered Rack support and interpreter")
    if digest(PROTOCOL) != protocol_sha256:
        raise RuntimeError("continuation protocol hash mismatch")
    document = read_json(PROTOCOL)
    if document.get("schema") != "brphm-f1-pre-final-continuation-protocol-v1":
        raise RuntimeError("continuation protocol schema mismatch")
    inputs = {row["path"]: row["sha256"] for row in document["input_files"]}
    if len(inputs) != len(document["input_files"]) or inputs.get(str(Path(__file__).resolve())) != digest(Path(__file__).resolve()):
        raise RuntimeError("continuation executable binding mismatch")
    inputs[str(PROTOCOL)] = protocol_sha256
    plan = fixed_plan(inputs)
    comparison = serializable(fixed_plan({}))
    if document.get("fixed_plan") != comparison:
        raise RuntimeError("registered command sequence differs from hardcoded fixed plan")
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only preflight; no process or output creation")
    mode.add_argument("--run", action="store_true", help="exclusive controller; no retries or path overrides")
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args(argv)
    plan = production_plan(args.protocol_sha256)
    result = preflight(plan) if args.check else run_controller(plan)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
