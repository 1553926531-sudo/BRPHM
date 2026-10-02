# F8 Evidence Ledger: Source Gate, GRU Eligibility, and Ablation Matrix

**Audit date:** 2026-10-02T18:18:49.393609+00:00  
**Status:** `RECEIPT_MATRIX_RECONCILED_CLUSTER_INFERENCE_PENDING`  
**Finding fields:** location, original text, problem, correction, evidence, source, date, hash, command, result, cross-check, confidence, remaining risk, status.

## Finding Record

- **Location:** IEEE review report F8; `work/paper/en/main.tex:72-91`; chart generator `work/paper/generate_figures.py`.
- **Original:** The paper reports a six-fold candidate progression and marks GRU with `--`; the generator interpreted the GRU receipt's absent formal failure count as numeric `0`.
- **Problem:** all six historical candidates reused the same outer folds while changing the route/model based on successive results. Those outcomes are development/diagnostic evidence, not six independent confirmatory evaluations. GRU fails both source gates and has no formal denominator. Its zero-valued metadata must never appear as zero failures. Original source-gate receipts include six directed metrics and three KS statistics but omit residual arrays and p-values.
- **Correction made:** the active figure generator now labels the six-fold sequence as development/diagnostic, prints a `k/6` denominator, and labels GRU `ineligible` with no numeric count. PDF figures now embed CID TrueType fonts. Paper body text remains pending the complete evidence pass.

## Recomputed Denominators and Failure Matrix

`candidate_fold_matrix.csv` contains 36 rows: six eligible candidates times six component-orbit folds. Its columns include unit/window counts, full-precision reference and candidate RMSE/MAE, deltas, per-metric gate booleans at `1e-12`, and failed metrics. `source_gate_matrix.csv` contains 126 rows across all seven receipts, both components, six directed transfers and three residual pairs.

| Candidate sequence | Diagnostic folds with a regression | Denominator | Formal status |
|---|---:|---:|---|
| `source_only_temporal_tcn_unit_first_relative` | 5 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_tcn_unit_first_relative_residual_centered` | 4 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_tcn_unit_first_relative_residual_centered_l1` | 3 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_tcn_unit_first_relative_residual_centered_l1_worst_direction` | 1 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_tcn_unit_first_relative_residual_centered_rwa_leo550_alpha_floor` | 3 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_tcn_unit_first_relative_residual_centered_uniform_alpha_floor` | 0 | 6 | reused outer folds; development/diagnostic only |
| `source_only_temporal_gru_unit_weighted` | N/A | 0 (ineligible) | source gate failed; no formal evaluation |

## Source Gate Metrics

All six directions are keyed as source orbit → validation orbit; window and unit counts are the validation sample sizes. The three KS pairs compare residuals from the reciprocal directed transfers. The receipt gate tolerance is `1e-12`; it rejects any RMSE, MAE, or KS regression over tolerance and requires at least one strict RMSE/MAE improvement. The CSV records each full-precision value and candidate-minus-control delta.

The original receipt contains KS statistics only. Its current p-value fields are explicitly marked as absent; the separate source-only replay is exporting per-unit residual vectors so candidate-vs-control KS-distance uncertainty can be computed with unit clusters. IID-window KS p-values will be shown only as non-inferential reference values. Any cluster test remains exploratory because the route was selected on the same source-validation information.

## Controlled Ablations

The retained sequence changes one declared factor at each adjacent step: residual centering; SmoothL1-to-L1 loss; route tie-break; RWA-specific alpha floor; uniform alpha floor. `candidate_fold_matrix.csv` provides the full six-fold metric matrix for each historical variant. Because the same outer folds informed the sequence, these are diagnostic ablations. Seed-level and unit-cluster uncertainty is available only for the final receipt in the current evidence tree; equivalent unit prediction exports for the earlier variants are not present. Do not claim independent ablation confirmation or statistical superiority from the progression chart.

## Evidence and Reproduction

- **Primary evidence:** the seven hash-bound source-gate/formal receipts and `work/paper/evidence/evidence_summary.json`.
- **Independent source:** F1 closeout ledger, which classifies all `5,4,3,1,3,0` outer-fold outcomes as development/diagnostic.
- **Commands:** `python work/paper/repro/build_f8_evidence_ledger_20261002.py`; per-unit replay command is recorded in `f8_evidence_ledger.json`.
- **Verification:** the builder asserts six complete folds for every eligible receipt, recomputes each failure count, matches all counts to the summary, and asserts that the ineligible GRU has no formal rows.
- **Source hashes:** see the `artifacts` object in `f8_evidence_ledger.json`; receipt full hashes are included there.
- **Result:** the historical fold/source metrics and GRU eligibility reconcile. The generated figure no longer depicts ineligibility as zero. Cluster-aware residual uncertainty is pending successful replay and reconciliation against the saved receipts.
- **Cross-check:** receipt metrics versus recomputation; per-direction candidate/control values from each same receipt; GRU source gate versus null formal; F1 disposition versus the supplied review report.
- **Confidence:** high for denominators, gate computations, and GRU status; medium for inferential uncertainty pending residual replay.
- **Remaining risk:** temporal overlap invalidates IID-window inference; source-gate route selection induces selection bias. Historical six-fold outcomes cannot be promoted back to final-test evidence.
- **Status:** `RECEIPT_MATRIX_RECONCILED_CLUSTER_INFERENCE_PENDING`.
