"""Hand-calculated and disposable integration cases; never real final data."""
from __future__ import annotations

import copy
import hashlib
import importlib
import io
import math
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

from test_leo900_terminal_evidence_20261018_r2 import Fixture, ProductionFixture
import leo900_terminal_evidence_20261018_r2 as provenance

try:
    subject = importlib.import_module('leo900_prediction_summary_audit_20261018')
except ModuleNotFoundError as exc:
    if exc.name != 'leo900_prediction_summary_audit_20261018':
        raise
    subject = None


def metrics(rmse, mae, bias, macro, upward, windows=5, units=2):
    return dict(rmse=rmse, mae=mae, bias=bias, unit_macro_rmse=macro,
                rul_upward_fraction=upward, n_windows=windows, n_units=units)


def summary(uid, n, csse, csae, rsse, rsae):
    # Independent scalar fixture arithmetic; no function under test is called.
    value = dict(unit_id=uid, n_windows=n, candidate_sse=csse, candidate_sae=csae,
                 reference_sse=rsse, reference_sae=rsae,
                 candidate_rmse=math.sqrt(csse / n), reference_rmse=math.sqrt(rsse / n),
                 candidate_mae=csae / n, reference_mae=rsae / n)
    for metric in ('rmse', 'mae'):
        c, r = value['candidate_' + metric], value['reference_' + metric]
        value['delta_' + metric] = c - r
        value['relative_change_percent_' + metric] = 100 * (c - r) / r if r else None
    return value


def hand_case():
    # B@2,A@0,B@0,A@1,B@1. Sorting must stay within each unit.
    rows = [dict(unit_id=u, t_end=t) for u, t in [('B', 2), ('A', 0), ('B', 0), ('A', 1), ('B', 1)]]
    candidate = np.array([.25, .5, .5, 0, .75], dtype=np.float32)
    control = np.array([.5, .25, .25, .5, 0], dtype=np.float32)
    alpha = np.ones(5, dtype=np.float32)
    arrays = dict(truth_rul=np.zeros(5, dtype=np.float32), truth_relative=np.zeros(5, dtype=np.float32),
                  candidate=candidate, control=control, alpha=alpha,
                  blended_before_final_projection=candidate.copy(), projected=candidate.copy())
    layout = dict(component='bat', rmax=8., rows=rows, seeds=None,
                  array_dtypes={k: str(v.dtype) for k, v in arrays.items()},
                  array_shapes={k: list(v.shape) for k, v in arrays.items()})
    c = metrics(math.sqrt(14.4), 3.2, 3.2, (math.sqrt(8) + math.sqrt(56/3))/2, 1/3)
    r = metrics(math.sqrt(8), 2.4, 2.4, (math.sqrt(10) + math.sqrt(20/3))/2, 2/3)
    result = dict(n_windows=5, n_units=2, unit_window_counts={'A': 2, 'B': 3},
                  route={'alpha_by_target': {'LEO900': 1.}},
                  metrics=c, candidate_only_metrics=copy.deepcopy(c), control_only_metrics=r)
    stats = dict(physical_unit='cycle', rmax=8., n_windows=5, n_units=2,
                 units=[summary('A', 2, 16., 4., 20., 6.), summary('B', 3, 56., 12., 20., 6.)],
                 metrics={k: copy.deepcopy(result[k]) for k in
                          ('metrics', 'candidate_only_metrics', 'control_only_metrics')},
                 seed_description={'constituents': [], 'independent_repeats': 0})
    return layout, arrays, result, stats


def real_array_fixture(root):
    """Replace *synthetic* NPZ placeholders and rebind the production chain."""
    fixture = ProductionFixture(root)
    receipt = fixture.documents['formal_output_execution_r1/final_receipt.json']
    stats = fixture.documents['formal_statistics_20261018_r1/f1_gate_statistics.json']
    for component in ('bat', 'rwa'):
        entry = receipt['results'][component]
        binding = entry['paired_predictions']
        key = str(fixture.formal.relative_to(root) / binding['layout_path'])
        layout = fixture.documents[key]
        n = len(layout['rows'])
        candidate = np.full(n, 1/256, dtype=np.float32)
        control = np.full(n, 1/128, dtype=np.float32)
        alpha = np.full(n, 1e-5, dtype=np.float32)
        blend = alpha * candidate + (1-alpha) * control
        arrays = dict(truth_rul=np.zeros(n, dtype=np.float32), truth_relative=np.zeros(n, dtype=np.float32),
                      candidate=candidate, control=control, alpha=alpha,
                      blended_before_final_projection=blend, projected=blend.copy(),
                      seed_raw_predictions=np.tile(candidate, (3, 1)))
        archive = fixture.formal / binding['arrays_path']
        with archive.open('wb') as handle:
            np.savez_compressed(handle, **arrays)
        layout.update(arrays_sha256=fixture.digest(archive),
                      array_dtypes={k: str(v.dtype) for k, v in arrays.items()},
                      array_shapes={k: list(v.shape) for k, v in arrays.items()})
        fixture.put(key, layout)
        binding.update(arrays_sha256=layout['arrays_sha256'], layout_sha256=fixture.digest(fixture.formal / binding['layout_path']))
        observed, baseline, raw = float(blend[0])*100, 100/128, 100/256
        def uniform(value):
            return metrics(value, value, value, value, 0., n, 48)
        entry.update(metrics=uniform(observed), candidate_only_metrics=uniform(raw), control_only_metrics=uniform(baseline))
        component_stats = stats['components'][component]
        component_stats.update(prediction_binding=copy.deepcopy(binding),
            metrics={k: copy.deepcopy(entry[k]) for k in ('metrics', 'candidate_only_metrics', 'control_only_metrics')},
            units=[summary(uid, 2, observed**2*2, observed*2, baseline**2*2, baseline*2)
                   for uid in sorted(entry['unit_window_counts'])],
            seed_description={'independent_repeats': 0,
                              'constituents': [{'seed': seed, 'raw_metrics': uniform(raw)} for seed in (17, 42, 73)]})
        for metric in ('rmse', 'mae'):
            for estimand in ('window_pooled', 'unit_macro'):
                point = component_stats['bootstrap'][metric][estimand]
                delta = observed - baseline
                point.update(candidate_point=observed, reference_point=baseline, point_delta=delta,
                             relative_change_percent=100*delta/baseline,
                             ci95=[delta-.02, delta+.02], ci_familywise_95_bonferroni_8=[delta-.03, delta+.03])
    fixture.put('formal_output_execution_r1/final_receipt.json', receipt)
    gate = fixture.documents['formal_output_execution_r1/same_partition_performance_gate.json']
    comparison = provenance.gate_calculation(receipt['results'])
    gate['comparison'].update(comparison)
    gate['metrics'] = {c: {'candidate_blend': receipt['results'][c]['metrics'],
                          'same_partition_reference': receipt['results'][c]['control_only_metrics']} for c in ('bat', 'rwa')}
    stats['gate'] = comparison
    fixture.put('formal_output_execution_r1/same_partition_performance_gate.json', gate)
    fixture.put('formal_statistics_20261018_r1/f1_gate_statistics.json', stats)
    fixture.write_csv()
    fixture.rebind()
    return fixture


class PredictionSummaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(subject, 'independent prediction-to-summary auditor is missing')
        self.layout, self.arrays, self.result, self.stats = hand_case()

    def verify(self):
        return subject.verify_component(self.layout, self.arrays, self.result, self.stats)

    def test_interleaved_unequal_units_match_hand_calculated_physical_errors(self):
        report = self.verify()
        self.assertEqual(report['n_windows'], 5)
        self.assertEqual(report['units'][0]['candidate_sse'], 16.)
        self.assertEqual(report['units'][1]['candidate_sae'], 12.)
        self.assertEqual(report['metrics']['metrics']['rul_upward_fraction'], 1/3)
        self.assertEqual(report['metrics']['control_only_metrics']['mae'], 2.4)

    def test_internally_consistent_but_wrong_unit_summary_is_rejected(self):
        self.stats['units'][0] = summary('A', 2, 18., 6., 20., 6.)
        with self.assertRaisesRegex(subject.EvidenceError, 'unit.*candidate_sse'):
            self.verify()

    def test_relabelled_rows_with_identical_counts_are_rejected(self):
        self.layout['rows'][0]['unit_id'], self.layout['rows'][1]['unit_id'] = 'A', 'B'
        with self.assertRaisesRegex(subject.EvidenceError, 'unit'):
            self.verify()

    def test_truth_division_preserves_float32_instead_of_upcasting(self):
        self.arrays['truth_rul'][:] = 1.
        self.layout['rmax'] = 3.
        self.stats['rmax'] = 3.
        self.arrays['truth_relative'] = self.arrays['truth_rul'].astype(np.float64) / 3.
        self.layout['array_dtypes']['truth_relative'] = 'float64'
        with self.assertRaisesRegex(subject.EvidenceError, 'label division'):
            self.verify()

    def test_alpha_must_match_frozen_source_route(self):
        self.arrays['alpha'][:] = 0.
        self.arrays['blended_before_final_projection'] = self.arrays['control'].copy()
        with self.assertRaisesRegex(subject.EvidenceError, 'alpha.*route'):
            self.verify()

    def test_blend_must_use_saved_float32_predictions(self):
        self.arrays['blended_before_final_projection'][0] += .125
        with self.assertRaisesRegex(subject.EvidenceError, 'blend'):
            self.verify()

    def test_shape_and_nonfinite_arrays_are_rejected(self):
        self.arrays['projected'] = self.arrays['projected'][:, None]
        with self.assertRaisesRegex(subject.EvidenceError, 'shape'):
            self.verify()
        self.layout, self.arrays, self.result, self.stats = hand_case()
        self.arrays['projected'][0] = np.nan
        with self.assertRaisesRegex(subject.EvidenceError, 'finite'):
            self.verify()

    def test_wrong_physical_scale_is_rejected(self):
        self.stats['rmax'] = 24.
        with self.assertRaisesRegex(subject.EvidenceError, 'rmax'):
            self.verify()

    def test_duplicate_npz_members_are_rejected_before_dictionary_conversion(self):
        with tempfile.TemporaryDirectory(prefix='leo900-duplicate-array-') as directory:
            path = Path(directory) / 'artificial.npz'
            stream = io.BytesIO()
            np.save(stream, np.zeros(1, dtype=np.float32))
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(path, 'w') as archive:
                    archive.writestr('projected.npy', stream.getvalue())
                    archive.writestr('projected.npy', stream.getvalue())
            with self.assertRaisesRegex(subject.EvidenceError, 'duplicate'):
                subject.load_arrays(path)

    def test_pending_terminal_does_not_decode_poisoned_prediction_archive(self):
        with tempfile.TemporaryDirectory(prefix='leo900-prediction-pending-') as directory:
            root = Path(directory)
            fixture = Fixture(root)
            (fixture.runtime / 'controller_terminal.json').unlink()
            (fixture.formal / 'final_bat_paired_predictions.npz').write_bytes(b'MUST NOT DECODE')
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            report = subject.audit(root, root / 'publication.json', anchors=fixture.anchors)
            self.assertEqual(report['status'], 'PENDING_TERMINAL')
            self.assertFalse(report['final_truth_or_prediction_arrays_decoded'])
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()})

    def test_complete_production_chain_verifies_saved_predictions_without_writes(self):
        with tempfile.TemporaryDirectory(prefix='leo900-prediction-complete-') as directory:
            fixture = real_array_fixture(Path(directory))
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.root.rglob('*') if p.is_file()}
            with patch.object(provenance, 'RUN', fixture.root), patch.object(provenance, 'ANCHORS', fixture.anchors):
                report = subject.audit(fixture.root, fixture.root / 'publication.json')
            self.assertEqual(report['status'], 'PREDICTION_SUMMARIES_VERIFIED')
            self.assertTrue(report['final_truth_or_prediction_arrays_decoded'])
            self.assertFalse(report['f1_closed'])
            self.assertFalse(report['models_or_evaluator_invoked'])
            self.assertEqual(report['components']['bat']['n_units'], 48)
            self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fixture.root.rglob('*') if p.is_file()})

    def test_rehashed_seed_metric_contradiction_is_detected(self):
        with tempfile.TemporaryDirectory(prefix='leo900-prediction-seed-') as directory:
            fixture = real_array_fixture(Path(directory))
            fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
                d['components']['bat']['seed_description']['constituents'][0]['raw_metrics'].update(mae=77.))
            fixture.rebind()
            with patch.object(provenance, 'RUN', fixture.root), patch.object(provenance, 'ANCHORS', fixture.anchors):
                with self.assertRaisesRegex(subject.EvidenceError, 'seed.*mae'):
                    subject.audit(fixture.root, fixture.root / 'publication.json')


if __name__ == '__main__':
    unittest.main(verbosity=2)
