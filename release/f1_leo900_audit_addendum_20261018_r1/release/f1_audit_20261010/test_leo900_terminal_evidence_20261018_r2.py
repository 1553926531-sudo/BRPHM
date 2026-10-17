"""Adversarial synthetic provenance fixtures; no Rack or real data access."""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import leo900_terminal_evidence_20261018_r2 as audit


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class Fixture:
    def __init__(self, root, *, positive=True):
        self.root = root
        self.formal = root / "formal_output_execution_r1"
        self.runtime = root / "final_continuation_runtime_20261018_r1"
        self.statistics = root / "formal_statistics_20261018_r1"
        self.seal = root / "metadata_seal_execution_20261018_r1"
        self.project = root / "evaluation_project_execution_r1"
        self.documents = {}
        self.files = {}
        self.times = {"publication": "2026-10-18T00:01:00Z", "seal": "2026-10-18T00:04:00Z",
                      "freeze": "2026-10-18T00:06:00Z", "claim": "2026-10-18T00:08:00Z",
                      "access": "2026-10-18T00:08:01Z", "final": "2026-10-18T00:09:00Z",
                      "statistics": "2026-10-18T00:11:00Z"}
        rows = []
        for index in range(96):
            component = "bat" if index < 48 else "rwa"
            rows.append({"sample_id": f"{component.upper()}_LEO900_B{(index % 48 // 16) * 30:02}_S{1300+index}",
                         "product_line": component, "orbit": "LEO900", "beta_deg": (index % 48 // 16) * 30,
                         "serial": 1300 + index, "seed": 894000 + index})
        self.plan = {"rows": rows, "unit_counts": {"bat": 48, "rwa": 48}}
        self.put("evidence/partition_plan.json", self.plan)
        self.routes = {c: {"alpha_by_target": {"LEO500": 1e-5, "LEO550": 1e-5, "LEO700": 1e-5, "LEO900": 1e-5},
                           "route_id": c + "_fixed"} for c in ("bat", "rwa")}
        self.candidate = {"method_id": "synthetic-fixed", "components": {c: {"selected_route": r} for c, r in self.routes.items()}}
        self.put("evidence/formal_candidate_receipt.json", self.candidate)
        self.raw("evaluation_project_execution_r1/source.bin", b"synthetic training bytes")
        source_record = self.record(self.project / "source.bin")
        protocol_inputs = [self.record(root / name) for name in ("evidence/partition_plan.json", "evidence/formal_candidate_receipt.json")]
        protocol_inputs.append(source_record)
        self.stages = [{"name": name, "command": ["synthetic-interpreter", name]} for name in ("seal", "freeze", "evaluate", "statistics")]
        self.fixed_plan = {"run_root": str(root), "runtime": str(self.runtime), "guard": str(root / "leo900_final_label_access_guard.json"),
                           "stages": self.stages, "inputs": {}, "production": True}
        protocol = {"fixed_plan": copy.deepcopy(self.fixed_plan), "input_files": protocol_inputs,
                    "created_utc": "2026-10-18T00:00:00Z"}
        self.put("final_continuation_support_20261018_r1/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json", protocol)
        actual_plan = copy.deepcopy(self.fixed_plan)
        actual_plan["inputs"] = {r["path"]: r["sha256"] for r in protocol_inputs}
        # production_plan also binds its protocol, beyond the 156 registered inputs.
        protocol_path = root / audit.PROTOCOL
        actual_plan["inputs"][str(protocol_path)] = self.digest(protocol_path)
        self.put("final_continuation_runtime_20261018_r1/controller_plan.json", actual_plan)
        self.put("publication.json", {"status": "PUBLISHED_AND_READBACK_VERIFIED", "repository": "https://github.com/1553926531-sudo/BRPHM",
            "commit": "a" * 40, "ended_utc": self.times["publication"], "api_ref_response_headers": {"Date": "Sun, 18 Oct 2026 00:00:59 GMT"},
            "package_manifest_sha256": "b" * 64, "api_blob_files_verified": 41,
            "independent_local_tree_and_commit_match": True,
            "files": {"F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json": self.digest(root / "final_continuation_support_20261018_r1/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json"),
                      **{"registered_inputs/" + p.relative_to(root).as_posix(): self.digest(p) for p in
                         [root / "evidence/partition_plan.json", root / "evidence/formal_candidate_receipt.json"]}}})
        sealed_rows = []
        for row in rows:
            path = root / "project/generated" / row["product_line"] / (row["sample_id"] + ".mat")
            self.raw(path.relative_to(root), b"artificial metadata-only fixture " + row["sample_id"].encode())
            sealed_rows.append({**row, "raw_path": str(path), "sha256": self.digest(path), "size": path.stat().st_size})
        self.put("metadata_seal_execution_20261018_r1/partition_manifest.json", {**self.plan, "rows": sealed_rows,
            "created_utc": self.times["seal"], "semantic_labels_read": False, "final_label_access": False})
        self.put("metadata_seal_execution_20261018_r1/seal_receipt.json", {"status": "PASS", "unit_counts": self.plan["unit_counts"],
            "partition_sha256": self.digest(self.seal / "partition_manifest.json"), "semantic_labels_read": False,
            "final_label_access": False, "created_utc": self.times["seal"]})
        self.put("formal_output_execution_r1/freeze_manifest.json", {"created_utc": self.times["freeze"],
            "candidate": {"method_id": "synthetic-fixed", "selected_routes": self.routes},
            "final_partition": {"manifest": self.record(self.seal / "partition_manifest.json"), "raw_files": sealed_rows, "n_units": self.plan["unit_counts"]},
            "dependencies": [source_record], "visible_information_before_freeze": {"candidate_history": {
                "leo800_influenced_candidate_revision": True, "leo800_status": "development_or_diagnostic_only"}}})
        self.put("formal_output_execution_r1/selection_decision.json", {"freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"), "selected_routes": self.routes})
        self.put("leo900_final_label_access_guard.json", {"created_utc": self.times["claim"], "output": str(self.formal),
            "freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"), "partition_manifest_sha256": self.digest(self.seal / "partition_manifest.json")})
        guard_record = self.record(root / "leo900_final_label_access_guard.json")
        results = {}
        for c in ("bat", "rwa"):
            metrics = {"rmse": 0.9 if positive else 1.1, "mae": 0.5, "n_units": 48, "n_windows": 96}
            baseline = {**metrics, "rmse": 1.0}
            results[c] = {"route": self.routes[c], "n_units": 48, "n_windows": 96,
                          "unit_window_counts": {r["sample_id"]: 2 for r in rows if r["product_line"] == c},
                          "metrics": metrics, "control_only_metrics": baseline}
        self.put("formal_output_execution_r1/final_receipt.json", {"created_utc": self.times["final"], "results": results,
            "freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"),
            "selection_decision_sha256": self.digest(self.formal / "selection_decision.json"),
            "candidate_id": "synthetic-fixed", "global_label_access_guard": guard_record,
            "training": {"holdout_used_for_training_or_selection": False},
            "holdout": {"manifest_sha256": self.digest(self.seal / "partition_manifest.json"), "units": self.plan["unit_counts"]}})
        self.comparison = {"passes": positive, "strict_gain": positive, "regressions": [] if positive else ["bat.rmse", "rwa.rmse"],
            "tolerance": 1e-12, "deltas_candidate_minus_same_partition_reference": {
                c: {"rmse": results[c]["metrics"]["rmse"] - 1.0, "mae": 0.0} for c in ("bat", "rwa")}}
        self.put("formal_output_execution_r1/same_partition_performance_gate.json", {"comparison": {
            **self.comparison,
            "rule": "both components must be non-inferior on RMSE and MAE to the same-partition projected frozen HGB/MLP reference, with at least one strict gain"},
            "final_receipt_sha256": self.digest(self.formal / "final_receipt.json"),
            "freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"),
            "partition_manifest_sha256": self.digest(self.seal / "partition_manifest.json"), "partition_unit_counts": self.plan["unit_counts"],
            "metrics": {c: {"candidate_blend": v["metrics"], "same_partition_reference": v["control_only_metrics"]} for c, v in results.items()}})
        bootstrap = {m: {e: {"ci95": [-0.2, 0.01], "ci_familywise_95_bonferroni_8": [-0.3, 0.1],
                            "point_delta": -0.1, "relative_change_percent": -10.} for e in ("window_pooled", "unit_macro")} for m in ("rmse", "mae")}
        self.put("formal_statistics_20261018_r1/f1_gate_statistics.json", {"created_utc": self.times["statistics"], "gate": self.comparison,
            "inputs": {name: self.digest(self.formal / name) for name in ("final_receipt.json", "same_partition_performance_gate.json", "freeze_manifest.json", "selection_decision.json")},
            "components": {c: {"n_units": 48, "n_windows": 96, "units": [{"unit_id": r["sample_id"], "n_windows": 2} for r in rows if r["product_line"] == c],
                "bootstrap_design": {"cluster": "unit_id", "paired": True, "all_unit_windows_retained": True, "seed": 20261018 + i, "repetitions": 20000},
                "seed_description": {"independent_repeats": 0}, "bootstrap": bootstrap,
                "metrics": {"metrics": results[c]["metrics"], "control_only_metrics": results[c]["control_only_metrics"]}}
                for i, c in enumerate(("bat", "rwa"))}})
        self.put("formal_statistics_20261018_r1/statistics_receipt.json", {"status": "PASS", "gate_passes": positive,
            "report_sha256": self.digest(self.statistics / "f1_gate_statistics.json")})
        self.formal_events = [
            ("preflight_recorded", "2026-10-18T00:05:59Z", {"holdout_label_read": False}),
            ("candidate_frozen", "2026-10-18T00:06:01Z", {"freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"), "selection_decision_sha256": self.digest(self.formal / "selection_decision.json"), "semantic_final_label_read": False}),
            ("final_label_access_started", self.times["access"], {"freeze_manifest_sha256": self.digest(self.formal / "freeze_manifest.json"), "global_label_access_guard": guard_record, "candidate_or_route_mutation_allowed": False}),
            ("final_evaluation_completed", "2026-10-18T00:09:01Z", {"final_receipt_sha256": self.digest(self.formal / "final_receipt.json")}),
            ("same_partition_reference_gate_completed", "2026-10-18T00:09:02Z", {"performance_gate_sha256": self.digest(self.formal / "same_partition_performance_gate.json"), "final_receipt_sha256": self.digest(self.formal / "final_receipt.json"), "gate_passed": positive})]
        self.events(self.formal / "events", self.formal_events, hashed_names=True)
        stage_rows = []
        control_events = [("controller_started", "2026-10-18T00:02:00Z", {"plan": self.record(self.runtime / "controller_plan.json")})]
        for index, spec in enumerate(self.stages):
            start_minute, end_minute = ((3, 4), (5, 6), (7, 9), (10, 11))[index]
            start = f"2026-10-18T00:{start_minute:02}:00Z"
            end = f"2026-10-18T00:{end_minute:02}:30Z"
            row = {**spec, "started_utc": start, "ended_utc": end, "exit_code": 0}
            stage_rows.append(row)
            control_events.extend([("stage_started", start, {**spec, "started_utc": start}),
                                   ("stage_exited", end, row), ("stage_artifacts_verified", end, {"stage": spec["name"], "artifacts": []})])
        self.put("final_continuation_runtime_20261018_r1/controller_terminal.json", {"state": "EVALUATION_AND_STATISTICS_COMPLETED",
            "started_utc": "2026-10-18T00:02:00Z", "ended_utc": "2026-10-18T00:12:00Z", "formal_gate_passes": positive, "stages": stage_rows})
        control_events.append(("controller_completed", "2026-10-18T00:12:00Z", self.documents["final_continuation_runtime_20261018_r1/controller_terminal.json"]))
        last = self.events(self.runtime / "events", control_events)
        self.documents["final_continuation_runtime_20261018_r1/controller_terminal.json"]["last_event_sha256"] = last
        self.put("final_continuation_runtime_20261018_r1/controller_terminal.json", self.documents["final_continuation_runtime_20261018_r1/controller_terminal.json"])
        self.anchors = {"protocol": self.digest(root / "final_continuation_support_20261018_r1/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json"),
                        "publication": self.digest(root / "publication.json"), "manifest": "b" * 64, "commit": "a" * 40}

    def raw(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def put(self, name, document):
        self.documents[str(name)] = copy.deepcopy(document)
        self.raw(name, encoded(document))

    def digest(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def record(self, path):
        return {"path": str(path), "sha256": self.digest(path), "size": path.stat().st_size}

    def events(self, folder, events, hashed_names=False):
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.glob("*.json"):
            path.unlink()  # synthetic fixture directory only
        previous = None
        for index, (kind, date, payload) in enumerate(events, 1):
            document = {"sequence": index, "previous_event_sha256": previous, "event_type": kind, "created_utc": date, "payload": payload}
            data = encoded(document)
            previous = hashlib.sha256(data).hexdigest()
            name = f"{index:04}_{kind}" + ("_" + previous[:16] if hashed_names else "") + ".json"
            (folder / name).write_bytes(data)
        return previous

    def run(self):
        return audit.audit(self.root, self.root / "publication.json", anchors=self.anchors)

    def mutate(self, name, modify):
        value = copy.deepcopy(self.documents[name])
        modify(value)
        self.put(name, value)


class ProductionFixture(Fixture):
    """Same production-only code paths, exclusively under a disposable root.

    Fake MAT/PT/NPZ bytes deliberately cannot be decoded as those formats.
    Rebinding hash edges lets tests expose semantic contradictions after all
    checksums/event chains have been consistently rebuilt.
    """
    def __init__(self, root):
        super().__init__(root)
        publication = self.documents['publication.json']
        publication.update(server_repository_identity={'full_name': '1553926531-sudo/BRPHM'},
                           origin_identity_verified=True)
        for index in range(41 - len(publication['files'])):
            publication['files'][f'synthetic_registered_member_{index}'] = '0' * 64
        self.put('publication.json', publication)
        self.anchors['publication'] = self.digest(root / 'publication.json')
        completion = {'success_count': 96, 'skip_count': 0, 'failure_count': 0,
                      'start_utc': '2026-10-17T11:01:20Z', 'end_utc': '2026-10-18T00:02:30Z'}
        self.raw('simulation_logs/completion.txt', b'synthetic metadata only')
        self.mutate('metadata_seal_execution_20261018_r1/partition_manifest.json', lambda d: d.update(
            completion_metadata=completion, bound_artifacts=[self.record(root / 'simulation_logs/completion.txt')]))
        candidate = copy.deepcopy(self.candidate)
        candidate['formal_protocol'] = {
            'loss': 'unit-balanced L1 on normalized RUL',
            'source_standardization': 'source-window channel mean/std',
            'residual_calibration': 'equal-unit median source residuals, shrink=0.25',
            'ensemble': 'median of three fixed seeds',
            'candidate_receipt_sha256': self.digest(root / 'evidence/formal_candidate_receipt.json'),
            'unseen_orbit': 'LEO900', 'selection_uses_unseen_labels': False}
        candidate['derivation'] = {
            'schema': 'brphm-f1-leo900-plain-l1-candidate-snapshot-v1',
            'base_candidate_receipt_sha256': candidate['formal_protocol']['candidate_receipt_sha256'],
            'unseen_orbit': 'LEO900',
            'alpha_rule': 'preserve the hash-bound source-selected routes and the fixed LEO900 source-protocol alpha floor',
            'alpha_value_by_component': {'bat': 1e-5, 'rwa': 1e-5},
            'selection_uses_unseen_labels': False}
        self.put('formal_output_execution_r1.candidate_snapshot.json', candidate)
        snapshot = self.record(root / 'formal_output_execution_r1.candidate_snapshot.json')
        freeze = self.documents['formal_output_execution_r1/freeze_manifest.json']
        freeze['candidate']['candidate_receipt'] = snapshot
        freeze.update(candidate_snapshot=snapshot, candidate_snapshot_sha256=snapshot['sha256'])
        for key in ('dependency_closure_registration', 'channel_policy_amendment', 'execution_amendment'):
            self.put(f'artificial_support/{key}.json', {'synthetic': key})
            freeze[key] = self.record(root / f'artificial_support/{key}.json')
        self.put('formal_output_execution_r1/freeze_manifest.json', freeze)
        receipt = self.documents['formal_output_execution_r1/final_receipt.json']
        stats = self.documents['formal_statistics_20261018_r1/f1_gate_statistics.json']
        # Base Fixture intentionally shares its compact bootstrap template. The
        # production structure has separate component/metric estimates.
        for c in audit.COMPONENTS:
            entry = receipt['results'][c]
            units = [r['sample_id'] for r in self.plan['rows'] if r['product_line'] == c]
            rows = [{'unit_id': u, 't_end': float(t)} for u in units for t in (0, 1)]
            entry['unit_window_counts'] = {u: 2 for u in units}
            tensor = f'final_{c}_payload.pt'
            arrays = f'final_{c}_paired_predictions.npz'
            layout_name = f'final_{c}_paired_predictions.json'
            self.raw(self.formal.relative_to(root) / tensor, b'not a tensor: ' + c.encode())
            self.raw(self.formal.relative_to(root) / arrays, b'not prediction arrays: ' + c.encode())
            entry.update(payload_path=tensor, payload_sha256=self.digest(self.formal / tensor),
                         training_diagnostics={'target_labels_used_in_training_or_correction': False})
            names = ('truth_rul', 'truth_relative', 'candidate', 'control', 'alpha',
                     'blended_before_final_projection', 'projected', 'seed_raw_predictions')
            layout = {'schema': 'brphm-f1-original-pass-paired-predictions-v1', 'component': c, 'rows': rows,
                      'rows_sha256': hashlib.sha256(audit.json_bytes(rows)).hexdigest(),
                      'arrays_path': arrays, 'arrays_sha256': self.digest(self.formal / arrays),
                      'payload_sha256': entry['payload_sha256'], 'rmax': 100., 'seeds': [17, 42, 73],
                      'array_dtypes': {n: 'float32' for n in names},
                      'array_shapes': {n: [3, 96] if n == 'seed_raw_predictions' else [96] for n in names}}
            self.put(self.formal.relative_to(root) / layout_name, layout)
            entry['paired_predictions'] = {
                'arrays_path': arrays, 'arrays_sha256': layout['arrays_sha256'],
                'layout_path': layout_name, 'layout_sha256': self.digest(self.formal / layout_name),
                'rows_sha256': layout['rows_sha256'], 'n_rows': 96}
            component = stats['components'][c]
            component.update(physical_unit='cycle' if c == 'bat' else 'day', rmax=100.,
                             prediction_binding=copy.deepcopy(entry['paired_predictions']))
            component['units'] = []
            for u in units:
                summary = {'unit_id': u, 'n_windows': 2}
                for prefix, values in (('candidate', entry['metrics']), ('reference', entry['control_only_metrics'])):
                    summary.update({f'{prefix}_sse': values['rmse'] ** 2 * 2,
                                    f'{prefix}_sae': values['mae'] * 2,
                                    f'{prefix}_rmse': values['rmse'], f'{prefix}_mae': values['mae']})
                for metric in ('rmse', 'mae'):
                    observed, baseline = summary[f'candidate_{metric}'], summary[f'reference_{metric}']
                    summary[f'delta_{metric}'] = observed - baseline
                    summary[f'relative_change_percent_{metric}'] = 100. * (observed - baseline) / baseline
                component['units'].append(summary)
            component['bootstrap'] = {}
            for metric in ('rmse', 'mae'):
                component['bootstrap'][metric] = {}
                for estimand in ('window_pooled', 'unit_macro'):
                    observed, baseline = entry['metrics'][metric], entry['control_only_metrics'][metric]
                    delta = observed - baseline
                    component['bootstrap'][metric][estimand] = {
                        'candidate_point': observed, 'reference_point': baseline, 'point_delta': delta,
                        'relative_change_percent': 100. * delta / baseline,
                        'relative_change_status': 'defined: 100 * paired delta / reference error',
                        'bootstrap_sd': 0.01, 'ci95': [delta - .02, delta + .02],
                        'ci_familywise_95_bonferroni_8': [delta - .03, delta + .03]}
        self.put('formal_output_execution_r1/final_receipt.json', receipt)
        self.raw('formal_statistics_20261018_r1/f1_unit_cluster_bootstrap.npz', b'not bootstrap arrays')
        stats.update(bootstrap_distributions={
            **self.record(self.statistics / 'f1_unit_cluster_bootstrap.npz'),
            'shapes': {f'{c}__{m}__{e}': [20000] for c in audit.COMPONENTS for m in ('rmse', 'mae')
                       for e in ('window_pooled', 'unit_macro')}},
            verification={'gate_matches_original': True, 'metrics_exactly_match_original': True,
                          'models_rerun': False, 'tensors_or_mat_loaded': False})
        self.put('formal_statistics_20261018_r1/f1_gate_statistics.json', stats)
        self.write_csv()
        self.rebind()

    def write_csv(self):
        fields = ('component', 'metric', 'physical_unit', 'n_units', 'n_windows', 'candidate', 'candidate_hex',
                  'reference', 'reference_hex', 'delta', 'delta_hex', 'reference_plus_tolerance',
                  'reference_plus_tolerance_hex', 'reference_minus_tolerance', 'reference_minus_tolerance_hex',
                  'regression', 'strict_gain')
        text = io.StringIO(newline='')
        writer = csv.DictWriter(text, fieldnames=fields)
        writer.writeheader()
        for c in audit.COMPONENTS:
            entry = self.documents['formal_output_execution_r1/final_receipt.json']['results'][c]
            for metric in ('rmse', 'mae'):
                observed, baseline = entry['metrics'][metric], entry['control_only_metrics'][metric]
                row = {'component': c, 'metric': metric, 'physical_unit': 'cycle' if c == 'bat' else 'day',
                       'n_units': entry['n_units'], 'n_windows': entry['n_windows'],
                       'regression': observed > baseline + 1e-12,
                       'strict_gain': observed < baseline - 1e-12}
                for name, value in (('candidate', observed), ('reference', baseline), ('delta', observed - baseline),
                                    ('reference_plus_tolerance', baseline + 1e-12),
                                    ('reference_minus_tolerance', baseline - 1e-12)):
                    row[name], row[name + '_hex'] = format(value, '.17g'), value.hex()
                writer.writerow(row)
        self.raw('formal_statistics_20261018_r1/f1_full_precision_gate.csv', text.getvalue().encode())

    def set_evaluated_unit_counts(self, component, counts):
        """Synthetic positive-window subset, with every receipt/layout edge bound.

        All synthetic units have the same errors, so changing their membership
        and lengths preserves the independently specified point metrics.
        """
        receipt = self.documents['formal_output_execution_r1/final_receipt.json']
        entry = receipt['results'][component]
        n_windows = sum(counts.values())
        entry.update(n_units=len(counts), n_windows=n_windows, unit_window_counts=dict(counts))
        for metric_set in ('metrics', 'control_only_metrics'):
            entry[metric_set].update(n_units=len(counts), n_windows=n_windows)
        paired = entry['paired_predictions']
        layout_key = self.formal.relative_to(self.root) / paired['layout_path']
        layout = self.documents[str(layout_key)]
        layout['rows'] = [{'unit_id': uid, 't_end': float(i)}
                          for uid, count in counts.items() for i in range(count)]
        layout['rows_sha256'] = hashlib.sha256(encoded(layout['rows'])).hexdigest()
        layout['array_shapes'] = {name: [3, n_windows] if name == 'seed_raw_predictions' else [n_windows]
                                  for name in layout['array_shapes']}
        self.put(layout_key, layout)
        paired.update(layout_sha256=self.digest(self.formal / paired['layout_path']),
                      rows_sha256=layout['rows_sha256'], n_rows=n_windows)
        self.put('formal_output_execution_r1/final_receipt.json', receipt)
        stats = self.documents['formal_statistics_20261018_r1/f1_gate_statistics.json']
        summaries = []
        template = stats['components'][component]['units'][0]
        for uid, count in counts.items():
            unit = copy.deepcopy(template)
            unit.update(unit_id=uid, n_windows=count)
            for prefix, values in (('candidate', entry['metrics']), ('reference', entry['control_only_metrics'])):
                unit.update({prefix + '_sse': values['rmse'] ** 2 * count,
                             prefix + '_sae': values['mae'] * count})
            summaries.append(unit)
        stats['components'][component].update(
            n_units=len(counts), n_windows=n_windows, units=summaries,
            prediction_binding=copy.deepcopy(paired),
            metrics={name: copy.deepcopy(entry[name]) for name in ('metrics', 'control_only_metrics')})
        self.put('formal_statistics_20261018_r1/f1_gate_statistics.json', stats)
        self.mutate('formal_output_execution_r1/same_partition_performance_gate.json', lambda d:
            d['metrics'].update({component: {'candidate_blend': entry['metrics'],
                                            'same_partition_reference': entry['control_only_metrics']}}))
        self.write_csv()
        self.rebind()

    def rebind(self):
        """Recompute hash edges only; retain the semantic payload being tested."""
        r = self.root
        for name, field, target in (
            ('metadata_seal_execution_20261018_r1/seal_receipt.json', 'partition_sha256', self.seal / 'partition_manifest.json'),
            ('formal_output_execution_r1/selection_decision.json', 'freeze_manifest_sha256', self.formal / 'freeze_manifest.json')):
            if name.startswith('formal_'):
                freeze = self.documents['formal_output_execution_r1/freeze_manifest.json']
                freeze['final_partition']['manifest'] = self.record(self.seal / 'partition_manifest.json')
                freeze['candidate_snapshot'] = self.record(r / 'formal_output_execution_r1.candidate_snapshot.json')
                freeze['candidate_snapshot_sha256'] = freeze['candidate_snapshot']['sha256']
                freeze['candidate']['candidate_receipt'] = copy.deepcopy(freeze['candidate_snapshot'])
                self.put('formal_output_execution_r1/freeze_manifest.json', freeze)
            self.mutate(name, lambda d, field=field, target=target: d.update({field: self.digest(target)}))
        freeze_hash = self.digest(self.formal / 'freeze_manifest.json')
        partition_hash = self.digest(self.seal / 'partition_manifest.json')
        self.mutate('leo900_final_label_access_guard.json', lambda d: d.update(
            freeze_manifest_sha256=freeze_hash, partition_manifest_sha256=partition_hash))
        guard = self.record(r / 'leo900_final_label_access_guard.json')
        receipt = self.documents['formal_output_execution_r1/final_receipt.json']
        receipt.update(freeze_manifest_sha256=freeze_hash,
                       selection_decision_sha256=self.digest(self.formal / 'selection_decision.json'),
                       global_label_access_guard=guard)
        receipt['holdout']['manifest_sha256'] = partition_hash
        self.put('formal_output_execution_r1/final_receipt.json', receipt)
        gate = self.documents['formal_output_execution_r1/same_partition_performance_gate.json']
        gate.update(final_receipt_sha256=self.digest(self.formal / 'final_receipt.json'),
                    freeze_manifest_sha256=freeze_hash, partition_manifest_sha256=partition_hash)
        self.put('formal_output_execution_r1/same_partition_performance_gate.json', gate)
        stats = self.documents['formal_statistics_20261018_r1/f1_gate_statistics.json']
        stats['inputs'] = {n: self.digest(self.formal / n) for n in
                           ('final_receipt.json', 'freeze_manifest.json', 'selection_decision.json', 'same_partition_performance_gate.json')}
        stats['full_precision_csv'] = self.record(self.statistics / 'f1_full_precision_gate.csv')
        self.put('formal_statistics_20261018_r1/f1_gate_statistics.json', stats)
        self.mutate('formal_statistics_20261018_r1/statistics_receipt.json', lambda d: d.update(
            report_sha256=self.digest(self.statistics / 'f1_gate_statistics.json')))
        events = copy.deepcopy(self.formal_events)
        events[1][2].update(freeze_manifest_sha256=freeze_hash,
                            selection_decision_sha256=self.digest(self.formal / 'selection_decision.json'))
        events[2][2].update(freeze_manifest_sha256=freeze_hash, global_label_access_guard=guard)
        events[3][2]['final_receipt_sha256'] = self.digest(self.formal / 'final_receipt.json')
        events[4][2].update(final_receipt_sha256=self.digest(self.formal / 'final_receipt.json'),
                            performance_gate_sha256=self.digest(self.formal / 'same_partition_performance_gate.json'))
        self.events(self.formal / 'events', events, hashed_names=True)
        terminal = self.documents['final_continuation_runtime_20261018_r1/controller_terminal.json']
        terminal.pop('last_event_sha256', None)
        control = [('controller_started', terminal['started_utc'], {'plan': self.record(self.runtime / 'controller_plan.json')})]
        artifacts = {'seal': [self.seal / 'seal_receipt.json'], 'freeze': [self.formal / 'freeze_manifest.json'],
                     'evaluate': [self.formal / 'same_partition_performance_gate.json', self.formal / 'final_receipt.json',
                                  r / 'leo900_final_label_access_guard.json'],
                     'statistics': [self.statistics / 'statistics_receipt.json']}
        for row in terminal['stages']:
            name = row['name']
            row['artifacts'] = [self.record(p) for p in artifacts[name]]
            for suffix in ('stdout', 'stderr'):
                self.raw(self.runtime.relative_to(r) / (name + '.' + suffix + '.log'), b'')
                row[suffix] = self.record(self.runtime / (name + '.' + suffix + '.log'))
            control.extend([('stage_started', row['started_utc'], {'name': name, 'command': row['command'], 'started_utc': row['started_utc']}),
                            ('stage_exited', row['ended_utc'], {k: v for k, v in row.items() if k != 'artifacts'}),
                            ('stage_artifacts_verified', row['ended_utc'], {'stage': name, 'artifacts': row['artifacts']})])
        control.append(('controller_completed', terminal['ended_utc'], copy.deepcopy(terminal)))
        terminal['last_event_sha256'] = self.events(self.runtime / 'events', control)
        self.put('final_continuation_runtime_20261018_r1/controller_terminal.json', terminal)

    def run(self):
        with patch.object(audit, 'RUN', self.root), patch.object(audit, 'ANCHORS', self.anchors):
            return audit.audit(self.root, self.root / 'publication.json')


class ProductionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='leo900-production-fixture-')
        self.addCleanup(self.temporary.cleanup)
        self.fixture = ProductionFixture(Path(self.temporary.name))

    def reject_rebound(self, expected):
        self.fixture.rebind()
        with self.assertRaisesRegex(audit.EvidenceError, expected):
            self.fixture.run()

    def test_production_only_branches_with_opaque_artifacts(self):
        self.assertEqual(self.fixture.run()['status'], 'EXECUTION_CHAIN_VERIFIED')

    def test_zero_window_generated_units_are_distinct_from_evaluated_units(self):
        bat = [r['sample_id'] for r in self.fixture.plan['rows'] if r['product_line'] == 'bat']
        rwa = [r['sample_id'] for r in self.fixture.plan['rows'] if r['product_line'] == 'rwa']
        self.fixture.set_evaluated_unit_counts('bat', {uid: 2 for uid in bat[1:]})
        self.fixture.set_evaluated_unit_counts('rwa', {rwa[0]: 1})
        report = self.fixture.run()
        self.assertEqual(report['status'], 'EXECUTION_CHAIN_VERIFIED')
        self.assertEqual(report['generated_unit_counts'], {'bat': 48, 'rwa': 48})
        self.assertEqual(report['evaluated_unit_counts'], {'bat': 47, 'rwa': 1})
        self.assertEqual(report['zero_window_unit_counts'], {'bat': 1, 'rwa': 47})
        self.assertEqual(report['unit_membership']['bat']['generated_unit_ids'], sorted(bat))
        self.assertEqual(report['unit_membership']['bat']['evaluated_unit_ids'], sorted(bat[1:]))
        self.assertEqual(report['unit_membership']['bat']['zero_window_unit_ids'], [bat[0]])
        self.assertEqual(report['unit_membership']['rwa']['zero_window_unit_ids'], sorted(rwa[1:]))
        self.assertFalse(report['f1_closed'])
        self.assertFalse(report['scientific_success_claimed'])

    def test_unknown_evaluated_unit_rejected_even_with_all_hash_edges_rebound(self):
        self.fixture.set_evaluated_unit_counts('bat', {'BAT_LEO900_B00_S9999': 2})
        with self.assertRaisesRegex(audit.EvidenceError, 'evaluated.*membership|partition.*subset'):
            self.fixture.run()

    def test_non_positive_or_non_integer_unit_windows_are_rejected(self):
        for invalid in (0, -1, True, 2.0):
            with self.subTest(count=invalid):
                original = copy.deepcopy(self.fixture.documents['formal_output_execution_r1/final_receipt.json'])
                self.fixture.mutate('formal_output_execution_r1/final_receipt.json', lambda d:
                    d['results']['bat']['unit_window_counts'].update(
                        {next(iter(d['results']['bat']['unit_window_counts'])): invalid}))
                self.reject_rebound('positive integer.*window|window.*positive integer')
                self.fixture.put('formal_output_execution_r1/final_receipt.json', original)
                self.fixture.rebind()

    def test_empty_evaluated_membership_cannot_be_a_complete_component(self):
        self.fixture.mutate('formal_output_execution_r1/final_receipt.json', lambda d:
            d['results']['bat'].update(unit_window_counts={}))
        self.reject_rebound('nonempty.*unit|evaluated.*empty')

    def test_receipt_unit_window_total_must_match_component_count(self):
        self.fixture.mutate('formal_output_execution_r1/final_receipt.json', lambda d:
            d['results']['bat']['unit_window_counts'].update(
                {next(iter(d['results']['bat']['unit_window_counts'])): 3}))
        self.reject_rebound('component.*window.*count|window.*total')

    def test_duplicated_statistics_unit_cannot_hide_missing_member(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
            d['components']['bat']['units'].__setitem__(1, copy.deepcopy(d['components']['bat']['units'][0])))
        self.reject_rebound('statistics.*unit.*membership|duplicate.*statistics')

    def test_boolean_metric_count_is_not_an_integer_unit_count(self):
        self.fixture.mutate('formal_output_execution_r1/final_receipt.json', lambda d:
            d['results']['bat']['metrics'].update(n_units=True))
        self.reject_rebound('metric.*count')

    def test_csv_numeric_tamper_after_hash_rebinding(self):
        p = self.fixture.statistics / 'f1_full_precision_gate.csv'
        p.write_bytes(p.read_bytes().replace(b'0.90000000000000002', b'0.80000000000000004'))
        self.reject_rebound('CSV|csv|precision')

    def test_csv_duplicate_metric_after_hash_rebinding(self):
        p = self.fixture.statistics / 'f1_full_precision_gate.csv'
        lines = p.read_bytes().splitlines(keepends=True)
        lines[2] = lines[1]
        p.write_bytes(b''.join(lines))
        self.reject_rebound('CSV|csv|precision')

    def test_statistics_unit_counts_must_match_original_layout(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d: (
            d['components']['bat']['units'][0].update(n_windows=1),
            d['components']['bat']['units'][1].update(n_windows=3)))
        self.reject_rebound('statistics.*unit|unit.*statistics|unit.*summary')

    def test_bootstrap_point_contradiction_after_hash_rebinding(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
            d['components']['bat']['bootstrap']['rmse']['window_pooled'].update(point_delta=-.9))
        self.reject_rebound('point|bootstrap|statistics')

    def test_bootstrap_inverted_ci_after_hash_rebinding(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
            d['components']['bat']['bootstrap']['rmse']['window_pooled'].update(ci95=[.1, -.1]))
        self.reject_rebound('interval|bootstrap|statistics')

    def test_bootstrap_negative_sd_after_hash_rebinding(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
            d['components']['bat']['bootstrap']['rmse']['window_pooled'].update(bootstrap_sd=-.1))
        self.reject_rebound('SD|sd|bootstrap|statistics')

    def test_wrong_physical_units_after_hash_rebinding(self):
        self.fixture.mutate('formal_statistics_20261018_r1/f1_gate_statistics.json', lambda d:
            d['components']['bat'].update(physical_unit='day'))
        self.reject_rebound('physical.*unit')

    def test_snapshot_wrong_method_after_hash_rebinding(self):
        self.fixture.mutate('formal_output_execution_r1.candidate_snapshot.json', lambda d: d.update(method_id='different'))
        self.reject_rebound('snapshot|candidate')

    def test_snapshot_wrong_derivation_after_hash_rebinding(self):
        self.fixture.mutate('formal_output_execution_r1.candidate_snapshot.json', lambda d:
            d['derivation'].update(base_candidate_receipt_sha256='0' * 64))
        self.reject_rebound('snapshot|derivation|candidate')

    def test_history_cannot_be_relabelled_as_source_only(self):
        self.fixture.mutate('formal_output_execution_r1/freeze_manifest.json', lambda d:
            d['visible_information_before_freeze']['candidate_history'].update(leo800_influenced_candidate_revision=False))
        self.reject_rebound('history|development')

    def test_extra_raw_member_is_rejected(self):
        self.fixture.raw('project/generated/bat/unregistered.mat', b'extra')
        self.reject_rebound('raw.*membership')


class ParserAndArithmeticTests(unittest.TestCase):
    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(audit.EvidenceError, 'duplicate'):
            audit.parse_json(b'{"gate":true,"gate":false}')

    def test_non_finite_json_rejected(self):
        for data in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}'):
            with self.subTest(data=data), self.assertRaisesRegex(audit.EvidenceError, 'non-finite'):
                audit.parse_json(data)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            files = audit.Files(Path(temporary))
            with self.assertRaisesRegex(audit.EvidenceError, 'traversal'):
                files.safe('../escape.json')

    def test_registered_gate_operation_order_at_float_boundary(self):
        reference = 1.0
        observed = reference + 1e-12
        self.assertGreater(observed - reference, 1e-12)
        results = {c: {'metrics': {'rmse': observed, 'mae': .5},
                       'control_only_metrics': {'rmse': reference, 'mae': .5}} for c in audit.COMPONENTS}
        gate = audit.gate_calculation(results)
        self.assertEqual(gate['regressions'], [])
        self.assertFalse(gate['passes'])
        self.assertFalse(gate['strict_gain'])


class TerminalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="leo900-terminal-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Fixture(Path(self.temporary.name))

    def reject(self, expected):
        with self.assertRaisesRegex(audit.EvidenceError, expected):
            self.fixture.run()

    def test_full_chain_verified_without_claiming_research_success(self):
        report = self.fixture.run()
        self.assertEqual(report["status"], "EXECUTION_CHAIN_VERIFIED")
        self.assertTrue(report["formal_gate_passes"])
        self.assertFalse(report["f1_closed"])
        self.assertFalse(report["scientific_success_claimed"])
        self.assertEqual(report["unit_counts"], {"bat": 48, "rwa": 48})

    def test_negative_gate_still_preserves_complete_audit(self):
        other = Path(self.temporary.name) / "negative"
        report = Fixture(other, positive=False).run()
        self.assertEqual(report["status"], "EXECUTION_CHAIN_VERIFIED")
        self.assertFalse(report["formal_gate_passes"])

    def test_in_progress_is_pending(self):
        (self.fixture.runtime / "controller_terminal.json").unlink()
        self.assertEqual(self.fixture.run()["status"], "PENDING_TERMINAL")

    def test_registered_source_drift(self):
        (self.fixture.project / "source.bin").write_bytes(b"changed")
        self.reject("registered input")

    def test_duplicate_final_access_even_with_valid_hash_chain(self):
        events = list(self.fixture.formal_events)
        events.insert(3, events[2])
        self.fixture.events(self.fixture.formal / "events", events, hashed_names=True)
        self.reject("event sequence|exactly once")

    def test_clock_reversal_even_with_valid_hash_chain(self):
        events = list(self.fixture.formal_events)
        kind, _, payload = events[2]
        events[2] = (kind, "2026-10-18T00:00:00Z", payload)
        self.fixture.events(self.fixture.formal / "events", events, hashed_names=True)
        self.reject("chronology|time")

    def test_freeze_after_guard_is_rejected(self):
        self.fixture.mutate("leo900_final_label_access_guard.json", lambda d: d.update(created_utc="2026-10-18T00:05:00Z"))
        self.reject("guard|chronology|freeze")

    def test_publication_after_access_is_rejected(self):
        self.fixture.mutate("publication.json", lambda d: d.update(ended_utc="2026-10-18T00:10:00Z"))
        self.fixture.anchors["publication"] = self.fixture.digest(self.fixture.root / "publication.json")
        self.reject("publication|chronology")

    def test_missing_component(self):
        self.fixture.mutate("formal_output_execution_r1/final_receipt.json", lambda d: d["results"].pop("rwa"))
        self.reject("component|receipt|hash")

    def test_statistics_report_drift(self):
        self.fixture.mutate("formal_statistics_20261018_r1/f1_gate_statistics.json", lambda d: d["components"]["bat"]["bootstrap_design"].update(seed=999))
        self.reject("statistics|hash")

    def test_inconsistent_gate(self):
        self.fixture.mutate("formal_statistics_20261018_r1/statistics_receipt.json", lambda d: d.update(gate_passes=False))
        self.reject("gate|artifact|hash")

    def test_raw_hash_drift(self):
        next((self.fixture.root / "project/generated/bat").glob("*.mat")).write_bytes(b"changed raw")
        self.reject("raw|hash")

    def test_wrong_repository_is_rejected(self):
        self.fixture.mutate("publication.json", lambda d: d.update(repository="https://github.com/unauthorized/other"))
        self.fixture.anchors["publication"] = self.fixture.digest(self.fixture.root / "publication.json")
        self.reject("repository")

    def test_controller_failure_is_rejected(self):
        self.fixture.mutate("final_continuation_runtime_20261018_r1/controller_terminal.json", lambda d: d.update(state="ERROR"))
        self.reject("terminal|controller")

    def test_event_byte_tamper(self):
        path = next((self.fixture.formal / "events").glob("0002*.json"))
        path.write_bytes(path.read_bytes().replace(b"candidate_frozen", b"candidate_changed"))
        self.reject("event|hash")

    def test_naive_timestamp_is_rejected(self):
        self.fixture.mutate("publication.json", lambda d: d.update(ended_utc="2026-10-18T00:01:00"))
        self.fixture.anchors["publication"] = self.fixture.digest(self.fixture.root / "publication.json")
        self.reject("timezone|timestamp")


if __name__ == "__main__":
    unittest.main()
