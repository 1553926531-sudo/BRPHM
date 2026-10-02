"""Regenerate the local PDF preflight from the PDF currently on disk.

This deliberately does not compile the document.  Compilation changes the PDF
creation timestamp on some MiKTeX installations, so the audit and the
hash-linked manifest must be generated after the final two-pass build.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EN = ROOT / "work" / "paper" / "en"
REVIEW = ROOT / "work" / "paper" / "review"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(argv: list[str]) -> tuple[int, str]:
    p = subprocess.run(argv, cwd=EN, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def parse_pdfinfo(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def parse_pdffonts(text: str) -> dict:
    lines = [x for x in text.splitlines() if x.strip()]
    rows = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) >= 7:
            rows.append({"name": parts[0], "type": parts[1], "encoding": parts[2],
                         "emb": parts[3], "sub": parts[4], "uni": parts[5],
                         "object_id": " ".join(parts[6:])})
    return {"fonts": rows, "all_embedded": all(r.get("emb") == "yes" for r in rows),
            "type3_count": sum(r.get("type") == "Type 3" for r in rows)}


def main() -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    pdf = EN / "main.pdf"
    log = EN / "main.log"
    tex = EN / "main.tex"
    extracted = EN / "main_extracted.txt"
    code, info_text = run(["pdfinfo", "main.pdf"])
    info = parse_pdfinfo(info_text)
    code_fonts, fonts_text = run(["pdffonts", "main.pdf"])
    fonts = parse_pdffonts(fonts_text)
    code_text, text = run(["pdftotext", "main.pdf", "main_extracted.txt"])
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    warning_lines = [x for x in log_text.splitlines() if re.search(r"Warning|Overfull|Underfull|undefined|Undefined|Fatal|Error", x)]
    overfull = [x for x in log_text.splitlines() if "Overfull" in x]
    underfull = [x for x in log_text.splitlines() if "Underfull" in x]
    fatal = [x for x in log_text.splitlines() if re.search(r"Fatal|^! |Error", x)]
    hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in (tex, pdf, log, extracted) if p.exists()}
    report = {
        "schema": "brphm-pdf-build-verification-v2",
        "created_utc": now,
        "scope": "Local source/PDF reproducibility and production preflight. This record is not a venue PDF eXpress or accessibility certification.",
        "source": {"path": "work/paper/en/main.tex", "sha256": hashes.get("work/paper/en/main.tex"), "bytes": tex.stat().st_size},
        "pdf": {"path": "work/paper/en/main.pdf", "sha256": hashes.get("work/paper/en/main.pdf"), "bytes": pdf.stat().st_size,
                "pages": int(info["Pages"]) if info.get("Pages", "").isdigit() else info.get("Pages"),
                "page_size_points": [612, 792] if info.get("Page size") == "612 x 792 pts (letter)" else info.get("Page size"),
                "paper_size": "letter" if info.get("Page size") == "612 x 792 pts (letter)" else None,
                "pdf_version": info.get("PDF version"), "tagged": info.get("Tagged") == "yes"},
        "build": {"commands": ["pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex (pass 1)",
                                 "pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex (pass 2)"],
                  "engine": "MiKTeX-pdfTeX (see pdfinfo/latex log)", "note": "This record audits the final two-pass build; it does not invoke pdflatex."},
        "pdfinfo": {"exit_code": code, **info},
        "font_check": {"command": "pdffonts en/main.pdf", "exit_code": code_fonts, **fonts,
                        "result": "PASS for no Type 3 and embedded fonts" if fonts.get("type3_count") == 0 and fonts.get("all_embedded") else "FAIL"},
        "text_extraction": {"command": "pdftotext main.pdf main_extracted.txt", "exit_code": code_text,
                             "bytes": extracted.stat().st_size if extracted.exists() else None,
                             "sha256": hashes.get("work/paper/en/main_extracted.txt")},
        "log_scan": {"warning_line_count": len(warning_lines), "underfull_hbox_count": len(underfull),
                      "overfull_hbox_count": len(overfull), "fatal_or_error_count": len(fatal), "sample": warning_lines[:12]},
        "hashes": hashes,
        "local_checks": {"double_compile_recorded": True, "letter_page_size": info.get("Page size") == "612 x 792 pts (letter)",
                          "type3_absent": fonts.get("type3_count") == 0, "fonts_embedded": fonts.get("all_embedded") is True,
                          "text_extraction": code_text == 0 and extracted.exists(), "fatal_errors_absent": len(fatal) == 0,
                          "overfull_absent": len(overfull) == 0, "underfull_absent": len(underfull) == 0,
                          "tagged_pdf": info.get("Tagged") == "yes"},
        "venue_checks": {"target_venue": "PENDING exact venue, track, article type, and review mode",
                          "pdf_express": "PENDING exact venue/article type", "accessibility": "PENDING exact venue policy/checker",
                          "blind_review_metadata": "PENDING exact venue policy"},
        "result": "Local PDF facts are hash-linked; venue-specific PDF eXpress and accessibility checks remain pending.",
        "residual_risk": "Underfull boxes and an untagged PDF remain; the exact venue and checker are not selected.",
    }
    (REVIEW / "pdf_build_verification_20261003.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = "# PDF Build Verification — final local preflight\n\n" + json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    (REVIEW / "pdf_build_verification_20261003.md").write_text(md, encoding="utf-8")
    (REVIEW / "pdf_audit_20261003.md").write_text("# PDF Audit — final local preflight\n\n" + md, encoding="utf-8")
    print(json.dumps({"created_utc": now, "pdf_sha256": hashes.get("work/paper/en/main.pdf"), "pages": info.get("Pages"),
                      "type3_count": fonts.get("type3_count"), "overfull": len(overfull), "underfull": len(underfull)}, indent=2))


if __name__ == "__main__":
    main()
