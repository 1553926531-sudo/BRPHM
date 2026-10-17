"""Artificial-data tests for the F1 postprocessor; no final data is used."""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from f1_paired_predictions_20261018 import write_paired_predictions

try:
    audit = importlib.import_module("f1_lossless_gate_statistics_20261018")
except ModuleNotFoundError as exc:
    if exc.name != "f1_lossless_gate_statistics_20261018":
        raise
    audit = None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def make_fixture(root):
    """Hand-checked: perfect candidate, unit physical error for control."""
    write_json(root / "freeze_manifest.json", {"fixture": "synthetic freeze"})
    write_json(root / "selection_decision.json", {"fixture": "synthetic selection"})
    results = {}
    for component in ("bat", "rwa"):
        rows = [{"unit_id": f"{component}_SYNTHETIC_A", "t_end": i} for i in range(3)]
        rows.append({"unit_id": f"{component}_SYNTHETIC_B", "t_end": 0})
        candidate = np.full(4, .5, np.float32)
        control = np.zeros(4, np.float32)
        paired = write_paired_predictions(
            root, component, rows, truth_rul=np.ones(4, np.float32), rmax=2.,
            candidate=candidate, control=control, alpha=np.ones(4, np.float32),
            blended=candidate, projected=candidate, payload_sha256="a" * 64,
            seed_raw_predictions=np.stack([candidate, candidate, candidate]), seeds=(17, 42, 73))
        candidate_metrics = {"rmse": 0., "mae": 0., "bias": 0., "unit_macro_rmse": 0.,
                             "rul_upward_fraction": 0., "n_windows": 4, "n_units": 2}
        reference_metrics = dict(candidate_metrics, rmse=1., mae=1., bias=-1., unit_macro_rmse=1.)
        results[component] = {"paired_predictions": paired, "n_windows": 4, "n_units": 2,
                              "payload_sha256": "a" * 64,
                              "metrics": candidate_metrics, "candidate_only_metrics": candidate_metrics,
                              "control_only_metrics": reference_metrics}
    receipt = {"schema": "brphm-f1-clean-final-evaluation-v1", "results": results,
               "freeze_manifest_sha256": digest(root / "freeze_manifest.json"),
               "selection_decision_sha256": digest(root / "selection_decision.json")}
    write_json(root / "final_receipt.json", receipt)
    gate = {"final_receipt_sha256": digest(root / "final_receipt.json"),
            "freeze_manifest_sha256": receipt["freeze_manifest_sha256"],
            "comparison": {"passes": True, "strict_gain": True, "regressions": [],
                           "tolerance": 1e-12,
                           "deltas_candidate_minus_same_partition_reference": {
                               c: {"rmse": -1., "mae": -1.} for c in ("bat", "rwa")}},
            "metrics": {c: {"candidate_blend": r["metrics"],
                            "same_partition_reference": r["control_only_metrics"]}
                        for c, r in results.items()}}
    write_json(root / "same_partition_performance_gate.json", gate)
    return receipt


class LosslessGateStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(audit, "the lossless gate/statistics implementation is missing")

    def test_float32_label_roundtrip_is_preserved(self):
        # Multiplying physical truth directly loses the evaluator's float32 division.
        truth_relative = np.array([0.6172839403152466], dtype=np.float32)
        row = [{"unit_id": "u"}]
        result = audit.recompute_metrics([0.], truth_relative, .2, row)
        self.assertEqual(result["mae"], 0.12345678806304933)
        self.assertNotEqual(result["mae"], float(np.float32(.123456789)))

    def test_metric_clipping_units_and_time_order_match_hand_oracle(self):
        rows = [{"unit_id": "a", "t_end": 2}, {"unit_id": "a", "t_end": 1},
                {"unit_id": "b", "t_end": 1}]
        value = audit.recompute_metrics([2., -.5, .5], [.5, .5, .5], 2., rows)
        self.assertEqual(value["rmse"], math.sqrt(2. / 3.))
        self.assertEqual(value["mae"], 2. / 3.)
        self.assertEqual(value["bias"], 0.)
        self.assertEqual(value["unit_macro_rmse"], .5)
        self.assertEqual(value["rul_upward_fraction"], 1.)

    def test_gate_uses_baseline_plus_tolerance_not_delta_threshold(self):
        reference = {c: {"rmse": 1., "mae": 1.} for c in ("bat", "rwa")}
        candidate = {c: dict(v) for c, v in reference.items()}
        candidate["bat"]["rmse"] = 1. + 1e-12
        candidate["rwa"]["mae"] = .9
        self.assertGreater(candidate["bat"]["rmse"] - 1., 1e-12)
        gate = audit.gate_decision(candidate, reference)
        self.assertTrue(gate["passes"])
        self.assertEqual(gate["regressions"], [])
        candidate["bat"]["rmse"] = np.nextafter(1. + 1e-12, math.inf)
        self.assertEqual(audit.gate_decision(candidate, reference)["regressions"], ["bat.rmse"])

    def test_gate_requires_gain_and_both_components(self):
        same = {c: {"rmse": 1., "mae": 1.} for c in ("bat", "rwa")}
        self.assertFalse(audit.gate_decision(same, same)["passes"])
        with self.assertRaises(ValueError):
            audit.gate_decision({"bat": same["bat"]}, same)
        invalid = {c: dict(v) for c, v in same.items()}
        invalid["rwa"]["mae"] = float("nan")
        with self.assertRaises(ValueError):
            audit.gate_decision(invalid, same)

    def test_cluster_bootstrap_retains_all_windows_and_paired_units(self):
        rows = [{"unit_id": "a"}] * 3 + [{"unit_id": "b"}]
        result = audit.paired_unit_statistics([0., 0., 0., 1.], [1., 1., 1., 0.],
                                            [0.] * 4, 1., rows, reps=2000, seed=73)
        self.assertEqual(result["n_units"], 2)
        self.assertEqual(result["n_windows"], 4)
        self.assertEqual(result["bootstrap"]["mae"]["window_pooled"]["point_delta"], -.5)
        self.assertEqual(result["bootstrap"]["mae"]["unit_macro"]["point_delta"], 0.)
        draws = result["bootstrap_draws"]["mae__window_pooled"]
        self.assertEqual(set(draws), {-1., -.5, 1.})
        macro = result["bootstrap_draws"]["mae__unit_macro"]
        self.assertEqual(set(macro), {-1., 0., 1.})
        np.testing.assert_array_equal(draws == -.5, macro == 0.)
        self.assertEqual(result["bootstrap"]["mae"]["window_pooled"]["ci95"], [-1., 1.])
        self.assertEqual(result["paired_tests"]["mae"]["sd_unit_delta"], math.sqrt(2.))

    def test_bootstrap_is_seed_reproducible_and_zero_differences_are_defined(self):
        rows = [{"unit_id": "a"}, {"unit_id": "b"}]
        left = audit.paired_unit_statistics([0., .5], [0., .5], [0., 0.], 1., rows,
                                           reps=100, seed=17)
        right = audit.paired_unit_statistics([0., .5], [0., .5], [0., 0.], 1., rows,
                                            reps=100, seed=17)
        for key in left["bootstrap_draws"]:
            np.testing.assert_array_equal(left["bootstrap_draws"][key], right["bootstrap_draws"][key])
        self.assertEqual(left["paired_tests"]["rmse"]["pvalue"], 1.)
        self.assertEqual(left["paired_tests"]["rmse"]["rank_biserial"], 0.)

    def test_single_unit_is_descriptive_and_invalid_rows_are_rejected(self):
        result = audit.paired_unit_statistics([0.], [1.], [0.], 1., [{"unit_id": "a"}],
                                            reps=100, seed=17)
        self.assertIsNone(result["paired_tests"]["rmse"]["pvalue"])
        self.assertIsNone(result["paired_tests"]["rmse"]["sd_unit_delta"])
        with self.assertRaises(ValueError):
            audit.paired_unit_statistics([0.], [1.], [0.], 1., [{}], reps=100, seed=17)

    def test_holm_adjusts_one_family_and_keeps_original_order(self):
        self.assertEqual(audit.holm_adjust([.04, .01, .03, 1.]), [.09, .04, .09, 1.])

    def test_signed_rank_ties_and_normal_approximation_have_independent_oracles(self):
        # Of 16 equally likely sign patterns, 10 have at most one sign of
        # either kind: C(4,0)+C(4,1)+C(4,3)+C(4,4) = 10.
        exact = audit.paired_test([-1., -1., -1., 1.])
        self.assertEqual(exact["pvalue"], .625)
        self.assertEqual(exact["rank_biserial"], -.5)
        self.assertEqual(exact["statistic"], 2.5)
        self.assertEqual(exact["standardized_paired_effect_dz"], -.5)
        # With 21 equal nonzero differences, the tie-corrected z magnitude
        # is sqrt(21), so its two-sided Gaussian tail is erfc(sqrt(21/2)).
        approximate = audit.paired_test([-1.] * 21)
        self.assertAlmostEqual(approximate["pvalue"], math.erfc(math.sqrt(21. / 2.)), places=17)
        self.assertEqual(approximate["rank_biserial"], -1.)

    def test_relative_change_and_standardized_effect_report_undefined_cases(self):
        rows = [{"unit_id": "a"}] * 3 + [{"unit_id": "b"}]
        result = audit.paired_unit_statistics([0., 0., 0., 1.], [1., 1., 1., 0.],
                                            [0.] * 4, 1., rows, reps=100, seed=73)
        pooled = result["bootstrap"]["mae"]["window_pooled"]
        self.assertIn("relative_change_percent", pooled)
        self.assertAlmostEqual(pooled["relative_change_percent"], -100. * 2. / 3.)
        self.assertEqual(pooled["reference_point"], .75)
        self.assertEqual(pooled["candidate_point"], .25)
        self.assertEqual(result["bootstrap"]["mae"]["unit_macro"]["relative_change_percent"], 0.)
        self.assertEqual(result["paired_tests"]["mae"]["standardized_paired_effect_dz"], 0.)
        single = audit.paired_test([1.])
        self.assertIsNone(single["standardized_paired_effect_dz"])
        self.assertEqual(single["standardized_effect_status"], "undefined: fewer than two units")
        # Relative change at a zero reference and dz at zero variance are
        # undefined, even when a point delta is numerically available.
        zero = audit.paired_unit_statistics([0., 0.], [0., 0.], [0., 0.], 1.,
                                          [{"unit_id": "a"}, {"unit_id": "b"}], reps=100, seed=17)
        self.assertIsNone(zero["bootstrap"]["rmse"]["window_pooled"]["relative_change_percent"])
        self.assertEqual(zero["bootstrap"]["rmse"]["window_pooled"]["relative_change_status"],
                         "undefined: reference error is zero")
        self.assertIsNone(zero["paired_tests"]["rmse"]["standardized_paired_effect_dz"])
        self.assertEqual(zero["paired_tests"]["rmse"]["standardized_effect_status"],
                         "undefined: paired unit delta variance is zero")

    def test_same_pass_files_reproduce_gate_and_describe_seeds_without_replication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_fixture(root)
            report, draws = audit.build_report(root, reps=100, seed=17)
            self.assertTrue(report["verification"]["gate_matches_original"])
            self.assertTrue(report["gate"]["passes"])
            self.assertEqual(report["components"]["bat"]["n_units"], 2)
            self.assertEqual(report["components"]["bat"]["seed_description"]["independent_repeats"], 0)
            self.assertEqual(len(draws), 8)
            self.assertFalse(any(root.glob("*.pt")), "postprocessing must not need a tensor")

    def test_npz_byte_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_fixture(root)
            with (root / "final_bat_paired_predictions.npz").open("ab") as handle:
                handle.write(b"unexpected bytes")
            with self.assertRaisesRegex(ValueError, "hash"):
                audit.build_report(root, reps=100, seed=17)

    def test_unrounded_receipt_disagreement_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = make_fixture(root)
            receipt["results"]["bat"]["metrics"]["mae"] = 5e-13
            write_json(root / "final_receipt.json", receipt)
            gate_path = root / "same_partition_performance_gate.json"
            gate = json.loads(gate_path.read_text())
            gate["final_receipt_sha256"] = digest(root / "final_receipt.json")
            gate["metrics"]["bat"]["candidate_blend"]["mae"] = 5e-13
            write_json(gate_path, gate)
            with self.assertRaisesRegex(ValueError, "metric"):
                audit.build_report(root, reps=100, seed=17)

    def test_report_output_is_exclusive_and_csv_preserves_float_precision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_fixture(root)
            output = root / "statistics"
            receipt = audit.write_report(root, output, reps=100, seed=17)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(digest(output / "f1_gate_statistics.json"), receipt["report_sha256"])
            self.assertIn("candidate_hex", (output / "f1_full_precision_gate.csv").read_text())
            before = {p.name: digest(p) for p in output.iterdir()}
            with self.assertRaises(FileExistsError):
                audit.write_report(root, output, reps=100, seed=17)
            self.assertEqual(before, {p.name: digest(p) for p in output.iterdir()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
