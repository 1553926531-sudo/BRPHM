"""Append F1 evidence only; preserve all prior receipts and frozen assets."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEW = Path(r"C:\Users\Administrator\Documents\Codex\2026-10-01\ni-d\outputs\IEEE_Review_Report_English.md")
REVIEW_SHA = "9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5"
PREVIOUS = "F1_LEO900_PREFLIGHT_EVIDENCE_20261018R6.json"
GREEN = "terminal_evidence_r2_local_green_20261018_r1.json"
DEPLOYMENT = "leo900_terminal_evidence_r2_deployment_20261017T204027Z.json"
INFERENCE = "F1_LEO900_INFERENCE_DEPENDENCIES_20261018R1.json"
GENERATION = "leo900_generation_metadata_20261017T203836Z.json"
CONTINUATION = "leo900_continuation_observation_20261017T203836Z.json"
AUDITOR = "leo900_terminal_evidence_20261018_r2.py"
TESTS = "test_leo900_terminal_evidence_20261018_r2.py"
REQUIRED = ("location", "original", "problem", "modification", "evidence", "source",
            "date", "hash", "command", "result", "cross_validation", "confidence",
            "remaining_risk", "status")
EXPECTED = {
    PREVIOUS: "78b50a8c44c47719359420a562c5be8334c18bcfb57203b8ceeb2f7d631493ff",
    GREEN: "3ba6d5a092dc3c4be17062e2a0713560a77c89614f8c4eacb2949298dc90842e",
    DEPLOYMENT: "7bb5ba31f64a7317f3787167f6ccd6844525f7b8ef1a61226f1773ebe604fc4e",
    INFERENCE: "37675a2e28c74abd0a0858010faf8171e1bdf1753e655b7f93c3256ec41605b0",
    GENERATION: "b3189fc5c020ec81856eaf7225e099736713ad585cf0b8021af2c54d644d9e28",
    CONTINUATION: "e24abe05b386d46c29fdaa53d201ffb6cca0f35cbc099e6069261ef10858802b",
    AUDITOR: "3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0",
    TESTS: "083d096d3e709fad922391a584c4d064c1a9fc0766bcaff8c3062320f1d3a15c",
    "terminal_unit_membership_red_20261018_r1.json": "c0e110bc912710e8d52aaa5838ea82359ed27d4ed921af91133ae5ca14556087",
    "terminal_unit_membership_red_20261018_r2.json": "219f33920a63dc284fa98f5be24d138418bb0741408e45e6ba0a6f3d3dcbfa62",
    "terminal_unit_membership_targeted_20261018_r1.json": "aa025f2adfc6b078d75d1024dc42d2d14321506c6734b27875b7c8fc466f86eb",
    "leo900_terminal_evidence_20261018.py": "f565bb1feeab8b963c124f1490a7b5de33d4bd8794ed400d839843e01304ad8e",
    "test_leo900_terminal_evidence_20261018.py": "b5f3766d31165823c68db2b21743c1c8f1e17bde84df2c00778cdcad28a87eec",
    "f1_clean_final_test_20261018_v3.py": "5fa91d9a00008fbeb69ba225f57d6163027ecc807a26b111bd97d7f0da9f0f57",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    output = HERE / "F1_LEO900_PREFLIGHT_EVIDENCE_20261018R7.json"
    markdown = output.with_suffix(".md")
    if output.exists() or markdown.exists():
        raise FileExistsError("R7 exists; append another revision without overwriting")
    assert sha(REVIEW) == REVIEW_SHA
    for name, expected in EXPECTED.items():
        assert sha(HERE / name) == expected, name
    green, deployed = load(GREEN), load(DEPLOYMENT)
    inference, generation, continuation = load(INFERENCE), load(GENERATION), load(CONTINUATION)
    assert green["exit_code"] == 0 and green["test_count"] == 39 and green["sources_unchanged"] is True
    assert re.search(r"Ran 39 tests in", green["stderr"]) and "skipped" not in green["stderr"]
    assert green["real_final_labels_read"] is False
    assert green["code_sha256"] == {name: EXPECTED[name] for name in (AUDITOR, TESTS)}
    assert deployed["status"] == "PASS" and deployed["ssh_exit_code"] == 0
    check = deployed["verification"]
    assert check["status"] == "PASS" and check["test_count"] == 39 and check["exit_code"] == 0
    assert re.search(r"Ran 39 tests in", check["stderr"]) and "skipped" not in check["stderr"]
    assert check["network_bytes_uploaded"] == 119285 and check["tensor_transfer_bytes"] == 0
    assert check["resources"]["cpu_affinity"] == [4] and check["resources"]["nice"] == 15
    for name in ("real_final_labels_read_by_tests", "simulation_or_configuration_modified",
                 "controller_or_evaluator_invoked", "candidate_or_route_modified"):
        assert check[name] is False, name
    for row in check["deployed_files"]:
        assert row["sha256"] == sha(HERE / Path(row["path"]).name)
    first_audit = deployed["read_only_audit"]["report"]
    assert first_audit["status"] == "PENDING_TERMINAL" and first_audit["f1_closed"] is False
    assert first_audit["registered_inputs_verified"] == 156
    assert first_audit["audit_code_sha256"] == EXPECTED[AUDITOR]
    assert first_audit["scientific_success_claimed"] is False
    assert first_audit["semantic_final_labels_read_by_auditor"] is False
    assert generation["counts"] == {"bat": 23, "rwa": 0}
    assert generation["mat_contents_read"] is False
    assert continuation["event_chain_valid"] is True
    assert not continuation["documents"]["guard"]["exists"]
    assert not continuation["documents"]["terminal"]["exists"]
    assert inference["f1_closed"] is False and len(inference["findings"]) == 10
    for row in inference["sources"].values():
        location = row["location"]
        if "::" not in location:
            assert sha(Path(location)) == row["sha256"], location

    now = datetime.now(timezone.utc).isoformat()
    records = {}

    def refs(*names):
        result = []
        for name in names:
            path = HERE / name
            assert path.is_file() and not path.is_symlink(), name
            key = path.relative_to(ROOT).as_posix()
            records[key] = sha(path)
            result.append(key)
        return result

    def finding(number, location, original, problem, modification, evidence,
                command, result, cross_validation, remaining_risk, status):
        return dict(id=f"F1-R7-{number:02d}", finding="F1", location=location,
                    original=original, problem=problem, modification=modification,
                    evidence=refs(*evidence), source="Original F1 review requirement and cited code/receipts; provenance limits stated per item",
                    date=now, hash="SHA256 entries in artifact_sha256; review SHA256 in review_report",
                    command=command, result=result, cross_validation=cross_validation,
                    confidence="High for byte-bound code and observed test/metadata facts; not a proof of all historic non-access",
                    remaining_risk=remaining_risk, status=status)

    findings = [
        finding(1, "Frozen raw evaluator build_raw_holdout_payload, lines450-519; independent auditor component/statistics checks",
                "Raw evaluator skips units when len(windows_array)==0 after the fixed finite/nonnegative label mask.",
                "The first independent auditor wrongly required48 evaluated units per component; generated partition membership and evaluable membership are distinct.",
                "Append R2: retain the96-unit generated partition; validate nonempty positive-integer unit-window maps as component-specific partition subsets; reconcile receipt, metrics, layout and statistics membership/counts; report generated/evaluated/zero-window sets separately.",
                ["f1_clean_final_test_20261018_v3.py", "leo900_terminal_evidence_20261018.py", AUDITOR, TESTS],
                "Inspect frozen evaluator450-519 and R2 membership checks; synthetic 48/48 generated,47/1 evaluated witness; no evaluator import or run.",
                "Auxiliary verification corrected. No candidate, split, window rule, gate, statistic, controller or evaluator changed. Actual evaluated counts await terminal artifacts.",
                "Frozen evaluator's skip branch and independent synthetic membership tests agree; the production branch also checks the original paired-layout Counter.",
                "Zero-window IDs are inferred from bound output metadata. Raw eligibility and each unit's exclusion cause are not independently recomputed here.",
                "CORRECTED; REAL TERMINAL CHECK PENDING"),
        finding(2, "R2 test-first reproduction and local verification receipts",
                "Reject the old48-unit assumption without weakening unknown-unit, duplicate-unit, invalid-count or total-count checks.",
                "The first RED attempt had a Windows fixture path-key KeyError, so it was not a valid reproduction of the production assumption.",
                "Retain the erroneous fixture attempt, fix the fixture, retain the genuine RED(final component route/count mismatch), then add seven behavior cases and verify all39 tests with unchanged source hashes.",
                ["terminal_unit_membership_red_20261018_r1.json", "terminal_unit_membership_red_20261018_r2.json",
                 "terminal_unit_membership_targeted_20261018_r1.json", GREEN, TESTS],
                "Recorded targeted7-case and python -B -m unittest -v test_leo900_terminal_evidence_20261018_r2 runs; receipts retain complete output and exact source hashes.",
                "Targeted7/7 and complete39/39 pass. Local full suite204.990s; sources_unchanged=true. Synthetic files only; real_final_labels_read=false.",
                "Genuine RED reproduces the old fixed-count failure. R2 positive subset witness passes while rehashed unknown membership, duplicate statistics units, invalid or empty maps and count contradictions are rejected.",
                "Artificial fixtures do not establish a real final result or rule out every production edge case.",
                "39/39 LOCAL; FAILURE ATTEMPTS PRESERVED"),
        finding(3, "Separate Rack terminal_evidence_support_20261018_r2; first_read_only_audit.json",
                "Deploy a verifier without starting or re-running evaluation or changing the running simulation.",
                "Local success alone cannot establish deployed byte identity or Rack behavior.",
                "Deploy R2 into a new support directory; retain39-test Rack receipt, deployed SHA256 values and first read-only preflight. Prior support directory and all receipts remain intact.",
                [DEPLOYMENT, GREEN, AUDITOR, TESTS, "deploy_leo900_terminal_evidence_20261018_r2.py"],
                "python -B release/f1_audit_20261010/deploy_leo900_terminal_evidence_20261018_r2.py (executed once); remote unittest39 cases then fixed read-only auditor CLI.",
                "Rack39/39 pass, CPU4/nice15, numeric libraries single-threaded; uploaded119285 bytes, tensor transfer0. First preflight verifies156 inputs and reports PENDING_TERMINAL; audit SHA1dccadb3d7de4ea56d9ee56f3579303f40a25d6675376dcff15e7a9ad7861f6e.",
                "Local green source SHA256 values equal transferred files and Rack verification records; first production preflight independently validates registered input anchors. This is execution checking, not an independent historical access witness.",
                "Complete terminal chronology, real predictions, exact gate and fixed statistics still require audit. A process or test PASS is not scientific superiority.",
                "DEPLOYED; F1 OPEN"),
        finding(4, "Registered inference/conversion/representation/projection dependencies; F1 source-only and final-access claims",
                "Candidate selection never reads outer labels; outer labels are evaluated once after the handoff.",
                "A training-label statement cannot describe the whole pipeline: BAT ideal capacity comes from truth/soh; conversion reads final labels/truth after guard; retained windows depend on finite/nonnegative labels; BAT PAVA uses future predictions.",
                "Append the18-source,4-anchor,10-finding static dependency audit. Preserve the frozen method, and require subsequent disclosure of simulation feature origins, label-conditioned membership, known orbit lookup, target-unit first-window input and offline projection.",
                [INFERENCE, "audit_leo900_inference_dependencies_20261018.py", "F1_LEO900_TRAINING_LABEL_FLOW_20261018R1.json"],
                "Recorded audit_leo900_inference_dependencies_20261018.py run; compare registered configs and full function excerpts; pure-function synthetic prefix/baseline witnesses only.",
                "BAT4→8 channels; RWA13→26. Frozen normalization/friction/age scales are source-based; alpha is fixed orbit-ID lookup(LEO9001e-5 each). BAT prefix[.1] becomes[.5,.5] after appending.9 under offline PAVA; RWA running-min alone preserves prefix. RWA574-second bins,30-bin window,stride1.",
                "Registered parent hashes/configurations and actual call/function excerpts cross-check the static dependency paths. Two registered projection implementations plus synthetic prefix witnesses agree. Hash copies are not independent historic no-access evidence.",
                "This is not a full-program information-flow proof, a validated real-sensor deployment, or an executed strictly online BAT experiment. Runtime binding and actual effect remain to be checked; historic outer/LEO800 development influence stays admitted.",
                "DEPENDENCIES DOCUMENTED; F1 OPEN"),
        finding(5, "2026-10-17T20:38:36Z generation/controller metadata observation; overall goal and manuscript freeze",
                "Existing normal simulation exit→seal→freeze→single evaluate→fixed statistics chain.",
                "Partial generation and a waiting controller do not satisfy the new untouched-final-test requirement.",
                "Append point-in-time read-only observation and maintain the current F1 OPEN disposition; preserve the running chain and all earlier records.",
                [PREVIOUS, GENERATION, CONTINUATION, "F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json",
                 "F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json"],
                "python -B release/f1_audit_20261010/capture_leo900_metadata_20261018.py; python -B release/f1_audit_20261010/capture_leo900_continuation_20261018.py (read-only observation).",
                "BAT23/48,RWA0/48; four MATLAB workers near99.7%CPU; controllerPID616411 waiting, two valid chained events, stderr empty; final guard/terminal absent at this observation. F1 OPEN, goal active, manuscript/F2-F10 substantive edits frozen.",
                "Filename/size/time metadata, ps-/proc-process evidence, and independently hashed controller event records agree at observation time; all are observations from the same host.",
                "No MAT values or labels were decoded. No completion time or future outcome is inferred. After final results, the candidate cannot be retuned and re-confirmed on the same final set.",
                "GENERATION RUNNING; GOAL ACTIVE"),
    ]
    refs(PREVIOUS)
    records[Path(__file__).resolve().relative_to(ROOT).as_posix()] = sha(Path(__file__))
    document = {
        "schema": "brphm-f1-additive-pre-final-evidence-r7", "created_utc": now,
        "status": "F1 OPEN", "f1_closed": False, "goal_status": "active",
        "scientific_success_claimed": False,
        "manuscript_and_f2_f10_substantive_edits_frozen": True,
        "previous_r6_sha256": EXPECTED[PREVIOUS],
        "review_report": {"path": str(REVIEW), "sha256": REVIEW_SHA, "lines": "19-25"},
        "artifact_sha256": dict(sorted(records.items())), "findings": findings,
        "new_support_directory": deployed["support"],
        "first_read_only_audit": deployed["read_only_audit"],
        "protected_boundaries": {
            "BRPHM-preview": "no access or modification", "ModelScope": "read-only; not accessed here",
            "IEEE": "no upload/submission/email/contact", "running_simulation": "no stop/restart/copy/configuration mutation"},
        "evidence_limit": "Local clocks/hash chains and external availability observations have distinct limits; no global historical non-access or scientific success is asserted.",
        "next_required": [
            "Let the existing simulation/controller chain finish without restart or duplicate evaluation",
            "Run the R2 auditor to a fresh output after the complete controller terminal is present",
            "Check actual generated/evaluated/zero-window membership, freeze/access chronology, exact gate and fixed statistics",
            "Assess physical-unit effect magnitude and uncertainty honestly, then decide F1",
            "Only after F1 closure resume substantive F2-F10/manuscript work; overall goal remains active until all findings and deliverables are handled"],
    }
    for row in findings:
        assert all(row.get(key) for key in REQUIRED), row["id"]
        assert all(key in records for key in row["evidence"])
    for key, expected in records.items():
        assert sha(ROOT / key) == expected, key
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    labels = dict(zip(REQUIRED, ("位置", "原文", "问题", "修改", "证据", "来源", "日期", "哈希", "命令", "结果", "交叉验证", "置信度", "剩余风险", "状态")))
    lines = ["# F1 LEO900 追加证据台账 R7", "", f"记录时间：{now}", "",
             "**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**", "",
             "本记录只追加单位计数核验修复、测试/部署收据、输入依赖审计和进度观察。旧代码、失败收据、预最终发布包及运行任务全部保留。", ""]
    for row in findings:
        lines.extend([f"## {row['id']}", ""])
        for key in REQUIRED:
            value = row[key]
            if isinstance(value, list):
                value = "; ".join(value)
            lines.extend([f"- **{labels[key]}**：{value}"])
        lines.append("")
    lines.extend(["## SHA256", "", "| 文件 | SHA256 |", "|---|---|"])
    lines.extend(f"| `{key}` | `{value}` |" for key, value in sorted(records.items()))
    lines.extend(["", "## 后续要求", ""])
    lines.extend(f"{i}. {value}" for i, value in enumerate(document["next_required"], 1))
    with markdown.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print(json.dumps({"output": str(output), "sha256": sha(output), "markdown": str(markdown),
                      "markdown_sha256": sha(markdown), "findings": len(findings),
                      "bound_artifacts": len(records), "status": document["status"]}))


if __name__ == "__main__":
    main()
