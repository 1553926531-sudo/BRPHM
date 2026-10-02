import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("f1_leo600_partition_builder_20261002.py")
SPEC = importlib.util.spec_from_file_location("f1_leo600_builder", MODULE_PATH)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Leo600PartitionBuilderTests(unittest.TestCase):
    def test_template_selection_is_stable_and_balanced_without_label_fields(self):
        rows = []
        for line in ("bat", "rwa"):
            for beta in (0, 30, 60):
                for i in range(5):
                    rows.append({
                        "sample_id": f"{line.upper()}_LEO500_B{beta:02d}_H{i % 3}_L{i % 4}_S{i:03d}",
                        "line": line,
                        "orbit": "LEO500",
                        "beta_deg": str(beta),
                        "h_level": f"H{i % 3}",
                        "l_level": f"L{i % 4}",
                        "seed": str(1000 + i),
                        "yaml": f"configs/{i}.yaml",
                        "label": f"must-not-be-read-{i}",
                    })

        selected = builder.select_templates(rows, set(), per_cell=2)
        shuffled = builder.select_templates(list(reversed(rows)), set(), per_cell=2)
        self.assertEqual(
            [[x["sample_id"] for x in group] for group in selected],
            [[x["sample_id"] for x in group] for group in shuffled],
        )
        self.assertEqual(len(selected), 6)
        self.assertTrue(all(len(group) == 2 for group in selected))
        self.assertEqual({r["line"] for group in selected for r in group}, {"bat", "rwa"})
        self.assertEqual({int(r["beta_deg"]) for group in selected for r in group}, {0, 30, 60})
        self.assertTrue(all("label" not in r for group in selected for r in group))

    def test_config_rewrite_binds_new_orbit_seed_beta_and_aligned_bat_stop(self):
        source = (
            "sample_id: BAT_LEO500_B00_H0_L1_S001\n"
            "line: bat\n"
            "orbit: LEO500\n"
            "beta_deg: 0\n"
            "seed: 100001\n"
            "stop_time_max_s: 1500000\n"
            "est_tf_days: 9.5\n"
            "  bat.aging_scale: 200\n"
        )
        result = builder.rewrite_config(
            source,
            sample_id="BAT_LEO600_B30_H1_L2_S940",
            orbit="LEO600",
            beta_deg=30,
            seed=891940,
            stop_time_s=1_500_000,
            line="bat",
        )
        self.assertIn("orbit: LEO600\n", result)
        self.assertIn("beta_deg: 30\n", result)
        self.assertIn("seed: 891940\n", result)
        self.assertIn("stop_time_max_s: 1498140\n", result)
        self.assertIn("  bat.aging_scale: 200\n", result)

    def test_manifest_row_binds_environment_tile_to_declared_beta(self):
        source = {
            "sample_id": "RWA_LEO500_B30_H1_L1_S051",
            "line": "rwa",
            "orbit": "LEO500",
            "beta_deg": "30",
            "yaml": "configs/sim/sample/source.yaml",
            "out_mat": "data/raw/sim/rwa/source.mat",
            "gmat_env": "sim/gmat/out/env_LEO500_B30.mat",
            "seed": "100123",
            "stop_time_s": "27170",
            "est_tf_days": "0.1399",
        }
        row = builder.make_manifest_row(
            source,
            sample_id="RWA_LEO600_B30_H1_L1_S940",
            beta_deg=30,
            seed=891940,
        )
        self.assertEqual(row["orbit"], "LEO600")
        self.assertEqual(row["gmat_env"], "sim/gmat/out/env_LEO600_B30.mat")
        self.assertEqual(row["sample_id"], "RWA_LEO600_B30_H1_L1_S940")
        self.assertEqual(row["seed"], "891940")
        self.assertEqual(row["beta_deg"], "30")

    def test_rwa_config_keeps_stop_bound_and_rejects_missing_binding(self):
        source = (
            "sample_id: RWA_LEO500_B30_H1_L1_S051\n"
            "line: rwa\n"
            "orbit: LEO500\n"
            "beta_deg: 30\n"
            "seed: 100123\n"
            "stop_time_s: 27170\n"
        )
        result = builder.rewrite_config(
            source,
            sample_id="RWA_LEO600_B30_H1_L1_S946",
            orbit="LEO600",
            beta_deg=30,
            seed=891946,
            stop_time_s=27170,
            line="rwa",
        )
        self.assertIn("stop_time_s: 27170\n", result)
        self.assertNotIn("stop_time_max_s", result)
        with self.assertRaisesRegex(ValueError, "expected one orbit entry"):
            builder.rewrite_config(
                "sample_id: X\nline: rwa\nbeta_deg: 30\nseed: 1\nstop_time_s: 10\n",
                sample_id="RWA_LEO600_B30_H1_L1_S946",
                orbit="LEO600",
                beta_deg=30,
                seed=891946,
                stop_time_s=27170,
                line="rwa",
            )

    def test_template_exclusion_cannot_be_replaced_by_an_unregistered_row(self):
        rows = [{
            "sample_id": "RWA_LEO500_B00_H0_L1_S001",
            "line": "rwa",
            "orbit": "LEO500",
            "beta_deg": "0",
            "yaml": "configs/sample.yaml",
        }]
        with self.assertRaisesRegex(ValueError, "need 2 unexcluded templates"):
            builder.select_templates(rows, {rows[0]["sample_id"]}, per_cell=2)

    def test_gmat_validation_binding_requires_all_three_label_free_orbits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            results = []
            for beta in (0, 30, 60):
                beta_text = f"{beta:02d}"
                folder = cache / f"f1_leo600_b{beta_text.lower()}_20261002"
                folder.mkdir(parents=True)
                report = folder / f"LEO600_B{beta_text}.csv"
                eclipse = folder / f"LEO600_B{beta_text}_eclipse.txt"
                imported = root / f"env_LEO600_B{beta_text}.mat"
                report.write_text("report", encoding="utf-8")
                eclipse.write_text("events", encoding="utf-8")
                imported.write_bytes(b"mat")
                results.append({
                    "id": f"LEO600_B{beta_text}",
                    "report_file": str(report),
                    "eclipse_file": str(eclipse),
                    "out_file": str(imported),
                    "grid_points": 259201,
                    "checks": [f"[PASS] V{i}" for i in range(1, 9)],
                })
            validation = root / "validation_manifest.json"
            validation.write_text(json.dumps({
                "schema": "f1_leo600_import_validation_v3",
                "semantic_labels_read": False,
                "final_label_access": False,
                "results": results,
            }), encoding="utf-8")
            records = builder.load_validated_environment_inputs(validation, cache)
            self.assertEqual(len(records), 3)
            self.assertTrue(all(len(row["checks"]) == 8 for row in records))
            doc = json.loads(validation.read_text(encoding="utf-8"))
            doc["final_label_access"] = True
            validation.write_text(json.dumps(doc), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "label access"):
                builder.load_validated_environment_inputs(validation, cache)


if __name__ == "__main__":
    unittest.main()
