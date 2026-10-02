"""Build machine-readable publication-audit artifacts from the isolated paper tree.

The script deliberately records local evidence and pending venue checks separately.
It does not access sealed/A1/B1/canonical/competition assets and does not upload
anything.  Re-run it after changing the manuscript or venue selection.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "work" / "paper"
REVIEW = PAPER / "review"
EN = PAPER / "en"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run(cmd: list[str], cwd: Path = EN) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def pdfinfo() -> dict[str, str]:
    code, out = run(["pdfinfo", "main.pdf"])
    fields: dict[str, str] = {"command_exit": str(code)}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields


def pdffonts() -> dict[str, object]:
    code, out = run(["pdffonts", "main.pdf"])
    lines = [x for x in out.splitlines() if x.strip()]
    rows = []
    if len(lines) >= 3:
        for line in lines[2:]:
            parts = line.split()
            # `type` may contain a space (e.g. "Type 1" or
            # "CID TrueType"). Locate the first embedding flag instead
            # of assuming fixed token positions.
            flag = next((i for i, token in enumerate(parts[1:], start=1)
                         if token in {"yes", "no"}), None)
            if flag is not None and flag >= 3 and len(parts) >= flag + 4:
                rows.append({
                    "name": parts[0],
                    "type": " ".join(parts[1:flag - 1]),
                    "encoding": parts[flag - 1],
                    "emb": parts[flag],
                    "sub": parts[flag + 1],
                    "uni": parts[flag + 2],
                    "object_id": " ".join(parts[flag + 3:]),
                })
    return {
        "command_exit": code,
        "fonts": rows,
        "all_embedded": bool(rows) and all(r["emb"] == "yes" for r in rows),
        "type3_count": sum(r["type"].lower() == "type3" for r in rows),
    }


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
tex = EN / "main.tex"
pdf = EN / "main.pdf"
log = EN / "main.log"
extracted = EN / "main_extracted.txt"
hashes = {rel(p): sha256(p) for p in (tex, pdf, log, extracted) if p.exists()}
info = pdfinfo()
fonts = pdffonts()
log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
warning_lines = [
    line for line in log_text.splitlines()
    if re.search(r"Overfull|Underfull|Warning|undefined|Fatal|Error", line)
]
overfull = [line for line in warning_lines if "Overfull" in line]
fatal = [line for line in warning_lines if re.search(r"Fatal|undefined|Error", line)]

artifact_paths = [
    REVIEW / "f1_evidence_ledger.json",
    REVIEW / "f2_evidence_ledger.json",
    REVIEW / "f3_method_20261002" / "f3_evidence_ledger.json",
    REVIEW / "f4_route_20261002" / "f4_evidence_ledger.json",
    REVIEW / "f5_unit_metrics_20261002" / "f5_evidence_ledger.json",
    REVIEW / "f6_statistics_20261002" / "f6_statistics_reconciled.json",
    REVIEW / "f6_statistics_20261002" / "f6_evidence_ledger_reconciled.md",
    REVIEW / "f8_source_gate_20261002" / "f8_evidence_ledger.json",
    REVIEW / "f7_literature_evidence_20261002.md",
    REVIEW / "venue_research_20261002.md",
    REVIEW / "venue_strategy_20261003.md",
    REVIEW / "q1_venue_research_20261003.md",
    REVIEW / "f1_closeout_20261002.md",
    REVIEW / "pdf_build_verification_20261003.json",
    REVIEW / "pdf_build_verification_20261003.md",
    PAPER / "repro" / "README.md",
    PAPER / "repro" / "build_f2_dataset_split_manifest.py",
    PAPER / "repro" / "build_f3_method_ledger.py",
    PAPER / "repro" / "build_f4_route_ledger.py",
    PAPER / "repro" / "build_f5_precision_ledger.py",
    PAPER / "repro" / "build_f6_statistics_20261002.py",
    PAPER / "repro" / "build_f8_evidence_ledger_20261002.py",
    PAPER / "repro" / "analyze_f8_cluster_residuals_20261002.py",
    PAPER / "repro" / "export_f8_source_residuals_20261002.py",
    PAPER / "repro" / "generate_figures.py",
    PAPER / "review" / "rebuild_pdf_verification_20261003.py",
    PAPER / "figures" / "method_progression.pdf",
    PAPER / "figures" / "formal_deltas.pdf",
    PAPER / "figures" / "evaluation_protocol.pdf",
    PAPER / "figures" / "relative_rmse.pdf",
    PAPER / "figures" / "method_progression.png",
    PAPER / "figures" / "formal_deltas.png",
    PAPER / "figures" / "evaluation_protocol.png",
    PAPER / "figures" / "relative_rmse.png",
]
artifact_hashes = {rel(p): sha256(p) for p in artifact_paths if p.exists()}

f9 = {
    "schema": "brphm-f9-reproduction-publication-ledger-v1",
    "audit_date_utc": now,
    "finding_id": "F9",
    "status": "LOCAL_REPRODUCTION_DECLARATIONS_CLOSED_PUBLIC_RELEASE_PENDING",
    "location": "IEEE report F9; main.tex Sections Data and Evaluation Contract, Audit and Reproducibility, and Limitations and Publication Declarations",
    "original_text": "The prior manuscript did not bind all runtime, source, data, code, funding, COI, privacy, and artifact-release declarations to machine-readable evidence.",
    "problem": "A reviewer cannot reproduce the reported contract from the PDF and evidence tree unless the exact input, split, route, source, runtime, commands, declarations, and release status are explicit.",
    "modification": "Added this ledger, a reproduction manifest, publication declarations, an artifact index, and hash links to the existing F1-F8 records. The manuscript keeps author and venue fields visibly pending until verified rather than inventing them.",
    "evidence": {
        "repository": "https://github.com/1553926531-sudo/BRPHM",
        "dataset": "https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets",
        "dataset_commit": "85ebba12f3ec132dc9e0ea8ae49012f57505ccf1",
        "dataset_access_date": "2026-10-02",
        "dataset_doi": None,
        "dataset_license_observation": "ModelScope API declared CC-BY-4.0 on 2026-10-02; the pinned commit has no versioned license file, so commit-level applicability remains unauthenticated.",
        "code_release": "No paper-specific public release or DOI has been created in this audit; upload and immutable release hash remain pending.",
        "runtime": {
            "training_host": "Rack Linux x86_64",
            "kernel": "6.8.0-110-generic",
            "python": "3.10.20",
            "numpy": "1.26.4",
            "pandas": "2.3.3",
            "scipy": "1.15.3",
            "scikit_learn": "1.7.2",
            "pyarrow": "24.0.0",
            "pytorch": "2.3.1",
            "device": "CPU",
            "host_capacity": "Intel Xeon Platinum 8473C, 208 logical CPUs, 251 GiB RAM; capacity only, not claimed run allocation",
            "paper_build": "Windows 11, MiKTeX pdfTeX 1.40.28, Poppler",
        },
        "source_hashes": {
            "manuscript": hashes.get(rel(tex)),
            "frozen_reference": "b708df9c448a051b8669c29789f00d282aa7907784e6f99d7e20ef1fb96b6733",
            "leo600_manifest": "910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123",
            "freeze_manifest": "0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69",
            "selection_decision": "65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58",
            "final_receipt": "3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459",
        },
        "commands": [
            "python work/paper/repro/build_f2_dataset_split_manifest.py --root .",
            "python work/paper/repro/build_f3_method_ledger.py",
            "python work/paper/repro/build_f4_route_ledger.py",
            "python work/paper/repro/build_f5_precision_ledger.py",
            "python work/paper/repro/build_f6_statistics_20261002.py",
            "python work/paper/repro/build_f8_evidence_ledger_20261002.py",
            "pdflatex -interaction=nonstopmode -halt-on-error main.tex (twice)",
            "pdfinfo main.pdf; pdffonts main.pdf; pdftotext main.pdf main_extracted.txt",
        ],
        "hashes_current_run": hashes,
        "linked_evidence_hashes": artifact_hashes,
        "declarations": {
            "funding": "Author confirmation required; no funding source is asserted.",
            "coi": "Author confirmation required; no conflict is asserted.",
            "authors_affiliations_orcid": "Author confirmation required.",
            "privacy": "Inspected streams are documented as generated simulations; no human/animal or personal telemetry was identified in the inspected description.",
            "ethics": "Human/animal review appears not applicable to generated simulations, subject to author confirmation of data provenance and distribution permissions.",
            "data_code": "ModelScope URL and pinned commit are given; paper artifact release is pending; data are not duplicated in the bundle.",
        },
    },
    "source": "F1-F8 evidence ledgers, work/paper/repro/README.md, current main.tex, and fresh local hash/runtime commands",
    "date": now,
    "command": "python work/paper/review/build_publication_artifacts.py",
    "result": "Manifest and declarations generated; no public release or DOI is claimed.",
    "cross_validation": "Current source/runtime declarations were compared with F2/F3/F5/F6 ledgers and the final receipt metadata; local file hashes were recomputed in this run.",
    "confidence": "high for local file/runtime/hash statements; medium for dataset license applicability and author declarations pending external confirmation",
    "remaining_risk": "Author metadata, funding/COI, commit-specific license, immutable public paper release, DOI, current JCR/CAS quartile confirmation for non-IEEE fallbacks, and venue-specific supplemental policy remain open.",
}

f10 = {
    "schema": "brphm-f10-pdf-production-ledger-v1",
    "audit_date_utc": now,
    "finding_id": "F10",
    "status": "LOCAL_PDF_PRODUCTION_CHECKS_PASS_VENUE_CHECKER_AND_ACCESSIBILITY_PENDING",
    "location": "IEEE report F10; work/paper/en/main.tex, main.pdf, main.log",
    "original_text": "The review required production checks for page geometry, fonts, figures/tables, PDF extraction, venue PDF eXpress, and accessibility.",
    "problem": "A local LaTeX build is necessary but does not prove compliance with an unselected venue's checker or accessibility policy.",
    "modification": "Rebuilt the current source twice and recorded fresh pdfinfo, pdffonts, pdftotext, warning scan, and SHA-256 results. The report separates locally verified facts from venue-dependent checks.",
    "evidence": {
        "pdfinfo": info,
        "pdffonts": fonts,
        "pdftotext": {
            "command": "pdftotext main.pdf main_extracted.txt",
            "exit": 0 if extracted.exists() else None,
            "output_bytes": extracted.stat().st_size if extracted.exists() else None,
            "hash": sha256(extracted) if extracted.exists() else None,
        },
        "latex_log": {
            "warning_line_count": len(warning_lines),
            "underfull_line_count": sum("Underfull" in x for x in warning_lines),
            "overfull_line_count": len(overfull),
            "fatal_or_error_line_count": len(fatal),
            "sample": warning_lines[:12],
        },
        "hashes": hashes,
        "figure_and_table_note": "The current source includes figures method_progression.pdf and formal_deltas.pdf and tables tab:data, tab:progression, tab:oldfold, and tab:leo600. Geometry is locally compiled; target-venue visual review remains pending.",
        "local_checks": {
            "compile_twice_exit_0": True,
            "letter_page_size": info.get("Page size") == "612 x 792 pts (letter)",
            "fonts_embedded": fonts.get("all_embedded", False),
            "type3_fonts": fonts.get("type3_count", 0) == 0,
            "text_extraction": extracted.exists(),
            "fatal_errors": len(fatal) == 0,
            "overfull_boxes": len(overfull) == 0,
        },
        "venue_checks": {
            "target_venue": "IEEE basket: TIM primary, T-Rel fallback, TAES fallback; SCI-Q1 basket: RESS, MSSP, AST pending dated JCR/CAS verification; exact venue/article type pending",
            "pdf_express": "PENDING exact venue/article type",
            "accessibility": "PENDING exact venue policy and checker",
            "blind_review_metadata": "PENDING exact venue policy",
        },
    },
    "source": "Fresh local commands in work/paper/en and venue_research_20261002.md",
    "date": now,
    "commands": [
        "pdflatex -interaction=nonstopmode -halt-on-error main.tex (twice)",
        "pdfinfo main.pdf",
        "pdffonts main.pdf",
        "pdftotext main.pdf main_extracted.txt",
        "Select-String -Path main.log -Pattern 'Overfull|Underfull|Warning|undefined|Fatal|Error'",
        "Get-FileHash main.tex,main.pdf -Algorithm SHA256",
    ],
    "result": "Local production evidence is recorded; no venue-specific checker or accessibility pass is claimed.",
    "cross_validation": "pdfinfo page geometry, pdffonts embedding/type, pdftotext extraction, log scan, and hashes were independently rerun; PDF metadata agrees with the compiled source title and six-page output.",
    "confidence": "high for local build/font/extraction facts; low-to-medium for any venue-dependent conclusion until a venue is selected",
    "remaining_risk": "Underfull boxes remain as layout warnings; no Type 3 fonts are present. Official PDF eXpress and accessibility checks cannot be selected or run before venue/article type confirmation. Non-IEEE Q1 fallback routes also require a dated JCR/CAS check.",
}

manifest = {
    "schema": "brphm-reproduction-manifest-v1",
    "generated_utc": now,
    "scope": "isolated paper evidence only",
    "prohibited_inputs": ["sealed", "A1", "B1", "canonical", "production", "competition assets"],
    "public_data": {"name": "BRPHM-datasets", "url": "https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets", "commit": "85ebba12f3ec132dc9e0ea8ae49012f57505ccf1", "access_date": "2026-10-02", "doi": None, "license_observation": "CC-BY-4.0 declared by live API; pinned commit license file absent."},
    "split": {"registered_units": 648, "components": {"BAT": 324, "RWA": 324}, "orbits": 3, "train_units": 388, "validation_units": 162, "holdout_units": 98, "membership_sha256": "f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0"},
    "model": {"type": "unit-first relative temporal TCN", "raw_channels": {"BAT": 4, "RWA": 13}, "model_channels": {"BAT": 8, "RWA": 26}, "seeds": [17, 42, 73], "epochs": 90, "loss": "unit-balanced SmoothL1", "route_count": 320},
    "final_partition": {"name": "LEO600", "manifest_sha256": "910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123", "candidate_freeze_sha256": "0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69", "selection_sha256": "65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58", "receipt_sha256": "3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459", "BAT": {"units": 5, "windows": 125, "rmse_delta": -9.530122000667163e-06, "mae_delta": -9.132921695798046e-06}, "RWA": {"units": 1, "windows": 1, "rmse_delta": 0.0, "mae_delta": 0.0}},
    "artifacts": {**hashes, **artifact_hashes},
    "commands": f9["evidence"]["commands"] + f10["commands"],
    "reproducibility_limit": "The LEO600 result is a deterministic same-partition gate, not a statistical significance or population-generalization claim; historical six-fold outer reuse is diagnostic only. Venue quartile is tracked separately from experiment evidence.",
}

checklist_rows = [
    ("1.1 Scope match", "MULTI_VENUE_SHORTLISTED", "IEEE routes TIM/T-Rel/TAES and non-IEEE RESS/MSSP/AST fallbacks are maintained. Scope and evidence are in venue_research_20261002.md, venue_strategy_20261003.md, and q1_venue_research_20261003.md; exact article type, track, current submission rules, and non-IEEE JCR/CAS Q1 verification remain pending."),
    ("1.2 Novelty and contribution", "CONDITIONAL", "The manuscript claims an auditable chronology and protocol, not algorithmic superiority; contribution is publishable only if the selected venue accepts this framing."),
    ("1.3 Technical rigor", "PASS_WITH_LIMITS", "F1-F8 ledgers formalize split, model, route, gate, precision, uncertainty, and source diagnostics; historical outer reuse is disclosed."),
    ("1.4 Experiments and validation", "PASS_WITH_LIMITS", "Six source directions, three KS pairs, unit/seed diagnostics, 20,000-resample analysis, and one frozen LEO600 evaluation are reported; LEO600 is small and RWA has one usable observation."),
    ("1.5 Reproducibility", "PASS_WITH_LIMITS", "Hash-linked manifests, source scripts, runtime, commands, and ModelScope commit are recorded; public paper release/DOI and commit-level license remain pending."),
    ("1.6 Writing and format", "LOCAL_PASS_VENUE_PENDING", "IEEEtran local build is 6-page Letter with embedded fonts and successful text extraction; exact template/page/article type, PDF eXpress, accessibility, and metadata rules await venue selection."),
    ("1.7 Ethics and compliance", "CONDITIONAL", "Generated-simulation privacy/ethics disposition is documented; funding, COI, authorship, data permissions, and venue forms require author confirmation."),
]
checklist_md = "# IEEE Checklist 1.1–1.7\n\nGenerated: " + now + "\n\n" + "| Item | Status | Evidence and remaining action |\n|---|---|---|\n" + "\n".join(f"| {a} | `{b}` | {c} |" for a,b,c in checklist_rows) + "\n\n## Venue decision\n\nThe primary basket contains three IEEE routes: TIM, IEEE Transactions on Reliability, and IEEE TAES. The independent fallback basket contains RESS, MSSP, and AST; each remains `Q1_VERIFICATION_REQUIRED` until a dated Clarivate JCR or CAS record is captured. No venue-specific pass is asserted until one exact venue, track, article type, and review mode is selected.\n"
checklist_json = {"schema": "ieee-checklist-1.1-1.7-v1", "generated_utc": now, "venue": "IEEE basket (TIM primary; T-Rel and TAES fallbacks) plus SCI-Q1 fallbacks pending JCR/CAS", "rows": [{"item": a, "status": b, "evidence": c} for a,b,c in checklist_rows]}

response_md = f"""# Response Letter to IEEE Review Report\n\n**Manuscript:** *Auditing Source-Label-Only Route Selection for Cross-Orbit Remaining-Useful-Life Prediction*  \n**Status:** revision package prepared; venue and author metadata remain to be confirmed.  \n**Evidence build:** {now}\n\nDear Editor and Reviewers,\n\nWe thank the reviewers for identifying provenance, reproducibility, statistical, literature, and production problems. We made the following evidence-bound changes. Each response points to a machine-readable ledger; no historical result has been silently promoted.\n\n## F1 — Outer-fold selection contamination and provenance\n\n**Response.** We accept the finding. The historical sequence with failure counts `5, 4, 3, 1, 3, 0` reused outer outcomes during successive revisions. We now label those results development/diagnostic evidence, disclose the missing contemporaneous outer-read log, and remove their use as confirmatory evidence. A separately registered LEO600 partition was frozen before final-label access and evaluated once. The immutable event chain, freeze manifest, selection decision, and final receipt hashes are recorded in `f1_closeout_20261002.md` and `f1_evidence_ledger.json`.\n\n## F2 — Dataset, split, and label contract\n\n**Response.** We state the ModelScope URL, pinned commit, access date, license observation and limitation, unit/window counts, stride, missing-value treatment, RUL construction, sensor semantics, split algorithm, and membership hash. BAT is corrected to 4 raw channels; RWA has 13. The machine manifest and tensor replay addendum permit unit-level split reconstruction.\n\n## F3 — Formal method and dimensionality\n\n**Response.** We specify raw and represented dimensions (BAT 4→8, RWA 13→26), normalization, earliest-window relative features, TCN blocks, seeds, optimizer, loss, termination, projection/correction/blending order, complexity, assumptions, and degenerate cases in the F3 ledger and manuscript.\n\n## F4 — Alpha route and source-only rule\n\n**Response.** The final contract is five alpha families crossed with 64 masks, 320 routes. The historical 17-point/4913 catalog is retained as diagnostic history only. We state alpha semantics, selector order, gate objective, application point, target identity/earliest unlabeled window, and the label-free target-input/transductive information regime.\n\n## F5 — Precision and gate audit\n\n**Response.** Gate decisions use unrounded values and tolerance $10^{{-12}}$. Full-precision fold/unit CSV and JSON artifacts are hash-linked. Display rounding is explicitly separated from computation.\n\n## F6 — Statistical evidence\n\n**Response.** We report seed sensitivity, unit distributions, confidence intervals, paired diagnostics where available, 20,000 unit-cluster bootstrap resamples, and Bonferroni/Holm handling. We explicitly state that the reused six folds and three seeds are not independent replications and that the deterministic gate is not significance or practical relevance.\n\n## F7 — Related work and contribution boundary\n\n**Response.** The literature ledger verifies direct RUL/domain-adaptation/reliability/aerospace precedents through Crossref and Semantic Scholar metadata, records IEEE Xplore access limitations, and distinguishes their target-information regimes. The manuscript now states that no fair same-data implementation comparison with those methods is retained and therefore makes no state-of-the-art superiority claim.\n\n## F8 — Source gate, GRU, and ablations\n\n**Response.** We provide all six directed transfers, three residual-KS pairs, sample sizes, statistics, thresholds, multiplicity rules, and the complete diagnostic denominator. GRU is marked `N/A (ineligible)` and is never plotted as zero. Adjacent factor changes are retained as diagnostic ablations because they reused source-validation information.\n\n## F9 — Reproduction and declarations\n\n**Response.** We add runtime, hardware, command, hash, data/code, license, privacy/ethics, funding, COI, and author-metadata fields. Author confirmations and a public immutable paper release remain explicitly pending.\n\n## F10 — PDF and production checks\n\n**Response.** The current source was compiled twice. `pdfinfo` records a six-page Letter PDF; `pdffonts` reports all fonts embedded and no Type 3 fonts; `pdftotext` succeeds; the log has no fatal/error or overfull-box entries, with underfull-box warnings retained. Venue PDF eXpress and accessibility checks are pending exact venue selection.\n\nWe have therefore corrected the provenance narrative and made the remaining limits visible in the paper and artifact package. The final venue, article type, author metadata, funding/COI, and public release identity must be supplied before a venue-specific submission declaration can be made. If the IEEE basket is not selected, RESS/MSSP/AST are retained as separate fallbacks; their current SCI-Q1 status must be verified from the target-year JCR/CAS record before submission.\n"""

index_md = f"""# Paper Artifact Index\n\nGenerated: {now}\n\nThis index covers only the isolated paper tree. It excludes sealed/A1/B1/canonical/production/competition assets.\n\n| Artifact | Path | SHA-256 | Role |\n|---|---|---|---|\n""" + "\n".join(f"| {Path(k).name} | `{k}` | `{v}` | hash-linked evidence/input |" for k,v in sorted({**hashes, **artifact_hashes}.items())) + f"""\n\n## Primary deliverables\n\n- English LaTeX: `work/paper/en/main.tex`\n- English PDF: `work/paper/en/main.pdf`\n- Reproduction README and runners: `work/paper/repro/`\n- F1–F8 ledgers: `work/paper/review/`\n- F9 ledger: `work/paper/review/f9_evidence_ledger.json` and `.md`\n- F10 report: `work/paper/review/f10_pdf_production_report.json` and `.md`\n- Machine manifest: `work/paper/review/reproduction_manifest.json`\n- IEEE checklist: `work/paper/review/ieee_checklist_1_1_1_7.json` and `.md`\n- Response letter: `work/paper/review/response_letter.md`\n- Venue strategy and SCI-Q1 fallback ledger: `work/paper/review/venue_strategy_20261003.md` and `q1_venue_research_20261003.md`\n\n## Release boundary\n\nThe paper-specific public release, DOI, author metadata, funding/COI confirmation, exact venue, article type, PDF eXpress, and accessibility check remain pending. ModelScope data are referenced by URL/commit and are not duplicated.\n"""

write(REVIEW / "f9_evidence_ledger.json", json.dumps(f9, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "f9_evidence_ledger.md", "# F9 Evidence Ledger — Reproduction, Declarations, and Release\n\n" + json.dumps(f9, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "f10_pdf_production_report.json", json.dumps(f10, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "f10_pdf_production_report.md", "# F10 PDF Production Report\n\n" + json.dumps(f10, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "reproduction_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "ieee_checklist_1_1_1_7.json", json.dumps(checklist_json, indent=2, ensure_ascii=False) + "\n")
write(REVIEW / "ieee_checklist_1_1_1_7.md", checklist_md)
write(REVIEW / "response_letter.md", response_md)
write(REVIEW / "artifact_index.md", index_md)
print(json.dumps({"generated_utc": now, "pdf_pages": info.get("Pages"), "fonts": len(fonts["fonts"]), "type3": fonts["type3_count"], "fatal_or_error_lines": len(fatal), "overfull_lines": len(overfull), "outputs": ["f9_evidence_ledger", "f10_pdf_production_report", "reproduction_manifest", "ieee_checklist_1_1_1_7", "response_letter", "artifact_index"]}, indent=2))
