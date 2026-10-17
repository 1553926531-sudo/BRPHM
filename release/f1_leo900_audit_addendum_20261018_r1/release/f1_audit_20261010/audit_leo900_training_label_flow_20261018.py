"""Static F1 review of registered source bytes; never imports research code.

Reads Python/JSON and archived Python members only. No MAT, tensors, prediction
arrays or model training. This report cannot prove historical absence of access.
"""
from __future__ import annotations

import ast
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).absolute().parent
ROOT = HERE.parent.parent
PROTOCOL = HERE / 'F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json'
AMENDMENT = HERE / 'F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json'
CLOSURE = (ROOT / 'release/f1_leo900_pre_final_commitment_20261018_r1/registered_inputs'
           '/dependency_support_20261018_r3a/F1_LEO900_DEPENDENCY_CLOSURE_20261018R3.json')
ARCHIVE = ROOT / 'release/paper_artifacts_20261018r91/paper_reproduction_20261018r91.tar.gz'
ARCHIVE_SHA256 = 'e8874a5bc8c7e4ced5c0c0e495216497e5d6b5e1d633523d9a0f8167ed4cafb3'
PREFIX = 'revision_20261018r91/audit/f7/host_longrun_20261015/'
CONTROL_DIRECTORY = 'work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    protocol_raw, closure_raw, amendment_raw = PROTOCOL.read_bytes(), CLOSURE.read_bytes(), AMENDMENT.read_bytes()
    require(digest(protocol_raw) == 'a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a', 'protocol drift')
    require(digest(closure_raw) == '1507c2b72ad12d7bc1dc080ede4a96b4a8efb216a09d870809c2758386a7cc61', 'closure drift')
    protocol, closure = json.loads(protocol_raw), json.loads(closure_raw)
    amendment_sha = digest(amendment_raw)
    require(any(r['path'].endswith('/' + AMENDMENT.name) and r['sha256'] == amendment_sha
                for r in protocol['input_files']), 'execution amendment parent binding mismatch')
    amendment = json.loads(amendment_raw)
    project_hashes = {r['path']: r['sha256'] for r in closure['project_files']}
    sources, records = {}, {}

    def add(key, raw, location, *, project_path=None, registered_suffix=None):
        sha = digest(raw)
        if project_path:
            require(project_hashes.get(project_path) == sha, 'project binding mismatch: ' + key)
            bindings = [r for r in closure['project_files'] if r['path'] == project_path]
        else:
            bindings = [r for r in protocol['input_files'] if r['path'].endswith('/' + registered_suffix) and r['sha256'] == sha]
            if not bindings:
                bindings = [{**r, 'parent_manifest_sha256': amendment_sha,
                             'parent_manifest': str(AMENDMENT)} for r in amendment['execution_files']
                            if r['path'] == registered_suffix and r['sha256'] == sha]
            require(bindings, 'protocol/amendment binding mismatch: ' + key)
        text = raw.decode('utf-8')
        ast.parse(text)
        sources[key] = text
        records[key] = {'location': location, 'sha256': sha, 'size': len(raw), 'registered_bindings': bindings}

    for key, path, suffix in (
        ('evaluator', HERE / 'f1_clean_final_test_20261018_v3.py', 'f1_clean_final_test_20261018_v3.py'),
        ('adapter', HERE / 'f1_leo900_plain_l1_clean_final_test_20261018_r1.py', 'f1_leo900_plain_l1_clean_final_test_20261018_r1.py'),
        ('trainer', HERE / 'leo900_source_trainer_20261018/run_l1_mmd_source_only_20261015.py', 'leo900_source_trainer_20261018/run_l1_mmd_source_only_20261015.py'),
        ('calibration', HERE / 'leo900_source_trainer_20261018/calibration_source_only.py', 'leo900_source_trainer_20261018/calibration_source_only.py'),
    ):
        add(key, path.read_bytes(), str(path), registered_suffix=suffix)
    route_path = HERE / 'source_bindings/temporal_tcn_global_inner_route_source_gate.py'
    add('route', route_path.read_bytes(), str(route_path),
        project_path='work/rul_next_electrochemical/temporal_tcn_global_inner_route_source_gate.py')
    require(digest(ARCHIVE.read_bytes()) == ARCHIVE_SHA256, 'reproduction archive drift')
    archive_names = {
        'control': 'run_segmented_hgb_mlp_source_gate_20260929.py',
        'fixed_mlp': 'run_leave_one_orbit_out_generalization_20260825.py',
        'base': 'run_component_blend_refinement_20260824.py',
    }
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        for key, name in archive_names.items():
            member = PREFIX + CONTROL_DIRECTORY + name
            entry = archive.getmember(member)
            require(entry.isfile(), 'non-file source member')
            add(key, archive.extractfile(entry).read(), str(ARCHIVE) + '::' + member,
                project_path=CONTROL_DIRECTORY + name)

    def function(key, name):
        nodes = [n for n in ast.parse(sources[key]).body if isinstance(n, ast.FunctionDef) and n.name == name]
        require(len(nodes) == 1, 'ambiguous source function: ' + key + '.' + name)
        return nodes[0]

    def excerpt(key, name):
        n = function(key, name)
        return {'source': key, 'function': name, 'first_line': n.lineno, 'last_line': n.end_lineno,
                'text': '\n'.join(sources[key].splitlines()[n.lineno - 1:n.end_lineno])}

    def normalized(key, name):
        return ast.unparse(function(key, name))

    evaluator = normalized('evaluator', 'evaluate')
    adapter = normalized('adapter', 'fit_plain_l1_formal')
    control = normalized('control', 'fit_predict_fixed')
    trainer = function('trainer', 'fit_model_mmd')
    fixed_mlp = function('fixed_mlp', 'fit_mlp')
    facts = []

    def fact(identity, condition, conclusion, references, limit):
        require(condition, identity)
        facts.append({'id': identity, 'status': 'STATIC_SOURCE_CHECK_PASS', 'conclusion': conclusion,
                      'evidence': [excerpt(*r) for r in references], 'remaining_risk': limit})

    fact('F1-LABEL-FLOW-01', all(s in evaluator for s in (
        'train = np.zeros(n_old + n_final, dtype=bool)', 'train[:n_old] = True', 'valid = ~train')),
        'Evaluation masks train on old registered tensors and hold out all appended final windows.',
        [('evaluator', 'evaluate')], 'Runtime masks and exact input hashes must still match the terminal receipts.')
    fact('F1-LABEL-FLOW-02', "source_y = data['y'][train] / float(data['rmax'])" in adapter
         and "data['y'][valid]" not in adapter and 'mmd_lambda=0.0, epochs_override=90' in adapter,
         'TCN normalization, labels and residual correction use source-fit rows; the registered trainer receives 90 epochs and lambda zero.',
         [('adapter', 'fit_plain_l1_formal'), ('calibration', 'unit_median_correction')],
         'This follows the registered code path; it does not establish historical absence of final-data access.')
    fact('F1-LABEL-FLOW-03',
         [a.arg for a in trainer.args.args] == ['sequences', 'targets', 'rows', 'cfg', 'seed', 'device_name', 'mmd_lambda', 'epochs_override']
         and not any(isinstance(n, ast.Break) for n in ast.walk(trainer))
         and 'for _ in range(max(1, epochs)):' in ast.unparse(trainer),
         'TCN fitting has a fixed epoch loop and no final-validation argument or validation early stopping. The extra representation forward remains present at lambda zero.',
         [('trainer', 'fit_model_mmd')], 'No training was executed by this static audit; broader data-generation assumptions remain separately reviewable.')
    imported = any(isinstance(n, ast.ImportFrom)
                   and n.module == 'run_leave_one_orbit_out_generalization_20260825'
                   and any(a.name == 'fit_mlp' and a.asname is None for a in n.names)
                   for n in ast.parse(sources['control']).body)
    fact('F1-LABEL-FLOW-04', imported
         and [a.arg for a in fixed_mlp.args.args] == ['X', 'y', 'cfg', 'seed', 'epochs', 'device_name']
         and not any(isinstance(n, ast.Break) for n in ast.walk(fixed_mlp))
         and 'for _ in range(max(1, int(epochs))):' in ast.unparse(fixed_mlp)
         and 'fit_mlp(age_train, target,' in control,
         'The control calls the fixed-epoch MLP imported from the leave-one-orbit module. The distinct base.fit_mlp function with Xva/yva early stopping is not the function called here.',
         [('control', 'fit_predict_fixed'), ('fixed_mlp', 'fit_mlp'), ('base', 'fit_mlp')],
         'Import order, frozen dependency bytes and runtime selection remain part of the terminal verification.')
    fact('F1-LABEL-FLOW-05', "y_train = data['y'][train] / data['rmax']" in control
         and 'hgb.fit(h_train, y_train)' in control
         and control.index('projected = base.project') < control.index("data['y'][valid]"),
         'The control trains HGB/MLP on y_train. It reads final labels to compute metrics and residuals after projected predictions; those labels are not inputs to its training or epoch selection.',
         [('control', 'fit_predict_fixed'), ('fixed_mlp', 'segmented'), ('base', 'project')],
         'HGB may use its own source-only internal validation; this audit does not claim every kind of early stopping is disabled.')
    route = normalized('route', 'reference_control_candidate')
    fact('F1-LABEL-FLOW-06', 'candidate = dict(segmented.CANDIDATES[component])' in route
         and "candidate['aggregation'] = 'median3'" in route,
         'The control configuration is copied from fixed component candidates with median3 aggregation, without final-metric-based route search.',
         [('route', 'reference_control_candidate'), ('evaluator', 'evaluate')],
         'Earlier outer and LEO800 feedback affected the development history; this narrow final execution review does not relabel that history as source-only.')

    report = {
        'schema': 'brphm-f1-registered-training-label-flow-review-v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'STATIC_REVIEW_CHECKS_PASS', 'f1_closed': False, 'scientific_success_claimed': False,
        'scope': 'Registered LEO900 final evaluator, TCN source-fit adapter/trainer and HGB/MLP control path.',
        'script_sha256': digest(Path(__file__).read_bytes()),
        'protocol': {'path': str(PROTOCOL), 'sha256': digest(protocol_raw)},
        'execution_amendment': {'path': str(AMENDMENT), 'sha256': amendment_sha},
        'closure': {'path': str(CLOSURE), 'sha256': digest(closure_raw)},
        'archive': {'path': str(ARCHIVE), 'sha256': ARCHIVE_SHA256},
        'sources': records, 'findings': facts,
        'real_final_labels_read': False, 'mat_tensor_or_prediction_arrays_decoded': False,
        'research_code_imported': False, 'training_or_evaluation_invoked': False,
        'confidence': 'High for the cited byte-bound static source facts; terminal runtime evidence and historical no-access claims are separate.',
        'cross_validation': 'Source snippets are checked against AST call/import relationships and the protocol/dependency-closure hashes. Copies and hashes are not independent no-access witnesses.',
        'limitations': ['Not a whole-program information-flow proof.',
                        'Cannot prove historical absence of access or independent ownership of all logs.',
                        'Does not establish scientific or practical superiority.',
                        'No final arrays are decoded or performance results inspected.'],
    }
    output = HERE / 'F1_LEO900_TRAINING_LABEL_FLOW_20261018R1.json'
    with output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(report, handle, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'output': str(output), 'sha256': digest(output.read_bytes()),
                      'status': report['status'], 'source_count': len(records), 'checks': len(facts)}))


if __name__ == '__main__':
    main()
