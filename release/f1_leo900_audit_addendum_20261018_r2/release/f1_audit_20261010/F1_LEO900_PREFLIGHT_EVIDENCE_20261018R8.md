# F1 LEO900 追加证据台账 R8

记录时间：2026-10-17T20:57:15.418317+00:00

**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**

本记录追加独立统计数值核验、失败/通过收据、独立支持目录部署和运行观察。它不改变冻结候选、统计设计、门禁或原始预最终承诺。

## F1-R8-01

- **位置**：R2 terminal auditor versus registered unit-cluster statistical analysis
- **原文**：Review F1 requires a reconstructable freeze/access/result chain; full-precision statistical evidence must retain its numerical meaning.
- **问题**：R2 validates structure, membership, point-metric consistency and hash edges, but does not recompute bootstrap draws, interval endpoints, SD, paired p-values or Holm. A plausible rehashed interval could therefore pass.
- **修改**：Add a separate read-only numerical verifier with count-weighted bootstrap arithmetic, manual linear percentile interpolation, compensated SD sums, independently ranked signed-rank tests and explicit sign enumeration/normal tails, then Holm. Require complete R2 terminal verification first.
- **证据**：release/f1_audit_20261010/leo900_statistics_numerical_audit_20261018.py; release/f1_audit_20261010/test_leo900_statistics_numerical_audit_20261018.py; release/f1_audit_20261010/leo900_terminal_evidence_20261018_r2.py; release/f1_audit_20261010/f1_lossless_gate_statistics_20261018.py; release/f1_audit_20261010/F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json
- **来源**：Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.
- **日期**：2026-10-17T20:57:15.418317+00:00
- **哈希**：SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.
- **命令**：python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018; inspect registered producer and independent verifier arithmetic.
- **结果**：Prepared verification covers 160000 draws, 16 intervals, 8 SD values and 4 paired tests per complete report. No frozen analysis or gate is changed; alternate arithmetic allows only 64 ULP at the underlying error scale. This allowance is never used for the 1e-12 gate.
- **交叉验证**：Registered indexed-summary reduction and independent count-matrix reduction agree on artificial inputs. Hand-derived unequal-window distributions and exact tied-rank p=.625 provide additional numerical oracles. The full-chain rehashed false interval passes R2 but is rejected by the numerical verifier.
- **置信度**：High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.
- **剩余风险**：Saved sufficient summaries remain an input assumption; this verifier does not independently derive their errors from raw labels/predictions. Same NumPy RNG contract, same dataset and same frozen design; not independent data replication.
- **状态**：NUMERICAL VERIFIER PREPARED; REAL FINAL NUMBERS AWAIT TERMINAL

## F1-R8-02

- **位置**：Local RED/GREEN records and complete artificial production-path witnesses
- **原文**：A prior 14-test pass cannot substantiate two later-added production-path tests.
- **问题**：The first 16-test run failed twice before reaching numerical checks: Windows path keys used backslashes while the new fixture looked up a slash-joined string. This was a test-fixture error, not a model or final-data result.
- **修改**：Retain initial missing-implementation RED, 14-test GREEN, failed 16-test receipt and current 16-test GREEN. Build the fixture layout key with the same Path operation used by the fixture. MAT/PT/prediction files remain undecodable fake bytes.
- **证据**：release/f1_audit_20261010/statistics_numerical_audit_red_20261018_r1.json; release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r1.json; release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r2.json; release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r3.json; release/f1_audit_20261010/test_leo900_statistics_numerical_audit_20261018.py
- **来源**：Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.
- **日期**：2026-10-17T20:57:15.418317+00:00
- **哈希**：SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.
- **命令**：Recorded python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018 with numeric libraries limited to one thread.
- **结果**：Current suite 16/16 passes with source hashes unchanged. It checks altered intervals, SD, p-values, Holm, draws, draw ordering, seeds, membership, NaN, one-unit/zero-difference cases, pending early exit and full production-shaped terminal input. Complete fixture remains byte-for-byte unchanged.
- **交叉验证**：The registered producer supplies the artificial comparison report; independently hand-checked distribution/rank witnesses avoid relying on that producer alone. Local hashes reconcile with Rack input hashes.
- **置信度**：High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.
- **剩余风险**：Synthetic tests do not prove all possible edge cases or actual final performance. The failed Windows fixture attempt is not counted as a genuine missing-behavior RED.
- **状态**：16/16 LOCAL; ALL FAILED ATTEMPTS RETAINED

## F1-R8-03

- **位置**：New Rack statistics_numerical_audit_support_20261018_r1 directory
- **原文**：Preserve the simulation, existing controller and one-shot final evaluation.
- **问题**：A local arithmetic pass alone does not establish deployed byte identity or Rack behavior.
- **修改**：Deploy only the seven small code/receipt inputs into a new exclusive support directory; run 16 artificial tests on CPU4/nice15 with single-threaded numerical libraries, then one fixed read-only preflight.
- **证据**：release/f1_audit_20261010/leo900_statistics_numerical_audit_deployment_20261017T205500Z.json; release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r3.json; release/f1_audit_20261010/leo900_statistics_numerical_audit_20261018.py; release/f1_audit_20261010/test_leo900_statistics_numerical_audit_20261018.py; release/f1_audit_20261010/deploy_leo900_statistics_numerical_audit_20261018_r1.py
- **来源**：Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.
- **日期**：2026-10-17T20:57:15.418317+00:00
- **哈希**：SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.
- **命令**：python -B release/f1_audit_20261010/deploy_leo900_statistics_numerical_audit_20261018_r1.py (once).
- **结果**：Rack 16/16 passes. Raw code/receipt transfer 170078 bytes; tensor transfer 0. Preflight validates 156 registered inputs and returns PENDING_TERMINAL; no bootstrap, truth or prediction arrays decoded. Preflight SHA256 3fa55b0e155a9cd20307442ebfba7871a475b862e50dd8181541c667065db9b8.
- **交叉验证**：Transferred hashes match current local GREEN hashes and deployed-file records. Windows/Python3.12 and Linux/Python3.10 executions agree for synthetic arithmetic; this is portability checking, not independent research replication.
- **置信度**：High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.
- **剩余风险**：The complete real chronology and numerical results must still be audited after the existing chain finishes. Do not redeploy over this directory or invoke evaluator again.
- **状态**：DEPLOYED; REAL TERMINAL VERIFICATION PENDING

## F1-R8-04

- **位置**：Current F1 disposition, active goal, manuscript and original pre-final commitment
- **原文**：Review F1: if outer outcomes affected revision, retain them as development/diagnostic evidence and supply a genuinely untouched final test.
- **问题**：Earlier F1-closed/accepted wording, including the active goal objective wording about 15/15 checks, is obsolete. Tests and preflight cannot establish the final scientific result.
- **修改**：Retain the prior records, explicitly maintain F1 OPEN and the manuscript/F2-F10 substantive freeze, and preserve the exact original pre-final package. Historic outer counts 5,4,3,1,3,0 and LEO800 feedback remain admitted development evidence.
- **证据**：release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R7.json; release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json; release/f1_audit_20261010/leo900_external_commitment_rest_publication_20261017T193909Z.json
- **来源**：Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.
- **日期**：2026-10-17T20:57:15.418317+00:00
- **哈希**：SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.
- **命令**：Hash frozen main.tex, main.pdf and pre-final SHA256_MANIFEST.json; read current active-goal status without closing it.
- **结果**：Frozen manuscript and original pre-final manifest hashes remain identical. F1 OPEN; goal active. The new numerical verifier is an audit addition, not a replacement candidate or a revised preregistration.
- **交叉验证**：Original review quotations, retained development chronology and separately registered LEO900 chain resolve the intended evidence roles. Server publication observations establish availability by response time, not immutable notarization or historical non-access.
- **置信度**：High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.
- **剩余风险**：F1 acceptance still requires actual final freeze/access chronology, original single evaluation, exact gate, fixed uncertainty and honest effect-size review. F2-F10 and all final deliverables remain required before goal completion.
- **状态**：F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE

## F1-R8-05

- **位置**：Read-only LEO900 observations at 2026-10-17T20:52:43Z/44Z
- **原文**：Normal simulation exit then seal, freeze, single evaluation and fixed statistics are handled by the existing controller.
- **问题**：Partial generation is not a finished final test, and no completion time follows from a snapshot.
- **修改**：Append filename/count/size/time and controller/process observations without decoding MAT/PT or modifying the running chain.
- **证据**：release/f1_audit_20261010/leo900_generation_metadata_20261017T205243Z.json; release/f1_audit_20261010/leo900_continuation_observation_20261017T205244Z.json
- **来源**：Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.
- **日期**：2026-10-17T20:57:15.418317+00:00
- **哈希**：SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.
- **命令**：python -B release/f1_audit_20261010/capture_leo900_metadata_20261018.py; python -B release/f1_audit_20261010/capture_leo900_continuation_20261018.py.
- **结果**：BAT23/48, RWA0/48; four MATLAB workers near99.7-99.8% CPU; controller PID616411 waiting. Two hash-linked controller events validate; stderr empty. No final guard or terminal at this observation.
- **交叉验证**：Output-directory metadata, OS ps/proc observations and controller event records agree at the sampled time. These channels share the same host and are not independent historical access attestations.
- **置信度**：High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.
- **剩余风险**：Status can advance after this observation. Preserve the running simulation and controller; after final visibility, no candidate revision can be confirmed again on this final set.
- **状态**：GENERATION RUNNING; EXISTING CHAIN PRESERVED

## SHA256

| 文件 | SHA256 |
|---|---|
| `release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json` | `a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a` |
| `release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R7.json` | `803a221e053008077d18d69a8ede52960d5b8de9c4e42dae9bcc2ef476900b2b` |
| `release/f1_audit_20261010/F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json` | `754326c717669f23f82d8cf044d87333772f21fe82a8b389a169389771506da1` |
| `release/f1_audit_20261010/append_f1_leo900_preflight_r8_20261018.py` | `f40788e5237d07423141c9e870e5ca9f603510e4d7405d0197129fe97db4c126` |
| `release/f1_audit_20261010/deploy_leo900_statistics_numerical_audit_20261018_r1.py` | `dccb0e40629e247afc65a53b897a30edff05705aefdeea637c1ee5f8701dd05d` |
| `release/f1_audit_20261010/f1_lossless_gate_statistics_20261018.py` | `adbd7ee1729b919fe0a5300105c78ef70689f38798ee6b2eae8b853a01e1741c` |
| `release/f1_audit_20261010/leo900_continuation_observation_20261017T205244Z.json` | `5df42319d954718ad76775cbb0fc420a421aaf3eda51bb880bb53a79b7512326` |
| `release/f1_audit_20261010/leo900_external_commitment_rest_publication_20261017T193909Z.json` | `5c60799f4d6154bf6235453a44e7ca385b27b5653d428ebc23031c2535bf7025` |
| `release/f1_audit_20261010/leo900_generation_metadata_20261017T205243Z.json` | `ca63432c0fb6795264ae6f8b01e006020299b4bc4ea05eb4f59c21cbedb7d51a` |
| `release/f1_audit_20261010/leo900_statistics_numerical_audit_20261018.py` | `105618a87df69fd750c70f3388e93c70af9d33ec46e60cfe73677dd8bc55f179` |
| `release/f1_audit_20261010/leo900_statistics_numerical_audit_deployment_20261017T205500Z.json` | `bda4a63b1350420e76fdc929633fbde87654499a07dfab0a8020da1ab11bb443` |
| `release/f1_audit_20261010/leo900_terminal_evidence_20261018_r2.py` | `3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0` |
| `release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r1.json` | `eb42b406dfb04977dbd4d0c8eaf7c0ede75728273f1fcf32f68f9d9f5e690653` |
| `release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r2.json` | `4efe49d29b1453e2f5250e624ff8653a5aeaecbf478b9b2890c20f41a81a3ec8` |
| `release/f1_audit_20261010/statistics_numerical_audit_local_20261018_r3.json` | `da952e4a4c976e7559f3275d7ef570c60720c0e5af30e154392ebb89de4e3e1d` |
| `release/f1_audit_20261010/statistics_numerical_audit_red_20261018_r1.json` | `410b6bb34dafd8039efd2dcf31ea2852124eb6c2c7bf549113a2f84ad5b1360b` |
| `release/f1_audit_20261010/test_leo900_statistics_numerical_audit_20261018.py` | `c8bfd63d3f93425ca6756900019f11509ffbf5c116146a980b9a03c1852c40b3` |

## 后续要求

1. Preserve the existing simulation/controller chain through its normal terminal.
2. After complete terminal, run the deployed R2 and numerical auditors to new output names; never repeat evaluation.
3. Audit generated96-unit partition versus positive-window evaluated subset, freeze/access chronology, original full-precision gate and fixed statistics.
4. Review physical-unit effect sizes and uncertainty honestly before deciding F1 acceptance.
5. After F1 closure, resume F2-F10 and all final deliverables. Do not close goal for auxiliary tests or process status.
