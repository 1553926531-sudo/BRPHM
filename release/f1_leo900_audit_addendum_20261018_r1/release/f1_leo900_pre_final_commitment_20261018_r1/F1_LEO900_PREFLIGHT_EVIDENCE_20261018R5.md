# F1 LEO900 additive evidence ledger R5

F1 remains OPEN; goal remains active. Manuscript and substantive F2-F10 edits are frozen.

Created UTC: 2026-10-17T19:30:39.259353+00:00. JSON SHA-256: `cfeb3f3b08f83db22c1e41e03dacb97a2d9513a8488c7edaeade4574843da2ea`.

This is a later additive record. Earlier evidence and failed attempts are preserved.

## F1-R5-01

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-01

**location**: Review F1; abstract/Fig.1/Section VII vs Section V/Table I/Fig.2

**original**: Candidate selection never reads outer labels; outer failure counts 5,4,3,1,3,0.

**problem**: Historic outer results influenced subsequent development; an old provenance boolean cannot undo that reuse.

**modification**: Retain historic outer/LEO800 as development evidence and require the fixed LEO900 final chain. Supersede earlier F1-closed implications.

**evidence**: F1_EVIDENCE_LEDGER_20261017.md; F1_LEO900_PREFLIGHT_EVIDENCE_20261018R4.json

**hash**: See artifact_sha256 for every cited package file

**command**: Inspect review F1, preserved chronology and registered candidate/partition input hashes.

**result**: F1 OPEN; no manuscript or substantive F2-F10 editing in this continuation.

**cross_validation**: Review quotations and archived candidate/failure chronology agree on reuse; new final is separately registered.

**remaining_risk**: Final evaluation and provenance verification still required; no claim of scientific success.

**status**: OPEN

## F1-R5-02

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-02

**location**: Fixed final statistical postprocessing

**original**: Gate tolerance 1e-12; seeds 17/42/73 are ensemble constituents.

**problem**: Rounded displays and window-wise uncertainty cannot independently substantiate the final decision.

**modification**: Register lossless same-pass NPZ/JSON reconstruction, unit-cluster bootstrap and multiplicity before final access.

**evidence**: F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json; leo900_statistics_protocol_deployment_r1_20261017T190734Z.json

**hash**: See artifact_sha256 for every cited package file

**command**: Recorded deployment/test commands; postprocessing command fixed in the statistical protocol.

**result**: Local/Rack 14-test suites; 18 metric and 124 gate oracle cases; artificial CLI with 20000 draws. All 14 input anchors unchanged.

**cross_validation**: Recomputed arithmetic checked against frozen metric/gate implementations and artificial known-answer fixtures.

**remaining_risk**: One final orbit; intervals condition on units and fitted models. Gate success does not imply meaningful effect.

**status**: REGISTERED; REAL RESULTS PENDING

## F1-R5-03

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-03

**location**: Continuation controller and preserved test history

**original**: seal -> freeze -> evaluate -> statistics; no automatic retries.

**problem**: An interrupted chat must not cause duplicate evaluation or a skipped statistics stage after a negative gate.

**modification**: Install a fixed-path exclusive controller with hash checks, output preservation, input drift checks and a single-access guard.

**evidence**: leo900_final_continuation_red_20261018_r1.json; leo900_final_continuation_local_green_20261018_r1.json; leo900_final_continuation_local_green_20261018_r3.json; leo900_final_continuation_deployment_20261017T192006Z.json

**hash**: See artifact_sha256 for every cited package file

**command**: python -B -m unittest test_leo900_final_continuation_20261018 -v (local and Rack, recorded commands)

**result**: Initial missing implementation RED retained. First implementation rejected Windows short paths (7 tests: 5 failures/2 errors); corrected symlink/junction checks. Final local/Rack 11/11 pass.

**cross_validation**: Disposable subprocess fixtures verify stage order, negative gate continuation, phase failures, missing receipts, drift and duplicate-output rejection; Rack deployment hashes match local files.

**remaining_risk**: Artificial tests verify execution behavior, not model performance or final-data validity.

**status**: IMPLEMENTED AND DEPLOYED

## F1-R5-04

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-04

**location**: First deployment and corrected deployment

**original**: Registered paths must use POSIX separators on Rack.

**problem**: First deploy attempt serialized Windows backslashes into a remote path.

**modification**: Use Path.as_posix(); preserve failed receipt and deploy only to the registered support directory.

**evidence**: leo900_final_continuation_deployment_20261017T191902Z.json; leo900_final_continuation_deployment_20261017T192006Z.json

**hash**: See artifact_sha256 for every cited package file

**command**: Recorded deploy_leo900_final_continuation_20261018.py invocation; do not rerun after controller start.

**result**: First attempt failed before remote mkdir. Corrected deployment transferred 28949 code bytes; tests and read-only preflight passed before launch.

**cross_validation**: Failure traceback plus corrected remote paths, deployed file hashes and Rack verification.

**remaining_risk**: Deployment success is an execution prerequisite, not an experimental result.

**status**: CORRECTED; BOTH ATTEMPTS RETAINED

## F1-R5-05

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-05

**location**: Controller launch and post-SSH process observation

**original**: Continue after normal simulation completion using fixed stages and outputs.

**problem**: A successful launch response alone does not establish process survival or protect the simulation.

**modification**: Record detached controller PID, affinity/nice, event chain and later read-only process evidence.

**evidence**: leo900_final_continuation_launch_20261017T192053Z.json; leo900_continuation_observation_20261017T192737Z.json

**hash**: See artifact_sha256 for every cited package file

**command**: python -B release/f1_audit_20261010/capture_leo900_continuation_20261018.py

**result**: PID616411 survives with PPID1, CPU4/nice15; four MATLAB workers CPU0-3 remain active. Two controller events; valid chain; stderr empty; waiting for simulation; guard absent.

**cross_validation**: Launch receipt, /proc state, ps output and byte-linked event files from a later SSH session.

**remaining_risk**: Process liveness is not completion; this is a point-in-time access/metadata observation.

**status**: RUNNING; WAITING FOR SIMULATION

## F1-R5-06

**finding**: F1

**source**: Original IEEE review F1 and byte-bound project records in this package

**date**: 2026-10-17T19:30:39.259353+00:00

**confidence**: High for code/bytes/process observations. Self-recorded timestamps and access guards are not independent no-access attestations.

**id**: F1-R5-06

**location**: Pre-final public commitment in BRPHM

**original**: Provide timestamps, input/output hashes, outer-read and selection-decision logs.

**problem**: Local hashes and clocks alone do not supply an external publication record.

**modification**: Publish this small fixed input/protocol/evidence package to an additive BRPHM branch with server readback; preserve all dirty work.

**evidence**: F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json; registered_input_export.json; registered_inputs/evidence/formal_candidate_receipt.json

**hash**: See artifact_sha256 for every cited package file

**command**: Dedicated alternate-index git commit and non-force push to BRPHM; verify commit/ref and blob hashes through independent readback.

**result**: Package prepared before observed final access. Remote commit and GitHub server metadata must be appended in a separate publication receipt.

**cross_validation**: Input bytes exported with registered hashes and guard absence before/after; GitHub acceptance to be checked separately.

**remaining_risk**: A GitHub commit is editable repository history, not immutable notarization; it cannot prove historic non-access or backdate this commitment.

**status**: PUBLICATION PENDING

