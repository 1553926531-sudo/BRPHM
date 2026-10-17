"""Read-only independent prediction-to-summary audit after complete terminal.

Uses the original single-pass NPZ, Python scalar errors and math.fsum. Never
imports a model, evaluator, registered metric/statistics producer, MAT or PT
decoder. The existing R2 audit must first verify the complete execution chain.
This changes neither the candidate nor any gate, estimand or statistical test.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import leo900_terminal_evidence_20261018_r2 as provenance

EvidenceError = provenance.EvidenceError
require = provenance.require
R2_SHA256 = '3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0'
ARRAYS = {'truth_rul', 'truth_relative', 'candidate', 'control', 'alpha',
          'blended_before_final_projection', 'projected'}
METRICS = ('rmse', 'mae', 'bias', 'unit_macro_rmse', 'rul_upward_fraction', 'n_windows', 'n_units')


def finite(value, context):
    require(type(value) in (int, float) and math.isfinite(value), context + ' must be finite')
    return float(value)


def close(actual, expected, context, *, scale=0.):
    """Alternative summation allowance only; never a gate decision tolerance."""
    if expected is None:
        require(actual is None, context + ' must remain undefined')
        return
    actual = finite(actual, context)
    require(abs(actual - expected) <= 64 * math.ulp(max(abs(expected), abs(scale))),
            context + ' disagrees with original predictions')


def load_arrays(path):
    with np.load(path, allow_pickle=False) as archive:
        require(len(archive.files) == len(set(archive.files)), 'duplicate prediction archive members')
        return {name: archive[name] for name in archive.files}


def scalar_errors(values, truth, rmax, rows):
    """Compute every physical error separately; use no producer reductions."""
    predicted = [min(1., max(0., float(value))) * rmax for value in values]
    errors = [value - float(label) * rmax for value, label in zip(predicted, truth)]
    groups = {}
    for index, row in enumerate(rows):
        groups.setdefault(row['unit_id'], []).append(index)
    units = {}
    for uid, indices in sorted(groups.items()):
        e = [errors[index] for index in indices]
        sse = math.fsum(value * value for value in e)
        sae = math.fsum(abs(value) for value in e)
        units[uid] = {'n_windows': len(e), 'sse': sse, 'sae': sae,
                      'rmse': math.sqrt(sse / len(e)), 'mae': sae / len(e)}
    upward = pairs = 0
    for indices in groups.values():
        ordered = sorted(indices, key=lambda i: float(rows[i].get('t_end', i)))
        for left, right in zip(ordered, ordered[1:]):
            pairs += 1
            upward += int(predicted[right] > predicted[left] + 1e-9)
    metrics = {'rmse': math.sqrt(math.fsum(e * e for e in errors) / len(errors)),
               'mae': math.fsum(abs(e) for e in errors) / len(errors),
               'bias': math.fsum(errors) / len(errors),
               'unit_macro_rmse': math.fsum(u['rmse'] for u in units.values()) / len(units),
               'rul_upward_fraction': upward / pairs if pairs else None,
               'n_windows': len(errors), 'n_units': len(units)}
    return metrics, units, max(abs(e) for e in errors)


def compare_metrics(saved, expected, context, *, scale):
    require(isinstance(saved, dict) and set(METRICS) <= set(saved), context + ' metric membership mismatch')
    for name in METRICS:
        if name in ('n_windows', 'n_units'):
            require(type(saved[name]) is int and saved[name] == expected[name], context + ' count mismatch')
        elif name == 'rul_upward_fraction':
            require(saved[name] == expected[name], context + ' upward fraction mismatch')
        else:
            close(saved[name], expected[name], context + '.' + name, scale=scale)


def verify_component(layout, arrays, result, stats):
    component = layout.get('component')
    require(component in provenance.COMPONENTS, 'prediction component mismatch')
    rows = layout.get('rows')
    require(isinstance(rows, list) and rows, 'prediction rows missing')
    for index, row in enumerate(rows):
        require(isinstance(row, dict) and isinstance(row.get('unit_id'), str)
                and row['unit_id'].strip(), 'prediction row unit identifier missing')
        finite(row.get('t_end', index), 'prediction row time')
    n = len(rows)
    require(set(arrays) in (ARRAYS, ARRAYS | {'seed_raw_predictions'}), 'prediction array membership mismatch')
    require(set(layout.get('array_dtypes', {})) == set(arrays)
            and set(layout.get('array_shapes', {})) == set(arrays), 'prediction array metadata membership mismatch')
    seeds = layout.get('seeds') or []
    if 'seed_raw_predictions' in arrays:
        require(isinstance(seeds, list) and seeds and all(type(s) is int for s in seeds)
                and len(set(seeds)) == len(seeds), 'prediction ensemble seed membership mismatch')
    else:
        require(not seeds, 'seed identities without saved raw constituent predictions')
    for name, values in arrays.items():
        shape = (len(seeds), n) if name == 'seed_raw_predictions' else (n,)
        require(isinstance(values, np.ndarray) and values.shape == shape
                and list(shape) == layout['array_shapes'][name], 'prediction array shape mismatch: ' + name)
        require(str(values.dtype) == layout['array_dtypes'][name] and values.dtype.kind == 'f',
                'prediction array dtype mismatch: ' + name)
        require(np.isfinite(values).all(), 'prediction array must be finite: ' + name)
    rmax = finite(layout.get('rmax'), 'prediction rmax')
    require(rmax > 0 and stats.get('rmax') == rmax, 'statistics rmax differs from prediction scale')
    require(stats.get('physical_unit') == provenance.PHYSICAL_UNITS[component], 'prediction physical unit mismatch')
    relative = arrays['truth_rul'] / float(rmax)
    require(relative.dtype == arrays['truth_relative'].dtype
            and np.array_equal(relative, arrays['truth_relative']), 'saved label division differs from original dtype arithmetic')
    alpha = arrays['alpha']
    route_alpha = finite(result.get('route', {}).get('alpha_by_target', {}).get('LEO900'), 'source route alpha')
    require(0 <= route_alpha <= 1 and alpha.dtype == np.dtype('float32')
            and np.array_equal(alpha, np.full(n, route_alpha, dtype=np.float32)), 'saved alpha differs from frozen source route')
    blended = (alpha * np.asarray(arrays['candidate'], dtype=np.float32)
               + (1. - alpha) * np.asarray(arrays['control'], dtype=np.float32))
    require(blended.dtype == arrays['blended_before_final_projection'].dtype
            and np.array_equal(blended, arrays['blended_before_final_projection']), 'saved candidate/control blend mismatch')
    counts = dict(Counter(row['unit_id'] for row in rows))
    require(result.get('unit_window_counts') == counts and result.get('n_windows') == n
            and result.get('n_units') == len(counts), 'prediction unit/window membership mismatch')
    require(type(stats.get('n_windows')) is int and stats['n_windows'] == n
            and type(stats.get('n_units')) is int and stats['n_units'] == len(counts), 'statistics unit/window count mismatch')
    units = stats.get('units')
    require(isinstance(units, list) and all(isinstance(u, dict) for u in units)
            and [u.get('unit_id') for u in units] == sorted(counts)
            and all(type(u.get('n_windows')) is int and u['n_windows'] == counts[u['unit_id']] for u in units),
            'statistics unit summary membership/count mismatch')
    calculated, by_variant, scales = {}, {}, {}
    for name, key in (('metrics', 'projected'), ('candidate_only_metrics', 'candidate'), ('control_only_metrics', 'control')):
        computed, per_unit, scale = scalar_errors(arrays[key], arrays['truth_relative'], rmax, rows)
        compare_metrics(result.get(name), computed, component + '.' + name, scale=scale)
        compare_metrics(stats.get('metrics', {}).get(name), computed, 'statistics.' + component + '.' + name, scale=scale)
        calculated[name], by_variant[name], scales[name] = computed, per_unit, scale
    independent_units = []
    for saved in units:
        uid = saved['unit_id']
        recomputed = {'unit_id': uid, 'n_windows': counts[uid]}
        for prefix, name in (('candidate', 'metrics'), ('reference', 'control_only_metrics')):
            expected = by_variant[name][uid]
            for field in ('sse', 'sae', 'rmse', 'mae'):
                close(saved.get(prefix + '_' + field), expected[field], 'unit ' + uid + '.' + prefix + '_' + field)
                recomputed[prefix + '_' + field] = expected[field]
        for metric in ('rmse', 'mae'):
            c, r = saved['candidate_' + metric], saved['reference_' + metric]
            require(saved.get('delta_' + metric) == c-r, 'unit saved delta mismatch')
            require(saved.get('relative_change_percent_' + metric) == (100. * (c-r) / r if r > 0 else None),
                    'unit saved relative change mismatch')
        independent_units.append(recomputed)
    descriptions = stats.get('seed_description', {})
    require(descriptions.get('independent_repeats') == 0, 'ensemble constituents cannot be independent repeats')
    constituents = descriptions.get('constituents')
    require(isinstance(constituents, list) and len(constituents) == len(seeds)
            and [entry.get('seed') for entry in constituents] == seeds, 'seed description membership/order mismatch')
    for entry, values in zip(constituents, arrays.get('seed_raw_predictions', [])):
        expected, _, scale = scalar_errors(values, arrays['truth_relative'], rmax, rows)
        compare_metrics(entry.get('raw_metrics'), expected, component + '.seed.' + str(entry['seed']), scale=scale)
    return {'n_windows': n, 'n_units': len(counts), 'physical_unit': provenance.PHYSICAL_UNITS[component],
            'metrics': calculated, 'units': independent_units, 'seed_descriptions_checked': len(seeds)}


def audit(root, publication_path, *, anchors=None):
    chain = provenance.audit(root, publication_path, anchors=anchors)
    if chain['status'] == 'PENDING_TERMINAL':
        return {**chain, 'prediction_summary_status': 'DEFERRED_UNTIL_COMPLETE_TERMINAL',
                'final_truth_or_prediction_arrays_decoded': False}
    require(chain['status'] == 'EXECUTION_CHAIN_VERIFIED', 'complete verified terminal required')
    files = provenance.Files(root)
    formal, statistics = files.root / 'formal_output_execution_r1', files.root / 'formal_statistics_20261018_r1'
    receipt = files.read(formal / 'final_receipt.json')
    stats = files.read(statistics / 'f1_gate_statistics.json')
    stats_receipt = files.read(statistics / 'statistics_receipt.json')
    require(stats_receipt.get('report_sha256') == files.digest(statistics / 'f1_gate_statistics.json'),
            'prediction auditor statistics report hash mismatch')
    verified = {}
    for component in provenance.COMPONENTS:
        result = receipt['results'][component]
        paired = result['paired_predictions']
        layout_path = files.record({'path': paired['layout_path'], 'sha256': paired['layout_sha256']},
                                   base=formal, context='prediction layout')
        archive = files.record({'path': paired['arrays_path'], 'sha256': paired['arrays_sha256']},
                               base=formal, context='prediction archive')
        layout = files.read(layout_path)
        require(layout.get('schema') == 'brphm-f1-original-pass-paired-predictions-v1'
                and layout.get('component') == component and layout.get('arrays_path') == archive.name
                and layout.get('arrays_sha256') == paired['arrays_sha256']
                and layout.get('payload_sha256') == result['payload_sha256'], 'prediction layout identity/hash mismatch')
        rows_hash = hashlib.sha256(provenance.json_bytes(layout['rows'])).hexdigest()
        require(rows_hash == layout.get('rows_sha256') == paired.get('rows_sha256')
                and len(layout['rows']) == paired.get('n_rows'), 'prediction rows hash/count mismatch')
        require(stats['components'][component].get('prediction_binding') == paired, 'statistics prediction hash binding mismatch')
        arrays = load_arrays(archive)
        require(files.digest(archive) == hashlib.sha256(archive.read_bytes()).hexdigest(), 'prediction archive changed while decoding')
        verified[component] = verify_component(layout, arrays, result, stats['components'][component])
        del arrays
    files.finish()
    return {'status': 'PREDICTION_SUMMARIES_VERIFIED', 'components': verified, 'execution_chain': chain,
            'final_truth_or_prediction_arrays_decoded': True, 'models_or_evaluator_invoked': False,
            'raw_mat_or_tensor_decoded': False, 'bootstrap_resampled': False,
            'f1_closed': False, 'scientific_success_claimed': False,
            'arithmetic_comparison': '64 ULP for alternative descriptive summations only; original gate remains exact and unchanged',
            'input_sha256': {str(path): digest for path, digest in files.hashes.items()},
            'limitations': ['Checks saved arrays against saved metadata; does not independently decode MAT/PT or reconstruct their labels/window eligibility.',
                            'Does not retrain models or independently recompute projection, centering or raw ensemble prediction generation.',
                            'The R2 execution audit checks exact registered gate arithmetic; this descriptive audit never substitutes a new gate.',
                            'One final orbit, fixed training run; constituent seeds are not independent training repetitions.',
                            'Hash-linked execution evidence cannot independently prove absence of all historic access.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).absolute().parent
    output = args.output.absolute()
    require(output.parent == here and not output.exists() and not output.is_symlink(), 'audit output must be new and beside this program')
    require(hashlib.sha256((here / 'leo900_terminal_evidence_20261018_r2.py').read_bytes()).hexdigest() == R2_SHA256,
            'registered R2 audit source drift')
    result = audit(provenance.RUN, here / provenance.PUBLICATION)
    result.update(created_utc=datetime.now(timezone.utc).isoformat(),
                  prediction_summary_audit_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  runtime={'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__})
    with output.open('xb') as handle:
        handle.write(provenance.json_bytes(result))
        handle.flush()
        os.fsync(handle.fileno())
    print(provenance.json_bytes({'status': result['status'], 'output': str(output),
          'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'f1_closed': False}).decode().strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
