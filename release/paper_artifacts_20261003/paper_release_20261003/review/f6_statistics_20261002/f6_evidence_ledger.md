# F6 Evidence Ledger: Statistical and Practical Evidence

**Audit date:** 2026-10-02 (UTC)  
**Status:** `EVIDENCE_CLOSED_CURRENT_ARTIFACTS_BOUND_VENUE_METADATA_PENDING`

## Finding

The six component-orbit summaries are domain folds, not six independent replications. This package uses the paired unit-level candidate/reference errors to report SD, percentile paired bootstrap 95% CIs, one-sided Wilcoxon tests, Bonferroni handling over 12 fold-metric tests, Cohen's paired `d_z`, relative changes, and physical units.

## Pre-specified analysis

- Bootstrap: `20000` paired resamples per fold/metric, RNG seed `20261002`, percentile 95% CI for the mean unit delta.
- Wilcoxon: one-sided alternative `candidate-reference < 0`, zero method `wilcox`.
- Multiplicity: 12 tests (6 folds x RMSE/MAE), Bonferroni adjusted alpha `0.00416666666667`.
- BAT units are cycles; RWA units are days.

## Outputs

The machine-readable file `f6_statistics.json` contains all six fold records and pooled unit distributions. Each record includes unit `n`, mean/median/SD, bootstrap CI, Wilcoxon statistic/p-value, Cohen's `d_z`, fold delta, and relative percent change.

## Seed disclosure

The promoted implementation trains seeds `(17, 42, 73)` and uses their elementwise median. The hash-linked seed export contains 18 fold-by-seed rows and 1,329 seed-by-unit rows. Fold-wise seed mean, sample SD, range, and seed-versus-reference deltas are included as descriptive sensitivity summaries (n=3); the published candidate remains the median ensemble.

## Hashes

- Paired input: `96047569d472141bbfd661fa740321e270297bf71090b0e58322d45260868446`
- Fold input: `6360a274c2ac31f9dee88b0ea42435c55a2dacbe7f38cf9e133a98b82f606c74`
- Seed fold input: `26e1c26e63e5c790ec1c389230b8ecf0e709120d7ce5c32a20d2c465eecc22a9`
- Statistics output: `3982617b15ec1003b015f96caaacda803edc05ba40305ac3464a80a725e07e70`

## Residual risk

Unit rows are paired observations within folds and do not make the six folds statistically independent. The deterministic gate pass must be reported separately from uncertainty, statistical significance, and engineering relevance.

**Result:** F6 evidence and the manuscript patch are closed for the available unit/fold/seed diagnostics; venue-specific metadata remain pending.
