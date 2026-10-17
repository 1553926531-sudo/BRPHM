# F1 LEO900 additive preflight evidence ledger — 2026-10-18 R4

F1 remains OPEN. This append-only report corrects earlier completion implications without replacing historic evidence. Manuscript and substantive F2–F10 changes remain frozen.

UTC generated: 2026-10-17T18:56:30.431930+00:00. Times are self-recorded, not externally notarized.

Machine-readable ledger SHA-256: `5d7f153acf7bbac5de6dbf7b28e02d49bc72931744a4e27c4d053b1faf03f2b6`.

## F1-LEO900-01

**location**: Review F1; historic outer sequence; earlier F1 ledgers

**original**: Candidate selection never reads outer labels; successive outer failure counts 5,4,3,1,3,0.

**problem**: Historic outer outcomes informed continuation and candidate/route development; the older bounded LEO600 acceptance wording is not the current completion criterion.

**modification**: Keep historic outer and LEO800 results as development/diagnostic evidence. Continue the registered untouched LEO900 96-unit experiment. This additive ledger supersedes any earlier implication that the current F1 task is closed.

**evidence**: review_report; F1_EVIDENCE_LEDGER_20261017.md; F1_CURRENT_EVIDENCE_LEDGER_20261012.md; leo900_partition_plan_20261017.json

**source_date**: 2026-10-18 Asia/Shanghai; raw observations use UTC

**command**: Read cited review and ledgers; verify registered partition and no-final-label execution chain.

**result**: Candidate/route selection input=true; candidate continuation input=true; source-route ranking input=false for old outer results. No new success claim.

**cross_validation**: Review contradiction and recorded candidate/failure chronology agree; new final chain must be checked separately.

**confidence**: High for the directly reproduced code defect and local/remote byte bindings; timestamp and no-read statements are self-recorded, not third-party attestations.

**remaining_risk**: Current clean-final confirmation and its gate have not yet been executed; old timestamps are not externally notarized.

**status**: OPEN: clean final experiment in progress

## F1-LEO900-02

**location**: Old evaluator build_raw_holdout_payload; frozen rwa_target.yaml:47; preprocess.py _bin_aggregate_rwa and normalize

**original**: channels_policy: impute_mean; retained singleton endpoint std values become NaN under ddof=1.

**problem**: The evaluator applied normalization but omitted the frozen imputation step. Original target preprocessing branch also omits it; this ledger does not claim that branch is correct.

**modification**: Add R4 wrapper honoring the frozen policy: replace normalized non-finite x cells by zero (frozen training mean); preserve finite float32 bit patterns and all labels/identities. Do not rebuild old training tensors or fit final-data statistics.

**evidence**: leo900_raw_payload_checks_r1_20261017T184448Z.json; leo900_channel_policy_deployment_r4a_20261017T185207Z.json; f1_leo900_channel_policy_clean_final_test_20261018_r4.py; leo900_channel_policy_20261018_r4.py; leo900_preprocess_source_snapshot_20261017T183744Z/src/datasets/preprocess.py; leo900_preprocess_source_snapshot_20261017T183744Z/configs/preprocess/rwa_target.yaml

**source_date**: 2026-10-18 Asia/Shanghai; raw observations use UTC

**command**: python -B -X utf8 release/f1_audit_20261010/deploy_f1_raw_payload_checks_20261018.py; then python -B -X utf8 release/f1_audit_20261010/deploy_leo900_channel_policy_20261018_r4.py --attempt r4a

**result**: RED: 12 tests, 1 failure, 0 errors. GREEN on Rack: 11 entry/helper checks and 15 synthetic-MAT integration checks pass; zero skips/errors/failures. Exactly three singleton std cells imputed in the artificial RWA endpoint case.

**cross_validation**: Frozen YAML and existing public imputation branch establish intended behavior; independent synthetic MAT/NumPy oracle verifies conversion, endpoint label, audit counts, strict/unknown policy, and unchanged finite cells. All 14 anchors match before/after; parent R3 verification passes.

**confidence**: High for the directly reproduced code defect and local/remote byte bindings; timestamp and no-read statements are self-recorded, not third-party attestations.

**remaining_risk**: A synthetic conversion check establishes implementation behavior; it does not establish final-data performance. Real per-channel/unit imputation counts will be saved in the single evaluation receipt.

**status**: IMPLEMENTATION CORRECTED AND REGISTERED BEFORE FINAL ACCESS

## F1-LEO900-03

**location**: /mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1/metadata_sealer_support_20261018_r1

**original**: 96 registered LEO900 units: BAT48/RWA48, beta 0/30/60 with 16 per component-beta cell.

**problem**: Incomplete generation must never be sealed or evaluated. Raw contents must remain unread before final access.

**modification**: Use already tested metadata-only sealer after job completion; enforce full membership, status0,96 successes,no skips/failures,config/input hashes,exclusive output,and streaming raw hashes only.

**evidence**: leo900_metadata_sealer_remote_checks_20261017T183745Z.json; leo900_generation_metadata_20261017T185424Z.json; leo900_metadata_sealer_20261018.py; leo900_partition_plan_20261017.json; leo900_simulation_schedule_20261017.json

**source_date**: 2026-10-18 Asia/Shanghai; raw observations use UTC

**command**: python -B -X utf8 release/f1_audit_20261010/capture_leo900_metadata_20261018.py; registered sealer --run-root RUN --output NEW_DIRECT_CHILD only after completion

**result**: Sealer: 26/26 Rack checks pass. Latest observation 2026-10-17T18:54:24.212737+00:00: BAT16/48,RWA0/48; four CPU-active workers; stderr0 bytes; job has no completion receipt yet.

**cross_validation**: Process metadata plus filesystem counts plus simulation log metadata; no MAT variable decoding. Sealer verified against missing,extra,symlink,hardlink,config-drift and completion-log fixtures.

**confidence**: High for the directly reproduced code defect and local/remote byte bindings; timestamp and no-read statements are self-recorded, not third-party attestations.

**remaining_risk**: The simulation remains active. Worker liveness does not prove completion or final-unit eligibility; full gate must wait for terminal job evidence.

**status**: GENERATION ACTIVE; SEAL DEFERRED UNTIL REGISTERED COMPLETION

## F1-LEO900-04

**location**: R4 registration; original evaluator paired-prediction output; forthcoming postprocessing

**original**: Gate compares unrounded RMSE/MAE with tolerance 1e-12; three seeds are ensemble constituents.

**problem**: Eight-decimal displays cannot audit the gate; overlapping windows and ensemble constituents cannot be treated as independent repetitions.

**modification**: Prepare an additive reader of same-pass lossless NPZ/layout/receipt, exact float64 metric/gate recomputation, and paired unit-cluster uncertainty. Preserve original source fit, route, alpha,projection and global once-only guard.

**evidence**: leo900_channel_policy_deployment_r4a_20261017T185207Z.json; f1_paired_predictions_20261018.py

**source_date**: 2026-10-18 Asia/Shanghai; raw observations use UTC

**command**: New postprocessing will consume final_receipt.json and hash-bound same-pass paired_predictions artifacts only; it must not load MAT/tensors/models or retrain.

**result**: Lossless same-pass writer is already bound; postprocessing tool preparation is the next step. No real final predictions have been read.

**cross_validation**: Original metric and gate source specify comparison arithmetic; forthcoming artificial fixtures will test precision boundaries,unit-cluster pairing and hash drift.

**confidence**: High for the directly reproduced code defect and local/remote byte bindings; timestamp and no-read statements are self-recorded, not third-party attestations.

**remaining_risk**: Conditional unit uncertainty is not independent orbit-level replication. The LEO900 gate and uncertainty remain to be measured.

**status**: IN PREPARATION

## Full byte bindings

- leo900_raw_payload_checks_r1_20261017T184448Z.json: `af10facf65a571f5d5e42788543631e011c2f14a26e6cbd8c93d774f47dc2ba5` (19364 bytes).
- leo900_channel_policy_deployment_r4a_20261017T185207Z.json: `ee582e07d0127fe9e04b904308ed2e5d431fe4d2db269d638b3bcdde581816b0` (32636 bytes).
- leo900_metadata_sealer_remote_checks_20261017T183745Z.json: `f924b20ea1d6035c9d1aa63e87067767594c59f87c5975f12fbbf984ac861ca3` (8222 bytes).
- leo900_generation_metadata_20261017T185424Z.json: `e71a9f89634dfdceb5d3dce48a5f0e86a987eb78bb0518ca20e36b142228f3bc` (5490 bytes).
- f1_leo900_channel_policy_clean_final_test_20261018_r4.py: `5b8acfe1eccc4f01e1e67ce0ef13f9d6768bb2ae9da152672974c2a7f1cf7a76` (6039 bytes).
- leo900_channel_policy_20261018_r4.py: `8ef26ac31b69397d4ce3d9960bee9c212c05d2f732698b575f0de90779c7326e` (2130 bytes).
- leo900_metadata_sealer_20261018.py: `4d29a8a43846812a66d0d1a15c977a935a86ea167e61951e3a6b0a8a255d3e4b` (21136 bytes).
- f1_paired_predictions_20261018.py: `15a61e2c4b0221f209e759133dfec5be3f02f39ce73417a6dedd2f0e0c2d983e` (4401 bytes).
- leo900_partition_plan_20261017.json: `c1a15e02fdedee94177ca3b1effae5d3781e12016ec86e5f88fe266e24e4c5b1` (30018 bytes).
- leo900_simulation_schedule_20261017.json: `2974b0853d54eb123a7e89028da91bbabd181127451b48b9797a594152b8456e` (12457 bytes).
- F1_EVIDENCE_LEDGER_20261017.md: `820d95cc95eb97353a1b0ea14b8e83079571b6f548e9af4acb4d511a35822558` (25766 bytes).
- F1_CURRENT_EVIDENCE_LEDGER_20261012.md: `90a1406d254fd02b765a8487b007bf2667bb17aef801bab4db9b2948529a892b` (8319 bytes).
- leo900_preprocess_source_snapshot_20261017T183744Z/src/datasets/preprocess.py: `5d6720d486a9c2cb7ef580881462492490b705311a69f7688487d2bda5868463` (282521 bytes).
- leo900_preprocess_source_snapshot_20261017T183744Z/configs/preprocess/rwa_target.yaml: `95d4fc52a5de90a7fb4513fad58d6f6edcb72aa7a2460f1b325940a3e1a76457` (7902 bytes).
- review_report: `9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5` (16146 bytes).

## New registration and continuation

R4 amendment: `/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1/channel_policy_support_20261018_r4a/F1_LEO900_CHANNEL_POLICY_AMENDMENT_20261018R4.json`; SHA-256 `8c38fde2466d76f2ae58c8bc9a7f3f390ee1728cfc7b6a00b5066d83fd0dd261`.

Registered formal entry: `/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1/channel_policy_support_20261018_r4a/f1_leo900_channel_policy_clean_final_test_20261018_r4.py`.

Existing single-access guard: `/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1/leo900_final_label_access_guard.json`. The same guard and fixed formal output remain mandatory even if evaluation fails.

Sequence: successful simulation → metadata seal → coverage checks → R4 freeze → exactly one evaluation → lossless gate reconstruction → paired unit statistics.

Venue preparation continues to list IEEE TIM, T-Rel and TAES as candidates; none is selected or submitted. No IEEE upload or external contact is authorized.
