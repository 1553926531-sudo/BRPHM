from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve()


def project_root() -> Path:
    candidates = (HERE.parent, *HERE.parents)
    for candidate in candidates:
        if (candidate / "work" / "paper").is_dir():
            return candidate
    for candidate in candidates:
        if (candidate / "review").is_dir() and (candidate / "repro").is_dir():
            return candidate
    raise RuntimeError(f"cannot resolve project root from {HERE}")


ROOT = project_root()
PAPER = ROOT / "work" / "paper" if (ROOT / "work" / "paper").is_dir() else ROOT
F5_SCRIPT = PAPER / "repro/build_f5_precision_ledger.py"
F6_SCRIPT = PAPER / "repro/build_f6_statistics_20261002.py"
OUTPUT = PAPER / "review/f6_statistics_20261002/f6_statistics_reconciled.json"


def test_f6_separates_frozen_benchmark_uncertainty_from_replay_sensitivity() -> None:
    subprocess.run([sys.executable, str(F5_SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(F6_SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)

    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert report["unit_pairing"]["frozen_reference_pairing_available"] is False
    assert report["unit_pairing"]["replay_csv_role"] == "DIAGNOSTIC_REPLAY_ONLY"
    assert report["frozen_fold_benchmark"]["fold_count"] == 6
    assert report["frozen_fold_benchmark"]["unit_cluster_bootstrap"]["window_counts_preserved"] is True
    assert report["replay_control_sensitivity"]["paired_unit_tests_are_diagnostic_only"] is True
    assert report["replay_control_sensitivity"]["multiplicity_family_size"] == 12
    assert report["seed_sensitivity"]["seed_count"] == 3
    assert report["seed_sensitivity"]["inferential_status"] == "DESCRIPTIVE_ONLY"
