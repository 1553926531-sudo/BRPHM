# F10 PDF Production Report

{
  "schema": "brphm-f10-pdf-production-ledger-v1",
  "audit_date_utc": "2026-10-02T19:09:18Z",
  "finding_id": "F10",
  "status": "LOCAL_PDF_PRODUCTION_CHECKS_PASS_VENUE_CHECKER_AND_ACCESSIBILITY_PENDING",
  "location": "IEEE report F10; work/paper/en/main.tex, main.pdf, main.log",
  "original_text": "The review required production checks for page geometry, fonts, figures/tables, PDF extraction, venue PDF eXpress, and accessibility.",
  "problem": "A local LaTeX build is necessary but does not prove compliance with an unselected venue's checker or accessibility policy.",
  "modification": "Rebuilt the current source twice and recorded fresh pdfinfo, pdffonts, pdftotext, warning scan, and SHA-256 results. The report separates locally verified facts from venue-dependent checks.",
  "evidence": {
    "pdfinfo": {
      "command_exit": "0",
      "Title": "Auditing Source-Label-Only Route Selection for Cross-Orbit Remaining-Useful-Life Prediction",
      "Subject": "",
      "Keywords": "",
      "Author": "Author metadata pending confirmation",
      "Creator": "LaTeX with hyperref",
      "Producer": "MiKTeX pdfTeX-1.40.28",
      "CreationDate": "Sat Oct  3 02:51:58 2026 中国标准时间",
      "ModDate": "Sat Oct  3 02:51:58 2026 中国标准时间",
      "Custom Metadata": "yes",
      "Metadata Stream": "no",
      "Tagged": "no",
      "UserProperties": "no",
      "Suspects": "no",
      "Form": "none",
      "JavaScript": "no",
      "Pages": "6",
      "Encrypted": "no",
      "Page size": "612 x 792 pts (letter)",
      "Page rot": "0",
      "File size": "323253 bytes",
      "Optimized": "no",
      "PDF version": "1.5"
    },
    "pdffonts": {
      "command_exit": 0,
      "fonts": [
        {
          "name": "QOKJQO+NimbusRomNo9L-Regu",
          "type": "Type 1",
          "encoding": "Custom",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "108 0"
        },
        {
          "name": "LREKMX+NimbusRomNo9L-MediItal",
          "type": "Type 1",
          "encoding": "Custom",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "110 0"
        },
        {
          "name": "IQBQDU+NimbusRomNo9L-Medi",
          "type": "Type 1",
          "encoding": "Custom",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "111 0"
        },
        {
          "name": "CZVSSV+CMR9",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "112 0"
        },
        {
          "name": "PQILTH+CMMI9",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "113 0"
        },
        {
          "name": "OPEKTB+CMSY9",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "114 0"
        },
        {
          "name": "HBIEHQ+CMSY6",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "115 0"
        },
        {
          "name": "SJQNVY+CMR6",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "116 0"
        },
        {
          "name": "YSAXAY+CMSY7",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "117 0"
        },
        {
          "name": "UGRNYW+NimbusRomNo9L-ReguItal",
          "type": "Type 1",
          "encoding": "Custom",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "130 0"
        },
        {
          "name": "XZOKWA+NimbusMonL-Regu",
          "type": "Type 1",
          "encoding": "Custom",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "131 0"
        },
        {
          "name": "PSQRFP+CMR10",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "133 0"
        },
        {
          "name": "TGBNJD+CMSY10",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "134 0"
        },
        {
          "name": "HSMEMO+CMMI10",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "135 0"
        },
        {
          "name": "FADMTX+CMMI7",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "136 0"
        },
        {
          "name": "GJAANQ+CMEX10",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "138 0"
        },
        {
          "name": "ZXOPOM+CMR7",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "139 0"
        },
        {
          "name": "QDTWCG+MSBM10",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "140 0"
        },
        {
          "name": "CUUNJW+CMMI5",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "141 0"
        },
        {
          "name": "EYETKE+DejaVuSans",
          "type": "CID TrueType",
          "encoding": "Identity-H",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "161 0"
        },
        {
          "name": "DEOWHK+DejaVuSans",
          "type": "CID TrueType",
          "encoding": "Identity-H",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "162 0"
        },
        {
          "name": "BAEDIA+DejaVuSans",
          "type": "CID TrueType",
          "encoding": "Identity-H",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "176 0"
        },
        {
          "name": "HMPEFZ+CMSY5",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "190 0"
        },
        {
          "name": "NXBXRT+CMR5",
          "type": "Type 1",
          "encoding": "Builtin",
          "emb": "yes",
          "sub": "yes",
          "uni": "yes",
          "object_id": "191 0"
        }
      ],
      "all_embedded": true,
      "type3_count": 0
    },
    "pdftotext": {
      "command": "pdftotext main.pdf main_extracted.txt",
      "exit": 0,
      "output_bytes": 32020,
      "hash": "77928910208f1efe8305855df1d504c727c3fee02dea85650377da033d6a71cb"
    },
    "latex_log": {
      "warning_line_count": 28,
      "underfull_line_count": 28,
      "overfull_line_count": 0,
      "fatal_or_error_line_count": 0,
      "sample": [
        "Underfull \\hbox (badness 10000) in paragraph at lines 45--46",
        "Underfull \\hbox (badness 3333) in paragraph at lines 45--46",
        "Underfull \\hbox (badness 5288) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 8113) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 75--76",
        "Underfull \\hbox (badness 10000) in paragraph at lines 89--90",
        "Underfull \\hbox (badness 2495) in paragraph at lines 89--90",
        "Underfull \\hbox (badness 1796) in paragraph at lines 89--90"
      ]
    },
    "hashes": {
      "work/paper/en/main.tex": "a6fa47353027862afeec3fe9b37c43984887e4738b4f528a854a71fb5587d783",
      "work/paper/en/main.pdf": "cb49907939e88aa0404368a5041ca12c1e626c82d672f6d5e7d0eabb118b1c83",
      "work/paper/en/main.log": "231e46b0b8c1998ab2757325764dcf0b5db4973469782c65c8a3879e7faaa622",
      "work/paper/en/main_extracted.txt": "77928910208f1efe8305855df1d504c727c3fee02dea85650377da033d6a71cb"
    },
    "figure_and_table_note": "The current source includes figures method_progression.pdf and formal_deltas.pdf and tables tab:data, tab:progression, tab:oldfold, and tab:leo600. Geometry is locally compiled; target-venue visual review remains pending.",
    "local_checks": {
      "compile_twice_exit_0": true,
      "letter_page_size": true,
      "fonts_embedded": true,
      "type3_fonts": true,
      "text_extraction": true,
      "fatal_errors": true,
      "overfull_boxes": true
    },
    "venue_checks": {
      "target_venue": "IEEE basket: TIM primary, T-Rel fallback, TAES fallback; SCI-Q1 basket: RESS, MSSP, AST pending dated JCR/CAS verification; exact venue/article type pending",
      "pdf_express": "PENDING exact venue/article type",
      "accessibility": "PENDING exact venue policy and checker",
      "blind_review_metadata": "PENDING exact venue policy"
    }
  },
  "source": "Fresh local commands in work/paper/en and venue_research_20261002.md",
  "date": "2026-10-02T19:09:18Z",
  "commands": [
    "pdflatex -interaction=nonstopmode -halt-on-error main.tex (twice)",
    "pdfinfo main.pdf",
    "pdffonts main.pdf",
    "pdftotext main.pdf main_extracted.txt",
    "Select-String -Path main.log -Pattern 'Overfull|Underfull|Warning|undefined|Fatal|Error'",
    "Get-FileHash main.tex,main.pdf -Algorithm SHA256"
  ],
  "result": "Local production evidence is recorded; no venue-specific checker or accessibility pass is claimed.",
  "cross_validation": "pdfinfo page geometry, pdffonts embedding/type, pdftotext extraction, log scan, and hashes were independently rerun; PDF metadata agrees with the compiled source title and six-page output.",
  "confidence": "high for local build/font/extraction facts; low-to-medium for any venue-dependent conclusion until a venue is selected",
  "remaining_risk": "Underfull boxes remain as layout warnings; no Type 3 fonts are present. Official PDF eXpress and accessibility checks cannot be selected or run before venue/article type confirmation. Non-IEEE Q1 fallback routes also require a dated JCR/CAS check."
}
