import json
import unittest

import f1_clean_final_test_leo600_20261002 as f1
from f1_clean_final_test_leo600_20261002 import (
    build_candidate_snapshot,
    compare_performance,
    validate_partition,
)


class SourceFloorRouteSelectionTests(unittest.TestCase):
    @staticmethod
    def receipt(route_sweep):
        directions = [
            "LEO500->LEO550",
            "LEO500->LEO700",
            "LEO550->LEO500",
            "LEO550->LEO700",
            "LEO700->LEO500",
            "LEO700->LEO550",
        ]
        component = {
            "input_tensor_sha256": "b" * 64,
            "selected_route": {"route_id": "old-route"},
            "route_sweep": route_sweep,
        }
        return {
            "method_id": "old-route-selection",
            "source_protocol": {
                "directions": directions,
                "route_catalog": {
                    "alpha_families": [[0.0, 0.5], [0.1, 0.5], [0.1, 0.25]],
                    "route_count": len(route_sweep),
                },
            },
            "components": {"bat": component, "rwa": component},
            "formal": {"must_not_be_copied": True},
        }

    @staticmethod
    def score(route_id, *, passes=True, ks=0.2, rmse=1.0, mae=1.0):
        return {
            "route_id": route_id,
            "gate": {
                "passes": passes,
                "worst_residual_ks": ks,
                "mean_rmse": rmse,
                "mean_mae": mae,
            },
        }

    def test_reconstructs_mask_direction_alphas_before_target_averaging(self):
        receipt = self.receipt([
            self.score("family0_mask00"),
            self.score("family1_mask04"),
        ])

        selector = getattr(f1, "select_source_floor_candidate", None)
        self.assertIsNotNone(selector, "source-floor selection must be implemented")
        selected = selector(receipt)

        expected = {"LEO500": 0.3, "LEO550": 0.1, "LEO700": 0.1}
        self.assertEqual(selected["components"]["bat"]["selected_route"]["route_id"], "family1_mask04")
        self.assertEqual(selected["components"]["bat"]["selected_route"]["alpha_by_target"], expected)
        self.assertNotIn("formal", selected)

    def test_tie_break_uses_residual_ks_after_total_and_max_alpha(self):
        receipt = self.receipt([
            self.score("family0_mask00", ks=0.0),
            self.score("family1_mask00", ks=0.08),
            self.score("family2_mask00", ks=0.03),
        ])

        selector = getattr(f1, "select_source_floor_candidate", None)
        self.assertIsNotNone(selector, "source-floor selection must be implemented")
        selected = selector(receipt)

        self.assertEqual(selected["components"]["bat"]["selected_route"]["route_id"], "family2_mask00")
        self.assertEqual(selected["components"]["bat"]["selected_route"]["alpha_by_target"], {
            "LEO500": 0.1, "LEO550": 0.1, "LEO700": 0.1,
        })

    def test_rejects_source_gate_with_no_route_above_the_alpha_floor(self):
        receipt = self.receipt([self.score("family0_mask00")])

        selector = getattr(f1, "select_source_floor_candidate", None)
        self.assertIsNotNone(selector, "source-floor selection must be implemented")
        with self.assertRaisesRegex(ValueError, "no source-gate route meets"):
            selector(receipt)

    def test_registered_v15_sweep_selects_the_floor_routes_from_source_gate_only(self):
        from pathlib import Path

        receipt_path = Path(__file__).parents[1] / "review" / "candidate_v15_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        selector = getattr(f1, "select_source_floor_candidate", None)
        self.assertIsNotNone(selector, "source-floor selection must be implemented")
        selected = selector(receipt)

        self.assertEqual(selected["components"]["bat"]["selected_route"]["route_id"], "family0_mask23")
        self.assertEqual(selected["components"]["rwa"]["selected_route"]["route_id"], "family1_mask00")
        self.assertEqual(selected["components"]["bat"]["source_gate_selection"]["floor_eligible_count"], 1)
        self.assertEqual(selected["components"]["rwa"]["source_gate_selection"]["floor_eligible_count"], 43)
        self.assertNotIn("formal", selected)


class CandidateSnapshotTests(unittest.TestCase):
    def test_unseen_orbit_uses_frozen_uniform_alpha_floor(self):
        candidate = {
            "method_id": "frozen-candidate",
            "source_protocol": {"uniform_alpha_floor": 1e-5},
            "components": {
                name: {"selected_route": {
                    "route_id": f"{name}-route",
                    "alpha_by_target": {"LEO500": 0.1, "LEO550": 0.2, "LEO700": 0.3},
                }}
                for name in ("bat", "rwa")
            },
        }

        snapshot = build_candidate_snapshot(candidate, "a" * 64, "LEO600")

        self.assertEqual(snapshot["components"]["bat"]["selected_route"]["alpha_by_target"]["LEO600"], 1e-5)
        self.assertEqual(snapshot["components"]["rwa"]["selected_route"]["alpha_by_target"]["LEO600"], 1e-5)
        self.assertEqual(snapshot["derivation"]["base_candidate_receipt_sha256"], "a" * 64)

    def test_snapshot_rejects_incomplete_registered_route(self):
        candidate = {
            "method_id": "frozen-candidate",
            "source_protocol": {"uniform_alpha_floor": 1e-5},
            "components": {
                name: {"selected_route": {
                    "route_id": f"{name}-route",
                    "alpha_by_target": {"LEO500": 0.1, "LEO550": 0.2},
                }}
                for name in ("bat", "rwa")
            },
        }

        with self.assertRaisesRegex(ValueError, "registered targets"):
            build_candidate_snapshot(candidate, "a" * 64, "LEO600")


class FinalPartitionTests(unittest.TestCase):
    def test_partition_rejects_any_non_target_orbit_unit(self):
        document = {
            "schema": "brphm-f1-raw-sim-partition-v1",
            "semantic_labels_read": False,
            "final_label_access": False,
            "rows": [
                {"sample_id": "BAT_LEO600_B30_H0_L1_S931", "product_line": "bat"},
                {"sample_id": "RWA_LEO550_B30_H0_L1_S932", "product_line": "rwa"},
            ],
        }

        with self.assertRaisesRegex(ValueError, "LEO600"):
            validate_partition(document, "LEO600")

    def test_partition_accepts_new_orbit_both_components_without_label_access(self):
        document = {
            "schema": "brphm-f1-raw-sim-partition-v1",
            "semantic_labels_read": False,
            "final_label_access": False,
            "rows": [
                {"sample_id": "BAT_LEO600_B30_H0_L1_S931", "product_line": "bat"},
                {"sample_id": "RWA_LEO600_B30_H0_L1_S932", "product_line": "rwa"},
            ],
        }

        self.assertEqual(validate_partition(document, "LEO600"), {"bat": 1, "rwa": 1})


class PerformanceGateTests(unittest.TestCase):
    def test_gate_requires_no_regression_and_at_least_one_strict_gain(self):
        candidate = {"bat": {"rmse": 0.9, "mae": 0.8}, "rwa": {"rmse": 0.7, "mae": 0.6}}
        reference = {"bat": {"rmse": 1.0, "mae": 0.8}, "rwa": {"rmse": 0.7, "mae": 0.6}}

        result = compare_performance(candidate, reference)

        self.assertTrue(result["passes"])
        self.assertTrue(result["strict_gain"])

    def test_gate_fails_if_any_component_metric_regresses(self):
        candidate = {"bat": {"rmse": 0.9, "mae": 0.81}, "rwa": {"rmse": 0.7, "mae": 0.6}}
        reference = {"bat": {"rmse": 1.0, "mae": 0.8}, "rwa": {"rmse": 0.7, "mae": 0.6}}

        result = compare_performance(candidate, reference)

        self.assertFalse(result["passes"])
        self.assertIn("bat.mae", result["regressions"])


if __name__ == "__main__":
    unittest.main()
