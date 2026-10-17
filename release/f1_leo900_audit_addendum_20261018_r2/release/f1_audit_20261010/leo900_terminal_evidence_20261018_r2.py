"""Independent, read-only terminal evidence audit; no evaluator/model imports.

The CLI fixes the registered production root and external-publication anchors.
An execution-chain PASS is not F1 closure or evidence of scientific superiority.
No MAT variables, tensors, models or prediction arrays are decoded here. Files
are streamed for hashes only after the complete controller terminal is present.

R2 distinguishes the complete generated partition from the positive-window
evaluation subset. It changes no model, split, window rule, gate or statistic.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RUN = Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
PROTOCOL = 'final_continuation_support_20261018_r1/F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json'
PUBLICATION = 'leo900_external_commitment_rest_publication_20261017T193909Z.json'
ANCHORS = {
    'protocol': 'a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a',
    'publication': '5c60799f4d6154bf6235453a44e7ca385b27b5653d428ebc23031c2535bf7025',
    'manifest': '7a489927d3cb6001fff91b7b9af77d9da0468f6721a053fa90be8d8025ca9490',
    'commit': '846cdaac03beab2bacb9834bde1ed8fff1c77141',
}
COMPONENTS = ('bat', 'rwa')
COUNTS = {'bat': 48, 'rwa': 48}
STAGES = ('seal', 'freeze', 'evaluate', 'statistics')
FORMAL_EVENTS = ('preflight_recorded', 'candidate_frozen', 'final_label_access_started',
                 'final_evaluation_completed', 'same_partition_reference_gate_completed')
TOLERANCE = 1e-12
GATE_RULE = ('both components must be non-inferior on RMSE and MAE to the same-partition '
             'projected frozen HGB/MLP reference, with at least one strict gain')
PHYSICAL_UNITS = {'bat': 'cycle', 'rwa': 'day'}
CSV_FIELDS = ('component', 'metric', 'physical_unit', 'n_units', 'n_windows',
              'candidate', 'candidate_hex', 'reference', 'reference_hex', 'delta', 'delta_hex',
              'reference_plus_tolerance', 'reference_plus_tolerance_hex',
              'reference_minus_tolerance', 'reference_minus_tolerance_hex', 'regression', 'strict_gain')


class EvidenceError(RuntimeError):
    """Missing, contradictory, unsafe or changed evidence; never rerun a stage."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def timestamp(value):
    require(isinstance(value, str), 'timestamp must be a timezone-aware string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise EvidenceError('invalid timestamp') from exc
    require(result.tzinfo is not None and result.utcoffset() is not None,
            'timestamp must include a timezone')
    return result.astimezone(timezone.utc)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'),
                       allow_nan=False) + '\n').encode('utf-8')


def parse_json(data):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate JSON key: ' + key)
            value[key] = item
        return value

    def number(value):
        parsed = float(value)
        require(math.isfinite(parsed), 'non-finite JSON number')
        return parsed

    def invalid(value):
        raise EvidenceError('non-finite JSON constant: ' + value)

    try:
        return json.loads(data, object_pairs_hook=pairs, parse_float=number, parse_constant=invalid)
    except (ValueError, UnicodeError) as exc:
        raise EvidenceError('invalid JSON evidence') from exc


def fingerprint(path):
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class Files:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.observed = {}
        self.hashes = {}
        self.safe(self.root, directory=True)

    def safe(self, value, *, base=None, directory=False):
        path = Path(value)
        require('..' not in path.parts, 'unsafe evidence path traversal')
        if not path.is_absolute():
            path = Path(base or self.root) / path
        require(path.is_relative_to(self.root), 'evidence path outside registered run: ' + str(path))
        for part in (path, *path.parents):
            require(not part.is_symlink() and not (hasattr(part, 'is_junction') and part.is_junction()),
                    'symlink/junction in evidence path: ' + str(path))
        require(path.is_dir() if directory else path.is_file(), 'missing evidence file/directory: ' + str(path))
        return path

    def exists(self, value):
        path = self.root / value
        if path.exists() or path.is_symlink():
            self.safe(path)
            return True
        return False

    def digest(self, value, *, base=None):
        path = self.safe(value, base=base)
        before = fingerprint(path)
        if path in self.hashes:
            require(before == self.observed[path], 'artifact changed during evidence audit: ' + str(path))
            return self.hashes[path]
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        require(before == fingerprint(path), 'artifact changed while hashing: ' + str(path))
        self.observed[path], self.hashes[path] = before, digest.hexdigest()
        return digest.hexdigest()

    def read(self, value):
        path = self.safe(value)
        digest = self.digest(path)
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == digest, 'JSON artifact drift: ' + str(path))
        return parse_json(data)

    def record(self, row, *, base=None, context='artifact'):
        require(isinstance(row, dict), context + ' record must be an object')
        path = self.safe(row.get('path', ''), base=base)
        expected = row.get('sha256')
        require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected) is not None,
                context + ' hash missing or malformed')
        require(self.digest(path) == expected, context + ' hash drift: ' + str(path))
        if 'size' in row:
            require(type(row['size']) is int and path.stat().st_size == row['size'], context + ' size drift')
        return path

    def finish(self):
        for path, before in self.observed.items():
            self.safe(path)
            require(fingerprint(path) == before, 'evidence drift during audit: ' + str(path))


def event_chain(files, folder, *, hashed_names=False):
    folder = files.safe(folder, directory=True)
    paths = sorted(folder.iterdir())
    require(paths and all(p.suffix == '.json' for p in paths), 'event directory membership mismatch')
    events, previous, last_time = [], None, None
    for index, path in enumerate(paths, 1):
        document = files.read(path)
        require(type(document.get('sequence')) is int and document['sequence'] == index,
                'event sequence gap or duplicate')
        require(document.get('previous_event_sha256') == previous, 'event hash chain mismatch')
        kind = document.get('event_type')
        require(isinstance(kind, str) and re.fullmatch('[a-z_]+', kind) is not None, 'event type malformed')
        previous = files.digest(path)
        name = f'{index:04d}_{kind}' + ('_' + previous[:16] if hashed_names else '') + '.json'
        require(path.name == name, 'event filename/hash mismatch')
        date = timestamp(document.get('created_utc'))
        require(last_time is None or date >= last_time, 'event chronology/time reversal')
        require(isinstance(document.get('payload'), dict), 'event payload malformed')
        last_time = date
        events.append(document)
    return events, previous


def gate_calculation(results):
    regressions, deltas, strict = [], {}, False
    for component in COMPONENTS:
        item = results[component]
        deltas[component] = {}
        for metric in ('rmse', 'mae'):
            observed, reference = item['metrics'][metric], item['control_only_metrics'][metric]
            require(type(observed) in (int, float) and type(reference) in (int, float)
                    and math.isfinite(observed) and math.isfinite(reference) and observed >= 0 and reference >= 0,
                    'non-finite/invalid gate metric')
            observed, reference = float(observed), float(reference)
            deltas[component][metric] = observed - reference
            # Preserve the registered operation order at floating-point boundaries.
            if observed > reference + TOLERANCE:
                regressions.append(component + '.' + metric)
            if observed < reference - TOLERANCE:
                strict = True
    return {'passes': not regressions and strict, 'strict_gain': strict,
            'regressions': sorted(regressions), 'tolerance': TOLERANCE,
            'deltas_candidate_minus_same_partition_reference': deltas}


def audit(root, publication_path, *, anchors=None):
    """Audit terminal evidence. Anchor injection is for disposable fixtures only."""
    production = anchors is None
    anchors = dict(ANCHORS if anchors is None else anchors)
    require(set(anchors) == {'protocol', 'publication', 'manifest', 'commit'}, 'anchor membership mismatch')
    if production:
        require(Path(root) == RUN, 'production audit root is fixed')
    files = Files(root)
    root = files.root
    require(files.digest(publication_path) == anchors['publication'], 'publication receipt hash mismatch')
    publication = files.read(publication_path)
    require(publication.get('repository') == 'https://github.com/1553926531-sudo/BRPHM', 'wrong repository identity')
    require(publication.get('status') == 'PUBLISHED_AND_READBACK_VERIFIED'
            and publication.get('independent_local_tree_and_commit_match') is True
            and publication.get('api_blob_files_verified') == 41, 'publication verification incomplete')
    require(publication.get('commit') == anchors['commit']
            and publication.get('package_manifest_sha256') == anchors['manifest'], 'publication commit/manifest anchor mismatch')
    published = timestamp(publication.get('ended_utc'))
    try:
        server_date = parsedate_to_datetime(publication['api_ref_response_headers']['Date'])
    except (ValueError, TypeError, KeyError) as exc:
        raise EvidenceError('publication server Date missing/malformed') from exc
    require(server_date.tzinfo is not None and server_date <= published, 'publication chronology/server Date contradiction')
    protocol = files.read(PROTOCOL)
    require(files.digest(PROTOCOL) == anchors['protocol'], 'registered protocol hash drift')
    require(publication.get('files', {}).get(Path(PROTOCOL).name) == anchors['protocol'], 'publication does not bind protocol')
    require(timestamp(protocol['created_utc']) <= published, 'protocol publication chronology')
    registered = {}
    for row in protocol['input_files']:
        path = files.record(row, context='registered input')
        require(str(path) not in registered, 'duplicate registered input')
        registered[str(path)] = row['sha256']
    require(registered, 'empty registered input set')
    for name, expected in publication['files'].items():
        if name.startswith('registered_inputs/'):
            path = files.safe(name.removeprefix('registered_inputs/'))
            require(registered.get(str(path)) == expected, 'publication registered input contradiction')
    plan = files.read('final_continuation_runtime_20261018_r1/controller_plan.json')
    expected_plan = dict(protocol['fixed_plan'])
    expected_plan['inputs'] = {**registered, str(root / PROTOCOL): anchors['protocol']}
    require(plan == expected_plan and plan.get('run_root') == str(root)
            and plan.get('production') is True, 'controller plan differs from registered fixed plan')
    runtime = root / 'final_continuation_runtime_20261018_r1'
    require(plan['runtime'] == str(runtime)
            and plan['guard'] == str(root / 'leo900_final_label_access_guard.json'), 'controller path identity mismatch')
    require(tuple(s['name'] for s in plan['stages']) == STAGES, 'fixed stage sequence mismatch')
    terminal_path = runtime / 'controller_terminal.json'
    if not files.exists(terminal_path):
        files.finish()
        return {'status': 'PENDING_TERMINAL', 'f1_closed': False, 'scientific_success_claimed': False,
                'semantic_final_labels_read_by_auditor': False, 'registered_inputs_verified': len(registered)}
    terminal = files.read(terminal_path)
    require(terminal.get('state') == 'EVALUATION_AND_STATISTICS_COMPLETED', 'controller terminal is not complete')
    control_events, last_hash = event_chain(files, runtime / 'events')
    require(terminal.get('last_event_sha256') == last_hash, 'controller terminal last event hash mismatch')
    require(control_events[0]['event_type'] == 'controller_started'
            and control_events[-1]['event_type'] == 'controller_completed', 'controller terminal event sequence mismatch')
    terminal_event = {k: v for k, v in terminal.items() if k != 'last_event_sha256'}
    require(control_events[-1]['payload'] == terminal_event, 'controller terminal/event contradiction')
    files.record(control_events[0]['payload']['plan'], context='controller plan')
    require(control_events[0]['payload']['plan']['sha256'] == files.digest(runtime / 'controller_plan.json'), 'controller start plan mismatch')
    started, ended = timestamp(terminal['started_utc']), timestamp(terminal['ended_utc'])
    require(started <= timestamp(control_events[0]['created_utc'])
            <= timestamp(control_events[-1]['created_utc']) and ended >= started, 'controller terminal chronology')
    allowed = {'controller_started', 'controller_completed', 'preflight_state', 'stage_started', 'stage_exited',
               'stage_artifacts_verified', 'waiting_for_resources', 'resources_ready'}
    require(all(e['event_type'] in allowed for e in control_events), 'unexpected controller event/error')
    stage_events = [e for e in control_events if e['event_type'].startswith('stage_')]
    require([e['event_type'] for e in stage_events] == ['stage_started', 'stage_exited', 'stage_artifacts_verified'] * 4,
            'controller stage event sequence/uniqueness mismatch')
    stage_rows = terminal.get('stages', [])
    require(len(stage_rows) == 4, 'terminal stage count mismatch')
    bounds, previous_end = {}, started
    for index, spec in enumerate(plan['stages']):
        row, triple = stage_rows[index], stage_events[index * 3:index * 3 + 3]
        name = spec['name']
        require(row.get('name') == name and row.get('command') == spec['command']
                and type(row.get('exit_code')) is int and row['exit_code'] == 0, 'controller stage/command/exit mismatch')
        begin, end = timestamp(row['started_utc']), timestamp(row['ended_utc'])
        require(previous_end <= begin <= end <= ended, 'controller stage chronology/overlap')
        for event, kind in zip(triple, ('stage_started', 'stage_exited', 'stage_artifacts_verified')):
            date, payload = timestamp(event['created_utc']), event['payload']
            if kind == 'stage_artifacts_verified':
                require(payload.get('stage') == name and date >= end, 'stage artifact event chronology')
                for artifact in payload.get('artifacts', []):
                    files.record(artifact, context='stage artifact')
            else:
                require(payload.get('name') == name and payload.get('command') == spec['command']
                        and payload.get('started_utc') == row['started_utc'], 'stage event command/identity contradiction')
                if kind == 'stage_exited':
                    require(payload.get('exit_code') == 0 and payload.get('ended_utc') == row['ended_utc']
                            and date >= end, 'stage exit event contradiction')
                else:
                    require(begin <= date <= end, 'stage start event chronology')
        if production:
            require(row.get('artifacts') == triple[2]['payload'].get('artifacts') and row['artifacts'], 'stage artifact records missing')
            for suffix in ('stdout', 'stderr'):
                path = files.record(row[suffix], context='controller stage log')
                require(path == runtime / (name + '.' + suffix + '.log'), 'controller stage log path mismatch')
        bounds[name], previous_end = (begin, end), end
    formal = root / 'formal_output_execution_r1'
    seal_root = root / 'metadata_seal_execution_20261018_r1'
    statistics_root = root / 'formal_statistics_20261018_r1'
    project = root / 'evaluation_project_execution_r1'
    partition = files.read(seal_root / 'partition_manifest.json')
    seal_receipt = files.read(seal_root / 'seal_receipt.json')
    partition_hash = files.digest(seal_root / 'partition_manifest.json')
    require(seal_receipt.get('status') == 'PASS' and seal_receipt.get('unit_counts') == COUNTS
            and seal_receipt.get('partition_sha256') == partition_hash, 'metadata seal hash/count mismatch')
    for document in (partition, seal_receipt):
        require(document.get('semantic_labels_read') is False and document.get('final_label_access') is False,
                'seal declared semantic label access')
        require(bounds['seal'][0] <= timestamp(document['created_utc']) <= bounds['seal'][1], 'seal time outside stage')
    partition_plan = files.read('evidence/partition_plan.json')
    rows, planned = partition['rows'], partition_plan['rows']
    require(partition_plan.get('unit_counts') == COUNTS and partition.get('unit_counts') == COUNTS
            and len(rows) == len(planned) == 96, 'partition unit count mismatch')
    by_id = {r['sample_id']: r for r in rows}
    require(len(by_id) == 96 and set(by_id) == {r['sample_id'] for r in planned}, 'partition unit membership mismatch')
    require({r['serial'] for r in rows} == set(range(1300, 1396))
            and {r['seed'] for r in rows} == set(range(894000, 894096)), 'partition serial/seed membership mismatch')
    require(Counter((r['product_line'], r['beta_deg']) for r in rows)
            == Counter({(c, b): 16 for c in COMPONENTS for b in (0, 30, 60)}), 'partition component/beta counts mismatch')
    expected_raw, inodes = set(), set()
    for row in planned:
        actual = by_id[row['sample_id']]
        require(all(actual.get(k) == v for k, v in row.items()) and actual.get('orbit') == 'LEO900', 'sealed row differs from registered plan')
        raw = root / 'project/generated' / actual['product_line'] / (actual['sample_id'] + '.mat')
        require(actual.get('raw_path') == str(raw), 'raw path differs from registered generated path')
        files.record({'path': str(raw), 'sha256': actual['sha256'], 'size': actual['size']}, context='raw artifact')
        key = fingerprint(raw)[:2]
        require(raw.stat().st_nlink == 1 and key not in inodes, 'duplicate/hardlinked raw artifact')
        inodes.add(key)
        expected_raw.add(raw)
    generated = files.safe(root / 'project/generated', directory=True)
    actual_raw = set()
    for path in generated.rglob('*'):
        files.safe(path, directory=path.is_dir())
        if path.is_file():
            actual_raw.add(path)
    require(actual_raw == expected_raw, 'raw artifact directory membership mismatch')
    freeze = files.read(formal / 'freeze_manifest.json')
    decision = files.read(formal / 'selection_decision.json')
    freeze_hash, decision_hash = files.digest(formal / 'freeze_manifest.json'), files.digest(formal / 'selection_decision.json')
    require(freeze.get('final_partition', {}).get('n_units') == COUNTS
            and decision.get('freeze_manifest_sha256') == freeze_hash, 'freeze/decision partition binding mismatch')
    require(files.record(freeze['final_partition']['manifest'], base=project, context='freeze partition') == seal_root / 'partition_manifest.json', 'freeze partition path mismatch')
    frozen_raw = freeze['final_partition']['raw_files']
    require(len(frozen_raw) == 96 and {r['sample_id']: r['sha256'] for r in frozen_raw}
            == {r['sample_id']: r['sha256'] for r in rows}, 'freeze raw hash/membership mismatch')
    dependencies = freeze.get('dependencies', [])
    require(dependencies, 'freeze dependencies missing')
    for row in dependencies:
        files.record(row, base=project, context='freeze dependency')
    history = freeze.get('visible_information_before_freeze', {}).get('candidate_history', {})
    require(history.get('leo800_influenced_candidate_revision') is True
            and history.get('leo800_status') == 'development_or_diagnostic_only', 'candidate history must acknowledge development feedback')
    candidate = files.read('evidence/formal_candidate_receipt.json')
    require(set(candidate.get('components', {})) == set(COMPONENTS), 'candidate component membership mismatch')
    routes = {c: candidate['components'][c]['selected_route'] for c in COMPONENTS}
    require(freeze['candidate']['method_id'] == candidate['method_id']
            and freeze['candidate']['selected_routes'] == routes and decision.get('selected_routes') == routes, 'candidate route changed after registration')
    require(all(routes[c].get('alpha_by_target', {}).get('LEO900') == 1e-5 for c in COMPONENTS), 'fixed LEO900 alpha drift')
    freeze_time = timestamp(freeze['created_utc'])
    require(bounds['freeze'][0] <= freeze_time <= bounds['freeze'][1], 'freeze time outside stage')
    guard = files.read('leo900_final_label_access_guard.json')
    guard_hash = files.digest('leo900_final_label_access_guard.json')
    guard_time = timestamp(guard['created_utc'])
    require(guard.get('output') == str(formal) and guard.get('freeze_manifest_sha256') == freeze_hash
            and guard.get('partition_manifest_sha256') == partition_hash, 'guard freeze/partition binding mismatch')
    require(published < guard_time and server_date < guard_time and freeze_time <= guard_time
            and bounds['evaluate'][0] <= guard_time <= bounds['evaluate'][1], 'publication/freeze/guard chronology contradiction')
    events, formal_last_hash = event_chain(files, formal / 'events', hashed_names=True)
    require(tuple(e['event_type'] for e in events) == FORMAL_EVENTS, 'formal event sequence must access labels exactly once')
    preflight, frozen_event, access, evaluated, gated = events
    require(bounds['freeze'][0] <= timestamp(preflight['created_utc']) <= freeze_time
            <= timestamp(frozen_event['created_utc']) <= bounds['freeze'][1], 'formal freeze event chronology')
    require(guard_time <= timestamp(access['created_utc']) <= timestamp(evaluated['created_utc'])
            <= timestamp(gated['created_utc']) <= bounds['evaluate'][1], 'formal access/evaluation event chronology')
    require(preflight['payload'].get('holdout_label_read') is False
            and frozen_event['payload'].get('semantic_final_label_read') is False
            and access['payload'].get('candidate_or_route_mutation_allowed') is False, 'formal access policy contradiction')
    require(frozen_event['payload'].get('freeze_manifest_sha256') == freeze_hash
            and frozen_event['payload'].get('selection_decision_sha256') == decision_hash
            and access['payload'].get('freeze_manifest_sha256') == freeze_hash, 'formal event freeze binding mismatch')
    require(access['payload'].get('global_label_access_guard', {}).get('sha256') == guard_hash, 'formal access guard hash mismatch')
    receipt = files.read(formal / 'final_receipt.json')
    receipt_hash = files.digest(formal / 'final_receipt.json')
    require(receipt.get('freeze_manifest_sha256') == freeze_hash and receipt.get('selection_decision_sha256') == decision_hash
            and receipt.get('candidate_id') == candidate['method_id'], 'final receipt candidate/freeze binding mismatch')
    require(timestamp(access['created_utc']) <= timestamp(receipt['created_utc']) <= timestamp(evaluated['created_utc']), 'final receipt chronology contradiction')
    require(receipt.get('global_label_access_guard', {}).get('sha256') == guard_hash
            and files.record(receipt['global_label_access_guard'], context='receipt guard') == root / 'leo900_final_label_access_guard.json', 'final receipt guard mismatch')
    require(receipt.get('training', {}).get('holdout_used_for_training_or_selection') is False
            and receipt.get('holdout', {}).get('manifest_sha256') == partition_hash
            and receipt['holdout'].get('units') == COUNTS, 'final receipt training/holdout contradiction')
    results = receipt.get('results', {})
    require(set(results) == set(COMPONENTS), 'final receipt component membership mismatch')
    membership = {}
    for c, item in results.items():
        generated_ids = {r['sample_id'] for r in rows if r['product_line'] == c}
        counts = item.get('unit_window_counts')
        require(isinstance(counts, dict) and counts, 'evaluated units must be a nonempty unit/window map')
        require(all(isinstance(uid, str) and type(n) is int and n > 0 for uid, n in counts.items()),
                'evaluated units require positive integer window counts')
        evaluated_ids = set(counts)
        require(evaluated_ids <= generated_ids, 'evaluated unit membership is not a partition subset')
        require(item.get('route') == routes[c] and type(item.get('n_units')) is int
                and item['n_units'] == len(counts), 'final component route/unit count mismatch')
        require(type(item.get('n_windows')) is int and item['n_windows'] == sum(counts.values()),
                'final component window count differs from unit window total')
        membership[c] = {'generated_unit_ids': sorted(generated_ids),
                         'evaluated_unit_ids': sorted(evaluated_ids),
                         'zero_window_unit_ids': sorted(generated_ids - evaluated_ids)}
        for metric_set in ('metrics', 'control_only_metrics'):
            require(type(item[metric_set].get('n_units')) is int
                    and item[metric_set]['n_units'] == item['n_units']
                    and type(item[metric_set].get('n_windows')) is int
                    and item[metric_set]['n_windows'] == item['n_windows'], 'component metric counts mismatch')
    gate = files.read(formal / 'same_partition_performance_gate.json')
    gate_hash = files.digest(formal / 'same_partition_performance_gate.json')
    calculated_gate = gate_calculation(results)
    require(gate.get('final_receipt_sha256') == receipt_hash and gate.get('freeze_manifest_sha256') == freeze_hash
            and gate.get('partition_manifest_sha256') == partition_hash and gate.get('partition_unit_counts') == COUNTS, 'gate input hash binding mismatch')
    require(gate.get('comparison') == {**calculated_gate, 'rule': GATE_RULE},
            'gate calculation contradiction')
    require(gate.get('metrics') == {c: {'candidate_blend': v['metrics'], 'same_partition_reference': v['control_only_metrics']}
                                  for c, v in results.items()}, 'gate metric binding mismatch')
    require(evaluated['payload'].get('final_receipt_sha256') == receipt_hash
            and gated['payload'].get('final_receipt_sha256') == receipt_hash
            and gated['payload'].get('performance_gate_sha256') == gate_hash
            and gated['payload'].get('gate_passed') is calculated_gate['passes'], 'formal completion event hash/gate mismatch')
    stats_receipt = files.read(statistics_root / 'statistics_receipt.json')
    stats = files.read(statistics_root / 'f1_gate_statistics.json')
    require(stats_receipt.get('status') == 'PASS' and stats_receipt.get('report_sha256') == files.digest(statistics_root / 'f1_gate_statistics.json'), 'statistics report hash mismatch')
    require(stats.get('gate') == calculated_gate and stats_receipt.get('gate_passes') is calculated_gate['passes']
            and terminal.get('formal_gate_passes') is calculated_gate['passes'], 'statistics/controller gate contradiction')
    require(bounds['statistics'][0] <= timestamp(stats['created_utc']) <= bounds['statistics'][1], 'statistics time outside stage')
    expected_inputs = {name: files.digest(formal / name) for name in ('final_receipt.json', 'same_partition_performance_gate.json', 'freeze_manifest.json', 'selection_decision.json')}
    require(stats.get('inputs') == expected_inputs and set(stats.get('components', {})) == set(COMPONENTS), 'statistics input hash/component mismatch')
    for index, c in enumerate(COMPONENTS):
        entry = stats['components'][c]
        require(type(entry.get('n_units')) is int and entry['n_units'] == results[c]['n_units']
                and type(entry.get('n_windows')) is int and entry['n_windows'] == results[c]['n_windows'],
                'statistics unit/window count mismatch')
        units = entry.get('units', [])
        require(isinstance(units, list) and len(units) == entry['n_units']
                and all(isinstance(u, dict) and isinstance(u.get('unit_id'), str)
                        and type(u.get('n_windows')) is int and u['n_windows'] > 0 for u in units)
                and len({u['unit_id'] for u in units}) == len(units)
                and {u['unit_id']: u['n_windows'] for u in units} == results[c]['unit_window_counts'],
                'statistics unit membership/counts mismatch')
        design = entry.get('bootstrap_design', {})
        require(all(design.get(k) == v for k, v in {'cluster': 'unit_id', 'paired': True,
                    'all_unit_windows_retained': True, 'seed': 20261018 + index, 'repetitions': 20000}.items()), 'statistics bootstrap design drift')
        require(entry.get('seed_description', {}).get('independent_repeats') == 0, 'ensemble seeds cannot be independent repeats')
        require(entry.get('metrics', {}).get('metrics') == results[c]['metrics']
                and entry['metrics'].get('control_only_metrics') == results[c]['control_only_metrics'], 'statistics metric contradiction')
    if production:
        verify_production_artifacts(files, root, partition, freeze, receipt, stats, publication, bounds)
    files.finish()
    return {'status': 'EXECUTION_CHAIN_VERIFIED', 'formal_gate_passes': calculated_gate['passes'],
            'gate': calculated_gate, 'unit_counts': COUNTS, 'f1_closed': False, 'scientific_success_claimed': False,
             'unit_count_semantics': 'unit_counts/generated_unit_counts describe the complete generated partition; evaluated_unit_counts describe its positive-window subset',
             'generated_unit_counts': {c: len(membership[c]['generated_unit_ids']) for c in COMPONENTS},
             'evaluated_unit_counts': {c: len(membership[c]['evaluated_unit_ids']) for c in COMPONENTS},
             'zero_window_unit_counts': {c: len(membership[c]['zero_window_unit_ids']) for c in COMPONENTS},
             'unit_membership': membership,
            'semantic_final_labels_read_by_auditor': False, 'prediction_arrays_decoded_by_auditor': False,
            'registered_inputs_verified': len(registered), 'files_hashed': len(files.hashes),
            'controller_last_event_sha256': last_hash, 'formal_last_event_sha256': formal_last_hash,
            'external_commit': anchors['commit'], 'publication_sha256': anchors['publication'],
            'limitations': ['Checks the supplied execution evidence; does not independently prove historic absence of access.',
                            'Zero-window membership is inferred from bound evaluator/layout/statistics metadata; the auditor does not recompute raw window eligibility or establish a specific exclusion cause.',
                           'Deterministic gate status alone is not statistical or practical superiority.',
                           'One final orbit; ensemble constituents are not independent training repeats.']}


def verify_production_artifacts(files, root, partition, freeze, receipt, stats, publication, bounds):
    """Additional required production artifacts, independently bound to receipts."""
    formal, statistics = root / 'formal_output_execution_r1', root / 'formal_statistics_20261018_r1'
    require(publication.get('server_repository_identity', {}).get('full_name') == '1553926531-sudo/BRPHM'
            and publication.get('origin_identity_verified') is True and len(publication['files']) == 41, 'production repository publication identity mismatch')
    completion = partition.get('completion_metadata', {})
    require(completion.get('success_count') == 96 and completion.get('skip_count') == 0 and completion.get('failure_count') == 0,
            'simulation completion counts mismatch')
    require(timestamp(completion['start_utc']) == timestamp('2026-10-17T11:01:20Z')
            and timestamp(completion['end_utc']) <= bounds['seal'][0], 'simulation completion chronology')
    for row in partition.get('bound_artifacts', []):
        files.record(row, context='seal bound artifact')
    require(partition.get('bound_artifacts'), 'seal bound artifacts missing')
    for key in ('dependency_closure_registration', 'channel_policy_amendment', 'execution_amendment', 'candidate_snapshot'):
        files.record(freeze[key], base=root / 'evaluation_project_execution_r1', context='freeze ' + key)
    snapshot_path = files.record(freeze['candidate']['candidate_receipt'], base=root / 'evaluation_project_execution_r1', context='snapshot candidate')
    require(snapshot_path == root / 'formal_output_execution_r1.candidate_snapshot.json', 'snapshot candidate path mismatch')
    verify_candidate_snapshot(files, root, freeze, snapshot_path)
    for c in COMPONENTS:
        entry = receipt['results'][c]
        files.record({'path': entry['payload_path'], 'sha256': entry['payload_sha256']}, base=formal, context='final tensor artifact')
        paired = entry['paired_predictions']
        for kind in ('layout', 'arrays'):
            files.record({'path': paired[kind + '_path'], 'sha256': paired[kind + '_sha256']}, base=formal, context='paired ' + kind)
        layout = files.read(formal / paired['layout_path'])
        require(layout.get('component') == c and layout.get('payload_sha256') == entry['payload_sha256']
                and layout.get('arrays_sha256') == paired['arrays_sha256']
                and hashlib.sha256(json_bytes(layout['rows'])).hexdigest() == paired['rows_sha256'] == layout['rows_sha256']
                and len(layout['rows']) == paired['n_rows'] == entry['n_windows'], 'paired layout row binding mismatch')
        require(layout.get('seeds') == [17, 42, 73], 'ensemble constituent seeds changed')
        require(Counter(r['unit_id'] for r in layout['rows']) == Counter(entry['unit_window_counts']), 'paired unit/window membership mismatch')
        require(stats['components'][c].get('prediction_binding') == paired, 'statistics prediction binding mismatch')
        require(entry.get('training_diagnostics', {}).get('target_labels_used_in_training_or_correction') is False, 'target labels used in training diagnostics')
        verify_statistics_semantics(c, entry, layout, stats['components'][c])
    for key in ('bootstrap_distributions', 'full_precision_csv'):
        files.record(stats[key], base=statistics, context='statistics ' + key)
    verify_precision_csv(files, statistics, stats, receipt)
    require(stats['bootstrap_distributions'].get('shapes') == {
        f'{c}__{m}__{e}': [20000] for c in COMPONENTS for m in ('rmse', 'mae')
        for e in ('window_pooled', 'unit_macro')}, 'bootstrap distribution declared shapes mismatch')
    require(stats.get('verification') == {'gate_matches_original': True, 'metrics_exactly_match_original': True,
                                         'models_rerun': False, 'tensors_or_mat_loaded': False}, 'statistics verification contract mismatch')


def verify_candidate_snapshot(files, root, freeze, snapshot_path):
    snapshot = files.read(snapshot_path)
    base = files.read('evidence/formal_candidate_receipt.json')
    base_hash = files.digest('evidence/formal_candidate_receipt.json')
    # The registered builder copies the whole base receipt and replaces exactly
    # these two fields. No training, route selection or builder imports here.
    expected = dict(base)
    expected['formal_protocol'] = {
        'loss': 'unit-balanced L1 on normalized RUL',
        'source_standardization': 'source-window channel mean/std',
        'residual_calibration': 'equal-unit median source residuals, shrink=0.25',
        'ensemble': 'median of three fixed seeds',
        'candidate_receipt_sha256': base_hash,
        'unseen_orbit': 'LEO900', 'selection_uses_unseen_labels': False}
    expected['derivation'] = {
        'schema': 'brphm-f1-leo900-plain-l1-candidate-snapshot-v1',
        'base_candidate_receipt_sha256': base_hash, 'unseen_orbit': 'LEO900',
        'alpha_rule': 'preserve the hash-bound source-selected routes and the fixed LEO900 source-protocol alpha floor',
        'alpha_value_by_component': {c: 1e-5 for c in COMPONENTS},
        'selection_uses_unseen_labels': False}
    require(snapshot == expected, 'snapshot candidate/derivation differs from registered base and fixed contract')
    require(freeze.get('candidate_snapshot_sha256') == files.digest(snapshot_path)
            and files.record(freeze['candidate_snapshot'], base=root / 'evaluation_project_execution_r1',
                             context='snapshot freeze binding') == snapshot_path,
            'snapshot freeze hash/path contradiction')


def finite_number(value, context, *, nonnegative=False):
    require(type(value) in (int, float) and math.isfinite(value)
            and (not nonnegative or value >= 0), context + ' must be a finite valid number')
    return float(value)


def close_summary(actual, expected, context, *, scale=0.):
    actual = finite_number(actual, context)
    # Only for alternative summation orders in descriptive summaries. Gate and
    # lossless CSV checks below remain exact and retain registered arithmetic.
    allowance = 64 * math.ulp(max(abs(expected), abs(scale)))
    require(abs(actual - expected) <= allowance, context + ' arithmetic contradiction')


def verify_statistics_semantics(component, result, layout, stats):
    require(stats.get('physical_unit') == PHYSICAL_UNITS[component], 'statistics physical unit mismatch')
    require(finite_number(layout.get('rmax'), 'paired layout rmax', nonnegative=True) > 0
            and stats.get('rmax') == layout['rmax'], 'statistics rmax/physical unit scale mismatch')
    counts = Counter(r['unit_id'] for r in layout['rows'])
    units = stats['units']
    require(len({u['unit_id'] for u in units}) == len(units)
            and {u['unit_id']: u['n_windows'] for u in units} == dict(counts),
            'statistics unit summary counts differ from original paired layout')
    for unit in units:
        n = unit['n_windows']
        for prefix in ('candidate', 'reference'):
            sse = finite_number(unit.get(prefix + '_sse'), 'statistics unit SSE', nonnegative=True)
            sae = finite_number(unit.get(prefix + '_sae'), 'statistics unit SAE', nonnegative=True)
            rmse = finite_number(unit.get(prefix + '_rmse'), 'statistics unit RMSE', nonnegative=True)
            mae = finite_number(unit.get(prefix + '_mae'), 'statistics unit MAE', nonnegative=True)
            close_summary(rmse, math.sqrt(sse / n), 'statistics unit RMSE')
            close_summary(mae, sae / n, 'statistics unit MAE')
            require(mae <= rmse + 64 * math.ulp(rmse), 'statistics unit MAE exceeds RMSE')
        for metric in ('rmse', 'mae'):
            observed, reference = unit['candidate_' + metric], unit['reference_' + metric]
            require(unit.get('delta_' + metric) == observed - reference, 'statistics unit delta contradiction')
            relative = 100. * (observed - reference) / reference if reference > 0 else None
            require(unit.get('relative_change_percent_' + metric) == relative,
                    'statistics unit relative change contradiction')
    require(set(stats.get('bootstrap', {})) == {'rmse', 'mae'}, 'statistics bootstrap metric membership mismatch')
    for metric, aggregate, transform in (('rmse', 'sse', math.sqrt), ('mae', 'sae', float)):
        for prefix, metrics in (('candidate', result['metrics']), ('reference', result['control_only_metrics'])):
            pooled = transform(math.fsum(u[prefix + '_' + aggregate] for u in units) / result['n_windows'])
            close_summary(metrics[metric], pooled, 'statistics pooled ' + prefix + ' ' + metric)
        estimands = stats['bootstrap'][metric]
        require(set(estimands) == {'window_pooled', 'unit_macro'}, 'statistics bootstrap estimand membership mismatch')
        for estimand, entry in estimands.items():
            if estimand == 'window_pooled':
                observed, reference = result['metrics'][metric], result['control_only_metrics'][metric]
                require(entry.get('candidate_point') == observed and entry.get('reference_point') == reference
                        and entry.get('point_delta') == observed - reference, 'bootstrap pooled point contradiction')
            else:
                observed = math.fsum(u['candidate_' + metric] for u in units) / len(units)
                reference = math.fsum(u['reference_' + metric] for u in units) / len(units)
                delta = math.fsum(u['delta_' + metric] for u in units) / len(units)
                close_summary(entry.get('candidate_point'), observed, 'bootstrap macro candidate point')
                close_summary(entry.get('reference_point'), reference, 'bootstrap macro reference point')
                close_summary(entry.get('point_delta'), delta, 'bootstrap macro delta point', scale=max(observed, reference))
            point = finite_number(entry.get('point_delta'), 'bootstrap point delta')
            baseline = finite_number(entry.get('reference_point'), 'bootstrap reference point', nonnegative=True)
            relative = 100. * point / baseline if baseline > 0 else None
            require(entry.get('relative_change_percent') == relative, 'bootstrap relative change contradiction')
            require(entry.get('relative_change_status') == (
                'defined: 100 * paired delta / reference error' if baseline > 0
                else 'undefined: reference error is zero'), 'bootstrap relative change status contradiction')
            finite_number(entry.get('bootstrap_sd'), 'bootstrap SD', nonnegative=True)
            intervals = []
            for key in ('ci95', 'ci_familywise_95_bonferroni_8'):
                interval = entry.get(key)
                require(isinstance(interval, list) and len(interval) == 2, 'bootstrap interval schema mismatch')
                low, high = (finite_number(v, 'bootstrap interval endpoint') for v in interval)
                require(low <= high, 'bootstrap interval endpoints inverted')
                intervals.append((low, high))
            inner, outer = intervals
            require(outer[0] <= inner[0] <= inner[1] <= outer[1], 'bootstrap familywise interval nesting contradiction')


def verify_precision_csv(files, statistics, stats, receipt):
    path = files.record(stats['full_precision_csv'], base=statistics, context='statistics precision CSV')
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == files.digest(path), 'precision CSV changed during read')
    try:
        reader = csv.DictReader(io.StringIO(data.decode('utf-8'), newline=''), strict=True)
        require(tuple(reader.fieldnames or ()) == CSV_FIELDS, 'precision CSV schema mismatch')
        rows = list(reader)
    except (csv.Error, UnicodeError) as exc:
        raise EvidenceError('invalid precision CSV') from exc
    require(len(rows) == 4, 'precision CSV row count mismatch')
    expected_pairs = {(c, m) for c in COMPONENTS for m in ('rmse', 'mae')}
    require({(r.get('component'), r.get('metric')) for r in rows} == expected_pairs,
            'precision CSV duplicate/missing metric')
    for row in rows:
        require(set(row) == set(CSV_FIELDS) and all(isinstance(v, str) for v in row.values()), 'precision CSV malformed row')
        c, metric = row['component'], row['metric']
        entry = receipt['results'][c]
        observed, reference = float(entry['metrics'][metric]), float(entry['control_only_metrics'][metric])
        require(row['physical_unit'] == PHYSICAL_UNITS[c] and row['n_units'] == str(entry['n_units'])
                and row['n_windows'] == str(entry['n_windows']), 'precision CSV physical unit/count contradiction')
        for key, value in (('candidate', observed), ('reference', reference), ('delta', observed - reference),
                           ('reference_plus_tolerance', reference + TOLERANCE),
                           ('reference_minus_tolerance', reference - TOLERANCE)):
            require(row[key] == format(value, '.17g') and row[key + '_hex'] == value.hex(),
                    'precision CSV numeric/hex contradiction: ' + c + '.' + metric + '.' + key)
        require(row['regression'] == str(observed > reference + TOLERANCE)
                and row['strict_gain'] == str(observed < reference - TOLERANCE), 'precision CSV gate contradiction')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New JSON report outside existing execution evidence')
    args = parser.parse_args()
    output = args.output.absolute()
    require(output.parent == Path(__file__).absolute().parent, 'report must be beside independent audit program')
    report = audit(RUN, Path(__file__).absolute().with_name(PUBLICATION))
    report['created_utc'] = datetime.now(timezone.utc).isoformat()
    report['audit_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with output.open('xb') as handle:
        handle.write(json_bytes(report))
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({'status': report['status'], 'output': str(output), 'f1_closed': False,
                      'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
