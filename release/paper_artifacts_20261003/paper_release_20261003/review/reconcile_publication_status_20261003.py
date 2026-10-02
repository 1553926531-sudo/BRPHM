from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

replacements = {
    "EVIDENCE_CLOSED_PAPER_PATCH_PENDING": "EVIDENCE_CLOSED_CURRENT_ARTIFACTS_BOUND_VENUE_METADATA_PENDING",
    "The paper still needs a machine-readable artifact link and an explicit statement that the gate uses unrounded values.": "The paper now links the machine-readable artifact and explicitly states that the gate uses unrounded values; venue-specific metadata remain pending.",
    "**Result:** F5 evidence is closed for the development artifact; paper patch remains pending.": "**Result:** F5 evidence and the manuscript patch are closed for the current artifact; venue-specific metadata remain pending.",
    "**Result:** F6 evidence is closed for the available unit/fold/seed diagnostics; paper patch remains pending.": "**Result:** F6 evidence and the manuscript patch are closed for the available unit/fold/seed diagnostics; venue-specific metadata remain pending.",
    "The manuscript body remains pending the complete evidence pass.": "The current manuscript body contains the F8 correction and the complete source-gate evidence boundary; venue-specific presentation checks remain pending.",
    "the PDF rebuild is still pending.": "the local PDF rebuild is recorded in `review/pdf_build_verification_20261003.json`.",
}

paths = [
    ROOT / "work" / "paper" / "review" / "f5_unit_metrics_20261002" / "f5_evidence_ledger.md",
    ROOT / "work" / "paper" / "review" / "f5_unit_metrics_20261002" / "f5_evidence_ledger.json",
    ROOT / "work" / "paper" / "review" / "f6_statistics_20261002" / "f6_evidence_ledger.md",
    ROOT / "work" / "paper" / "review" / "f6_statistics_20261002" / "f6_statistics.json",
    ROOT / "work" / "paper" / "review" / "f8_source_gate_20261002" / "f8_evidence_ledger.md",
    ROOT / "work" / "paper" / "review" / "f1_evidence_ledger.md",
]

for path in paths:
    text = path.read_text(encoding="utf-8")
    old = text
    for source, target in replacements.items():
        text = text.replace(source, target)
    if text != old:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"updated {path.relative_to(ROOT)}")

