"""Append prediction-summary verification evidence; preserve all prior records."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REVIEW = Path(r'C:\Users\Administrator\Documents\Codex\2026-10-01\ni-d\outputs\IEEE_Review_Report_English.md')
PREVIOUS = 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json'
GREEN = 'prediction_summary_audit_local_20261018_r2.json'
DEPLOY = 'leo900_prediction_summary_audit_deployment_20261017T211424Z.json'
GENERATED = 'leo900_generation_metadata_20261017T211439Z.json'
OBSERVED = 'leo900_continuation_observation_20261017T211439Z.json'
AUDITOR = 'leo900_prediction_summary_audit_20261018.py'
TEST = 'test_leo900_prediction_summary_audit_20261018.py'
DEPLOYER = 'deploy_leo900_prediction_summary_audit_20261018_r1.py'
PUBLICATION = 'leo900_audit_addendum_publication_20261017T210327Z.json'
FIELDS = ('location', 'original', 'problem', 'modification', 'evidence', 'source',
          'date', 'hash', 'command', 'result', 'cross_validation', 'confidence', 'remaining_risk', 'status')
EXPECTED = {
    PREVIOUS: '7ace7afcbb8756f681134975fc999865745086d8b62db751977c73a138de2f29',
    GREEN: 'e541a2c36f011dde2ebd5d354bd589873311edc569b4ca1f9eb11c224e797038',
    DEPLOY: '1e79319f2809660973b5b8549afda1b7bc7fe3055624bbf6b3d3ad9bd6cee3d8',
    GENERATED: '2deb91e8032abf7884f5e353a7381265fbd9a18f3a22e07294833e289c987c27',
    OBSERVED: '6dc96dbfedbbb5ca5946ad15ccc3b97733755b660b22f94a5c5d8a3afe769ace',
    AUDITOR: '8c2fbabdcedf8a3263a951baa3114415687a970446666f1e87e9b3af09450c2c',
    TEST: '7d195a43649c5c615f223b395c8ed501d55988eccd3d2c2b5d9edb0759b68411',
    DEPLOYER: 'a06aabdb79202c90ba579713a01eba27604c01e8a12104e1bf5b70c3df76288c',
    'prediction_summary_audit_red_20261018_r1.json': '7ccb2e4218384f16d512f3dc7575c854a5a482ac8c098ea002daa636ee84317d',
    'prediction_summary_audit_local_20261018_r1.json': '0046cea59c053f5fbe4f46ab7693db052c5f6ec4e3e7cca10b524318bbf4b00b',
    PUBLICATION: '887d833e37c1d499180a0eda9459475de54af1186d7baaa4c2b143929c1018a7',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    output = HERE / 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json'
    markdown = output.with_suffix('.md')
    if output.exists() or markdown.exists():
        raise FileExistsError('R9 already exists; append a new revision')
    review_sha = '9d75bf227ae883552af326352f3586bc23b84ebaf4c73d2a7fa4d1a26cfc8be5'
    assert digest(REVIEW) == review_sha
    for name, value in EXPECTED.items():
        assert digest(HERE / name) == value, name
    green, deployed = load(GREEN), load(DEPLOY)
    assert green['exit_code'] == 0 and green['test_count'] == 12 and green['sources_unchanged']
    assert 'Ran 12 tests in' in green['stderr'] and 'skipped' not in green['stderr']
    for name, expected in green['code_sha256'].items():
        assert digest(HERE / name) == expected
    rack = deployed['verification']
    assert deployed['status'] == rack['status'] == 'PASS'
    assert deployed['ssh_exit_code'] == rack['exit_code'] == 0 and rack['test_count'] == 12
    assert 'Ran 12 tests in' in rack['stderr'] and 'skipped' not in rack['stderr']
    assert rack['resources']['cpu_affinity'] == [4] and rack['resources']['nice'] == 15
    assert all(v == '1' for v in rack['resources']['numeric_threads'].values())
    assert rack['raw_code_and_receipt_bytes_uploaded'] == 144218 and rack['tensor_transfer_bytes'] == 0
    for name in ('real_final_labels_read_by_tests', 'simulation_or_configuration_modified',
                 'controller_or_evaluator_invoked', 'candidate_or_route_modified'):
        assert rack[name] is False
    for row in rack['deployed_files']:
        assert row['sha256'] == digest(HERE / Path(row['path']).name)
    preflight = deployed['read_only_audit']['report']
    assert preflight['status'] == 'PENDING_TERMINAL' and preflight['registered_inputs_verified'] == 156
    assert preflight['final_truth_or_prediction_arrays_decoded'] is False and preflight['f1_closed'] is False
    assert load('prediction_summary_audit_local_20261018_r1.json')['exit_code'] == 1
    generated, observed = load(GENERATED), load(OBSERVED)
    assert generated['counts'] == {'bat': 25, 'rwa': 0} and generated['mat_contents_read'] is False
    assert observed['event_chain_valid'] and not observed['documents']['terminal']['exists']
    assert not observed['documents']['guard']['exists']
    assert [row['document']['event_type'] for row in observed['events']] == ['controller_started', 'preflight_state']
    frozen = {
        'research/rul_space_paper_20261001/en/main.tex': '4e1c2c1b3f1fedbb902af7d1a3415e8730d39d2702fbf5ad921a0ae6d522665b',
        'research/rul_space_paper_20261001/en/main.pdf': '468338bb904734cd49649680e37b8ce447a447e46e45e7083a5b3bfa13460750',
        'release/f1_leo900_pre_final_commitment_20261018_r1/SHA256_MANIFEST.json': '7a489927d3cb6001fff91b7b9af77d9da0468f6721a053fa90be8d8025ca9490',
        'release/f1_leo900_audit_addendum_20261018_r1/SHA256_MANIFEST.json': '7101789f22c45000d8d6c5e3476e7e7f40af26125d45b9363afeb4aff1b39b2e',
    }
    for name, expected in frozen.items():
        assert digest(ROOT / name) == expected
    now = datetime.now(timezone.utc).isoformat()
    records = {}

    def refs(names):
        keys = []
        for name in names:
            path = HERE / name
            assert path.is_file() and not path.is_symlink()
            key = path.relative_to(ROOT).as_posix()
            records[key] = digest(path)
            keys.append(key)
        return keys

    def finding(index, location, original, problem, modification, names, command, result, cross, risk, status):
        return dict(id=f'F1-R9-{index:02d}', finding='F1', location=location, original=original,
            problem=problem, modification=modification, evidence=refs(names),
            source='Review F1; saved registered prediction/statistical contracts; independent scalar arithmetic; hand-derived artificial cases; hash-bound local/Rack receipts. Independence is qualified in cross_validation.',
            date=now, hash='Full artifact SHA256 values appear in artifact_sha256; the original review is separately hash-bound.',
            command=command, result=result, cross_validation=cross,
            confidence='High for the stated implementation, synthetic tests, byte identity and observations; no final scientific conclusion follows before complete terminal review.',
            remaining_risk=risk, status=status)

    findings = [
        finding(1, 'Prediction NPZ -> formal metrics and saved unit sufficient summaries',
            'R8 explicitly retained saved sufficient summaries as an input assumption of its independent bootstrap verifier.',
            'Hash-linked internally consistent unit errors may still disagree with the original saved predictions. An independent numerical bootstrap check alone would not detect that upstream contradiction.',
            'Add an independent read-only scalar-error/math.fsum auditor of original single-pass predictions. It first requires R2 complete terminal verification, then checks pooled/unit errors, physical scale, label division dtype, route alpha, float32 blend and constituent descriptions without invoking model, evaluator or statistical producer.',
            [AUDITOR, TEST, 'leo900_terminal_evidence_20261018_r2.py', 'leo900_statistics_numerical_audit_20261018.py', PREVIOUS],
            'python -B -m unittest -v test_leo900_prediction_summary_audit_20261018; after full terminal only, invoke the deployed read-only CLI with a new output name.',
            'Prepared verifier covers projected/candidate-only/control-only pooled RMSE/MAE/bias, unit-macro RMSE, upward fraction, unit/window membership, per-unit SSE/SAE/RMSE/MAE, saved deltas/relative changes and three seed constituent descriptions. Alternative descriptive sums allow64 ULP; the original1e-12 gate remains exact and unchanged.',
            'Interleaved unequal-size units have independently hand-derived physical errors: candidate A SSE16/SAE4 and B SSE56/SAE12, pooled RMSEsqrt(14.4)/MAE3.2; control pooled RMSEsqrt8/MAE2.4. A rehashed contradictory seed metric passes structural binding but is rejected here. These are independent calculations, not independent research data.',
            'Does not independently decode raw MAT/PT, reconstruct label eligibility, or reproduce projection/centering/model predictions. Saved prediction arrays and their row metadata remain inputs. Passing these checks cannot establish population generalization.',
            'PREDICTION-SUMMARY VERIFIER PREPARED; REAL FINAL READ DEFERRED'),
        finding(2, 'Missing-implementation RED, first GREEN attempt and corrected synthetic fixture',
            'Tests must reach the intended arithmetic contract and preserve failed attempts.',
            'The first12-test GREEN attempt had11 passes and1 failure: its label-division fixture changed layout rmax8->3 but left statistics rmax8, so validation correctly stopped at the scale mismatch before testing dtype arithmetic.',
            'Preserve the genuine missing-implementation RED and failed first GREEN receipt. Correct only the artificial fixture statistics rmax to3, then run the full12-test suite with unchanged implementation and source hashes recorded.',
            ['prediction_summary_audit_red_20261018_r1.json', 'prediction_summary_audit_local_20261018_r1.json', GREEN, TEST, AUDITOR],
            'Recorded python -B -m unittest -v test_leo900_prediction_summary_audit_20261018, numerical libraries constrained to one thread.',
            'Local12/12 pass in19.636s, sources_unchanged=true. Tests reject wrong summaries, relabelled rows, wrong physical scale, NaN/shape mismatch, duplicate NPZ members, wrong alpha/blend/dtype and contradictory seed metrics. Pending-terminal witness leaves poisoned predictions unread; complete synthetic production-shaped chain remains byte-identical.',
            'Hand-derived arithmetic provides an oracle separate from the implementation. Synthetic ProductionFixture exercises complete R2 provenance binding before independent scalar checking. No real final data were used by tests.',
            'The corrected fixture failure was not a missing-implementation RED. Tests do not exhaust all possible inputs or validate the actual final scientific result.',
            '12/12 LOCAL; RED AND FAILED ATTEMPT RETAINED'),
        finding(3, 'Rack prediction_summary_audit_support_20261018_r1 deployment',
            'Existing one-shot final execution and simulation must be preserved.',
            'Local passing tests alone do not establish deployed code identity or behavior on Rack.',
            'Deploy six small source/receipt files once to a new exclusive support directory; run only artificial tests and the fixed read-only audit on CPU4/nice15 with one numerical thread.',
            [DEPLOY, DEPLOYER, GREEN, AUDITOR, TEST],
            'python -B release/f1_audit_20261010/deploy_leo900_prediction_summary_audit_20261018_r1.py (already executed once; never repeat over this directory).',
            'Rack12/12 passes.144218 raw code/receipt bytes uploaded;0 tensor bytes. Preflight validates156 registered inputs and defers prediction decoding until complete terminal. Audit SHA256 c1190d3ebd7b87184b102676fc05bd31f50712d883191cb6109b52f9b77c03ac. Candidate, controller and simulation unchanged.',
            'Local GREEN source hashes agree with transfer records and deployed-file hashes. Windows/Python3.12 and Linux/Python3.10 run the same12 artificial cases successfully. This establishes portability of the tested code, not independent model replication.',
            'Real saved prediction/summary agreement remains to be checked after terminal. Do not repeat evaluation or alter the frozen candidate after observing final data.',
            'DEPLOYED; REAL PREDICTION AUDIT AWAITS COMPLETE TERMINAL'),
        finding(4, 'F1 disposition, continuing simulation, frozen manuscript and public audit addendum',
            'Review F1 requires an untouched final test after development used outer feedback; F1 must precede substantive F2-F10/manuscript changes.',
            'Auxiliary tests, public audit publication and normal process activity cannot close F1. Earlier15/15-closed wording in the retained goal objective is obsolete.',
            'Maintain F1 OPEN and goal active, preserve original commitments/manuscript and append this evidence. Historical outer counts5,4,3,1,3,0 and LEO800 remain development/diagnostic evidence. Preserve the running simulation and existing automatic controller.',
            [PREVIOUS, GENERATED, OBSERVED, PUBLICATION, 'F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json'],
            'Read-only metadata/controller captures at2026-10-17T21:14:39Z; SHA256-check main.tex/main.pdf and both existing package manifests.',
            'BAT25/48,RWA0/48 at this observation; four MATLAB workers near99.7%CPU, no MATLAB stderr. Controller616411 waiting, two-event hash chain valid. Frozen file hashes unchanged. Earlier R5-R8 audit addendum published and read back in BRPHM commit b8ad940e5779692f25643cdaa2fac346e4385760.',
            'File metadata, OS process observations and controller event chain agree at capture time but share one host. GitHub readback corroborates the published bytes by server response time; it is neither historical non-access proof nor immutable notarization.',
            'Remaining generated members, seal/freeze/evaluation/statistics chronology, original gate, physical effects and uncertainty require actual terminal audit. One held-out orbit and ensemble constituents cannot establish independent multi-orbit replication.',
            'F1 OPEN; GOAL ACTIVE; SUBSTANTIVE MANUSCRIPT/F2-F10 FREEZE'),
    ]
    refs(['append_f1_leo900_preflight_r9_20261018.py'])
    document = dict(schema='brphm-f1-additive-pre-final-evidence-r9', created_utc=now,
        status='F1 OPEN', f1_closed=False, goal_status='active', scientific_success_claimed=False,
        manuscript_and_f2_f10_substantive_edits_frozen=True, previous_r8_sha256=EXPECTED[PREVIOUS],
        review_report={'path':str(REVIEW),'sha256':review_sha,'lines':'19-25'}, findings=findings,
        artifact_sha256=dict(sorted(records.items())), frozen_artifact_sha256=frozen,
        new_support_directory=deployed['support'], first_read_only_prediction_audit=deployed['read_only_audit'],
        protected_boundaries={'BRPHM-preview':'no access or modification','ModelScope':'read-only; not accessed here',
            'IEEE':'no upload/submission/email/contact','simulation':'no stop/restart/copy/configuration modification',
            'controller':'no duplicate start/freeze/evaluate'},
        next_required=['Preserve the existing simulation/controller through normal terminal.',
            'At complete terminal run R2, numerical-statistics and prediction-summary auditors to new output names; never repeat evaluation.',
            'Audit96 generated members versus positive-window evaluated subset, freeze/access chronology and original precision gate.',
            'Assess registered statistics, physical-unit effect size and uncertainty before deciding F1.',
            'After actual F1 closure, resume F2-F10 and all final deliverables; auxiliary tests cannot complete the goal.'])
    for row in findings:
        assert all(row.get(key) for key in FIELDS)
        assert all(key in records for key in row['evidence'])
    for name, expected in records.items():
        assert digest(ROOT / name) == expected
    with output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(document,handle,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False);handle.write('\n')
    labels = ('位置','原文','问题','修改','证据','来源','日期','哈希','命令','结果','交叉验证','置信度','剩余风险','状态')
    lines = ['# F1 LEO900 追加证据台账 R9','',f'记录时间：{now}','','**F1 OPEN；goal active；正文及 F2–F10 实质修改冻结。**','',
        '追加预测到单位汇总的独立核验、保留的失败测试、Rack 部署及运行观察。候选、门禁、统计设计和原始预最终承诺保持原登记字节。','']
    for row in findings:
        lines.extend([f"## {row['id']}",''])
        for key,label in zip(FIELDS,labels):
            value='; '.join(row[key]) if isinstance(row[key],list) else row[key]
            lines.append(f'- **{label}**：{value}')
        lines.append('')
    lines.extend(['## SHA256','','| 文件 | SHA256 |','|---|---|'])
    lines.extend(f'| `{name}` | `{value}` |' for name,value in sorted(records.items()))
    lines.extend(['','## 后续要求',''])
    lines.extend(f'{i}. {value}' for i,value in enumerate(document['next_required'],1))
    with markdown.open('x',encoding='utf-8',newline='\n') as handle:
        handle.write('\n'.join(lines)+'\n')
    print(json.dumps({'json':str(output),'sha256':digest(output),'markdown':str(markdown),
        'markdown_sha256':digest(markdown),'findings':len(findings),'bound_artifacts':len(records),'status':'F1 OPEN'}))


if __name__ == '__main__':
    main()
