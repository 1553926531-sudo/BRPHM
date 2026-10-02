from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "work" / "paper" / "review"

replacements = {
    "2bc6e20a496ee33babeb656af2bdfc79ca2138bce4211bcb0e49f8b45ca4b766": "fbb2d6e4359f187e575551ba709f947b14e1301a502ab51fddd08aa5860325ef",
    "28e64036194decd95bbb068b0994c72cf7cd371496684c7befb36f42683fe7c9": "fbb2d6e4359f187e575551ba709f947b14e1301a502ab51fddd08aa5860325ef",
    "a55fc02a3f05a8bb6f011fe84852ecbb969786b7d09f2c34cf43999df4138fb9": "451ebc0929e94c5a4d19bd16a077adad8eb52012e9d05165f02272636e69f3d4",
    "fbb2d6e4359f187e575551ba709f947b14e1301a502ab51fddd08aa5860325ef": "80dc05172481586a629449cf3df595fea0fda48bfe1d5e953f6fbca6875511db",
}

paths = [
    REVIEW / "f1_closeout_20261002.md",
    REVIEW / "f1_evidence_ledger.md",
    REVIEW / "f1_evidence_ledger.json",
    REVIEW / "pdf_build_verification_20261003.json",
    REVIEW / "pdf_audit_20261003.md",
]

for path in paths:
    text = path.read_text(encoding="utf-8")
    old = text
    for source, target in replacements.items():
        text = text.replace(source, target)
    if text != old:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"updated {path.relative_to(ROOT)}")
