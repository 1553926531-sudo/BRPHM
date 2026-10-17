"""Verify the registered statistics after terminal, without models or labels.

The CLI first requires the separate R2 execution-chain audit. Numerical checks
use saved per-unit sufficient summaries and the bootstrap archive, never raw
MAT, PT, final truth/prediction arrays, or an evaluator. The registered producer
is not imported. Count-weighted bootstrap arithmetic and Python rank/tail
calculations supply a different arithmetic implementation of the fixed design.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import leo900_terminal_evidence_20261018_r2 as provenance

EvidenceError = provenance.EvidenceError
require = provenance.require
COMPONENTS = ('bat', 'rwa')
METRICS = ('rmse', 'mae')
ESTIMANDS = ('window_pooled', 'unit_macro')
REPETITIONS = 20000


def number(value, context):
    require(type(value) in (int, float) and math.isfinite(value), context + ' must be finite')
    return float(value)


def close(actual, expected, context, *, scale=0.):
    """Allow summation-order rounding only; never use this for the F1 gate."""
    if expected is None:
        require(actual is None, context + ' must remain undefined')
        return
    actual = number(actual, context)
    expected = number(expected, context)
    allowance = 64 * math.ulp(max(abs(expected), abs(scale)))
    require(abs(actual - expected) <= allowance, context + ' arithmetic disagreement')


def paired_oracle(values):
    """Independent ranks, explicit sign sums, and erfc normal tail; no SciPy."""
    delta = [number(v, 'paired delta') for v in values]
    require(delta, 'paired unit deltas cannot be empty')
    n = len(delta)
    mean = math.fsum(delta) / n
    ordered = sorted(delta)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    sd = math.sqrt(math.fsum((d - mean) ** 2 for d in delta) / (n - 1)) if n > 1 else None
    dz = mean / sd if sd is not None and sd > 0 else None
    nonzero = [d for d in delta if d != 0]
    result = {'mean_unit_delta': mean, 'median_unit_delta': median, 'sd_unit_delta': sd,
              'standardized_paired_effect_dz': dz,
              'fraction_units_lower_error': sum(d < 0 for d in delta) / n,
              'fraction_units_equal_error': sum(d == 0 for d in delta) / n,
              'n_units': n, 'n_nonzero': len(nonzero)}
    if n == 1:
        return {**result, 'pvalue': None, 'statistic': None, 'rank_biserial': None}
    if not nonzero:
        return {**result, 'pvalue': 1., 'statistic': 0., 'rank_biserial': 0.}
    absolute = sorted(abs(d) for d in nonzero)
    ranks, ties, begin = {}, [], 0
    while begin < len(absolute):
        end = begin + 1
        while end < len(absolute) and absolute[end] == absolute[begin]:
            end += 1
        ranks[absolute[begin]] = (begin + 1 + end) / 2
        ties.append(end - begin)
        begin = end
    ranked = [ranks[abs(d)] for d in nonzero]
    positive = math.fsum(rank for d, rank in zip(nonzero, ranked) if d > 0)
    negative = math.fsum(rank for d, rank in zip(nonzero, ranked) if d < 0)
    statistic = min(positive, negative)
    if len(nonzero) <= 20:
        # Enumerate every subset sum, unlike the producer's convolution counts.
        sums = np.array([0], dtype=np.int64)
        for rank in ranked:
            sums = np.concatenate((sums, sums + int(2 * rank)))
        total = int(2 * math.fsum(ranked))
        extreme = np.count_nonzero(np.minimum(sums, total - sums) <= int(2 * statistic))
        pvalue = int(extreme) / len(sums)
    else:
        count = len(nonzero)
        variance = (count * (count + 1) * (2 * count + 1)
                    - math.fsum(t ** 3 - t for t in ties) / 2) / 24
        z = abs(positive - count * (count + 1) / 4) / math.sqrt(variance)
        pvalue = math.erfc(z / math.sqrt(2))
    return {**result, 'pvalue': pvalue, 'statistic': statistic,
            'rank_biserial': (positive - negative) / (positive + negative)}


def percentile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    fraction = position - lower
    return float(sorted_values[lower]) * (1 - fraction) + float(sorted_values[upper]) * fraction


def bootstrap_oracle(units, seed):
    """Use sampled multiplicity counts, rather than indexed-summary reduction."""
    n = len(units)
    summary = np.array([[u[key] for key in ('n_windows', 'candidate_sse', 'reference_sse',
                                          'candidate_sae', 'reference_sae')] for u in units], dtype=np.float64)
    macro = {m: np.array([u['candidate_' + m] - u['reference_' + m] for u in units]) for m in METRICS}
    output = {f'{m}__{e}': np.empty(REPETITIONS, dtype=np.float64) for m in METRICS for e in ESTIMANDS}
    generator = np.random.default_rng(seed)
    for begin in range(0, REPETITIONS, 128):
        end = min(REPETITIONS, begin + 128)
        selected = generator.integers(0, n, size=(end - begin, n))
        counts = np.zeros((end - begin, n), dtype=np.int64)
        np.add.at(counts, (np.repeat(np.arange(end - begin), n), selected.ravel()), 1)
        totals = counts @ summary
        output['rmse__window_pooled'][begin:end] = (np.sqrt(totals[:, 1] / totals[:, 0])
                                                  - np.sqrt(totals[:, 2] / totals[:, 0]))
        output['mae__window_pooled'][begin:end] = (totals[:, 3] - totals[:, 4]) / totals[:, 0]
        for metric in METRICS:
            output[f'{metric}__unit_macro'][begin:end] = (counts @ macro[metric]) / n
    return output


def verify_statistics(report, distributions):
    require(isinstance(report, dict) and set(report.get('components', {})) == set(COMPONENTS),
            'statistics component membership mismatch')
    keys = {f'{c}__{m}__{e}' for c in COMPONENTS for m in METRICS for e in ESTIMANDS}
    require(set(distributions) == keys, 'bootstrap distribution membership mismatch')
    tests, family = {}, []
    checked = 0
    for component_index, component in enumerate(COMPONENTS):
        entry = report['components'][component]
        require(entry.get('physical_unit') == provenance.PHYSICAL_UNITS[component], 'statistics physical unit mismatch')
        units = entry.get('units')
        require(isinstance(units, list) and units and all(isinstance(u, dict) for u in units),
                'statistics units missing')
        ids = [u.get('unit_id') for u in units]
        require(all(isinstance(u, str) and u.strip() for u in ids)
                and len(set(ids)) == len(ids) and ids == sorted(ids), 'statistics unit ordering/membership mismatch')
        require(type(entry.get('n_units')) is int and entry['n_units'] == len(units), 'statistics unit count mismatch')
        require(all(type(u.get('n_windows')) is int and u['n_windows'] > 0 for u in units)
                and type(entry.get('n_windows')) is int
                and entry['n_windows'] == sum(u['n_windows'] for u in units), 'statistics unit window count mismatch')
        design = entry.get('bootstrap_design', {})
        expected_design = {'cluster': 'unit_id', 'paired': True, 'all_unit_windows_retained': True,
                           'seed': 20261018 + component_index, 'repetitions': REPETITIONS,
                           'interval': 'percentile', 'one_unit_limitation': len(units) < 2}
        require(design == expected_design, 'bootstrap seed/design mismatch')
        require(entry.get('seed_description', {}).get('independent_repeats') == 0,
                'ensemble constituents cannot be independent unit replicates')
        for unit in units:
            for prefix in ('candidate', 'reference'):
                for field in ('sse', 'sae', 'rmse', 'mae'):
                    require(number(unit.get(prefix + '_' + field), 'unit ' + field) >= 0,
                            'unit error summary must be nonnegative')
                close(unit[prefix + '_rmse'], math.sqrt(unit[prefix + '_sse'] / unit['n_windows']), 'unit RMSE')
                close(unit[prefix + '_mae'], unit[prefix + '_sae'] / unit['n_windows'], 'unit MAE')
        oracle = bootstrap_oracle(units, 20261018 + component_index)
        for metric in METRICS:
            scale = max(u[p + '_' + metric] for u in units for p in ('candidate', 'reference'))
            allowance = 64 * math.ulp(scale)
            for estimand in ESTIMANDS:
                key = f'{component}__{metric}__{estimand}'
                values = np.asarray(distributions[key])
                require(values.dtype == np.dtype('float64') and values.shape == (REPETITIONS,)
                        and np.isfinite(values).all(), 'bootstrap distribution shape/dtype/finite mismatch')
                require(np.all(np.abs(values - oracle[f'{metric}__{estimand}']) <= allowance),
                        'bootstrap distribution differs from registered unit/seed arithmetic: ' + key)
                checked += len(values)
                saved = entry['bootstrap'][metric][estimand]
                ordered = np.sort(values)
                mean = math.fsum(float(v) for v in values) / len(values)
                sd = math.sqrt(math.fsum((float(v) - mean) ** 2 for v in values) / (len(values) - 1))
                close(saved.get('bootstrap_sd'), sd, 'bootstrap SD ' + key, scale=scale)
                for name, probs in (('ci95', (.025, .975)),
                                    ('ci_familywise_95_bonferroni_8', (.003125, .996875))):
                    interval = saved.get(name)
                    require(isinstance(interval, list) and len(interval) == 2, 'bootstrap interval schema mismatch')
                    for actual, probability in zip(interval, probs):
                        close(actual, percentile(ordered, probability), 'bootstrap interval ' + key + '.' + name, scale=scale)
            expected = paired_oracle([u['candidate_' + metric] - u['reference_' + metric] for u in units])
            actual = entry['paired_tests'][metric]
            for field, value in expected.items():
                if field in ('n_units', 'n_nonzero'):
                    require(type(actual.get(field)) is int and actual[field] == value, 'paired unit count mismatch')
                else:
                    field_scale = scale if field in ('mean_unit_delta', 'median_unit_delta', 'sd_unit_delta') else 1.
                    close(actual.get(field), value, 'paired ' + field + ' ' + component + '.' + metric, scale=field_scale)
            tests[(component, metric)] = expected
            family.append((component, metric))
    ranked = sorted(family, key=lambda key: (tests[key]['pvalue'] if tests[key]['pvalue'] is not None else 1., key))
    previous = 0.
    for index, key in enumerate(ranked):
        raw = tests[key]['pvalue']
        previous = max(previous, min(1., (len(family) - index) * (raw if raw is not None else 1.)))
        close(report['components'][key[0]]['paired_tests'][key[1]].get('holm_pvalue_family4'),
              previous if raw is not None else None, 'Holm adjusted paired pvalue', scale=1.)
    return {'status': 'NUMERICAL_STATISTICS_VERIFIED', 'bootstrap_draws_checked': checked,
            'bootstrap_intervals_checked': 16, 'bootstrap_sd_checked': 8, 'paired_tests_checked': 4,
            'holm_family_size': 4, 'f1_closed': False, 'scientific_success_claimed': False,
            'arithmetic_comparison': '64 ULP at the underlying component error scale for alternative summation; not the gate tolerance',
            'gate_recalibration_or_retesting': False,
            'limitations': ['Uses saved per-unit sufficient summaries; does not independently recompute their errors from final labels/predictions.',
                            'Uses the same NumPy integer RNG contract as the registered analysis, with different count-weighted arithmetic.',
                            'An arithmetic check does not establish independence, distribution assumptions, practical superiority, or historic non-access.',
                            'One final orbit; ensemble constituents are not independent training repetitions.']}


def audit(root, publication_path, *, anchors=None):
    chain = provenance.audit(root, publication_path, anchors=anchors)
    if chain['status'] == 'PENDING_TERMINAL':
        return {**chain, 'numerical_statistics_status': 'DEFERRED_UNTIL_COMPLETE_TERMINAL',
                'bootstrap_arrays_decoded': False, 'final_truth_or_prediction_arrays_decoded': False}
    require(chain['status'] == 'EXECUTION_CHAIN_VERIFIED', 'complete verified terminal required')
    files = provenance.Files(root)
    statistics = files.root / 'formal_statistics_20261018_r1'
    report = files.read(statistics / 'f1_gate_statistics.json')
    receipt = files.read(statistics / 'statistics_receipt.json')
    require(receipt.get('report_sha256') == files.digest(statistics / 'f1_gate_statistics.json'),
            'numerical audit statistics report hash mismatch')
    path = files.record(report['bootstrap_distributions'], base=statistics, context='bootstrap archive')
    with np.load(path, allow_pickle=False) as archive:
        require(len(archive.files) == len(set(archive.files)), 'duplicate bootstrap archive members')
        distributions = {name: archive[name] for name in archive.files}
    require(files.digest(path) == hashlib.sha256(path.read_bytes()).hexdigest(), 'bootstrap archive changed during decode')
    result = verify_statistics(report, distributions)
    files.finish()
    return {**result, 'execution_chain': chain, 'bootstrap_arrays_decoded': True,
            'final_truth_or_prediction_arrays_decoded': False, 'models_or_evaluator_invoked': False,
            'input_sha256': {str(path): digest for path, digest in files.hashes.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    here = Path(__file__).absolute().parent
    require(output.parent == here, 'numerical audit output must be beside this program')
    require(not output.exists() and not output.is_symlink(), 'numerical audit output must be new')
    require(hashlib.sha256((here / 'leo900_terminal_evidence_20261018_r2.py').read_bytes()).hexdigest()
            == '3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0',
            'registered R2 audit source drift')
    report = audit(provenance.RUN, here / provenance.PUBLICATION)
    report.update(created_utc=datetime.now(timezone.utc).isoformat(),
                  numerical_audit_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  runtime={'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__})
    with output.open('xb') as handle:
        handle.write(provenance.json_bytes(report))
        handle.flush()
        os.fsync(handle.fileno())
    print(provenance.json_bytes({'status': report['status'], 'output': str(output),
        'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'f1_closed': False}).decode().strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
