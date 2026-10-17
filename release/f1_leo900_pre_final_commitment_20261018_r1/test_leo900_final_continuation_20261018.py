"""Exercise exact-once continuation with disposable child programs, never MAT data."""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    continuation = importlib.import_module("leo900_final_continuation_20261018")
except ModuleNotFoundError as exc:
    if exc.name != "leo900_final_continuation_20261018":
        raise
    continuation = None


CHILD = r'''
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);stage=sys.argv[2]
with (root/'calls.txt').open('a') as handle:handle.write(stage+'\n')
if (root/('fail_'+stage)).exists():
 print('artificial failure on '+stage,file=sys.stderr);raise SystemExit(7)
if (root/('omit_'+stage)).exists():raise SystemExit(0)
def write(path,doc):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as handle:json.dump(doc,handle)
if stage=='seal':write(root/'seal/seal_receipt.json',{'status':'PASS','unit_counts':{'bat':48,'rwa':48}})
elif stage=='freeze':write(root/'formal/freeze_manifest.json',{'final_partition':{'n_units':{'bat':48,'rwa':48}}})
elif stage=='evaluate':
 if not (root/'formal/freeze_manifest.json').exists():raise RuntimeError('labels before freeze')
 write(root/'guard.json',{'fixture':'single label claim'})
 write(root/'formal/final_receipt.json',{'fixture':'evaluation complete'})
 write(root/'formal/same_partition_performance_gate.json',{'comparison':{'passes':False}})
elif stage=='statistics':
 if not (root/'formal/final_receipt.json').exists():raise RuntimeError('statistics before evaluation')
 write(root/'statistics/statistics_receipt.json',{'status':'PASS','gate_passes':(root/'mismatch_gate').exists()})
if stage=='evaluate' and (root/'change_frozen_receipt').exists():
 (root/'formal/freeze_manifest.json').write_text('{"replaced":"must detect this drift"}')
'''


def fixture(root, *, complete=True):
    logs = root / "simulation_logs"
    logs.mkdir()
    (logs / "start_utc.txt").write_text("2026-10-17T11:01:20Z\n")
    if complete:
        (logs / "end_utc.txt").write_text("2026-10-19T11:01:20Z\n")
        (logs / "exit_status.txt").write_text("0\n")
    child = root / "synthetic_child.py"
    child.write_text(CHILD, encoding="utf-8")
    return {"run_root": root, "runtime": root / "controller_runtime", "guard": root / "guard.json",
            "inputs": {str(child): hashlib.sha256(child.read_bytes()).hexdigest()},
            "fresh_outputs": [root / "seal", root / "formal", root / "statistics"],
            "stages": [{"name": stage, "command": [sys.executable, "-B", str(child), str(root), stage]}
                       for stage in ("seal", "freeze", "evaluate", "statistics")],
            "artifacts": {"seal": root / "seal/seal_receipt.json",
                          "freeze": root / "formal/freeze_manifest.json",
                          "evaluate": root / "formal/same_partition_performance_gate.json",
                          "final_receipt": root / "formal/final_receipt.json",
                          "statistics": root / "statistics/statistics_receipt.json"},
            "production": False}


class FinalContinuationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(continuation, "final continuation implementation is missing")

    def test_incomplete_job_preflight_has_no_outputs_or_label_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root, complete=False)
            # A raw-looking file must not be opened or parsed by the preflight.
            (root / "NEVER_READ.mat").write_bytes(b"not a MAT; do not parse")
            result = continuation.preflight(plan)
            self.assertEqual(result["state"], "WAITING_FOR_SIMULATION")
            self.assertFalse(plan["runtime"].exists())
            self.assertFalse(plan["guard"].exists())
            self.assertFalse((root / "calls.txt").exists())

    def test_full_pipeline_retains_negative_gate_and_executes_statistics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            result = continuation.run_controller(plan)
            self.assertEqual(result["state"], "EVALUATION_AND_STATISTICS_COMPLETED")
            self.assertFalse(result["formal_gate_passes"])
            self.assertEqual((root / "calls.txt").read_text().splitlines(),
                             ["seal", "freeze", "evaluate", "statistics"])
            self.assertTrue(plan["guard"].exists())
            self.assertEqual(len(result["stages"]), 4)
            self.assertTrue(all(row["exit_code"] == 0 for row in result["stages"]))

    def test_failed_phase_preserves_logs_and_never_advances(self):
        for stage, expected in (("seal", ["seal"]), ("freeze", ["seal", "freeze"]),
                                ("evaluate", ["seal", "freeze", "evaluate"]),
                                ("statistics", ["seal", "freeze", "evaluate", "statistics"])):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = fixture(root)
                (root / ("fail_" + stage)).touch()
                with self.assertRaisesRegex(RuntimeError, "exit code 7"):
                    continuation.run_controller(plan)
                self.assertEqual((root / "calls.txt").read_text().splitlines(), expected)
                terminal = json.loads((plan["runtime"] / "controller_terminal.json").read_text())
                self.assertEqual(terminal["state"], "ERROR")
                self.assertEqual(terminal["stages"][-1]["exit_code"], 7)
                self.assertIn("artificial failure", (plan["runtime"] / f"{stage}.stderr.log").read_text())

    def test_simulation_failure_never_launches_a_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            (root / "simulation_logs/exit_status.txt").write_text("9\n")
            with self.assertRaisesRegex(RuntimeError, "simulation exit status"):
                continuation.run_controller(plan)
            self.assertFalse((root / "calls.txt").exists())
            self.assertFalse(plan["guard"].exists())

    def test_guard_existing_outputs_and_input_drift_are_rejected_before_commands(self):
        for mode in ("guard", "output", "drift"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = fixture(root)
                if mode == "guard":
                    plan["guard"].write_text("preserve existing final access")
                elif mode == "output":
                    plan["fresh_outputs"][0].mkdir()
                else:
                    with (root / "synthetic_child.py").open("ab") as handle:
                        handle.write(b"\n# drift\n")
                with self.assertRaises((RuntimeError, FileExistsError)):
                    continuation.run_controller(plan)
                self.assertFalse((root / "calls.txt").exists())
                if mode == "guard":
                    self.assertEqual(plan["guard"].read_text(), "preserve existing final access")

    def test_wait_rechecks_input_integrity_before_any_final_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root, complete=False)
            def simulate_completion_and_drift(seconds):
                self.assertEqual(seconds, 60)
                (root / "simulation_logs/end_utc.txt").write_text("2026-10-19T11:01:20Z\n")
                (root / "simulation_logs/exit_status.txt").write_text("0\n")
                with (root / "synthetic_child.py").open("ab") as handle:
                    handle.write(b"\n# drift while waiting\n")
            with self.assertRaisesRegex(RuntimeError, "input hash"):
                continuation.run_controller(plan, wait_fn=simulate_completion_and_drift)
            self.assertFalse((root / "calls.txt").exists())
            self.assertFalse(plan["guard"].exists())

    def test_existing_controller_runtime_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            plan["runtime"].mkdir()
            marker = plan["runtime"] / "previous_evidence.txt"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                continuation.run_controller(plan)
            self.assertEqual(marker.read_text(), "preserve")
            self.assertFalse((root / "calls.txt").exists())

    def test_zero_exit_without_receipt_cannot_advance_to_freeze(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            (root / "omit_seal").touch()
            with self.assertRaises((RuntimeError, FileNotFoundError)):
                continuation.run_controller(plan)
            self.assertEqual((root / "calls.txt").read_text().splitlines(), ["seal"])
            terminal = json.loads((plan["runtime"] / "controller_terminal.json").read_text())
            self.assertEqual(terminal["state"], "ERROR")
            self.assertEqual(terminal["stages"][0]["exit_code"], 0)

    def test_modified_freeze_evidence_is_detected_before_statistics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            (root / "change_frozen_receipt").touch()
            with self.assertRaisesRegex(RuntimeError, "evidence drift"):
                continuation.run_controller(plan)
            self.assertEqual((root / "calls.txt").read_text().splitlines(), ["seal", "freeze", "evaluate"])
            self.assertTrue(plan["guard"].exists())

    def test_mismatched_statistics_gate_is_an_error_after_one_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = fixture(root)
            (root / "mismatch_gate").touch()
            with self.assertRaisesRegex(RuntimeError, "gate differs"):
                continuation.run_controller(plan)
            self.assertEqual((root / "calls.txt").read_text().splitlines(), ["seal", "freeze", "evaluate", "statistics"])
            terminal = json.loads((plan["runtime"] / "controller_terminal.json").read_text())
            self.assertEqual(terminal["state"], "ERROR")
            self.assertFalse(terminal["formal_gate_passes"])
            with self.assertRaises(FileExistsError):
                continuation.run_controller(plan)

    def test_partial_completion_markers_do_not_start_final_stages(self):
        for name, value in (("end_utc.txt", "2026-10-19T11:01:20Z\n"), ("exit_status.txt", "0\n")):
            with self.subTest(marker=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = fixture(root, complete=False)
                (root / "simulation_logs" / name).write_text(value)
                self.assertEqual(continuation.preflight(plan)["state"], "WAITING_FOR_SIMULATION")
                self.assertFalse(plan["runtime"].exists())
                self.assertFalse((root / "calls.txt").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
