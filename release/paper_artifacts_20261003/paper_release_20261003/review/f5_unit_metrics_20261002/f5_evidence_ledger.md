# F5 Evidence Ledger: Unrounded Metrics and Gate Recalculation

**Audit date:** 2026-10-02 (UTC)  
**Status:** `EVIDENCE_CLOSED_CURRENT_ARTIFACTS_BOUND_VENUE_METADATA_PENDING`

## Finding

The prior PDF printed only eight decimals while claiming a `1e-12` gate. A frozen-route development replay now emits unrounded fold metrics and a per-unit CSV. The validator recomputes every delta and pass flag from full precision, checks all six component-orbit folds, and binds the files by SHA-256.

## Location and problem

- **Manuscript:** `work/paper/en/main.tex:38,108,112`
- **Problem:** rounded values such as the RWA/LEO550 row cannot independently reproduce a `1e-12` decision; no unit-level metric table was previously available.

## Aggregation and gate

- Fold RMSE/MAE are computed in physical units over all outer windows.
- The unit CSV reports per-unit RMSE, MAE, bias, and window count.
- `delta = candidate - reference`; each metric passes when `delta <= 1e-12`.
- The six-fold promotion rule additionally requires at least one strict gain below `-1e-12`.

Gate result from the validator: `{"tolerance": 1e-12, "fold_count": 6, "all_primary_metrics_nonregressive": true, "at_least_one_strict_gain": true, "promotion_eligible": true, "rule": "all six folds pass RMSE and MAE at tolerance 1e-12 and at least one strict gain"}`

## Hash-linked artifacts

| Artifact | SHA-256 |
|---|---|
| `formal_metrics_unrounded.json` | `6360a274c2ac31f9dee88b0ea42435c55a2dacbe7f38cf9e133a98b82f606c74` |
| `formal_unit_metrics.csv` | `e13f9443d0f7b99c77110344d7f3fc1947484f60d328770eadf4f5e8641f4d7a` |
| `frozen_candidate_receipt.json` | `b99ed8a3d2f168483f1072e7363fe1793a08708c16693ea6ba59e29bf03631f1` |
| `build_f5_precision_ledger.py` | `c190513d564aecab7026f5c523da051c47cacf414ecbb7a59a180b1b30eae4be` |

## Verification

- Delta recomputation: **PASS**.
- Fold grid completeness: **PASS** (`2 x 3 = 6`).
- Unit-to-fold window/unit counts: **PASS**.
- Hash binding: **PASS**.

**Commands:**

```text
python work/paper/repro/build_f5_precision_ledger.py
```

## Confidence and remaining risk

Confidence is high for numerical reproducibility and deterministic gate logic; statistical significance and practical relevance remain F6. The paper now links the machine-readable artifact and explicitly states that the gate uses unrounded values; venue-specific metadata remain pending.

**Result:** F5 evidence and the manuscript patch are closed for the current artifact; venue-specific metadata remain pending.

