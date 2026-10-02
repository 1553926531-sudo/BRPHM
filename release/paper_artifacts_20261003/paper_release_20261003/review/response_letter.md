# Response Letter to IEEE Review Report

**Manuscript:** *Auditing Source-Label-Only Route Selection for Cross-Orbit Remaining-Useful-Life Prediction*  
**Status:** revision package prepared; venue and author metadata remain to be confirmed.  
**Evidence build:** 2026-10-02T19:09:18Z

Dear Editor and Reviewers,

We thank the reviewers for identifying provenance, reproducibility, statistical, literature, and production problems. We made the following evidence-bound changes. Each response points to a machine-readable ledger; no historical result has been silently promoted.

## F1 — Outer-fold selection contamination and provenance

**Response.** We accept the finding. The historical sequence with failure counts `5, 4, 3, 1, 3, 0` reused outer outcomes during successive revisions. We now label those results development/diagnostic evidence, disclose the missing contemporaneous outer-read log, and remove their use as confirmatory evidence. A separately registered LEO600 partition was frozen before final-label access and evaluated once. The immutable event chain, freeze manifest, selection decision, and final receipt hashes are recorded in `f1_closeout_20261002.md` and `f1_evidence_ledger.json`.

## F2 — Dataset, split, and label contract

**Response.** We state the ModelScope URL, pinned commit, access date, license observation and limitation, unit/window counts, stride, missing-value treatment, RUL construction, sensor semantics, split algorithm, and membership hash. BAT is corrected to 4 raw channels; RWA has 13. The machine manifest and tensor replay addendum permit unit-level split reconstruction.

## F3 — Formal method and dimensionality

**Response.** We specify raw and represented dimensions (BAT 4→8, RWA 13→26), normalization, earliest-window relative features, TCN blocks, seeds, optimizer, loss, termination, projection/correction/blending order, complexity, assumptions, and degenerate cases in the F3 ledger and manuscript.

## F4 — Alpha route and source-only rule

**Response.** The final contract is five alpha families crossed with 64 masks, 320 routes. The historical 17-point/4913 catalog is retained as diagnostic history only. We state alpha semantics, selector order, gate objective, application point, target identity/earliest unlabeled window, and the label-free target-input/transductive information regime.

## F5 — Precision and gate audit

**Response.** Gate decisions use unrounded values and tolerance $10^{-12}$. Full-precision fold/unit CSV and JSON artifacts are hash-linked. Display rounding is explicitly separated from computation.

## F6 — Statistical evidence

**Response.** We report seed sensitivity, unit distributions, confidence intervals, paired diagnostics where available, 20,000 unit-cluster bootstrap resamples, and Bonferroni/Holm handling. We explicitly state that the reused six folds and three seeds are not independent replications and that the deterministic gate is not significance or practical relevance.

## F7 — Related work and contribution boundary

**Response.** The literature ledger verifies direct RUL/domain-adaptation/reliability/aerospace precedents through Crossref and Semantic Scholar metadata, records IEEE Xplore access limitations, and distinguishes their target-information regimes. The manuscript now states that no fair same-data implementation comparison with those methods is retained and therefore makes no state-of-the-art superiority claim.

## F8 — Source gate, GRU, and ablations

**Response.** We provide all six directed transfers, three residual-KS pairs, sample sizes, statistics, thresholds, multiplicity rules, and the complete diagnostic denominator. GRU is marked `N/A (ineligible)` and is never plotted as zero. Adjacent factor changes are retained as diagnostic ablations because they reused source-validation information.

## F9 — Reproduction and declarations

**Response.** We add runtime, hardware, command, hash, data/code, license, privacy/ethics, funding, COI, and author-metadata fields. Author confirmations and a public immutable paper release remain explicitly pending.

## F10 — PDF and production checks

**Response.** The current source was compiled twice. `pdfinfo` records a six-page Letter PDF; `pdffonts` reports all fonts embedded and no Type 3 fonts; `pdftotext` succeeds; the log has no fatal/error or overfull-box entries, with underfull-box warnings retained. Venue PDF eXpress and accessibility checks are pending exact venue selection.

We have therefore corrected the provenance narrative and made the remaining limits visible in the paper and artifact package. The final venue, article type, author metadata, funding/COI, and public release identity must be supplied before a venue-specific submission declaration can be made. If the IEEE basket is not selected, RESS/MSSP/AST are retained as separate fallbacks; their current SCI-Q1 status must be verified from the target-year JCR/CAS record before submission.
