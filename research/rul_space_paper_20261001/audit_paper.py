import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
summary = json.loads((ROOT / "evidence" / "evidence_summary.json").read_text(encoding="utf-8"))
folds = summary["final_formal_folds"]
assert len(folds) == 6
assert all(row["rmse_delta"] <= 0 and row["mae_delta"] <= 0 for row in folds)
assert summary["final_provenance"]["outer_evaluated_once"] is True
assert summary["final_provenance"]["outer_test_used_for_selection"] is False
assert summary["final_provenance"]["sealed_holdout_read"] is False
assert summary["final_provenance"]["a1_b1_source_heldout_read"] is False
assert summary["final_provenance"]["canonical_data_modified"] is False
assert summary["final_provenance"]["competition_line_modified"] is False

final_receipt = ROOT.parent / "rul_next_electrochemical" / "temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001_remote.json"
assert final_receipt.exists()
receipt_hash = hashlib.sha256(final_receipt.read_bytes()).hexdigest()
assert summary["generated_from"][final_receipt.name] == receipt_hash

for rel in ["en/main.tex", "zh/main.tex", "en/main.pdf", "zh/main.pdf", "en/paper_en.docx", "zh/paper_zh.docx"]:
    p = ROOT / rel
    assert p.exists() and p.stat().st_size > 0, rel

for rel in ["en/main.tex", "zh/main.tex"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    markers = ["1.94580391", "0.02072511", "10^{-5}", "holdout"]
    markers.append("population" if rel.startswith("en/") else "总体范围")
    for marker in markers:
        assert marker in text, f"{marker} missing from {rel}"

report = {
    "final_method": folds[0]["method_id"],
    "formal_fold_count": len(folds),
    "all_rmse_and_mae_deltas_nonpositive": True,
    "receipt_sha256": receipt_hash,
    "pdf_bytes": {rel: (ROOT / rel).stat().st_size for rel in ["en/main.pdf", "zh/main.pdf"]},
    "docx_bytes": {rel: (ROOT / rel).stat().st_size for rel in ["en/paper_en.docx", "zh/paper_zh.docx"]},
    "provenance": summary["final_provenance"],
}
(ROOT / "paper_audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
