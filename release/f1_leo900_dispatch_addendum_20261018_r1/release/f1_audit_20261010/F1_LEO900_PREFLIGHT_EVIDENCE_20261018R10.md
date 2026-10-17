# F1 LEO900 追加证据台账 R10

记录时间：2026-10-17T21:37:43.325366+00:00

**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**

记录已经启动的终态核验衔接任务、既有测试及部署证据和只读进度。辅助核验不能替代真实最终结果审查。

## F1-R10-01

- **位置**：Existing controller terminal -> three existing independent auditors
- **原文**：R9 required terminal provenance, prediction-summary and numerical-statistics verification after completed execution.
- **问题**：Prepared auditors alone did not guarantee operational dispatch after a long simulation and evaluation.
- **修改**：A separate audit-only watcher waits for the existing controller to flush/fsync and make its successful terminal read-only, then dispatches chain, prediction and statistics auditors once. It does not launch simulation, training, freeze, evaluate or the production statistics program.
- **证据**：release/f1_audit_20261010/leo900_terminal_audit_watcher_20261018_r1.py; release/f1_audit_20261010/test_leo900_terminal_audit_watcher_20261018_r1.py; release/f1_audit_20261010/leo900_terminal_audit_watcher_deployment_20261017T212856Z.json; release/f1_audit_20261010/leo900_terminal_audit_watcher_launch_20261017T213248Z.json; release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json
- **来源**：Review F1; recorded local/Rack artificial tests; fixed auditor code; hash-bound deployment/launch receipts and read-only OS/controller observations. Source independence is qualified below.
- **日期**：2026-10-17T21:37:43.325366+00:00
- **哈希**：Full SHA256 values are in artifact_sha256 and frozen_artifact_sha256; the review is separately bound.
- **命令**：Deployed fixed --run --registration-sha256 command is recorded in launch_intent; do not execute it again.
- **结果**：The watcher accepts EVALUATION_AND_STATISTICS_COMPLETED regardless of the sign of the deterministic gate. It preserves exclusive outputs and stops on an audit error, pending report, nonzero exit or input/controller drift. Its successful terminal remains f1_closed=false and scientific_success_claimed=false.
- **交叉验证**：Static allowed command list matches deployment registration. Synthetic child processes exercise ordering, one-time dispatch and failure handling. These checks are separate from the research data and do not establish model performance.
- **置信度**：High for the stated recorded bytes and observations; final scientific validity remains subject to actual terminal review.
- **剩余风险**：The real terminal and three audit reports remain pending at this observation. The watcher cannot establish historical non-access or scientific success.
- **状态**：AUTOMATIC TERMINAL AUDIT DISPATCH REGISTERED; FINAL REVIEW PENDING

## F1-R10-02

- **位置**：Watcher tests and Rack deployment identity
- **原文**：Operational changes must preserve negative evidence and be verified on the actual execution host.
- **问题**：A local-only test result cannot establish deployed file identity or actual Rack execution behavior.
- **修改**：Retain the genuine missing-implementation RED, local GREEN and Rack receipt; verify all source/deployment hashes without rerunning research or changing existing files.
- **证据**：release/f1_audit_20261010/terminal_audit_watcher_red_20261018_r1.json; release/f1_audit_20261010/terminal_audit_watcher_local_20261018_r1.json; release/f1_audit_20261010/leo900_terminal_audit_watcher_deployment_20261017T212856Z.json; release/f1_audit_20261010/leo900_terminal_audit_watcher_20261018_r1.py; release/f1_audit_20261010/test_leo900_terminal_audit_watcher_20261018_r1.py; release/f1_audit_20261010/deploy_leo900_terminal_audit_watcher_20261018_r1.py
- **来源**：Review F1; recorded local/Rack artificial tests; fixed auditor code; hash-bound deployment/launch receipts and read-only OS/controller observations. Source independence is qualified below.
- **日期**：2026-10-17T21:37:43.325366+00:00
- **哈希**：Full SHA256 values are in artifact_sha256 and frozen_artifact_sha256; the review is separately bound.
- **命令**：Recorded python -B -m unittest -v test_leo900_terminal_audit_watcher_20261018_r1; receipt and source SHA256 rechecked by this append command.
- **结果**：Recorded RED:9 failures with implementation missing. Recorded GREEN:9/9 in4.547s on Windows/Python3.12; Rack:9/9 in0.500s on Linux/Python3.10.21256 code/receipt bytes uploaded,0 tensor bytes. Tests used artificial data and temporary child processes; production evaluator and real final data were not used.
- **交叉验证**：Local source hashes equal deployed-file hashes; both operating systems ran the same nine cases. Tests include duplicate start, existing-output preservation, pending report, drift and child-process failure. This is implementation corroboration, not independent research replication.
- **置信度**：High for the stated recorded bytes and observations; final scientific validity remains subject to actual terminal review.
- **剩余风险**：Artificial cases do not exhaust all possible runtime failures or validate the real final result.
- **状态**：RECORDED LOCAL/RACK9/9; RED RETAINED; BYTE IDENTITIES RECHECKED

## F1-R10-03

- **位置**：Single watcher launch and process observation
- **原文**：The launch receipt intentionally said LAUNCHED_UNCONFIRMED and cannot alone prove continued execution.
- **问题**：A successful SSH launch could precede immediate child exit; current process/start evidence is needed.
- **修改**：Preserve the original launch receipt and append a separate read-only observation of watcher_started, PID, command, affinity, memory, stage records and stderr.
- **证据**：release/f1_audit_20261010/leo900_terminal_audit_watcher_launch_20261017T213248Z.json; release/f1_audit_20261010/leo900_terminal_audit_watcher_observation_20261017T213616Z.json; release/f1_audit_20261010/start_leo900_terminal_audit_watcher_20261018_r1.py
- **来源**：Review F1; recorded local/Rack artificial tests; fixed auditor code; hash-bound deployment/launch receipts and read-only OS/controller observations. Source independence is qualified below.
- **日期**：2026-10-17T21:37:43.325366+00:00
- **哈希**：Full SHA256 values are in artifact_sha256 and frozen_artifact_sha256; the review is separately bound.
- **命令**：Read-only SSH observation at2026-10-17T21:36:16.582574Z; capture code and its hash are embedded in the observation.
- **结果**：PID792920 matches launch and live command; watcher_started exists. CPU4,nice15,one thread,RSS17192kB,sleeping; stderr0bytes. No audit stage has started and no watcher terminal is present. Registration SHA256 ee50eff95fa3232f5b7c0133a5c328a57c560a8cc0344ac7bd057415c119dbf3 remains bound.
- **交叉验证**：Launch/PID records, watcher-start artifact and live OS process agree at observation time. They share one Rack host; no external process attestation is claimed.
- **置信度**：High for the stated recorded bytes and observations; final scientific validity remains subject to actual terminal review.
- **剩余风险**：Liveness is a point-in-time observation and does not promise future completion. Do not duplicate the watcher or manually write its registered report paths.
- **状态**：ONE WATCHER OBSERVED WAITING; NO DUPLICATE DISPATCH

## F1-R10-04

- **位置**：F1 disposition and preserved scientific/manuscript state
- **原文**：Review F1 requires admitting historical outer reuse and a frozen candidate evaluated once on an untouched final test.
- **问题**：Auxiliary test passes, audit publication and normal process activity cannot establish F1 acceptance. The retained goal objective contains obsolete15/15-closed wording.
- **修改**：Keep F1 OPEN and goal active. Preserve the running simulation, existing controller, registered candidate/gate/statistics and frozen manuscript. Historical outer counts5,4,3,1,3,0 and LEO800 feedback remain development/diagnostic evidence.
- **证据**：release/f1_audit_20261010/leo900_generation_metadata_20261017T213514Z.json; release/f1_audit_20261010/leo900_continuation_observation_20261017T213514Z.json; release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json; release/f1_audit_20261010/leo900_audit_addendum_publication_20261017T211740Z.json; release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json; release/f1_audit_20261010/F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json; release/f1_audit_20261010/F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json
- **来源**：Review F1; recorded local/Rack artificial tests; fixed auditor code; hash-bound deployment/launch receipts and read-only OS/controller observations. Source independence is qualified below.
- **日期**：2026-10-17T21:37:43.325366+00:00
- **哈希**：Full SHA256 values are in artifact_sha256 and frozen_artifact_sha256; the review is separately bound.
- **命令**：Read-only metadata/controller capture at2026-10-17T21:35:14Z; rehash fixed manuscript, protocols and published manifests.
- **结果**：BAT26/48,RWA0/48; four MATLAB workers near99.7%CPU,stderr0bytes. Controller616411 is waiting; its two-event hash chain is valid, and final label guard is not present. Frozen hashes agree. R9 audit package was published/read back in BRPHM commit523619aed9dfb8f5622332acfe26363ffd682b2c.
- **交叉验证**：File metadata, process status and controller events corroborate execution state but share one host. GitHub publication corroborates published bytes by server response time; it is not immutable notarization or proof of historical non-access.
- **置信度**：High for the stated recorded bytes and observations; final scientific validity remains subject to actual terminal review.
- **剩余风险**：Actual generated membership, positive-window evaluation subset, single-access chronology, original-precision gate, physical effect and uncertainty still require terminal review. One final orbit and ensemble members cannot establish independent multi-orbit replication.
- **状态**：F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE

## SHA256

| 文件 | SHA256 |
|---|---|
| `release/f1_audit_20261010/F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json` | `50e43a0e342799976841da57116bacf09502855f27b116077826bed5b96de8f2` |
| `release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json` | `a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a` |
| `release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json` | `6de13be7865f3b603933ccf2aece3d97297d7dd01fe98a61bac0b3ee56695ca1` |
| `release/f1_audit_20261010/F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json` | `754326c717669f23f82d8cf044d87333772f21fe82a8b389a169389771506da1` |
| `release/f1_audit_20261010/append_f1_leo900_preflight_r10_20261018.py` | `db4745025d4e5c6c2cf73464438195d46424b5722a373d6f230e2ff4f29c7165` |
| `release/f1_audit_20261010/deploy_leo900_terminal_audit_watcher_20261018_r1.py` | `95527d485e76557fa902b48ae02d37cfc7c1a30c9e02193161683c340699a065` |
| `release/f1_audit_20261010/leo900_audit_addendum_publication_20261017T211740Z.json` | `256dc278808cb1a4312526a74beb5d8d8ab67cab02592a8584545f76713c285d` |
| `release/f1_audit_20261010/leo900_continuation_observation_20261017T213514Z.json` | `4644068193c2fabdcd8ccdb64eb4e7cc9900b0cdf470db7164188824b4889c0a` |
| `release/f1_audit_20261010/leo900_generation_metadata_20261017T213514Z.json` | `18f0f25a97da224ca598d1c653b6087c9a3152a3becd8a5ffa772c91a4b7a126` |
| `release/f1_audit_20261010/leo900_terminal_audit_watcher_20261018_r1.py` | `a5f309edd78d0b902ce62a06a0965e7d9ddc67a8328e64ea046d13cf34194fc7` |
| `release/f1_audit_20261010/leo900_terminal_audit_watcher_deployment_20261017T212856Z.json` | `7ad1cc4ec56a0289606bd49823448d818b0f6ac26ad241994c99c69b64bf126e` |
| `release/f1_audit_20261010/leo900_terminal_audit_watcher_launch_20261017T213248Z.json` | `8411f515e5e9f5dcbb693d6134064d39a9157f4f4e15d2668253bb0de3ad25bc` |
| `release/f1_audit_20261010/leo900_terminal_audit_watcher_observation_20261017T213616Z.json` | `edff2e885e231784aeb8f503e13149e78477de07b40bbf1eb46e195c16bec51a` |
| `release/f1_audit_20261010/start_leo900_terminal_audit_watcher_20261018_r1.py` | `d740262eb243ceae6f61218f5912b31493d7d478ebbe0fc8516d283ffadcef12` |
| `release/f1_audit_20261010/terminal_audit_watcher_local_20261018_r1.json` | `bc34f257093d3eda59dda2e6709a36f3aa11f9246c2195cb8fca8b6e70da472d` |
| `release/f1_audit_20261010/terminal_audit_watcher_red_20261018_r1.json` | `1fdf49251f0b291823c46029efad4c76b7e3428097fbc518b0f023064b1492bd` |
| `release/f1_audit_20261010/test_leo900_terminal_audit_watcher_20261018_r1.py` | `cbdb6ec4f4a577f3eea296ec55337a6814fbdf6b5c649b2b3dc05df54c91f393` |

## 后续要求

1. Preserve normal simulation/controller execution and the existing automatic audit watcher; observe metadata at reasonable intervals.
2. After complete terminal, read controller_terminal, watcher_terminal and its three registered reports; do not manually start duplicate audits.
3. If an audit fails, preserve all outputs and resolve the audit issue without changing the candidate or repeating evaluation.
4. Review96 generated members versus positive-window subset, access/freeze chronology, original gate, physical effects and registered uncertainty before deciding F1.
5. Only after actual F1 closure resume substantive F2-F10 and all final deliverables; no auxiliary check completes the goal.
