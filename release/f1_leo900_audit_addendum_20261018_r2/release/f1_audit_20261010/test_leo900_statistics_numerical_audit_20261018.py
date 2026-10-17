"""Independent arithmetic checks on artificial statistics, never final labels."""
from __future__ import annotations

import copy
import hashlib
import importlib
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import f1_lossless_gate_statistics_20261018 as registered
from test_leo900_terminal_evidence_20261018_r2 import Fixture, ProductionFixture

try:
    numerical = importlib.import_module('leo900_statistics_numerical_audit_20261018')
except ModuleNotFoundError as exc:
    if exc.name != 'leo900_statistics_numerical_audit_20261018':
        raise
    numerical = None


def artificial_report(candidate=None, reference=None, rows=None):
    """Use the registered producer as the other implementation, on fake data."""
    if candidate is None:
        candidate = [0., .25, .5, .75, .25, .25, 0.]
        reference = [.75, .5, .75, 0., .5, .25, .25]
        rows = [{'unit_id': u, 't_end': i} for i, u in
                enumerate(['a', 'a', 'a', 'b', 'c', 'c', 'd'])]
    report, draws = {'components': {}}, {}
    for index, c in enumerate(('bat', 'rwa')):
        entry = registered.paired_unit_statistics(
            candidate, reference, [0.] * len(rows), 1., rows,
            reps=20000, seed=20261018 + index)
        draws.update({f'{c}__{key}': value for key, value in entry.pop('bootstrap_draws').items()})
        entry.update(physical_unit={'bat': 'cycle', 'rwa': 'day'}[c],
                     seed_description={'independent_repeats': 0})
        report['components'][c] = entry
    family = [(c, m) for c in ('bat', 'rwa') for m in ('rmse', 'mae')]
    adjusted = registered.holm_adjust([
        report['components'][c]['paired_tests'][m]['pvalue']
        if report['components'][c]['paired_tests'][m]['pvalue'] is not None else 1.
        for c, m in family])
    for (c, m), value in zip(family, adjusted):
        test = report['components'][c]['paired_tests'][m]
        test['holm_pvalue_family4'] = value if test['pvalue'] is not None else None
    return report, draws


def complete_fixture(root):
    """Hash-bound production scaffold with real *artificial* bootstrap arrays.

    Its MAT, PT and paired-prediction files remain deliberately undecodable.
    Only the synthetic sufficient summaries and bootstrap archive are replaced.
    """
    fixture = ProductionFixture(root)
    receipt = fixture.documents['formal_output_execution_r1/final_receipt.json']
    stats = fixture.documents['formal_statistics_20261018_r1/f1_gate_statistics.json']
    draws = {}
    for index, c in enumerate(('bat', 'rwa')):
        saved = receipt['results'][c]
        layout_key = fixture.formal.relative_to(root) / saved['paired_predictions']['layout_path']
        rows = fixture.documents[str(layout_key)]['rows']
        candidate, reference, truth = [.0025] * len(rows), [.005] * len(rows), [0.] * len(rows)
        metrics = registered.recompute_metrics(candidate, truth, 100., rows)
        baseline = registered.recompute_metrics(reference, truth, 100., rows)
        saved.update(metrics=metrics, control_only_metrics=baseline)
        entry = registered.paired_unit_statistics(candidate, reference, truth, 100., rows,
                                                  seed=20261018 + index, reps=20000)
        draws.update({f'{c}__{name}': value for name, value in entry.pop('bootstrap_draws').items()})
        entry.update(physical_unit='cycle' if c == 'bat' else 'day', rmax=100.,
                     seed_description={'independent_repeats': 0}, prediction_binding=saved['paired_predictions'],
                     metrics={'metrics': metrics, 'control_only_metrics': baseline})
        stats['components'][c] = entry
    family = [(c, m) for c in ('bat', 'rwa') for m in ('rmse', 'mae')]
    adjusted = registered.holm_adjust([stats['components'][c]['paired_tests'][m]['pvalue'] for c, m in family])
    for (c, m), value in zip(family, adjusted):
        stats['components'][c]['paired_tests'][m]['holm_pvalue_family4'] = value
    archive = fixture.statistics / 'f1_unit_cluster_bootstrap.npz'
    with archive.open('wb') as handle:
        np.savez_compressed(handle, **draws)
    stats['bootstrap_distributions'].update(fixture.record(archive))
    fixture.put('formal_output_execution_r1/final_receipt.json', receipt)
    gate = fixture.documents['formal_output_execution_r1/same_partition_performance_gate.json']
    comparison = registered.gate_decision({c: receipt['results'][c]['metrics'] for c in ('bat', 'rwa')},
                                          {c: receipt['results'][c]['control_only_metrics'] for c in ('bat', 'rwa')})
    gate['comparison'].update(comparison)
    gate['metrics'] = {c: {'candidate_blend': receipt['results'][c]['metrics'],
                          'same_partition_reference': receipt['results'][c]['control_only_metrics']}
                       for c in ('bat', 'rwa')}
    fixture.put('formal_output_execution_r1/same_partition_performance_gate.json', gate)
    stats['gate'] = comparison
    fixture.put('formal_statistics_20261018_r1/f1_gate_statistics.json', stats)
    fixture.write_csv()
    fixture.rebind()
    return fixture


class NumericalStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(numerical, 'independent numerical verification is missing')
        self.report, self.draws = artificial_report()

    def reject(self, pattern='bootstrap|interval|paired|Holm|seed|unit|distribution'):
        with self.assertRaisesRegex(numerical.EvidenceError, pattern):
            numerical.verify_statistics(self.report, self.draws)

    def test_valid_registered_statistics_match_a_different_arithmetic_implementation(self):
        result = numerical.verify_statistics(self.report, self.draws)
        self.assertEqual(result['status'], 'NUMERICAL_STATISTICS_VERIFIED')
        self.assertEqual(result['bootstrap_draws_checked'], 160000)
        self.assertEqual(result['paired_tests_checked'], 4)
        self.assertFalse(result['f1_closed'])
        self.assertFalse(result['scientific_success_claimed'])

    def test_unequal_window_weights_have_a_hand_checked_distribution(self):
        rows = [{'unit_id': 'a'}] * 3 + [{'unit_id': 'b'}]
        report, draws = artificial_report([0., 0., 0., 1.], [1., 1., 1., 0.], rows)
        result = numerical.verify_statistics(report, draws)
        self.assertEqual(set(draws['bat__mae__window_pooled']), {-1., -.5, 1.})
        self.assertEqual(set(draws['bat__mae__unit_macro']), {-1., 0., 1.})
        self.assertEqual(report['components']['bat']['bootstrap']['mae']['window_pooled']['point_delta'], -.5)
        self.assertEqual(result['bootstrap_draws_checked'], 160000)

    def test_plausible_nested_but_wrong_interval_is_rejected(self):
        entry = self.report['components']['bat']['bootstrap']['rmse']['window_pooled']
        low, high = entry['ci95']
        entry['ci95'] = [low + .1 * (high - low), high - .1 * (high - low)]
        self.reject('interval')

    def test_positive_but_wrong_bootstrap_sd_is_rejected(self):
        self.report['components']['bat']['bootstrap']['mae']['unit_macro']['bootstrap_sd'] *= 1.01
        self.reject('bootstrap.*SD')

    def test_shifted_draws_and_consistently_shifted_intervals_are_rejected(self):
        key = 'rwa__rmse__window_pooled'
        self.draws[key] = self.draws[key] + .01
        entry = self.report['components']['rwa']['bootstrap']['rmse']['window_pooled']
        for field in ('ci95', 'ci_familywise_95_bonferroni_8'):
            entry[field] = [value + .01 for value in entry[field]]
        self.reject('distribution')

    def test_permuted_draws_with_identical_summary_are_rejected(self):
        self.draws['bat__mae__unit_macro'] = self.draws['bat__mae__unit_macro'][::-1].copy()
        self.reject('distribution')

    def test_plausible_but_wrong_pvalue_is_rejected(self):
        self.report['components']['bat']['paired_tests']['rmse']['pvalue'] = .123456
        self.reject('paired.*pvalue')

    def test_plausible_but_wrong_holm_adjustment_is_rejected(self):
        self.report['components']['rwa']['paired_tests']['mae']['holm_pvalue_family4'] = .123456
        self.reject('Holm')

    def test_signed_rank_ties_and_normal_tail_have_hand_checked_oracles(self):
        exact = numerical.paired_oracle([-1., -1., -1., 1.])
        self.assertEqual(exact['pvalue'], .625)
        self.assertEqual(exact['statistic'], 2.5)
        self.assertEqual(exact['rank_biserial'], -.5)
        self.assertEqual(exact['standardized_paired_effect_dz'], -.5)
        approximate = numerical.paired_oracle([-1.] * 21)
        self.assertAlmostEqual(approximate['pvalue'], math.erfc(math.sqrt(21. / 2.)), places=17)

    def test_single_unit_and_all_zero_differences_keep_undefined_values(self):
        for candidate, reference, rows in [([0.], [1.], [{'unit_id': 'a'}]),
                ([0., 0.], [0., 0.], [{'unit_id': 'a'}, {'unit_id': 'b'}])]:
            report, draws = artificial_report(candidate, reference, rows)
            numerical.verify_statistics(report, draws)
        bad = copy.deepcopy(report)
        bad['components']['bat']['paired_tests']['rmse']['standardized_paired_effect_dz'] = 0.
        with self.assertRaisesRegex(numerical.EvidenceError, 'paired.*standardized'):
            numerical.verify_statistics(bad, draws)

    def test_large_unit_normal_approximation_matches_registered_output(self):
        rows = [{'unit_id': f'u{i:02}'} for i in range(25)]
        report, draws = artificial_report([.2] * 21 + [.8] * 4, [.5] * 25, rows)
        numerical.verify_statistics(report, draws)

    def test_wrong_seed_and_missing_draw_key_are_rejected(self):
        self.report['components']['bat']['bootstrap_design']['seed'] += 1
        self.reject('seed|design')
        self.report, self.draws = artificial_report()
        self.draws.pop('rwa__mae__unit_macro')
        self.reject('membership')

    def test_nonfinite_draw_is_rejected(self):
        self.draws['bat__rmse__unit_macro'][13] = np.nan
        self.reject('finite|distribution')

    def test_unfinished_chain_does_not_decode_even_a_poisoned_statistics_archive(self):
        with tempfile.TemporaryDirectory(prefix='leo900-numeric-pending-') as directory:
            root = Path(directory)
            fixture = Fixture(root)
            (fixture.runtime / 'controller_terminal.json').unlink()
            archive = fixture.statistics / 'f1_unit_cluster_bootstrap.npz'
            archive.write_bytes(b'THIS MUST NEVER BE DECODED BEFORE TERMINAL')
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in root.rglob('*') if p.is_file()}
            result = numerical.audit(root, root / 'publication.json', anchors=fixture.anchors)
            self.assertEqual(result['status'], 'PENDING_TERMINAL')
            self.assertFalse(result['bootstrap_arrays_decoded'])
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in root.rglob('*') if p.is_file()})

    def test_complete_production_chain_checks_numbers_without_decoding_predictions(self):
        with tempfile.TemporaryDirectory(prefix='leo900-numeric-complete-') as directory:
            fixture = complete_fixture(Path(directory))
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in fixture.root.rglob('*') if p.is_file()}
            with patch.object(numerical.provenance, 'RUN', fixture.root), \
                    patch.object(numerical.provenance, 'ANCHORS', fixture.anchors):
                result = numerical.audit(fixture.root, fixture.root / 'publication.json')
            self.assertEqual(result['status'], 'NUMERICAL_STATISTICS_VERIFIED')
            self.assertTrue(result['bootstrap_arrays_decoded'])
            self.assertFalse(result['final_truth_or_prediction_arrays_decoded'])
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in fixture.root.rglob('*') if p.is_file()})

    def test_rehashed_plausible_ci_passes_structural_auditor_but_fails_numerical_auditor(self):
        with tempfile.TemporaryDirectory(prefix='leo900-numeric-rehashed-ci-') as directory:
            fixture = complete_fixture(Path(directory))
            fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
                d['components']['bat']['bootstrap']['rmse']['window_pooled'].update(
                    ci95=[-.26, -.24], ci_familywise_95_bonferroni_8=[-.27, -.23]))
            fixture.rebind()
            self.assertEqual(fixture.run()['status'], 'EXECUTION_CHAIN_VERIFIED')
            with patch.object(numerical.provenance, 'RUN', fixture.root), \
                    patch.object(numerical.provenance, 'ANCHORS', fixture.anchors):
                with self.assertRaisesRegex(numerical.EvidenceError, 'interval'):
                    numerical.audit(fixture.root, fixture.root / 'publication.json')


if __name__ == '__main__':
    unittest.main(verbosity=2)
