# F1 Evidence Delivery Packet

**Audit date:** 2026-10-02 UTC  
**Finding:** F1 - outer-fold selection contamination and provenance contradiction  
**Disposition:** PROVENANCE_REMEDIATED; REPLACEMENT_GATE_PASS; OLD_OUTER_DEVELOPMENT_ONLY

## Finding record

| Field | Record |
|---|---|
| Position | IEEE review report F1; current source en/main.tex abstract, Introduction, Chronology and Development Diagnostics, Results, and Audit sections. The pre-reconciliation conflict was recorded at source lines 12, 38, 43, 66-67, 92, and 133. |
| Original text | “Candidate selection never reads outer labels”; “Outer labels are evaluated once after the handoff”; successive failure counts 5, 4, 3, 1, 3, 0; “The uniform floor fixed all six folds.” |
| Problem | Rack receipt completion times precede creation of later candidate scripts, and every formal candidate reused the same six outer folds. The historical sequence therefore served development/diagnostic iteration. Exact old outer-read and selection-decision events were not logged. |
| Correction | The old six-fold outcomes are explicitly development/diagnostic evidence. The post-outcome uniform floor is disclosed. A separate LEO600 partition was preregistered, candidate and route were frozen before semantic final-label access, and the partition was evaluated once. |
| Evidence | f1_evidence_ledger.json; f1_closeout_20261002.md; f1_leo600_final_verification_20261002.json; f1_leo600_final_retry1_20261002 event/hash chain. |
| Confidence | High for historical reuse and replacement event order; medium for performance generalization because the replacement has 5 usable BAT units and 1 usable RWA unit. |
| Residual risk | Historical individual label-read events and exact old shell argv cannot be recovered. Rack timestamps and mode 0444 are strong local evidence, not a trusted third-party timestamp. |
| Status | F1 provenance and the declared deterministic replacement gate are closed/pass. The source manuscript is reconciled and the current PDF has been rebuilt; local production details are recorded in `review/pdf_build_verification_20261003.json`. |

## Historical candidate sequence

All times are Rack Asia/Shanghai. Each formal candidate used the same six outer folds.

| Order | Candidate family | Script created | Receipt completed | Formal failures |
|---:|---|---|---|---:|
| 1 | Unit-first TCN | 2026-10-01 00:34:00.007 | 2026-10-01 01:08:02.994 | 5 |
| 2 | Residual-centered | 2026-10-01 01:28:30.470 | 2026-10-01 02:04:29.078 | 4 |
| 3 | Residual-centered L1 | 2026-10-01 02:06:11.706 | 2026-10-01 02:46:20.282 | 3 |
| 4 | L1 worst-direction | 2026-10-01 02:52:07.158 | 2026-10-01 03:26:23.182 | 1 |
| 5 | RWA LEO550 floor | 2026-10-01 03:32:14.193 | 2026-10-01 04:06:22.766 | 3 |
| 6 | Uniform alpha floor | 2026-10-01 04:09:35.986 | 2026-10-01 04:43:40.840 | 0 |

Script and receipt hashes are recorded in f1_evidence_ledger.json and the closeout ledger. The ordering plus the manuscript repair narrative establishes development reuse; it does not fabricate an individual read event.

## Replacement timeline

Replacement directory: work/paper/review/f1_leo600_final_retry1_20261002.

| Sequence | Event | UTC timestamp | SHA-256 |
|---:|---|---|---|
| 1 | preflight_recorded | 2026-10-02T10:29:05.858190Z | e0a6a7379b89893229464f72bfb3d9db25cedc6ca1e1e667cda4a8a32ed42ce0 |
| 2 | candidate_frozen | 2026-10-02T10:29:05.879031Z | aa85bab5b3fa1124db9d1cb1e7090f13248bfc8cb646e7276d534358a7d0d2e7 |
| 3 | final_label_access_started | 2026-10-02T10:29:41.612195Z | 0fe031378ac1fbad08f760b58467ac76e7483d295568ced9ce0537759116b339 |
| 4 | final_evaluation_completed | 2026-10-02T10:38:35.143702Z | 85ff12b6a6c005e66ebb04cdd093066e9ae758e25aef8c5f358bac03360d1c13 |
| 5 | same_partition_reference_gate_completed | 2026-10-02T10:38:35.144547Z | b69310177df39dd4d18f6b8a0ceda69abc724bfa6049b9e463f291098ac7cd04 |

Supporting hashes:

- freeze_manifest.json: 0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69
- selection_decision.json: 65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58
- final_receipt.json: 3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459
- same_partition_performance_gate.json: 1f7be0be1ef4761e37b311f3f764094bfac4cd26871c497e9576617585e3bc5b
- LEO600 partition_manifest.json: 910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123

## Gate result

The predeclared rule requires non-inferiority to the same-partition projected frozen HGB/MLP reference on RMSE and MAE for BAT and RWA at tolerance 1e-12, with at least one strict gain.

| Component | Candidate RMSE | Reference RMSE | Delta | Candidate MAE | Reference MAE | Delta | Usable sample | Result |
|---|---:|---:|---:|---:|---:|---:|---|---|
| BAT | 1.1142871129918521 | 1.1142966431138528 | -9.530122000667163e-06 | 0.673842205479741 | 0.6738513384014369 | -9.132921695798046e-06 | 5 units / 125 windows | non-inferior with strict gain |
| RWA | 0.005497685074806214 | 0.005497685074806214 | 0 | 0.005497685074806214 | 0.005497685074806214 | 0 | 1 unit / 1 window | tie / non-inferior |

Result: passes=true, strict_gain=true, regressions=[]. This is a deterministic same-partition gate, not a significance test or population-generalization proof. The RWA result is one unit and one window. LEO600 GMAT period is about 5819 s while the model tile is 5740 s, a roughly 79 s / 608 km seam.

## Commands and verification

The historical exact commands were not captured and are not reconstructed as execution evidence. Replacement artifact checks used:

    Get-FileHash -Algorithm SHA256 -LiteralPath work/paper/review/f1_leo600_final_retry1_20261002/freeze_manifest.json
    Get-FileHash -Algorithm SHA256 -LiteralPath work/paper/review/f1_leo600_final_retry1_20261002/selection_decision.json
    Get-FileHash -Algorithm SHA256 -LiteralPath work/paper/review/f1_leo600_final_retry1_20261002/final_receipt.json
    Get-FileHash -Algorithm SHA256 -LiteralPath work/paper/review/f1_leo600_final_retry1_20261002/same_partition_performance_gate.json

Independent validation recomputed all local hashes, event previous-hash links, candidate/partition bindings, RMSE/MAE deltas, and the 1e-12 gate: PASS. Rack sha256sum matched local copies for the clean artifacts and all 12 raw files; Rack stat returned mode 444 for the checked freeze, decision, receipt, and event files.

## Manuscript reconciliation record

Pre-reconciliation source SHA-256: d99e2023bd8f665e040bcb66b2c107b35076f0f7b514ec04aadf6873705f7dc9. Current reconciled source SHA-256: 4dc54e2a8ccd3aa087344ae52737b5f9f1bc5bb97faa9926c1d0aa6cf5d33621.

A source scan of the current en/main.tex confirms: the old sequence is classified as development/diagnostic; the LEO600 comparison reports reference and candidate RMSE/MAE; GRU is N/A (ineligible); and the historical sequence is not claimed as untouched confirmation. The source action and local PDF rebuild are complete. The PDF hash, font scan, layout log scan, and remaining untagged/underfull findings are recorded in `review/pdf_build_verification_20261003.json` and `review/pdf_audit_20261003.md`. Venue-specific PDF eXpress and accessibility claims remain pending exact venue confirmation.

## Required disposition

F1 is closed for provenance and the declared deterministic replacement gate. Do not use the LEO600 final metrics to select another candidate, revise the route, or claim statistical significance. Proceed to F2-F10 only with the old outer sequence marked diagnostic and with the current source/PDF hashes recorded.



