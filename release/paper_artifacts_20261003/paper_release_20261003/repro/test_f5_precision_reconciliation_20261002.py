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
SCRIPT = PAPER / "repro/build_f5_precision_ledger.py"
LEDGER = PAPER / "review/f5_unit_metrics_20261002/f5_evidence_ledger_reconciled.json"


def test_f5_reconciles_frozen_fold_gate_without_mislabeling_replay_pairs() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert ledger["gate"]["fold_count"] == 6
    assert ledger["gate"]["all_primary_metrics_nonregressive"] is True
    assert ledger["reference_binding"]["summary_sha256_matches_receipt"] is True
    assert ledger["candidate_unit_reaggregation"]["all_six_folds_match"] is True
    assert ledger["unit_pairing"]["frozen_reference_pairing"] == "NOT_AVAILABLE"
    assert ledger["unit_pairing"]["replay_csv_role"] == "DIAGNOSTIC_REPLAY_ONLY"
    assert ledger["unit_pairing"]["replay_reference_fold_mismatches"] > 0
