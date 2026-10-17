"""Append the audit dispatch evidence without changing any existing artifact."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEW = Path(r'C:\Users\Administrator\Documents\Codex\2026-10-01\ni-d\outputs\IEEE_Review_Report_English.md')
FIELDS = ('location', 'original', 'problem', 'modification', 'evidence', 'source',
          'date', 'hash', 'command', 'result', 'cross_validation', 'confidence', 'remaining_risk', 'status')
PREVIOUS = 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json'
RED = 'terminal_audit_watcher_red_20261018_r1.json'
GREEN = 'terminal_audit_watcher_local_20261018_r1.json'
DEPLOY = 'leo900_terminal_audit_watcher_deployment_20261017T212856Z.json'
LAUNCH = 'leo900_terminal_audit_watcher_launch_20261017T213248Z.json'
WATCH = 'leo900_terminal_audit_watcher_observation_20261017T213616Z.json'
GEN = 'leo900_generation_metadata_20261017T213514Z.json'
CONTROL = 'leo900_continuation_observation_20261017T213514Z.json'
CODE = 'leo900_terminal_audit_watcher_20261018_r1.py'
TEST = 'test_leo900_terminal_audit_watcher_20261018_r1.py'
PUBLISH = 'leo900_audit_addendum_publication_20261017T211740Z.json'
EXPECTED = {
    PREVIOUS: '6de13be7865f3b603933ccf2aece3d97297d7dd01fe98a61bac0b3ee56695ca1',
    RED: '1fdf49251f0b291823c46029efad4c76b7e3428097fbc518b0f023064b1492bd',
    GREEN: 'bc34f257093d3eda59dda2e6709a36f3aa11f9246c2195cb8fca8b6e70da472d',
    DEPLOY: '7ad1cc4ec56a0289606bd49823448d818b0f6ac26ad241994c99c69b64bf126e',
    LAUNCH: '8411f515e5e9f5dcbb693d6134064d39a9157f4f4e15d2668253bb0de3ad25bc',
    WATCH: 'edff2e885e231784aeb8f503e13149e78477de07b40bbf1eb46e195c16bec51a',
    GEN: '18f0f25a97da224ca598d1c653b6087c9a3152a3becd8a5ffa772c91a4b7a126',
    CONTROL: '4644068193c2fabdcd8ccdb64eb4e7cc9900b0cdf470db7164188824b4889c0a',
    CODE: 'a5f309edd78d0b902ce62a06a0965e7d9ddc67a8328e64ea046d13cf34194fc7',
    TEST: 'cbdb6ec4f4a577f3eea296ec55337a6814fbdf6b5c649b2b3dc05df54c91f393',
    PUBLISH: '256dc278808cb1a4312526a74beb5d8d8ab67cab02592a8584545f76713c285d',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    output = HERE / 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R10.json'
    markdown = output.with_suffix('.md')
    if output.exists() or markdown.exists():
        raise FileExistsError('R10 already exists; append a later revision')
    review_sha = '9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5'
    assert digest(REVIEW) == review_sha
    for name, expected in EXPECTED.items():
        assert digest(HERE / name) == expected, name
    red, green, deployed = load(RED), load(GREEN), load(DEPLOY)
    assert red['exit_code'] == 1 and red['implementation_exists'] is False
    assert 'FAILED (failures=9)' in red['stderr']
    assert green['exit_code'] == 0 and green['test_count'] == 9 and green['sources_unchanged']
    assert green['real_final_data_read'] is False
    for name, expected in green['code_sha256'].items():
        assert digest(HERE / name) == expected
    rack = deployed['verification']
    assert deployed['status'] == rack['status'] == 'PASS'
    assert deployed['ssh_exit_code'] == rack['exit_code'] == 0 and rack['test_count'] == 9
    assert 'Ran 9 tests in 0.500s' in rack['stderr'] and 'skipped' not in rack['stderr']
    assert rack['resources']['cpu_affinity'] == [4] and rack['resources']['nice'] == 15
    assert rack['resources']['numeric_threads'] == 1
    assert rack['raw_code_and_receipt_bytes_uploaded'] == 21256 and rack['tensor_transfer_bytes'] == 0
    for key in ('evaluator_invoked', 'real_final_data_read', 'simulation_or_controller_modified'):
        assert rack[key] is False
    for row in rack['deployed_files']:
        assert digest(HERE / Path(row['path']).name) == row['sha256']
    assert digest(HERE / 'deploy_leo900_terminal_audit_watcher_20261018_r1.py') == deployed['deployer_sha256']
    launch, watch = load(LAUNCH), load(WATCH)
    assert launch['ssh_exit_code'] == 0 and launch['deployment_receipt_sha256'] == EXPECTED[DEPLOY]
    assert digest(HERE / 'start_leo900_terminal_audit_watcher_20261018_r1.py') == launch['launcher_sha256']
    assert launch['pid_record']['pid'] == watch['pid_record']['document']['pid'] == 792920
    assert watch['watcher_started']['exists'] and not watch['terminal']['exists']
    assert watch['stage_records'] == [] and watch['stderr']['size'] == 0
    assert watch['watcher_process']['cpu_affinity'] == [4] and watch['watcher_process']['nice'] == 15
    assert watch['watcher_process']['status']['Threads'] == '1'
    assert watch['remote_writes'] is False and watch['mat_or_tensor_decoded'] is False
    assert watch['evaluator_invoked'] is False
    generated, control = load(GEN), load(CONTROL)
    assert generated['counts'] == {'bat': 26, 'rwa': 0}
    assert generated['logs']['matlab_stderr.log']['size'] == 0
    assert generated['mat_contents_read'] is False and generated['remote_writes'] is False
    assert control['event_chain_valid'] and not control['documents']['terminal']['exists']
    assert not control['documents']['guard']['exists']
    assert [r['document']['event_type'] for r in control['events']] == ['controller_started', 'preflight_state']
    frozen = {
        'research/rul_space_paper_20261001/en/main.tex': '4e1c2c1b3f1fedbb902af7d1a3415e8730d39d2702fbf5ad921a0ae6d522665b',
        'research/rul_space_paper_20261001/en/main.pdf': '468338bb904734cd49649680e37b8ce447a447e46e45e7083a5b3bfa13460750',
        'release/f1_leo900_pre_final_commitment_20261018_r1/SHA256_MANIFEST.json': '7a489927d3cb6001fff91b7b9af77d9da0468f6721a053fa90be8d8025ca9490',
        'release/f1_leo900_audit_addendum_20261018_r2/SHA256_MANIFEST.json': '204714677d70194eb42dc7f6bc7d856270e5ce9e2681f929d9f8308890aeaf9e',
        'release/f1_audit_20261010/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json': 'a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a',
        'release/f1_audit_20261010/F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json': '50e43a0e342799976841da57116bacf09502855f27b116077826bed5b96de8f2',
        'release/f1_audit_20261010/F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json': '754326c717669f23f82d8cf044d87333772f21fe82a8b389a169389771506da1',
    }
    for name, expected in frozen.items():
        assert digest(ROOT / name) == expected, name
    now, records = datetime.now(timezone.utc).isoformat(), {}

    def refs(names):
        result = []
        for name in names:
            path = HERE / name
            assert path.is_file() and not path.is_symlink()
            key = path.relative_to(ROOT).as_posix()
            records[key] = digest(path)
            result.append(key)
        return result

    def finding(index, location, original, problem, modification, names, command, result, cross, risk, status):
        return dict(id=f'F1-R10-{index:02d}', finding='F1', location=location, original=original,
            problem=problem, modification=modification, evidence=refs(names),
            source='Review F1; recorded local/Rack artificial tests; fixed auditor code; hash-bound deployment/launch receipts and read-only OS/controller observations. Source independence is qualified below.',
            date=now, hash='Full SHA256 values are in artifact_sha256 and frozen_artifact_sha256; the review is separately bound.',
            command=command, result=result, cross_validation=cross,
            confidence='High for the stated recorded bytes and observations; final scientific validity remains subject to actual terminal review.',
            remaining_risk=risk, status=status)

    findings = [
        finding(1, 'Existing controller terminal -> three existing independent auditors',
            'R9 required terminal provenance, prediction-summary and numerical-statistics verification after completed execution.',
            'Prepared auditors alone did not guarantee operational dispatch after a long simulation and evaluation.',
            'A separate audit-only watcher waits for the existing controller to flush/fsync and make its successful terminal read-only, then dispatches chain, prediction and statistics auditors once. It does not launch simulation, training, freeze, evaluate or the production statistics program.',
            [CODE, TEST, DEPLOY, LAUNCH, PREVIOUS],
            'Deployed fixed --run --registration-sha256 command is recorded in launch_intent; do not execute it again.',
            'The watcher accepts EVALUATION_AND_STATISTICS_COMPLETED regardless of the sign of the deterministic gate. It preserves exclusive outputs and stops on an audit error, pending report, nonzero exit or input/controller drift. Its successful terminal remains f1_closed=false and scientific_success_claimed=false.',
            'Static allowed command list matches deployment registration. Synthetic child processes exercise ordering, one-time dispatch and failure handling. These checks are separate from the research data and do not establish model performance.',
            'The real terminal and three audit reports remain pending at this observation. The watcher cannot establish historical non-access or scientific success.',
            'AUTOMATIC TERMINAL AUDIT DISPATCH REGISTERED; FINAL REVIEW PENDING'),
        finding(2, 'Watcher tests and Rack deployment identity',
            'Operational changes must preserve negative evidence and be verified on the actual execution host.',
            'A local-only test result cannot establish deployed file identity or actual Rack execution behavior.',
            'Retain the genuine missing-implementation RED, local GREEN and Rack receipt; verify all source/deployment hashes without rerunning research or changing existing files.',
            [RED, GREEN, DEPLOY, CODE, TEST, 'deploy_leo900_terminal_audit_watcher_20261018_r1.py'],
            'Recorded python -B -m unittest -v test_leo900_terminal_audit_watcher_20261018_r1; receipt and source SHA256 rechecked by this append command.',
            'Recorded RED:9 failures with implementation missing. Recorded GREEN:9/9 in4.547s on Windows/Python3.12; Rack:9/9 in0.500s on Linux/Python3.10.21256 code/receipt bytes uploaded,0 tensor bytes. Tests used artificial data and temporary child processes; production evaluator and real final data were not used.',
            'Local source hashes equal deployed-file hashes; both operating systems ran the same nine cases. Tests include duplicate start, existing-output preservation, pending report, drift and child-process failure. This is implementation corroboration, not independent research replication.',
            'Artificial cases do not exhaust all possible runtime failures or validate the real final result.',
            'RECORDED LOCAL/RACK9/9; RED RETAINED; BYTE IDENTITIES RECHECKED'),
        finding(3, 'Single watcher launch and process observation',
            'The launch receipt intentionally said LAUNCHED_UNCONFIRMED and cannot alone prove continued execution.',
            'A successful SSH launch could precede immediate child exit; current process/start evidence is needed.',
            'Preserve the original launch receipt and append a separate read-only observation of watcher_started, PID, command, affinity, memory, stage records and stderr.',
            [LAUNCH, WATCH, 'start_leo900_terminal_audit_watcher_20261018_r1.py'],
            'Read-only SSH observation at2026-10-17T21:36:16.582574Z; capture code and its hash are embedded in the observation.',
            'PID792920 matches launch and live command; watcher_started exists. CPU4,nice15,one thread,RSS17192kB,sleeping; stderr0bytes. No audit stage has started and no watcher terminal is present. Registration SHA256 ee50eff95fa3232f5b7c0133a5c328a57c560a8cc0344ac7bd057415c119dbf3 remains bound.',
            'Launch/PID records, watcher-start artifact and live OS process agree at observation time. They share one Rack host; no external process attestation is claimed.',
            'Liveness is a point-in-time observation and does not promise future completion. Do not duplicate the watcher or manually write its registered report paths.',
            'ONE WATCHER OBSERVED WAITING; NO DUPLICATE DISPATCH'),
        finding(4, 'F1 disposition and preserved scientific/manuscript state',
            'Review F1 requires admitting historical outer reuse and a frozen candidate evaluated once on an untouched final test.',
            'Auxiliary test passes, audit publication and normal process activity cannot establish F1 acceptance. The retained goal objective contains obsolete15/15-closed wording.',
            'Keep F1 OPEN and goal active. Preserve the running simulation, existing controller, registered candidate/gate/statistics and frozen manuscript. Historical outer counts5,4,3,1,3,0 and LEO800 feedback remain development/diagnostic evidence.',
            [GEN, CONTROL, PREVIOUS, PUBLISH, 'F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json',
             'F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json', 'F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json'],
            'Read-only metadata/controller capture at2026-10-17T21:35:14Z; rehash fixed manuscript, protocols and published manifests.',
            'BAT26/48,RWA0/48; four MATLAB workers near99.7%CPU,stderr0bytes. Controller616411 is waiting; its two-event hash chain is valid, and final label guard is not present. Frozen hashes agree. R9 audit package was published/read back in BRPHM commit523619aed9dfb8f5622332acfe26363ffd682b2c.',
            'File metadata, process status and controller events corroborate execution state but share one host. GitHub publication corroborates published bytes by server response time; it is not immutable notarization or proof of historical non-access.',
            'Actual generated membership, positive-window evaluation subset, single-access chronology, original-precision gate, physical effect and uncertainty still require terminal review. One final orbit and ensemble members cannot establish independent multi-orbit replication.',
            'F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE'),
    ]
    refs([Path(__file__).name])
    document = dict(schema='brphm-f1-additive-pre-final-evidence-r10', created_utc=now,
        status='F1 OPEN', f1_closed=False, scientific_success_claimed=False, goal_status='active',
        manuscript_and_f2_f10_substantive_edits_frozen=True, previous_r9_sha256=EXPECTED[PREVIOUS],
        review_report={'path':str(REVIEW),'sha256':review_sha,'lines':'19-25'}, findings=findings,
        artifact_sha256=dict(sorted(records.items())), frozen_artifact_sha256=frozen,
        watcher_registration=deployed['registration_record'], watcher_pid=792920,
        protected_boundaries={'BRPHM':'read/write authorized', 'BRPHM-preview':'no access or modification',
            'ModelScope':'read-only; not accessed here', 'IEEE':'no upload/submission/email/contact',
            'simulation':'no stop/restart/copy/configuration change',
            'controller_and_watcher':'preserve existing processes; no duplicate freeze/evaluate/audit dispatch'},
        next_required=[
            'Preserve normal simulation/controller execution and the existing automatic audit watcher; observe metadata at reasonable intervals.',
            'After complete terminal, read controller_terminal, watcher_terminal and its three registered reports; do not manually start duplicate audits.',
            'If an audit fails, preserve all outputs and resolve the audit issue without changing the candidate or repeating evaluation.',
            'Review96 generated members versus positive-window subset, access/freeze chronology, original gate, physical effects and registered uncertainty before deciding F1.',
            'Only after actual F1 closure resume substantive F2-F10 and all final deliverables; no auxiliary check completes the goal.'])
    for row in findings:
        assert all(row.get(key) for key in FIELDS)
        assert all(key in records for key in row['evidence'])
    for name, expected in {**records, **frozen}.items():
        assert digest(ROOT / name) == expected
    with output.open('x', encoding='utf-8', newline='\n') as h:
        json.dump(document, h, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        h.write('\n')
    labels = ('位置','原文','问题','修改','证据','来源','日期','哈希','命令','结果','交叉验证','置信度','剩余风险','状态')
    lines = ['# F1 LEO900 追加证据台账 R10', '', f'记录时间：{now}', '',
        '**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**', '',
        '记录已经启动的终态核验衔接任务、既有测试及部署证据和只读进度。辅助核验不能替代真实最终结果审查。', '']
    for row in findings:
        lines.extend([f"## {row['id']}", ''])
        for key, label in zip(FIELDS, labels):
            value = '; '.join(row[key]) if isinstance(row[key], list) else row[key]
            lines.append(f'- **{label}**：{value}')
        lines.append('')
    lines.extend(['## SHA256', '', '| 文件 | SHA256 |', '|---|---|'])
    lines.extend(f'| `{name}` | `{value}` |' for name, value in sorted(records.items()))
    lines.extend(['', '## 后续要求', ''])
    lines.extend(f'{index}. {value}' for index, value in enumerate(document['next_required'], 1))
    with markdown.open('x', encoding='utf-8', newline='\n') as h:
        h.write('\n'.join(lines) + '\n')
    print(json.dumps({'json':str(output), 'sha256':digest(output), 'markdown':str(markdown),
        'markdown_sha256':digest(markdown), 'findings':len(findings), 'bound_artifacts':len(records),
        'status':'F1 OPEN', 'goal_status':'active'}))


if __name__ == '__main__':
    main()
