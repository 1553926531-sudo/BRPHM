# F5 Reconciled Evidence Ledger

**Audit date:** 2026-10-02 UTC  
**Status:** `AGGREGATE_GATE_VERIFIED_FROZEN_UNIT_PAIRING_INVALID`

## Finding

The old F5 ledger incorrectly treated the unit-level `reference_*` columns as errors from the frozen reference. The builder actually captured a newly fitted control model, while the fold gate used the hash-bound frozen-reference summary. The old paired CSV is retained as a diagnostic replay only. The aggregate gate and candidate unit metrics have now been independently reconciled.

## Location and original text

- **Manuscript:** `work/paper/en/main.tex:38,108,112`
- **Issue:** the table shows eight decimal places for a gate tolerance of `1e-12`.

## Reference, aggregation, and gate

- Frozen summary: `C:\Users\Administrator\Documents\Codex\2026-09-26\new-chat\reference_summary_remote.json`
- SHA-256: `b708df9c448a051b8669c29789f00d282aa7907784e6f99d7e20ef1fb96b6733`
- Gate: `delta = candidate - frozen reference`; each RMSE and MAE delta must be `<= 1e-12` on all six folds, with at least one strict gain below `-1e-12`.
- Unit aggregation reconstructs the candidate fold metrics using each unit's window count.

| Component | Orbit | Units | Windows | Frozen RMSE | Candidate RMSE | Delta RMSE | Frozen MAE | Candidate MAE | Delta MAE | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BAT | LEO500 | 70 | 1377 | 1.9458075686003256 | 1.9458039118294947 | -3.6567708308066216e-06 | 1.2965988587913477 | 1.2965975128997191 | -1.3458916285902234e-06 | RMSE True, MAE True |
| BAT | LEO550 | 68 | 1178 | 1.7944888327735873 | 1.7944792392764701 | -9.5934971171551808e-06 | 1.1889396841474829 | 1.1889357521418609 | -3.9320056219871447e-06 | RMSE True, MAE True |
| BAT | LEO700 | 65 | 1126 | 2.3908374358972697 | 2.3908073726542862 | -3.0063242983491278e-05 | 1.5583111231774527 | 1.5582925316087028 | -1.8591568749837251e-05 | RMSE True, MAE True |
| RWA | LEO500 | 78 | 2352 | 0.020750278352438312 | 0.02072511343967948 | -2.5164912758831454e-05 | 0.015583504892392552 | 0.015582983999944547 | -5.2089244800476719e-07 | RMSE True, MAE True |
| RWA | LEO550 | 79 | 2324 | 0.020271678060433281 | 0.020271664723422712 | -1.3337010568853502e-08 | 0.01505406402486654 | 0.015054062536072867 | -1.4887936734125917e-09 | RMSE True, MAE True |
| RWA | LEO700 | 83 | 2375 | 0.021490337094875866 | 0.021490307719580153 | -2.9375295713257588e-08 | 0.016712293430036058 | 0.016712271758414634 | -2.1671621424496079e-08 | RMSE True, MAE True |

Gate result: `all_nonregressive=True`, `strict_gain=True`, `promotion_eligible=True`.

## Pairing provenance correction

`formal_unit_paired_metrics.csv` was built by refitting the control through the current `fit_predict_fixed` implementation. It is not the historical frozen-reference prediction. Its window-weighted fold RMSE/MAE differ from the frozen summary in `6` of six folds, so it cannot be used for frozen-reference paired bootstrap or Wilcoxon inference. F6 separates replay sensitivity from uncertainty against the fixed fold benchmark.

## Artifacts and verification

The machine-readable ledger contains full-precision fold values and SHA-256 hashes for the reference summary, candidate receipt, fold JSON, both unit CSVs, and builders. Verification command:

```text
python work/paper/repro/build_f5_precision_ledger.py
```

- Frozen-reference summary hash and fold values: **PASS**.
- Candidate unit-to-fold reconstruction: **PASS**, six of six folds.
- Delta and gate recomputation at full precision: **PASS**.
- Frozen-reference unit pairing: **INVALID in the old paired CSV; marked diagnostic-only**.

## Confidence and remaining risk

Confidence is high for the aggregate gate and candidate unit metrics. Exact frozen-reference unit predictions are not present in the searched receipt bundle, so paired inference against those historical predictions is not claimed. The paper must cite the reconciled JSON and candidate unit CSV and must not label the replay CSV as frozen-reference pairs.
