"""Append an evidence ledger; never modify earlier receipts or the committed package."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEW = Path(r"C:\Users\Administrator\Documents\Codex\2026-10-01\ni-d\outputs\IEEE_Review_Report_English.md")
REVIEW_SHA = "9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5"
PREVIOUS_SHA = "cfeb3f3b08f83db22c1e41e03dacb97a2d9513a8488c7edaeade4574843da2ea"
REQUIRED = ("location", "original", "problem", "modification", "evidence", "source",
            "date", "hash", "command", "result", "cross_validation", "confidence",
            "remaining_risk", "status")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    output = HERE / "F1_LEO900_PREFLIGHT_EVIDENCE_20261018R6.json"
    markdown = output.with_suffix(".md")
    if output.exists() or markdown.exists():
        raise FileExistsError("R6 already exists; append another revision instead")
    assert sha(REVIEW) == REVIEW_SHA
    assert sha(HERE / "F1_LEO900_PREFLIGHT_EVIDENCE_20261018R5.json") == PREVIOUS_SHA
    now = datetime.now(timezone.utc).isoformat()
    publication_name = "leo900_external_commitment_rest_publication_20261017T193909Z.json"
    publication = load(publication_name)
    generation_name = "leo900_generation_metadata_20261017T201536Z.json"
    generation = load(generation_name)
    observation_name = "leo900_continuation_observation_20261017T201536Z.json"
    observation = load(observation_name)
    deployment_name = "leo900_terminal_evidence_deployment_20261017T200942Z.json"
    deployment = load(deployment_name)
    flow_name = "F1_LEO900_TRAINING_LABEL_FLOW_20261018R1.json"
    flow = load(flow_name)
    assert publication["status"] == "PUBLISHED_AND_READBACK_VERIFIED"
    assert publication["repository"] == "https://github.com/1553926531-sudo/BRPHM"
    assert publication["commit"] == "846cdaac03beab2bacb9834bde1ed8fff1c77141"
    assert generation["counts"] == {"bat": 22, "rwa": 0}
    assert observation["event_chain_valid"] is True
    assert not observation["documents"]["guard"]["exists"]
    assert not observation["documents"]["terminal"]["exists"]
    assert deployment["verification"]["test_count"] == 32
    assert deployment["verification"]["exit_code"] == 0
    assert deployment["read_only_audit"]["report"]["status"] == "PENDING_TERMINAL"
    assert flow["status"] == "STATIC_REVIEW_CHECKS_PASS"
    assert len(flow["sources"]) == 8 and len(flow["findings"]) == 6

    records = {}

    def refs(*names):
        paths = []
        for name in names:
            parent = ROOT / "release/f1_leo900_pre_final_commitment_20261018_r1" if name.startswith("registered_inputs/") else HERE
            path = parent / name
            assert path.is_file() and not path.is_symlink(), name
            key = path.relative_to(ROOT).as_posix()
            records[key] = sha(path)
            paths.append(key)
        return paths

    def item(number, location, original, problem, modification, evidence, command,
             result, cross_validation, confidence, remaining_risk, status):
        return dict(id=f"F1-R6-{number:02d}", finding="F1", location=location,
                    original=original, problem=problem, modification=modification,
                    evidence=refs(*evidence), source="Original review F1, cited byte-bound project records, and observed GitHub server response where specified",
                    date=now, hash="Exact SHA256 values in artifact_sha256; original review in review_report",
                    command=command, result=result, cross_validation=cross_validation,
                    confidence=confidence, remaining_risk=remaining_risk, status=status)

    findings = [
        item(1, "Review F1, lines 19-25; abstract/Fig.1/Section VII vs Section V/Table I/Fig.2; active goal text",
             '“Candidate selection never reads outer labels”; successive failures “5, 4, 3, 1, 3, 0”; “The uniform floor fixed all six folds.”',
             "Historic outer outcomes and LEO800 feedback affected development. An old F1-pass entry in the goal objective and provenance booleans cannot establish a clean history.",
             "Retain those outcomes as development/diagnostic evidence. Explicitly supersede earlier F1-closed implications; require the separate LEO900 final chain before manuscript editing resumes.",
             ["F1_EVIDENCE_LEDGER_20261017.md", "F1_LEO900_PREFLIGHT_EVIDENCE_20261018R5.json", flow_name],
             "Read original review F1, preserved chronology, and source/route records; get_goal read-only snapshot on this continuation.",
             "F1 OPEN; goal active; manuscript and substantive F2-F10 changes frozen. The goal's stale wording is not an acceptance result.",
             "Review quotations and archived candidate chronology agree on reuse. Registered continuation records explicitly retain LEO800 influence; none is an independent witness to all historic accesses.",
             "High for the documented contradiction and current status; no global absence-of-access proof claimed.",
             "A real final result, complete execution binding, and an honest revised manuscript are still required.", "OPEN"),
        item(2, "BRPHM additive pre-final publication, separate branch; previous R5 publication-pending entry",
             "Provide candidate sequence, timestamps, input/output hashes, outer-read and selection-decision logs.",
             "A locally authored timestamp alone does not establish external availability; three publication attempts failed before successful publication.",
             "Append successful REST publication and server readback without altering the committed package, prior attempts, working branch, or dirty files.",
             [publication_name, "leo900_external_commitment_publication_20261017T193202Z.json",
              "leo900_external_commitment_publication_20261017T193303Z.json",
              "leo900_external_commitment_rest_publication_20261017T193737Z.json"],
             "Recorded publish_leo900_external_commitment_rest_20261018.py transaction and GET ref/commit/tree/blob readbacks; do not republish.",
             "Commit 846cdaac03beab2bacb9834bde1ed8fff1c77141, parent 8449f14551c4ba229b2596e86b9fabd80df72a2a, branch f1-leo900-prefinal-20261018-r1; 41 files/519673 bytes verified. Observed GitHub ref Date: Sat, 17 Oct 2026 19:39:35 GMT; repository id 1392841783. Failures retained: no GCM credential, smart-Git reset, and first REST base-commit GET404 assumption.",
             "Local Git object/tree checks and GitHub ref/commit/tree/blob byte readbacks agree; server metadata supplies an external availability observation.",
             "High for published bytes and observed availability time.",
             "GitHub history is editable. Server Date is not immutable notarization, cannot backdate the commitment, and does not prove historical non-access.",
             "PUBLISHED_AND_READBACK_VERIFIED; F1 STILL OPEN"),
        item(3, "LEO900 simulation and detached continuation controller, read-only 20:15 UTC observation",
             "Simulation completion -> metadata seal -> candidate freeze -> single evaluate -> fixed statistics.",
             "Process launch and partial MAT generation do not establish completed generation, final evaluation, or success.",
             "Append metadata/process/event observations only; preserve the running simulation, configuration, and controller.",
             [generation_name, observation_name, "leo900_final_continuation_launch_20261017T192053Z.json"],
             "python -B release/f1_audit_20261010/capture_leo900_metadata_20261018.py; python -B release/f1_audit_20261010/capture_leo900_continuation_20261018.py",
             "At 2026-10-17T20:15:36Z, BAT22/48 and RWA0/48. Four MATLAB workers remain near 99.7% CPU. Controller PID616411, PPID1, CPU4/nice15; two events, valid chain, empty stderr, waiting for simulation; final-access guard and terminal receipt not yet created.",
             "File names/sizes/timestamps, /proc and ps state, controller event hashes, and simulation status-file metadata agree. These are point-in-time observations from the same host.",
             "High for observed process/metadata facts, conditional on the host and capture code.",
             "File presence is not semantic validity; no MAT contents or labels were decoded. No completion or runtime ETA is inferred.",
             "GENERATION RUNNING; CONTROLLER WAITING"),
        item(4, "Independent terminal verifier: fixed-plan binding and production-artifact schemas",
             "Exact fixed-plan input binding; lossless final gate and statistics reconciliation.",
             "Initial verifier treated 156 registered inputs as the full 157-entry controller plan, omitted semantic contradiction checks, and confused the formal comparison schema with the numeric-only statistics gate schema.",
             "Include the protocol itself in expected plan inputs; add semantic checks; compare formal comparison against five numeric fields plus its fixed rule, while statistics gate retains the five numeric fields. No registered evaluator was changed.",
             ["terminal_evidence_plan_binding_red_20261018_r2.json", "terminal_evidence_production_red_20261018_r3.json",
              "terminal_evidence_local_green_attempt_20261018_r4.json", "terminal_evidence_registered_gate_schema_red_20261018_r5.json",
              "leo900_terminal_evidence_20261018.py", "test_leo900_terminal_evidence_20261018.py"],
             "Recorded unittest commands in each RED/GREEN receipt; inspect registered protocol, controller plan schema, evaluator comparison.rule and statistics gate schema.",
             "Plan test first rejected a valid fixture. Sixteen added production/parser tests exposed nine missing semantic rejections. R4 green fixture omitted the formal rule; the production-schema RED retained this error, followed by the corrected R6 green run.",
             "Artificial opaque-array fixtures exercise production-only artifact branches; rehashed tampering is rejected by semantic checks. Actual evaluator/statistics source schemas supply the second comparison path, not independent historic access evidence.",
             "High for the reproduced verifier faults and tested corrections.",
             "Fixture success does not guarantee every production edge case. Actual terminal artifacts remain to be audited; gate success does not establish useful effect size.",
             "CORRECTED; ALL ATTEMPTS RETAINED"),
        item(5, "Independent terminal verifier: local/Rack verification, deployment, and first production preflight",
             "Audit terminal chronology, hashes, membership, precision, gate arithmetic, statistics summaries and reporting boundaries.",
             "A synthetic pass or deployed script alone cannot establish the registered real final execution.",
             "Deploy a separate stdlib verifier with fixed anchors; retain local/Rack test and preflight receipts, without invoking the controller, evaluator, or training.",
             ["terminal_evidence_local_green_attempt_20261018_r6.json", deployment_name,
              "leo900_terminal_evidence_20261018.py", "test_leo900_terminal_evidence_20261018.py", "deploy_leo900_terminal_evidence_20261018.py"],
             "python -B -m unittest -v test_leo900_terminal_evidence_20261018 (recorded local/Rack runs); fixed remote verifier CLI --output first_read_only_audit.json.",
             "Local32/32 in177.682s with unchanged before/after source hashes; Rack32/32 in1.618s. Uploaded108694 bytes, CPU4/nice15, numeric libraries single-threaded. First real read-only audit: PENDING_TERMINAL, registered_inputs_verified156, f1_closed=false, scientific_success_claimed=false.",
             "Local final source hashes match Rack deployed files; Rack tests agree with the local suite; first preflight verifies the registered production input anchors.",
             "High for the recorded checks and deployed bytes.",
             "Auditor streams raw bytes only for hashes, does not decode MAT/tensor/prediction/bootstrap arrays, and does not independently recompute bootstrap intervals. Summary sums allow64ULP for aggregation order; gate and lossless CSV comparisons remain exact.",
             "DEPLOYED; REAL TERMINAL AUDIT PENDING"),
        item(6, "Registered training/control label-flow static review, eight sources and six findings",
             "Candidate training, calibration, epoch selection and route must not use final labels.",
             "A same-named MLP helper uses Xva/yva early stopping, so names alone cannot establish which implementation is called. First static audit also incorrectly assumed all execution files were directly registered in the main protocol.",
             "Follow the main protocol -> execution amendment -> source hash chain and AST call/import bindings. Record complete function excerpts and distinguish the actual fixed-epoch imported MLP from the unused validation-label helper.",
             [flow_name, "audit_leo900_training_label_flow_20261018.py", "leo900_static_training_label_flow_binding_rejection_20261018_r1.json",
              "F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json"],
             "Recorded python -B release/f1_audit_20261010/audit_leo900_training_label_flow_20261018.py execution; do not overwrite the existing report.",
             "STATIC_REVIEW_CHECKS_PASS: old registered tensor rows train, appended final rows valid; TCN normalization/correction use source-fit labels; 90 fixed epochs and lambda0 preserve the original extra forward; actual MLP has fixed epochs; HGB/MLP receive y_train; final labels compute metrics/residuals after predictions; control copies fixed candidates with median3. No model imported or training invoked.",
             "AST call/import relationships, full cited function excerpts, and protocol/amendment/dependency-closure/archive hashes agree. Copies and hashes are not independent no-access witnesses.",
             "High for cited static code facts; runtime and all-history non-access require separate evidence.",
             "Not a whole-program information-flow proof. Runtime masks, dependency bytes and final access chronology must still match terminal receipts. Source-only internal HGB validation may exist.",
             "STATIC CHECKS PASS; RUNTIME BINDING PENDING"),
        item(7, "Locked LEO900 method/statistical protocol and scope of resulting evidence",
             "One frozen candidate, one final orbit; ensemble seeds17/42/73; paired unit uncertainty.",
             "Three ensemble constituents are not three independent experiment repetitions. A nonpositive delta at tolerance1e-12 is not sufficient to claim practical or population-wide improvement.",
             "Retain candidate/floor/route and fixed statistical protocol unchanged. Keep descriptive, uncertainty, execution-integrity and scientific-conclusion decisions explicit.",
             ["registered_inputs/evidence/formal_candidate_receipt.json", "F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json",
              "F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json", "registered_inputs/channel_policy_support_20261018_r4a/F1_LEO900_CHANNEL_POLICY_AMENDMENT_20261018R4.json"],
             "Read registered method/statistics/channel-policy commitments; compare their existing SHA256 anchors. No final result used to alter these commitments.",
             "LEO900 alpha1e-5 fixed for BAT and RWA; training seeds17/42/73, 90epochs, lambda0, source unit-median correction. Fixed20000 paired-unit bootstrap draws, component seeds20261018/20261019, pointwise95% plus eight-comparison Bonferroni intervals and four-test Holm handling. One final orbit; independent experiment replicates from ensemble seeds=0.",
             "Candidate receipt, execution adapter, registered statistical protocol and deployed verifier agree on the fixed constants; this agreement is not an independent proof of generalization.",
             "High for fixed configurations and statistical scope.",
             "Unit resampling conditions on fitted models and the one final orbit; it does not estimate across-orbit population uncertainty. Tiny alpha can yield tiny effects and requires honest magnitude reporting.",
             "LOCKED BEFORE OBSERVED FINAL ACCESS"),
        item(8, "F1 remaining acceptance path; freeze on other findings and manuscript",
             "A genuinely untouched final test after acknowledged outer reuse, with reconstructable freeze/access/decision chronology.",
             "No terminal final execution or scientific conclusion can be inferred from running processes, tests, code hashes, or an old F1-pass label.",
             "Keep goal active. Let the already running controller finish the registered chain; then run the deployed independent verifier to a new output and inspect the prespecified final effect/uncertainty. Preserve every outcome and make no post-result candidate changes against the same final set.",
             ["F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json", "F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json", deployment_name, observation_name,
              "leo900_r6_ledger_path_binding_rejection_20261018_r1.json"],
             "Future fixed read-only verifier CLI is recorded in the deployment receipt; use a fresh output filename after controller termination, never rerun evaluate.",
             "Next required: normal simulation exit,96-unit seal(BAT48/RWA48), freeze->guard->access->final->statistics chronology, real artifact verification, final result interpretation, then F1 decision. Substantive F2-F10/manuscript work remains frozen until that decision. This ledger helper first rejected its own wrong package-relative reference before creating outputs; the rejection receipt and correction are retained.",
             "Acceptance is grounded in original review F1 plus protocol/receipt chain, not a single provenance boolean; server availability and local execution records have distinct proof limits.",
             "High for the remaining recorded requirements; no result anticipated.",
             "If a new method is needed after observing final outcomes, this final set becomes development evidence for that method; a new independent final procedure is required. Goal completion also requires all F2-F10 deliverables.",
             "OPEN; GOAL ACTIVE"),
    ]
    package_manifest = ROOT / "release/f1_leo900_pre_final_commitment_20261018_r1/SHA256_MANIFEST.json"
    records[package_manifest.relative_to(ROOT).as_posix()] = sha(package_manifest)
    assert records[package_manifest.relative_to(ROOT).as_posix()] == publication["package_manifest_sha256"]
    records[Path(__file__).resolve().relative_to(ROOT).as_posix()] = sha(Path(__file__))
    document = {
        "schema": "brphm-f1-additive-pre-final-evidence-r6", "created_utc": now,
        "status": "F1 OPEN", "goal_status": "active", "f1_closed": False,
        "scientific_success_claimed": False, "manuscript_and_f2_f10_substantive_edits_frozen": True,
        "previous_r5_sha256": PREVIOUS_SHA,
        "review_report": {"path": str(REVIEW), "sha256": REVIEW_SHA, "lines": "19-25"},
        "repository_write_scope": "1553926531-sudo/BRPHM only",
        "protected_boundaries": {"BRPHM-preview": "no access or modification", "ModelScope": "read-only; not accessed by this ledger generator",
                                 "IEEE": "no upload, submission, email or external contact", "running_simulation": "no stop/restart/copy/configuration mutation"},
        "external_commitment": {k: publication[k] for k in ("repository", "branch", "commit", "commit_url", "base_commit", "package_manifest_sha256", "api_ref_response_headers", "status")},
        "snapshot_observation_utc": observation["observed_utc"],
        "artifact_sha256": dict(sorted(records.items())), "findings": findings,
        "evidence_limit": "Self-recorded clocks and access guards do not prove global historic non-access; GitHub readback establishes only observed external availability. F1 acceptance still requires the real final chain and honest disclosure.",
        "next_required": ["Complete the existing registered simulation/controller chain without restart",
                          "Run the already deployed independent terminal verifier to a fresh report",
                          "Verify real chronology, membership, exact metrics/gates and fixed statistics",
                          "Interpret actual effect and uncertainty without post-final tuning",
                          "Decide F1, then unfreeze substantive F2-F10/manuscript work; keep the overall goal active"],
    }
    for row in findings:
        assert all(row.get(key) for key in REQUIRED), row["id"]
        assert all(key in document["artifact_sha256"] for key in row["evidence"])
    for key, expected in document["artifact_sha256"].items():
        assert sha(ROOT / key) == expected, key
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    lines = ["# F1 LEO900 追加证据台账 R6", "", f"记录时间（UTC）：{now}", "",
             "**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**", "",
             "本追加台账保留全部旧登记、失败收据、已发布包和当前运行任务。旧 goal objective 中的 F1 已通过措辞已过时，不能用于销项。", "",
             f"机器可读台账：`{output.name}`；SHA256：`{sha(output)}`。", "",
             "外部发布证明所观察到的可用时间，不是不可变公证，也不证明历史上无人访问。测试通过不构成方法收益或泛化结论。", ""]
    labels = [("location", "位置"), ("original", "原文/登记约束"), ("problem", "问题"), ("modification", "修改/本次处理"),
              ("evidence", "证据"), ("source", "来源"), ("date", "日期"), ("hash", "哈希"), ("command", "命令"),
              ("result", "结果"), ("cross_validation", "交叉验证"), ("confidence", "置信度"), ("remaining_risk", "剩余风险"), ("status", "状态")]
    for row in findings:
        lines += [f"## {row['id']}", ""]
        for key, label in labels:
            value = row[key]
            if key == "evidence":
                value = "; ".join(f"`{name}` (SHA256 `{records[name]}`)" for name in value)
            lines += [f"**{label}：** {value}", ""]
    lines += ["## 接续顺序", ""] + [f"{i}. {text}" for i, text in enumerate(document["next_required"], 1)] + [""]
    with markdown.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    print(json.dumps({"status": document["status"], "goal_status": "active", "finding_count": len(findings),
                      "artifact_count": len(records), "json": str(output), "json_sha256": sha(output),
                      "markdown": str(markdown), "markdown_sha256": sha(markdown)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
