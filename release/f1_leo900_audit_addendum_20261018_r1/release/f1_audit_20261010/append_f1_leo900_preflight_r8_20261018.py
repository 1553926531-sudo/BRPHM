"""Append arithmetic-verification evidence; never overwrite earlier evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEW = Path(r'C:\Users\Administrator\Documents\Codex\2026-10-01\ni-d\outputs\IEEE_Review_Report_English.md')
GREEN = 'statistics_numerical_audit_local_20261018_r3.json'
DEPLOY = 'leo900_statistics_numerical_audit_deployment_20261017T205500Z.json'
GENERATED = 'leo900_generation_metadata_20261017T205243Z.json'
OBSERVED = 'leo900_continuation_observation_20261017T205244Z.json'
NUMERICAL = 'leo900_statistics_numerical_audit_20261018.py'
TEST = 'test_leo900_statistics_numerical_audit_20261018.py'
PREVIOUS = 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R7.json'
FIELDS = ('location', 'original', 'problem', 'modification', 'evidence', 'source',
          'date', 'hash', 'command', 'result', 'cross_validation', 'confidence', 'remaining_risk', 'status')
EXPECTED = {
    PREVIOUS: '803a221e053008077d18d69a8ede52960d5b8de9c4e42dae9bcc2ef476900b2b',
    GREEN: 'da952e4a4c976e7559f3275d7ef570c60720c0e5af30e154392ebb89de4e3e1d',
    DEPLOY: 'bda4a63b1350420e76fdc929633fbde87654499a07dfab0a8020da1ab11bb443',
    GENERATED: 'ca63432c0fb6795264ae6f8b01e006020299b4bc4ea05eb4f59c21cbedb7d51a',
    OBSERVED: '5df42319d954718ad76775cbb0fc420a421aaf3eda51bb880bb53a79b7512326',
    NUMERICAL: '105618a87df69fd750c70f3388e93c70af9d33ec46e60cfe73677dd8bc55f179',
    TEST: 'c8bfd63d3f93425ca6756900019f11509ffbf5c116146a980b9a03c1852c40b3',
    'leo900_terminal_evidence_20261018_r2.py': '3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0',
    'f1_lossless_gate_statistics_20261018.py': 'adbd7ee1729b919fe0a5300105c78ef70689f38798ee6b2eae8b853a01e1741c',
    'statistics_numerical_audit_red_20261018_r1.json': '410b6bb34dafd8039efd2dcf31ea2852124eb6c2c7bf549113a2f84ad5b1360b',
    'statistics_numerical_audit_local_20261018_r1.json': 'eb42b406dfb04977dbd4d0c8eaf7c0ede75728273f1fcf32f68f9d9f5e690653',
    'statistics_numerical_audit_local_20261018_r2.json': '4efe49d29b1453e2f5250e624ff8653a5aeaecbf478b9b2890c20f41a81a3ec8',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    output = HERE / 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json'
    markdown = output.with_suffix('.md')
    if output.exists() or markdown.exists():
        raise FileExistsError('R8 already exists; append a new revision')
    review_sha = '9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5'
    assert digest(REVIEW) == review_sha
    for name, value in EXPECTED.items():
        assert digest(HERE / name) == value, name
    green, deployment = load(GREEN), load(DEPLOY)
    assert green['exit_code'] == 0 and green['test_count'] == 16 and green['sources_unchanged']
    assert 'Ran 16 tests in' in green['stderr'] and 'skipped' not in green['stderr']
    for name, expected in green['code_sha256'].items():
        assert digest(HERE / name) == expected
    rack = deployment['verification']
    assert deployment['status'] == rack['status'] == 'PASS'
    assert deployment['ssh_exit_code'] == rack['exit_code'] == 0
    assert rack['test_count'] == 16 and 'Ran 16 tests in' in rack['stderr']
    assert rack['resources']['cpu_affinity'] == [4] and rack['resources']['nice'] == 15
    assert rack['raw_code_and_receipt_bytes_uploaded'] == 170078 and rack['tensor_transfer_bytes'] == 0
    for name in ('real_final_labels_read_by_tests', 'simulation_or_configuration_modified',
                 'controller_or_evaluator_invoked', 'candidate_or_route_modified'):
        assert rack[name] is False
    for row in rack['deployed_files']:
        assert row['sha256'] == digest(HERE / Path(row['path']).name)
    audit = deployment['read_only_audit']['report']
    assert audit['status'] == 'PENDING_TERMINAL' and audit['registered_inputs_verified'] == 156
    assert audit['bootstrap_arrays_decoded'] is False and audit['final_truth_or_prediction_arrays_decoded'] is False
    assert audit['f1_closed'] is False and audit['scientific_success_claimed'] is False
    generated, observed = load(GENERATED), load(OBSERVED)
    assert generated['counts'] == {'bat': 23, 'rwa': 0} and generated['mat_contents_read'] is False
    assert observed['event_chain_valid'] and not observed['documents']['terminal']['exists']
    assert not observed['documents']['guard']['exists']
    assert [r['document']['event_type'] for r in observed['events']] == ['controller_started', 'preflight_state']
    assert load('statistics_numerical_audit_local_20261018_r2.json')['exit_code'] == 1
    frozen = {
        'research/rul_space_paper_20261001/en/main.tex': '4e1c2c1b3f1fedbb902af7d1a3415e8730d39d2702fbf5ad921a0ae6d522665b',
        'research/rul_space_paper_20261001/en/main.pdf': '468338bb904734cd49649680e37b8ce447a447e46e45e7083a5b3bfa13460750',
        'release/f1_leo900_pre_final_commitment_20261018_r1/SHA256_MANIFEST.json': '7a489927d3cb6001fff91b7b9af77d9da0468f6721a053fa90be8d8025ca9490',
    }
    for path, value in frozen.items():
        assert digest(ROOT / path) == value, path

    now = datetime.now(timezone.utc).isoformat()
    records = {}

    def refs(*names):
        keys = []
        for name in names:
            path = HERE / name
            assert path.is_file() and not path.is_symlink()
            key = path.relative_to(ROOT).as_posix()
            records[key] = digest(path)
            keys.append(key)
        return keys

    def finding(i, location, original, problem, modification, names, command, result, cross, risk, status):
        return dict(id=f'F1-R8-{i:02d}', finding='F1', location=location, original=original,
            problem=problem, modification=modification, evidence=refs(*names),
            source='Review F1, registered statistical analysis, independent arithmetic code, synthetic witnesses and byte-bound execution receipts; source independence is qualified below.',
            date=now, hash='SHA256 for every cited artifact is listed in artifact_sha256; review hash is separately bound.',
            command=command, result=result, cross_validation=cross,
            confidence='High for these arithmetic/test/deployment observations; does not establish scientific superiority or historic non-access.',
            remaining_risk=risk, status=status)

    findings = [
        finding(1, 'R2 terminal auditor versus registered unit-cluster statistical analysis',
            'Review F1 requires a reconstructable freeze/access/result chain; full-precision statistical evidence must retain its numerical meaning.',
            'R2 validates structure, membership, point-metric consistency and hash edges, but does not recompute bootstrap draws, interval endpoints, SD, paired p-values or Holm. A plausible rehashed interval could therefore pass.',
            'Add a separate read-only numerical verifier with count-weighted bootstrap arithmetic, manual linear percentile interpolation, compensated SD sums, independently ranked signed-rank tests and explicit sign enumeration/normal tails, then Holm. Require complete R2 terminal verification first.',
            [NUMERICAL, TEST, 'leo900_terminal_evidence_20261018_r2.py', 'f1_lossless_gate_statistics_20261018.py', 'F1_LEO900_STATISTICAL_ANALYSIS_PROTOCOL_20261018R1.json'],
            'python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018; inspect registered producer and independent verifier arithmetic.',
            'Prepared verification covers 160000 draws, 16 intervals, 8 SD values and 4 paired tests per complete report. No frozen analysis or gate is changed; alternate arithmetic allows only 64 ULP at the underlying error scale. This allowance is never used for the 1e-12 gate.',
            'Registered indexed-summary reduction and independent count-matrix reduction agree on artificial inputs. Hand-derived unequal-window distributions and exact tied-rank p=.625 provide additional numerical oracles. The full-chain rehashed false interval passes R2 but is rejected by the numerical verifier.',
            'Saved sufficient summaries remain an input assumption; this verifier does not independently derive their errors from raw labels/predictions. Same NumPy RNG contract, same dataset and same frozen design; not independent data replication.',
            'NUMERICAL VERIFIER PREPARED; REAL FINAL NUMBERS AWAIT TERMINAL'),
        finding(2, 'Local RED/GREEN records and complete artificial production-path witnesses',
            'A prior 14-test pass cannot substantiate two later-added production-path tests.',
            'The first 16-test run failed twice before reaching numerical checks: Windows path keys used backslashes while the new fixture looked up a slash-joined string. This was a test-fixture error, not a model or final-data result.',
            'Retain initial missing-implementation RED, 14-test GREEN, failed 16-test receipt and current 16-test GREEN. Build the fixture layout key with the same Path operation used by the fixture. MAT/PT/prediction files remain undecodable fake bytes.',
            ['statistics_numerical_audit_red_20261018_r1.json', 'statistics_numerical_audit_local_20261018_r1.json', 'statistics_numerical_audit_local_20261018_r2.json', GREEN, TEST],
            'Recorded python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018 with numeric libraries limited to one thread.',
            'Current suite 16/16 passes with source hashes unchanged. It checks altered intervals, SD, p-values, Holm, draws, draw ordering, seeds, membership, NaN, one-unit/zero-difference cases, pending early exit and full production-shaped terminal input. Complete fixture remains byte-for-byte unchanged.',
            'The registered producer supplies the artificial comparison report; independently hand-checked distribution/rank witnesses avoid relying on that producer alone. Local hashes reconcile with Rack input hashes.',
            'Synthetic tests do not prove all possible edge cases or actual final performance. The failed Windows fixture attempt is not counted as a genuine missing-behavior RED.',
            '16/16 LOCAL; ALL FAILED ATTEMPTS RETAINED'),
        finding(3, 'New Rack statistics_numerical_audit_support_20261018_r1 directory',
            'Preserve the simulation, existing controller and one-shot final evaluation.',
            'A local arithmetic pass alone does not establish deployed byte identity or Rack behavior.',
            'Deploy only the seven small code/receipt inputs into a new exclusive support directory; run 16 artificial tests on CPU4/nice15 with single-threaded numerical libraries, then one fixed read-only preflight.',
            [DEPLOY, GREEN, NUMERICAL, TEST, 'deploy_leo900_statistics_numerical_audit_20261018_r1.py'],
            'python -B release/f1_audit_20261010/deploy_leo900_statistics_numerical_audit_20261018_r1.py (once).',
            'Rack 16/16 passes. Raw code/receipt transfer 170078 bytes; tensor transfer 0. Preflight validates 156 registered inputs and returns PENDING_TERMINAL; no bootstrap, truth or prediction arrays decoded. Preflight SHA256 3fa55b0e155a9cd20307442ebfba7871a475b862e50dd8181541c667065db9b8.',
            'Transferred hashes match current local GREEN hashes and deployed-file records. Windows/Python3.12 and Linux/Python3.10 executions agree for synthetic arithmetic; this is portability checking, not independent research replication.',
            'The complete real chronology and numerical results must still be audited after the existing chain finishes. Do not redeploy over this directory or invoke evaluator again.',
            'DEPLOYED; REAL TERMINAL VERIFICATION PENDING'),
        finding(4, 'Current F1 disposition, active goal, manuscript and original pre-final commitment',
            'Review F1: if outer outcomes affected revision, retain them as development/diagnostic evidence and supply a genuinely untouched final test.',
            'Earlier F1-closed/accepted wording, including the active goal objective wording about 15/15 checks, is obsolete. Tests and preflight cannot establish the final scientific result.',
            'Retain the prior records, explicitly maintain F1 OPEN and the manuscript/F2-F10 substantive freeze, and preserve the exact original pre-final package. Historic outer counts 5,4,3,1,3,0 and LEO800 feedback remain admitted development evidence.',
            [PREVIOUS, 'F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json', 'leo900_external_commitment_rest_publication_20261017T193909Z.json'],
            'Hash frozen main.tex, main.pdf and pre-final SHA256_MANIFEST.json; read current active-goal status without closing it.',
            'Frozen manuscript and original pre-final manifest hashes remain identical. F1 OPEN; goal active. The new numerical verifier is an audit addition, not a replacement candidate or a revised preregistration.',
            'Original review quotations, retained development chronology and separately registered LEO900 chain resolve the intended evidence roles. Server publication observations establish availability by response time, not immutable notarization or historical non-access.',
            'F1 acceptance still requires actual final freeze/access chronology, original single evaluation, exact gate, fixed uncertainty and honest effect-size review. F2-F10 and all final deliverables remain required before goal completion.',
            'F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE'),
        finding(5, 'Read-only LEO900 observations at 2026-10-17T20:52:43Z/44Z',
            'Normal simulation exit then seal, freeze, single evaluation and fixed statistics are handled by the existing controller.',
            'Partial generation is not a finished final test, and no completion time follows from a snapshot.',
            'Append filename/count/size/time and controller/process observations without decoding MAT/PT or modifying the running chain.',
            [GENERATED, OBSERVED],
            'python -B release/f1_audit_20261010/capture_leo900_metadata_20261018.py; python -B release/f1_audit_20261010/capture_leo900_continuation_20261018.py.',
            'BAT23/48, RWA0/48; four MATLAB workers near99.7-99.8% CPU; controller PID616411 waiting. Two hash-linked controller events validate; stderr empty. No final guard or terminal at this observation.',
            'Output-directory metadata, OS ps/proc observations and controller event records agree at the sampled time. These channels share the same host and are not independent historical access attestations.',
            'Status can advance after this observation. Preserve the running simulation and controller; after final visibility, no candidate revision can be confirmed again on this final set.',
            'GENERATION RUNNING; EXISTING CHAIN PRESERVED'),
    ]
    refs('append_f1_leo900_preflight_r8_20261018.py')
    document = dict(schema='brphm-f1-additive-pre-final-evidence-r8', created_utc=now,
        status='F1 OPEN', f1_closed=False, goal_status='active', scientific_success_claimed=False,
        manuscript_and_f2_f10_substantive_edits_frozen=True, previous_r7_sha256=EXPECTED[PREVIOUS],
        review_report={'path':str(REVIEW),'sha256':review_sha,'lines':'19-25'},
        findings=findings, artifact_sha256=dict(sorted(records.items())), frozen_artifact_sha256=frozen,
        new_support_directory=deployment['support'], first_read_only_numerical_audit=deployment['read_only_audit'],
        protected_boundaries={'BRPHM-preview':'no access or modification','ModelScope':'read-only; not accessed here',
            'IEEE':'no upload/submission/email/contact','simulation':'no stop/restart/copy/configuration modification',
            'controller':'no duplicate start/freeze/evaluate'},
        next_required=['Preserve the existing simulation/controller chain through its normal terminal.',
            'After complete terminal, run the deployed R2 and numerical auditors to new output names; never repeat evaluation.',
            'Audit generated96-unit partition versus positive-window evaluated subset, freeze/access chronology, original full-precision gate and fixed statistics.',
            'Review physical-unit effect sizes and uncertainty honestly before deciding F1 acceptance.',
            'After F1 closure, resume F2-F10 and all final deliverables. Do not close goal for auxiliary tests or process status.'])
    for row in findings:
        assert all(row.get(key) for key in FIELDS)
        assert all(key in records for key in row['evidence'])
    for path, expected in records.items():
        assert digest(ROOT / path) == expected
    with output.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(document,handle,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False);handle.write('\n')
    labels = ('位置','原文','问题','修改','证据','来源','日期','哈希','命令','结果','交叉验证','置信度','剩余风险','状态')
    lines = ['# F1 LEO900 追加证据台账 R8','',f'记录时间：{now}','','**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**','',
        '本记录追加独立统计数值核验、失败/通过收据、独立支持目录部署和运行观察。它不改变冻结候选、统计设计、门禁或原始预最终承诺。','']
    for row in findings:
        lines.extend([f"## {row['id']}",''])
        for key,label in zip(FIELDS,labels):
            value = '; '.join(row[key]) if isinstance(row[key],list) else row[key]
            lines.append(f'- **{label}**：{value}')
        lines.append('')
    lines.extend(['## SHA256','','| 文件 | SHA256 |','|---|---|'])
    lines.extend(f'| `{key}` | `{value}` |' for key,value in sorted(records.items()))
    lines.extend(['','## 后续要求',''])
    lines.extend(f'{i}. {value}' for i,value in enumerate(document['next_required'],1))
    with markdown.open('x',encoding='utf-8',newline='\n') as handle:
        handle.write('\n'.join(lines)+'\n')
    print(json.dumps({'json':str(output),'sha256':digest(output),'markdown':str(markdown),
        'markdown_sha256':digest(markdown),'findings':len(findings),'bound_artifacts':len(records),'status':'F1 OPEN'}))


if __name__ == '__main__':
    main()
