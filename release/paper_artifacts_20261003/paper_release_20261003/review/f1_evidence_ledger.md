# F1 Evidence Ledger: Outer-Fold Selection Provenance

**Audit date:** 2026-10-01 (Asia/Shanghai)  
**Scope:** F1 only. At the initial 2026-10-01 audit, F2-F10, manuscript wording, and publication packaging were frozen pending a clean final-test chain. The LEO600 chain closed F1 on 2026-10-02; the remaining findings are the next phase.  
**Project:** `BRPHM/rul-space`  
**Rack:** `Rack-Server`, `/mnt/data/BRPHM/rul-space`  
**Local ledger JSON:** `work/paper/review/f1_evidence_ledger.json`

**Current disposition (2026-10-02): F1 provenance CLOSED/PASS; the predeclared same-partition performance gate PASS.** The original six-fold outer sequence is retained only as development/diagnostic evidence. The LEO600 closeout, its bounded sample counts, full artifact hashes, verification commands, cross-checks, and residual risks are recorded in [f1_closeout_20261002.md](f1_closeout_20261002.md). The source-level F1 wording is reconciled in `en/main.tex` (pre-reconciliation SHA-256 `d99e2023bd8f665e040bcb66b2c107b35076f0f7b514ec04aadf6873705f7dc9`; current SHA-256 `a6fa47353027862afeec3fe9b37c43984887e4738b4f528a854a71fb5587d783`). The PDF was rebuilt from the current source on 2026-10-03 (SHA-256 `cb49907939e88aa0404368a5041ca12c1e626c82d672f6d5e7d0eabb118b1c83`); full build record is `review/pdf_build_verification_20261003.json`. Venue-specific PDF eXpress and accessibility checks remain pending.

## Finding

**Historical status as of 2026-10-01: FAIL for the original outer-fold claim.** The old outer-fold results cannot be treated as an unbiased one-time confirmation. The manuscript states that each successive candidate repaired the preceding outer failure count, while Rack evidence shows each preceding receipt completed before the next candidate script was created. No immutable candidate-freeze timestamp, outer-read log, selection-decision log, or append-only provenance chain exists for that old sequence. The receipt booleans are post-run declarations and do not establish temporal independence. This historical finding remains true; it is now addressed by relabeling the old results and evaluating the frozen candidate on a separate pre-registered LEO600 partition.

The six TCN candidates therefore have the following status:

| Order | Candidate | Rack receipt completion (+08:00) | Formal failures | Evidence status |
|---:|---|---|---:|---|
| 1 | unit-first TCN | 2026-10-01 01:08:02.994 | 5 | development/diagnostic only |
| 2 | residual-centered | 2026-10-01 02:04:29.078 | 4 | development/diagnostic only |
| 3 | residual-centered L1 | 2026-10-01 02:46:20.282 | 3 | development/diagnostic only |
| 4 | L1 worst-direction | 2026-10-01 03:26:23.182 | 1 | development/diagnostic only |
| 5 | RWA LEO550 floor | 2026-10-01 04:06:22.767 | 3 | development/diagnostic only |
| 6 | uniform alpha floor | 2026-10-01 04:43:40.840 | 0 | development/diagnostic only |

The GRU candidate completed a source gate only and was not formally evaluated.

## Direct Evidence

1. `work/paper/en/main.tex:66-67` says residual centering reduced failures, L1 reduced them again, worst-direction selection reduced them to one, the RWA floor changed the remaining pattern, and the uniform floor fixed all six folds.
2. `work/paper/en/main.tex:38,43` says outer labels are evaluated once after handoff and candidate selection never reads them. Those claims conflict with the successive-repair narrative unless an immutable pre-registration and read barrier exists.
3. Rack receipts contain `formal.results[*]` for the same six outer folds and report `outer_evaluated_once=true`, but no event chronology.
4. Rack filesystem metadata gives the monotonic script/receipt sequence. The next candidate script was created after the preceding candidate receipt completed.
5. `work/paper/generate_evidence.py` hashes receipts and extracts metrics, but does not capture candidate freeze, outer read, or selection-decision events.

## Candidate Evidence

The machine-readable ledger records every script SHA-256, receipt SHA-256, available run-log SHA-256, Rack mtime, input tensor hashes, frozen-reference hash, gate status, failure count, failed fold list, reconstructed command contract, and confidence. The frozen reference is:

`/mnt/data/BRPHM/rul-space/work/augmented_features_isolated_20260929/reference_summary_remote.json`  
SHA-256: `b708df9c448a051b8669c29789f00d282aa7907784e6f99d7e20ef1fb96b6733`

Input tensor hashes are BAT `9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` and RWA `9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595`.

## Missing Evidence

- No pre-registered candidate sequence with an immutable creation hash.
- No candidate-freeze timestamp before outer labels were read.
- No per-fold outer-read event log.
- No selection-decision log showing the visible information set.
- No append-only hash chain linking run start, source gate, freeze, outer read and final receipt.
- Exact remote shell wrapper commands were not retained. The CLI contract is reconstructable from the runner, but reconstruction is not execution evidence.

## Consequence

The failure counts and old outer metrics are retained as development/diagnostic evidence. The uniform-alpha-floor result cannot be reported as an unbiased final confirmation. No revision to the paper is allowed to preserve the old one-time outer claim.

## Required Clean Chain

1. Freeze one candidate and all source-only route decisions in a signed/hashed manifest.
2. Create a new untouched final-test partition that was not used in the old candidate chain.
3. Record UTC start/end, script/config/input/reference hashes and resource contract before execution.
4. Read final labels only after the freeze record is immutable.
5. Evaluate once; do not feed final outcomes into model, route, threshold, feature, loss, paper or venue decisions.
6. Publish the manifest, event log, receipt, hashes and exact command together.

## Residual Risk and Confidence

**Confidence in F1 failure:** high. The precise individual read event cannot be recovered because the old process did not emit a read log, but the manuscript's explicit repair chain plus the Rack chronology is enough to reject the no-reuse claim.

## Historical / superseded clean-chain snapshots

The records in this section are retained for provenance and failure analysis only. They are not the current final result and were not used as confirmatory evidence after the LEO600 candidate was frozen.

### Historical snapshot (superseded): LEO500 clean retry (2026-10-01)

The old outer chain remains **development/diagnostic only**. A frozen uniform-alpha-floor candidate was evaluated once on the registered holdout after an immutable freeze record. The clean chain is recorded under:

`/mnt/data/BRPHM/rul-space/work/augmented_features_isolated_20260929/f1_clean_final_20261001_retry1`

Local evidence copy:

`work/paper/review/f1_clean_final_20261001_retry1/`

### Immutable chain

| Artifact | SHA-256 | Evidence |
|---|---|---|
| `freeze_manifest.json` | `56a685ec43e8fd76ec47c4b68003a2f1363e18a005ec9daffbb5757eedfa88ca` | candidate, routes, holdout hashes and prohibitions frozen before semantic label access |
| `selection_decision.json` | `b67066f06591e8af7f2b6e508f8b0945808444df1fa39fe144081c2827705e55` | binds the selection decision to the freeze manifest |
| `final_receipt.json` | `6539846060867f598732a3a4b7d17a71cca05bb5f54c2e22426d6056c2b39b20` | one-time evaluation receipt |
| `final_bat_payload.pt` | `b645169c7d129297075ec46181708ab7f24d64e61389e37b3f04590b34d40560` | materialized BAT holdout payload |
| `final_rwa_payload.pt` | `d8e869e12842b729a4c8d15ea12648b2f68634c2e7347c4fc0a81b007e6eb5dd` | materialized RWA holdout payload |

The event chain is:

1. `preflight_recorded`, `2026-10-01T07:17:17.257904Z`, SHA-256 `46157598c3f7bfe88a12f0f64723c9325c674fa66e049766950ae2d49efaa49f`.
2. `candidate_frozen`, `2026-10-01T07:17:17.286075Z`, SHA-256 `8e86c7148fbe8cd918f03913d0497378c885743e95bb804d409d00b1bf6fdf4`.
3. `final_label_access_started`, `2026-10-01T07:17:44.307780Z`, SHA-256 `24fc83e7f2e1151d10d8cfc8f01d4a33d148387d15c734d1d8812746615966f8`.
4. `final_evaluation_completed`, `2026-10-01T07:23:23.765386Z`, SHA-256 `9461f1fb7b3beebc55fb879f4b358f9a8a44216a76439be03693656d2d073856`.

All four event files, the freeze manifest, selection decision and final receipt were mode `0444` on Rack. The receipt independently verifies the manifest and decision hashes. It states `evaluation=exactly_once_after_freeze`, `holdout_used_for_training_or_selection=false`, `sealed_read=false`, `a1_b1_read=false`, `canonical_project_modified=false`, `competition_line_modified=false`, and `holdout_written=false`.

### Retry provenance

The first execution directory, `f1_clean_final_20261001`, is retained and not overwritten. It recorded `preflight_recorded`, `candidate_frozen`, and `final_label_access_started` (event SHA-256 `f31ef795a68081bdcaa71f2c540335f5bc8e492e4cb626bf5842a88eb7324830`) before failing at `ModuleNotFoundError: No module named 'src'`. No holdout payload, final receipt, metric or selection decision was produced by that attempt. The retry added the project root to `PYTHONPATH`, created a new immutable freeze directory, and completed the same already-frozen candidate without changing the route or candidate.

### Historical snapshot (superseded): failed new-partition attempt v6 (2026-10-01)

The v6 generator completed with exit code `0` and produced three BAT and three RWA files. A file-metadata-only manifest was created at `/mnt/data/BRPHM/rul-space/work/f1_final_partition_v6_20261001/partition_manifest.json` (SHA-256 `ca3567124fd6d3f0d3ebbd3548160093c52c494e49920df150366eb81b0b6ef0`). The candidate was frozen before final-label access:

| Event | UTC | SHA-256 |
|---|---|---|
| `preflight_recorded` | `2026-10-01T14:28:17.967177Z` | `20631d2bad0f7c24492067d54c6c4a7b290776c23cf6d943806f661c44f1ebdc` |
| `candidate_frozen` | `2026-10-01T14:28:17.982408Z` | `abd41d414d63d7aa3b8975f58645ed87b2c058d057eae128e5b9d747c3df833b` |
| `final_label_access_started` | `2026-10-01T14:28:48.458304Z` | `1a7c4ee738176862f8df8a37e89423964d8d2c1eb3985f32d3c06951ecd37451` |

The one evaluation invocation failed with `RuntimeError: zero final windows for bat`. The loader reported the three BAT conversions had 56, 48, and 50 rows; it constructed no BAT windows, computed no metric, wrote no final receipt, and emitted no `final_evaluation_completed` event. Evaluator SHA-256: `7cf9be5fc5d19859955f71384afcfd27533dbd098369e0767fac73c0715f2482`. Partition builder SHA-256: `9834e76a4953ba6ff302b99218ea9b894f1e788898f3995fd124696a9629c217`.

**Disposition:** this is a failed, label-accessed partition and is burned. Do not rerun evaluation on these six units. The v7 manifest must use distinct unit IDs and must not include any v6 raw file. The failure cause is the BAT generated sequence length/window-construction path; it is not a model performance result.

### Frozen candidate and final metrics

The route was fixed before final-label access:

- BAT: `LEO500=1e-5`, `LEO550=1e-5`, `LEO700=1e-5`.
- RWA: `LEO500=0.02`, `LEO550=1e-5`, `LEO700=1e-5`.

The raw manifest contains 49 BAT and 49 RWA holdout units. After window construction, 38 BAT units/732 windows and 42 RWA units/1,260 windows had usable evaluation windows. Final metrics were:

| Component | RMSE | MAE | Usable units | Windows |
|---|---:|---:|---:|---:|
| BAT | `1.6578676802765389` cycles | `1.0855729667557303` cycles | 38 | 732 |
| RWA | `0.018801855461304577` days | `0.01389681839862735` days | 42 | 1,260 |

Against the frozen reference thresholds (`BAT RMSE <= 1.5708675425257754`, `BAT MAE <= 0.9909339180191383`, `RWA RMSE <= 0.01847260338317068`, `RWA MAE <= 0.014055847407832358`), BAT fails both metrics; RWA fails RMSE and passes MAE. The clean provenance gate therefore **passes**, while the frozen-candidate performance gate **fails**. This is not evidence of method success and is not a basis for paper claims.

### F1 disposition

`F1 provenance: CLOSED/PASS` — the old outer reuse is explicitly acknowledged and the replacement evaluation has an immutable freeze-to-read-to-receipt chain.

`F1 performance: FAIL` — the frozen candidate does not beat the frozen reference on the complete component metric gate. F2-F10 and manuscript wording remain frozen until a subsequent development candidate is designed and tested without touching this final receipt. The clean final metrics are diagnostic and cannot be fed back into this candidate or route.

## Current final chain: untouched-orbit LEO600 Run 1 (2026-10-02)

### Finding record

- **Position:** supplied report F1; manuscript p. 1 abstract, p. 2 Fig. 1 / Section V / Table I / Fig. 2, p. 3 Section VII; source locations `main.tex:12,38,43,66-67,92,133`.
- **Original text at issue:** “Candidate selection never reads outer labels”; “Outer labels are evaluated once after the handoff”; the successive formal failure sequence `5, 4, 3, 1, 3, 0`; and “The uniform floor fixed all six folds.”
- **Problem:** the successive repair narrative and receipt chronology establish that the six old outer folds informed iteration. The one-time/no-selection claim is not supportable for those folds.
- **Disposition/change at this stage:** all old outer results remain development/diagnostic evidence. The 2026-10-01 clean LEO500 retry also failed its full performance gate (BAT both metrics fail; RWA RMSE fails), so it is recorded as visible before this run. The LEO600 candidate was frozen from source-only route evidence and a disclosed uniform alpha floor before LEO600 labels were read. This line records the state before the later source reconciliation; the final verification addendum below records the subsequent manuscript correction and the current PDF-rebuild state.
- **Evidence:** candidate snapshot SHA-256 `bdcbb38020dc84c077445929f30cd86c24ea7bf4ce9eb665e6e723578fe1f92b`; candidate preregistration SHA-256 `128bc704843332440057b9f65700c57034d7835a4eb91c5c6521ba25abc46b53`; preparation manifest SHA-256 `4cdf569ff96022d1897de88687742ef1ef1ab46f57089dec7b9d9a4f5cd02f21`. Its preregistration records the old sequence as diagnostic, the failed LEO500 metrics as visible but not used to rank routes, and the floor rule as a post-outcome repair choice.
- **Sources and dates:** IEEE report supplied at `C:/Users/Administrator/Documents/Codex/2026-10-01/ni-d/outputs/IEEE_Review_Report_English.md`, read 2026-10-02; `work/paper/en/main.tex` and Rack receipts read 2026-10-02; candidate/preparation records created on Rack at `2026-10-02T06:36:59.136563Z`.
- **Commands:** Rack accessed with `ssh -i C:/Users/Administrator/Documents/id_ed25519 first@10.123.100.40`; process state via `ps -eo pid,ppid,ni,stat,etime,pcpu,pmem,args`; output inventory via `find /mnt/data/BRPHM/rul-space/work/f1_generator_20261002_leo600_v1/generated -maxdepth 2 -type f -printf ...`; hashes via `sha256sum`; log inspected with `tail`.
- **Current result at 2026-10-02 07:19:16Z:** the 8-worker low-priority MATLAB run is active (launcher PID 7120, MATLAB PID 7122, workers 9780/9786/9788/9791/9793/9795/9797/9799, CPU affinity 0-7). Three RWA raw files are complete with MATLAB `status=ok`, zero reported failures; six BAT and three RWA units remain. File hashes, paths, timestamps and contemporaneous log hash are in `execution_snapshot_20261002T071916Z.json`, SHA-256 `f71baba6cc406290d1d1e6d0171b22e60aabebd24b7c4be8ee5dd8522c48d105`.
- **Cross-check:** the Rack PID file mtime is `2026-10-02T07:09:10.545858157Z`; the process list independently confirms 8 workers and nice 15; the MATLAB log confirms “Workers=8”, “已连接到具有 8 个工作进程的并行池”, and three successful outputs; `sha256sum` independently binds each raw output and the contemporaneous log. Final-label access has not begun.
- **Confidence:** high that the old outer folds are reused and must be diagnostic only; high that the current run uses its preregistered untouched LEO600 raw units; no performance conclusion is available before the one-time evaluation.
- **Residual risk:** the model fixes each environment tile at 5,740 s, while the LEO600 GMAT orbit is about 5,819 s, a 79 s difference and approximately 608 km spatial tile seam. Importer checks V1-V8 pass but do not test periodic tile closure. Any result is specific to this simulator configuration; it does not establish physical-orbit accuracy.
- **Status:** superseded by the final verification addendum below; old-outer provenance is downgraded and the LEO600 clean chain is now closed.

### Resource-attempt timeline

| UTC | Attempt | Evidence and disposition |
|---|---|---|
| 2026-10-02 06:44:44–07:08:38 | 2 workers, PIDs 4160191/4163311/4163313, CPUs 0-1 | At 07:00:48 the host had 208 logical CPUs, 89% idle over the sample, 132 GiB available RAM, no swap I/O, and no raw output. Rechecked zero outputs, sent SIGTERM to these exact LEO600 generator PIDs, and confirmed they were absent by 07:08:38. No label read or evaluation occurred. OS exit status was not captured; original log SHA-256 `5ab6de68faaf29fc9257ddb6bd646a7dd7ca321c692660900c584ac29b9fa07a` is retained. |
| 2026-10-02 07:09:10 onward | 8 workers, PIDs 9780/9786/9788/9791/9793/9795/9797/9799, CPUs 0-7 | Active run; 3 RWA raw files completed and hash-bound by 07:19:16. Exit code will be captured by `generator_w8.exitcode` after completion. This run is being retained; no second generator is active. |
| Proposed at 07:15:44; cancelled by 07:19:15 | 12 workers | The 12-worker plan estimated 39.6 GiB total at 3.3 GiB/worker and would leave 196 logical CPUs unused. A fresh output check found the active 8-worker run had begun writing raw units; the plan was cancelled before execution. Amendment `resource_amendment_w12.json`, SHA-256 `13c0f43387391617243d5519e8b2618f90daa7c362801a2ea6cf1723210c2131`, records the proposal and cancellation. No W12 process or output exists. |

The executed W8 script, runner and launcher hashes are respectively `c5ac3dd6323cf760612b984c1f26252c61f3e7a3d3d26d9877e6098731e16dcf`, `e397f9807d16483671c94e6ba0c9e2e920166896d61c886e89943e6fa64923b1`, and `8d5ae3b6e8f241360a3edf15dcd05dd852d5b8d77c3dc40f5f9348c208b90f57`. Rack `bash -n` passed for the W8 runner and launcher. Effective command: `taskset -c 0-7 nice -n 15 ionice -c 3 matlab -batch "run('/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_generate_w8_20261002.m')"`.

### Next immutable events

1. Let the current registered generator finish; record MATLAB summary, raw hashes, log hash, process exit code, and timestamps.
2. Run builder `seal` only after all 12 expected raw files exist. It reads metadata and hashes, not semantic/final RUL labels. Verify exact IDs S940-S951, six units/component, and all raw/config bindings.
3. Run evaluator `freeze` to create and hash preflight, candidate freeze manifest, selection decision and event chain. Confirm these are read-only and the frozen route matches the candidate snapshot.
4. Invoke `evaluate` once. Confirm `final_label_access_started` follows `candidate_frozen`; verify the final receipt and same-partition candidate-versus-control gate from unrounded metrics. Do not use LEO600 outcomes to change the tested candidate.
5. Update F1 status only from those artifacts. Keep the result bounded by the simulator tile-closure risk above.

### Progress observation: 2026-10-02 07:28:38Z

All six RWA tasks (manifest positions 7-12; S946-S951) have completed with MATLAB `status=ok`, zero reported failures, and individually hashed raw files. The six BAT tasks (S940-S945) remain active. The log SHA-256 at this observation is `eef44b1f19e2a07a30ce390c719b4e385d7f563954c9727bf9fc589411aa817f`. Machine-readable snapshot: `execution_snapshot_20261002T072838Z.json`, SHA-256 `eb5bcbf325f5a1bffa47d7b51a388604e7ececf2e2a94ec082807147cd0786ce`; the snapshot and sidecar were copied to Rack and set mode `0444`. Wrapper tests: 10 passed; partition-builder tests: 6 passed. No semantic/final label read, partition seal, freeze, or evaluation has started.

### Label-isolation code audit: 2026-10-02

The frozen evaluator's fit boundary was checked directly before final-label access. In `temporal_tcn_orbit_fallback_source_gate.py:48-63`, TCN fitting forms `source_x = data["x"][train]` and `source_y = data["y"][train]`, computes normalization from `source_x` only, fits the three fixed-seed models with `source_y`, then predicts from `data["x"][valid]`. In `run_segmented_hgb_mlp_source_gate_20260929.py:99-130`, HGB/MLP control fitting likewise uses `x_train/y_train`; `x_valid` is used for prediction. The control helper computes metrics and residuals from `y[valid]` after prediction, so this reporting is permitted only after the final-label-access event and is not used for fitting or route selection. The wrapper appends `final_label_access_started` before it constructs payloads or calls either fit path.

Rack code hashes: fallback `facca14f7abc9b78956245be102b131100f73a29988562766237f293b6a6f65d`; relative-blend `f9fa246661793ad098231efeb45f5967f33cd83f35f80aa179453e53d1cacc09`; relative model `386de2a1a2a2073215ccf7b526e2f7bb20cffd00c6366a83e08391e3830c1cbf`; base TCN `0a50fe3839fdb804903cf8ece5e6191e1cb4dd9bf6b8e23938ae13ab946b1d74`; control `658b99fecc31689ef624e0726b330b07bccf377ce7f0977d1814331a728f6bf7`. Commands: `grep -R -n 'def fit_tcn_formal\|def fit_predict_fixed' ...`, `nl -ba <file> | sed -n ...`, and `sha256sum <five files>`. Cross-check: wrapper order is `verify_freeze` → append `final_label_access_started` → load/build payload → fit/predict → report metrics/receipt. Confidence is high for static fit/label separation. Runtime confirmation is pending; final receipt must bind code dependency hashes and event order.

## Final Verification Addendum: LEO600 Run 1 (2026-10-02)

The old outer sequence `5, 4, 3, 1, 3, 0` remains development/diagnostic evidence. A new source-only candidate was frozen from source-gate information on a pre-registered LEO600 partition, then evaluated exactly once after the immutable freeze event.

**F1 provenance: CLOSED/PASS. F1 performance: CLOSED/PASS.** The provenance chain is independently hash-linked and the same-partition performance gate passes. F2-F10 and manuscript edits remain unchanged and can proceed in the next phase.

### Raw and seal evidence

The W8 MATLAB runner completed all 12 units with exit code `0`, zero runner failures, and one legitimate censored BAT trajectory (`BAT_LEO600_B60_H1_L3_S944`, code `0`). Metadata-only seal verified BAT/RWA counts `6/6` without semantic-label access.

| Artifact | SHA-256 |
|---|---|
| `partition_manifest.json` | `910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123` |
| `partition_manifest.json.sha256` | `cabfffc3a2c9f61ceee9bdb86227c2a5e9316b46850c6bc3282476d6dd84d0f0` |
| final W8 log | `69735acb97691b71335239210d9ba5f1befa13af6a12a1bdeb6987623d9ee9bb` |
| `generator_w8.exitcode` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| W8 resource amendment | `01f2475767b4d1d052aa4715c5ab1428e48e6205195b35870e20771f26ae366d` |

The W8 amendment was created before raw output and changed only resource allocation and exit-status capture. The executed command was `taskset -c 0-7 nice -n 15 ionice -c 3 matlab -batch "run('/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_generate_w8_20261002.m')"`.

### Failed attempt and repair

The first evaluation directory `/mnt/data/BRPHM/rul-space/work/f1_leo600_final_20261002` is retained. Its label-access event hash is `8c0d457e703ab0b0d5138e1251654f7c1f048f9773f1c46cc8d907fa33f2256d`; it failed at `ModuleNotFoundError: No module named 'src'` before writing payload, receipt or metrics. The retry amendment is `work/paper/review/f1_leo600_retry_amendment_20261002.json`, SHA-256 `8e2fb3ae9d4c7e68f7e5358c676665dd008a235b53067e51c7756bc5b1f5b96e`. It records `PYTHONPATH=/mnt/data/BRPHM/rul-space` as the only repair and binds unchanged candidate, route, partition and thresholds.

### Immutable retry chain

Retry output is `/mnt/data/BRPHM/rul-space/work/f1_leo600_final_retry1_20261002`; local evidence is `work/paper/review/f1_leo600_final_retry1_20261002/`.

| Artifact | SHA-256 |
|---|---|
| `freeze_manifest.json` | `0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69` |
| `selection_decision.json` | `65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58` |
| `final_receipt.json` | `3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459` |
| `same_partition_performance_gate.json` | `1f7be0be1ef4761e37b311f3f764094bfac4cd26871c497e9576617585e3bc5b` |
| machine-readable verification | `work/paper/review/f1_leo600_final_verification_20261002.json` |

The event chain is `preflight_recorded` (`e0a6a7379b89893229464f72bfb3d9db25cedc6ca1e1e667cda4a8a32ed42ce0`) -> `candidate_frozen` (`aa85bab5b3fa1124db9d1cb1e7090f13248bfc8cb646e7276d534358a7d0d2e7`) -> `final_label_access_started` (`0fe031378ac1fbad08f760b58467ac76e7483d295568ced9ce0537759116b339`) -> `final_evaluation_completed` (`85ff12b6a6c005e66ebb04cdd093066e9ae758e25aef8c5f358bac03360d1c13`) -> `same_partition_reference_gate_completed` (`b69310177df39dd4d18f6b8a0ceda69abc724bfa6049b9e463f291098ac7cd04`). All retry artifacts/events are mode `0444` on Rack.

The receipt asserts `evaluation=exactly_once_after_freeze`, `holdout_used_for_training_or_selection=false`, `sealed_read=false`, `a1_b1_read=false`, `canonical_project_modified=false`, `competition_line_modified=false`, and `holdout_written=false`.

### Final metrics and gate

| Component | Candidate RMSE | Reference RMSE | Delta | Candidate MAE | Reference MAE | Delta | Usable units/windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| BAT | `1.1142871129918521` | `1.1142966431138528` | `-9.530122000667163e-06` | `0.673842205479741` | `0.6738513384014369` | `-9.132921695798046e-06` | 5 / 125 |
| RWA | `0.005497685074806214` | `0.005497685074806214` | `0.0` | `0.005497685074806214` | `0.005497685074806214` | `0.0` | 1 / 1 |

Gate tolerance is `1e-12`; both components are non-inferior on RMSE and MAE, BAT supplies the strict gain, and the gate reports `passes=true`, `strict_gain=true`, `regressions=[]`. The RWA result is limited to one usable unit and one window. The remaining physical-model limitation is unchanged: GMAT LEO600 is approximately 5819 s while the model tile is fixed at 5740 s (about 608 km seam), so the result is scoped to this simulator configuration.

The complete machine-readable record is [f1_leo600_final_verification_20261002.json](/C:/Users/Administrator/Documents/Codex/2026-09-26/new-chat/work/paper/review/f1_leo600_final_verification_20261002.json).

## Current-Turn Adjudication Card (2026-10-02)

### Finding record

- **Position:** Supplied review report, F1; manuscript `main.tex` lines 12, 43, and 67. Report SHA-256: `9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5`. Pre-reconciliation manuscript SHA-256: `d99e2023bd8f665e040bcb66b2c107b35076f0f7b514ec04aadf6873705f7dc9`; current reconciled source SHA-256: `a6fa47353027862afeec3fe9b37c43984887e4738b4f528a854a71fb5587d783`.
- **Original text:** “Candidate selection never reads outer labels”; “Outer labels are evaluated once after the handoff”; and “The uniform floor fixed all six folds.” The same abstract reports the six-fold improvement claim, while Section V gives the successive formal failure counts `5, 4, 3, 1, 3, 0`.
- **Problem:** the old six-fold outer outcomes were visible during successive candidate revisions. No contemporaneous outer-read or selection-decision event log exists for that historical sequence. The six-fold results cannot support the manuscript's original one-time-confirmation claim.
- **Correction:** acknowledge outer reuse and classify all original outer results as development/diagnostic evidence. The uniform alpha floor is disclosed as a post-outcome repair. The new candidate was preregistered and hash-bound before LEO600 raw generation, then frozen before final-label access and evaluated once on a separate raw partition. The current source contains this correction; the local PDF rebuild is recorded in `review/pdf_build_verification_20261003.json`.
- **Visible before new-candidate freeze:** the old outer sequence and the failed 2026-10-01 known-orbit retry were visible. The preregistration explicitly says the floor's historical origin was not independently preregistered and the known-orbit retry was visible. Thus the new result tests a frozen post-development candidate; it does not restore independence to the old folds.
- **Decision:** F1 chronology is closed for the new one-time evaluation. The original outer-fold evidence remains diagnostic. The predeclared same-partition deterministic gate passes, but that pass is not statistical significance or population-wide generalization.

### Immutable timeline and cross-checks

| Event | UTC | Bound evidence |
|---|---|---|
| Candidate and unit plan preregistered | 2026-10-02 06:36:59.136563 | `candidate_preregistration.json`, SHA-256 `128bc704843332440057b9f65700c57034d7835a4eb91c5c6521ba25abc46b53` |
| Raw generation starts | 2026-10-02 07:09:10.545858 | Resource-limited MATLAB command and candidate hashes in the runtime snapshot |
| Metadata-only partition sealed | 2026-10-02 10:22:41.821860 | `partition_manifest.json`, SHA-256 `910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123`; 12 registered units, 6 BAT / 6 RWA |
| Candidate frozen | 2026-10-02 10:29:05.879031 | Event SHA-256 `aa85bab5b3fa1124db9d1cb1e7090f13248bfc8cb646e7276d534358a7d0d2e7`; freeze manifest SHA-256 `0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69` |
| Final-label access starts | 2026-10-02 10:29:41.612195 | Event SHA-256 `0fe031378ac1fbad08f760b58467ac76e7483d295568ced9ce0537759116b339` |
| Evaluation completes | 2026-10-02 10:38:35.143702 | Receipt SHA-256 `3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459`; event SHA-256 `85ff12b6a6c005e66ebb04cdd093066e9ae758e25aef8c5f358bac03360d1c13` |
| Same-partition gate completes | 2026-10-02 10:38:35.144547 | Gate SHA-256 `1f7be0be1ef4761e37b311f3f764094bfac4cd26871c497e9576617585e3bc5b`; event SHA-256 `b69310177df39dd4d18f6b8a0ceda69abc724bfa6049b9e463f291098ac7cd04` |

Rack `sha256sum` and local `Get-FileHash` matched the freeze manifest, selection decision (`65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58`), receipt, gate, partition manifest, candidate preregistration, and all four post-freeze events. Rack `stat -c %a` returned `444` for each checked freeze/decision/receipt/event file. The event `previous_event_sha256` links form one ordered chain from preflight through gate. The evaluation receipt binds the candidate snapshot and freeze/selection hashes and states that the candidate route was unchanged and final metrics were not used for selection or paper decisions.

### Result, commands, and limits

The same-partition gate compares the frozen candidate with the projected frozen HGB/MLP reference at tolerance `1e-12`. BAT: RMSE delta `-9.530122000667163e-06`, MAE delta `-9.132921695798046e-06`, 5 usable units / 125 windows. RWA: both deltas `0`, 1 usable unit / 1 window. The censored BAT unit is not part of the usable metric count. The gate passes both-metric non-inferiority for each component and strict gain for BAT; the RWA comparison is a one-observation tie.

Commands run for this audit on 2026-10-02:

```powershell
Get-FileHash -LiteralPath <artifact-path> -Algorithm SHA256
Select-String -Path work/paper/en/main.tex -Pattern 'Candidate selection never reads outer labels|Outer labels are evaluated once after the handoff|uniform floor fixed all six folds'
ssh -i C:\Users\Administrator\Documents\id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=yes first@10.123.100.40 sha256sum -- <Rack artifact paths>
ssh -i C:\Users\Administrator\Documents\id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=yes first@10.123.100.40 stat -c %a -- <freeze, decision, receipt, event paths>
```

Results: manuscript conflict reproduced at lines 12, 43, and 67; local/Rack hashes matched for all listed key artifacts; all seven checked Rack files returned mode `444`. Confidence is **high** for historical outer reuse and for the new event/hash chronology. Residual risks: this is not a third-party trusted timestamp; the old outer-read events and exact old shell argv are unrecoverable; RWA's final usable sample is one window; LEO600 simulation period is about 5819 s versus the fixed 5740 s model tile (about 608 km seam). Do not use the exposed LEO600 final metrics to select another candidate or revise the method.



