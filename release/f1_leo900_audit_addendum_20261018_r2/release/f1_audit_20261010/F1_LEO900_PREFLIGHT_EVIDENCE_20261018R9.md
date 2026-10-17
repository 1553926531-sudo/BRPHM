# F1 LEO900 追加证据台账 R9

记录时间：2026-10-17T21:15:57.666034+00:00

**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**

追加预测到单位汇总的独立核验、保留的失败测试、Rack 部署及运行观察。候选、门禁、统计设计和原始预最终承诺保持原登记字节。

## F1-R9-01

- **位置**：Prediction NPZ -> formal metrics and saved unit sufficient summaries
- **原文**：R8 explicitly retained saved sufficient summaries as an input assumption of its independent bootstrap verifier.
- **问题**：Hash-linked internally consistent unit errors may still disagree with the original saved predictions. An independent numerical bootstrap check alone would not detect that upstream contradiction.
- **修改**：Add an independent read-only scalar-error/math.fsum auditor of original single-pass predictions. It first requires R2 complete terminal verification, then checks pooled/unit errors, physical scale, label division dtype, route alpha, float32 blend and constituent descriptions without invoking model, evaluator or statistical producer.
- **证据**：release/f1_audit_20261010/leo900_prediction_summary_audit_20261018.py; release/f1_audit_20261010/test_leo900_prediction_summary_audit_20261018.py; release/f1_audit_20261010/leo900_terminal_evidence_20261018_r2.py; release/f1_audit_20261010/leo900_statistics_numerical_audit_20261018.py; release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json
- **来源**：Review F1; saved registered prediction/statistical contracts; independent scalar arithmetic; hand-derived artificial cases; hash-bound local/Rack receipts. Independence is qualified in cross_validation.
- **日期**：2026-10-17T21:15:57.666034+00:00
- **哈希**：Full artifact SHA256 values appear in artifact_sha256; the original review is separately hash-bound.
- **命令**：python -B -m unittest -v test_leo900_prediction_summary_audit_20261018; after full terminal only, invoke the deployed read-only CLI with a new output name.
- **结果**：Prepared verifier covers projected/candidate-only/control-only pooled RMSE/MAE/bias, unit-macro RMSE, upward fraction, unit/window membership, per-unit SSE/SAE/RMSE/MAE, saved deltas/relative changes and three seed constituent descriptions. Alternative descriptive sums allow64 ULP; the original1e-12 gate remains exact and unchanged.
- **交叉验证**：Interleaved unequal-size units have independently hand-derived physical errors: candidate A SSE16/SAE4 and B SSE56/SAE12, pooled RMSEsqrt(14.4)/MAE3.2; control pooled RMSEsqrt8/MAE2.4. A rehashed contradictory seed metric passes structural binding but is rejected here. These are independent calculations, not independent research data.
- **置信度**：High for the stated implementation, synthetic tests, byte identity and observations; no final scientific conclusion follows before complete terminal review.
- **剩余风险**：Does not independently decode raw MAT/PT, reconstruct label eligibility, or reproduce projection/centering/model predictions. Saved prediction arrays and their row metadata remain inputs. Passing these checks cannot establish population generalization.
- **状态**：PREDICTION-SUMMARY VERIFIER PREPARED; REAL FINAL READ DEFERRED

## F1-R9-02

- **位置**：Missing-implementation RED, first GREEN attempt and corrected synthetic fixture
- **原文**：Tests must reach the intended arithmetic contract and preserve failed attempts.
- **问题**：The first12-test GREEN attempt had11 passes and1 failure: its label-division fixture changed layout rmax8->3 but left statistics rmax8, so validation correctly stopped at the scale mismatch before testing dtype arithmetic.
- **修改**：Preserve the genuine missing-implementation RED and failed first GREEN receipt. Correct only the artificial fixture statistics rmax to3, then run the full12-test suite with unchanged implementation and source hashes recorded.
- **证据**：release/f1_audit_20261010/prediction_summary_audit_red_20261018_r1.json; release/f1_audit_20261010/prediction_summary_audit_local_20261018_r1.json; release/f1_audit_20261010/prediction_summary_audit_local_20261018_r2.json; release/f1_audit_20261010/test_leo900_prediction_summary_audit_20261018.py; release/f1_audit_20261010/leo900_prediction_summary_audit_20261018.py
- **来源**：Review F1; saved registered prediction/statistical contracts; independent scalar arithmetic; hand-derived artificial cases; hash-bound local/Rack receipts. Independence is qualified in cross_validation.
- **日期**：2026-10-17T21:15:57.666034+00:00
- **哈希**：Full artifact SHA256 values appear in artifact_sha256; the original review is separately hash-bound.
- **命令**：Recorded python -B -m unittest -v test_leo900_prediction_summary_audit_20261018, numerical libraries constrained to one thread.
- **结果**：Local12/12 pass in19.636s, sources_unchanged=true. Tests reject wrong summaries, relabelled rows, wrong physical scale, NaN/shape mismatch, duplicate NPZ members, wrong alpha/blend/dtype and contradictory seed metrics. Pending-terminal witness leaves poisoned predictions unread; complete synthetic production-shaped chain remains byte-identical.
- **交叉验证**：Hand-derived arithmetic provides an oracle separate from the implementation. Synthetic ProductionFixture exercises complete R2 provenance binding before independent scalar checking. No real final data were used by tests.
- **置信度**：High for the stated implementation, synthetic tests, byte identity and observations; no final scientific conclusion follows before complete terminal review.
- **剩余风险**：The corrected fixture failure was not a missing-implementation RED. Tests do not exhaust all possible inputs or validate the actual final scientific result.
- **状态**：12/12 LOCAL; RED AND FAILED ATTEMPT RETAINED

## F1-R9-03

- **位置**：Rack prediction_summary_audit_support_20261018_r1 deployment
- **原文**：Existing one-shot final execution and simulation must be preserved.
- **问题**：Local passing tests alone do not establish deployed code identity or behavior on Rack.
- **修改**：Deploy six small source/receipt files once to a new exclusive support directory; run only artificial tests and the fixed read-only audit on CPU4/nice15 with one numerical thread.
- **证据**：release/f1_audit_20261010/leo900_prediction_summary_audit_deployment_20261017T211424Z.json; release/f1_audit_20261010/deploy_leo900_prediction_summary_audit_20261018_r1.py; release/f1_audit_20261010/prediction_summary_audit_local_20261018_r2.json; release/f1_audit_20261010/leo900_prediction_summary_audit_20261018.py; release/f1_audit_20261010/test_leo900_prediction_summary_audit_20261018.py
- **来源**：Review F1; saved registered prediction/statistical contracts; independent scalar arithmetic; hand-derived artificial cases; hash-bound local/Rack receipts. Independence is qualified in cross_validation.
- **日期**：2026-10-17T21:15:57.666034+00:00
- **哈希**：Full artifact SHA256 values appear in artifact_sha256; the original review is separately hash-bound.
- **命令**：python -B release/f1_audit_20261010/deploy_leo900_prediction_summary_audit_20261018_r1.py (already executed once; never repeat over this directory).
- **结果**：Rack12/12 passes.144218 raw code/receipt bytes uploaded;0 tensor bytes. Preflight validates156 registered inputs and defers prediction decoding until complete terminal. Audit SHA256 c1190d3ebd7b87184b102676fc05bd31f50712d883191cb6109b52f9b77c03ac. Candidate, controller and simulation unchanged.
- **交叉验证**：Local GREEN source hashes agree with transfer records and deployed-file hashes. Windows/Python3.12 and Linux/Python3.10 run the same12 artificial cases successfully. This establishes portability of the tested code, not independent model replication.
- **置信度**：High for the stated implementation, synthetic tests, byte identity and observations; no final scientific conclusion follows before complete terminal review.
- **剩余风险**：Real saved prediction/summary agreement remains to be checked after terminal. Do not repeat evaluation or alter the frozen candidate after observing final data.
- **状态**：DEPLOYED; REAL PREDICTION AUDIT AWAITS COMPLETE TERMINAL

## F1-R9-04

- **位置**：F1 disposition, continuing simulation, frozen manuscript and public audit addendum
- **原文**：Review F1 requires an untouched final test after development used outer feedback; F1 must precede substantive F2-F10/manuscript changes.
- **问题**：Auxiliary tests, public audit publication and normal process activity cannot close F1. Earlier15/15-closed wording in the retained goal objective is obsolete.
- **修改**：Maintain F1 OPEN and goal active, preserve original commitments/manuscript and append this evidence. Historical outer counts5,4,3,1,3,0 and LEO800 remain development/diagnostic evidence. Preserve the running simulation and existing automatic controller.
- **证据**：release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json; release/f1_audit_20261010/leo900_generation_metadata_20261017T211439Z.json; release/f1_audit_20261010/leo900_continuation_observation_20261017T211439Z.json; release/f1_audit_20261010/leo900_audit_addendum_publication_20261017T210327Z.json; release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json
- **来源**：Review F1; saved registered prediction/statistical contracts; independent scalar arithmetic; hand-derived artificial cases; hash-bound local/Rack receipts. Independence is qualified in cross_validation.
- **日期**：2026-10-17T21:15:57.666034+00:00
- **哈希**：Full artifact SHA256 values appear in artifact_sha256; the original review is separately hash-bound.
- **命令**：Read-only metadata/controller captures at2026-10-17T21:14:39Z; SHA256-check main.tex/main.pdf and both existing package manifests.
- **结果**：BAT25/48,RWA0/48 at this observation; four MATLAB workers near99.7%CPU, no MATLAB stderr. Controller616411 waiting, two-event hash chain valid. Frozen file hashes unchanged. Earlier R5-R8 audit addendum published and read back in BRPHM commit b8ad940e5779692f25643cdaa2fac346e4385760.
- **交叉验证**：File metadata, OS process observations and controller event chain agree at capture time but share one host. GitHub readback corroborates the published bytes by server response time; it is neither historical non-access proof nor immutable notarization.
- **置信度**：High for the stated implementation, synthetic tests, byte identity and observations; no final scientific conclusion follows before complete terminal review.
- **剩余风险**：Remaining generated members, seal/freeze/evaluation/statistics chronology, original gate, physical effects and uncertainty require actual terminal audit. One held-out orbit and ensemble constituents cannot establish independent multi-orbit replication.
- **状态**：F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE

## SHA256

| 文件 | SHA256 |
|---|---|
| `release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json` | `a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a` |
| `release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json` | `7ace7afcbb8756f681134975fc999865745086d8b62db751977c73a138de2f29` |
| `release/f1_audit_20261010/append_f1_leo900_preflight_r9_20261018.py` | `bd5f74b59cff75a3bac0f280d26f96df99c0d0784a01cfd9303bb8f47f9372b8` |
| `release/f1_audit_20261010/deploy_leo900_prediction_summary_audit_20261018_r1.py` | `a06aabdb79202c90ba579713a01eba27604c01e8a12104e1bf5b70c3df76288c` |
| `release/f1_audit_20261010/leo900_audit_addendum_publication_20261017T210327Z.json` | `887d833e37c1d499180a0eda9459475de54af1186d7baaa4c2b143929c1018a7` |
| `release/f1_audit_20261010/leo900_continuation_observation_20261017T211439Z.json` | `6dc96dbfedbbb5ca5946ad15ccc3b97733755b660b22f94a5c5d8a3afe769ace` |
| `release/f1_audit_20261010/leo900_generation_metadata_20261017T211439Z.json` | `2deb91e8032abf7884f5e353a7381265fbd9a18f3a22e07294833e289c987c27` |
| `release/f1_audit_20261010/leo900_prediction_summary_audit_20261018.py` | `8c2fbabdcedf8a3263a951baa3114415687a970446666f1e87e9b3af09450c2c` |
| `release/f1_audit_20261010/leo900_prediction_summary_audit_deployment_20261017T211424Z.json` | `1e79319f2809660973b5b8549afda1b7bc7fe3055624bbf6b3d3ad9bd6cee3d8` |
| `release/f1_audit_20261010/leo900_statistics_numerical_audit_20261018.py` | `105618a87df69fd750c70f3388e93c70af9d33ec46e60cfe73677dd8bc55f179` |
| `release/f1_audit_20261010/leo900_terminal_evidence_20261018_r2.py` | `3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0` |
| `release/f1_audit_20261010/prediction_summary_audit_local_20261018_r1.json` | `0046cea59c053f5fbe4f46ab7693db052c5f6ec4e3e7cca10b524318bbf4b00b` |
| `release/f1_audit_20261010/prediction_summary_audit_local_20261018_r2.json` | `e541a2c36f011dde2ebd5d354bd589873311edc569b4ca1f9eb11c224e797038` |
| `release/f1_audit_20261010/prediction_summary_audit_red_20261018_r1.json` | `7ccb2e4218384f16d512f3dc7575c854a5a482ac8c098ea002daa636ee84317d` |
| `release/f1_audit_20261010/test_leo900_prediction_summary_audit_20261018.py` | `7d195a43649c5c615f223b395c8ed501d55988eccd3d2c2b5d9edb0759b68411` |

## 后续要求

1. Preserve the existing simulation/controller through normal terminal.
2. At complete terminal run R2, numerical-statistics and prediction-summary auditors to new output names; never repeat evaluation.
3. Audit96 generated members versus positive-window evaluated subset, freeze/access chronology and original precision gate.
4. Assess registered statistics, physical-unit effect size and uncertainty before deciding F1.
5. After actual F1 closure, resume F2-F10 and all final deliverables; auxiliary tests cannot complete the goal.
