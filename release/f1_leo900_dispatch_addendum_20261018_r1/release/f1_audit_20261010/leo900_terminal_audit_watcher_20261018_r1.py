"""Dispatch the three existing read-only auditors once after complete terminal.

This is execution plumbing: it never launches simulation, training, freezing,
evaluation or the production statistics program, and cannot close F1/the goal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
SUPPORT = RUN / 'terminal_audit_watcher_support_20261018_r1'
REGISTRATION = SUPPORT / 'terminal_audit_watcher_registration.json'
PYTHON = '/mnt/data/BRPHM/rul-space/.venv-fm/bin/python'
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')
AUDITORS = (
    ('chain', 'terminal_evidence_support_20261018_r2',
     'leo900_terminal_evidence_20261018_r2.py',
     '3d8ba40c8712a9af08b8fd684dda75ba86ef70a19530fd4111b4015ee190afd0',
     'EXECUTION_CHAIN_VERIFIED'),
    ('predictions', 'prediction_summary_audit_support_20261018_r1',
     'leo900_prediction_summary_audit_20261018.py',
     '8c2fbabdcedf8a3263a951baa3114415687a970446666f1e87e9b3af09450c2c',
     'PREDICTION_SUMMARIES_VERIFIED'),
    ('statistics', 'statistics_numerical_audit_support_20261018_r1',
     'leo900_statistics_numerical_audit_20261018.py',
     '105618a87df69fd750c70f3388e93c70af9d33ec46e60cfe73677dd8bc55f179',
     'NUMERICAL_STATISTICS_VERIFIED'),
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def regular(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts or not path.is_file() or any(
            p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
            for p in (path, *path.parents)):
        raise RuntimeError('unsafe or missing regular evidence: ' + str(path))
    return path


def capture(path):
    path = regular(path)
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise RuntimeError('evidence changed while reading: ' + str(path))
    return raw, {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def write_new(path, document):
    path = Path(path)
    with path.open('x', encoding='utf-8', newline='\n') as h:
        json.dump(document, h, sort_keys=True, indent=2, allow_nan=False)
        h.write('\n')
        h.flush()
        os.fsync(h.fileno())
    if os.name == 'posix':
        path.chmod(0o444)


def verify_inputs(plan):
    if not plan['inputs']:
        raise RuntimeError('empty input hash registry')
    for path, expected in plan['inputs'].items():
        if capture(path)[1]['sha256'] != expected:
            raise RuntimeError('input hash drift: ' + path)


def fresh_outputs(plan):
    for stage in plan['stages']:
        path = Path(stage['output'])
        if path.exists() or path.is_symlink():
            raise FileExistsError('preserve existing audit output: ' + str(path))


def preflight(plan, *, own_runtime=False):
    if not own_runtime and Path(plan['runtime']).exists():
        raise FileExistsError('audit watcher runtime already exists')
    verify_inputs(plan)
    fresh_outputs(plan)
    terminal = Path(plan['terminal'])
    if not terminal.exists() and not terminal.is_symlink():
        return {'state': 'WAITING_FOR_CONTROLLER_TERMINAL', 'observed_utc': utc_now()}
    regular(terminal)
    # The existing controller chmods only after flush/fsync. Avoid its write window.
    if plan['production'] and terminal.stat().st_mode & 0o222:
        return {'state': 'WAITING_FOR_CONTROLLER_TERMINAL', 'observed_utc': utc_now()}
    raw, record = capture(terminal)
    doc = json.loads(raw)
    if (doc.get('schema') != 'brphm-f1-final-continuation-terminal-v1'
            or doc.get('state') != 'EVALUATION_AND_STATISTICS_COMPLETED'):
        raise RuntimeError('controller terminal is not complete; preserve its error evidence')
    if plan['production']:
        if (sorted(os.sched_getaffinity(0)) != [4] or os.getpriority(os.PRIO_PROCESS, 0) < 15
                or any(os.environ.get(k) != '1' for k in THREADS)):
            raise RuntimeError('watcher requires CPU4, nice>=15, numeric threads=1')
        mem = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:'))
        if mem < 1024**3 or shutil.disk_usage(RUN).free < 1024**3:
            return {'state': 'WAITING_FOR_AUDIT_RESOURCES', 'observed_utc': utc_now()}
    return {'state': 'READY_FOR_READ_ONLY_AUDITS', 'controller_terminal': record,
            'formal_gate_passes': doc.get('formal_gate_passes'), 'observed_utc': utc_now()}


def run(plan, *, wait_fn=time.sleep):
    runtime = Path(plan['runtime'])
    runtime.mkdir(exist_ok=False)
    started, completed = utc_now(), []
    write_new(runtime / 'watcher_started.json', {'started_utc': started, 'plan': plan,
              'automatic_retry_permitted': False, 'f1_closed': False})
    try:
        while True:
            state = preflight(plan, own_runtime=True)
            if state['state'] == 'READY_FOR_READ_ONLY_AUDITS':
                break
            wait_fn(plan['poll_seconds'])
        terminal_record = state['controller_terminal']

        def check_protected():
            verify_inputs(plan)
            if capture(plan['terminal'])[1] != terminal_record:
                raise RuntimeError('controller terminal changed after audit dispatch')

        for stage in plan['stages']:
            check_protected()
            output = Path(stage['output'])
            if output.exists() or output.is_symlink():
                raise FileExistsError('preserve existing audit output: ' + str(output))
            row = {'name': stage['name'], 'command': stage['command'], 'started_utc': utc_now()}
            completed.append(row)
            write_new(runtime / (stage['name'] + '_started.json'), row)
            stdout, stderr = (runtime / (stage['name'] + suffix) for suffix in ('.stdout.log', '.stderr.log'))
            with stdout.open('xb') as out, stderr.open('xb') as err:
                result = subprocess.run(stage['command'], stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                    cwd=Path(stage['command'][2]).parent,
                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            row.update(exit_code=result.returncode, ended_utc=utc_now(),
                       stdout=capture(stdout)[1], stderr=capture(stderr)[1])
            write_new(runtime / (stage['name'] + '_exited.json'), row)
            if result.returncode:
                raise RuntimeError(stage['name'] + ' audit exit code ' + str(result.returncode))
            raw, output_record = capture(output)
            report = json.loads(raw)
            if (report.get('status') != stage['expected_status']
                    or report.get('f1_closed', False) is not False
                    or report.get('scientific_success_claimed', False) is not False):
                raise RuntimeError(stage['name'] + ' audit status/claim mismatch')
            check_protected()
            row.update(output=output_record, verified_status=report['status'])
            write_new(runtime / (stage['name'] + '_verified.json'), row)
        terminal = {'state': 'AUDIT_REPORTS_VERIFIED', 'started_utc': started, 'ended_utc': utc_now(),
            'controller_terminal': terminal_record, 'formal_gate_passes': state['formal_gate_passes'],
            'stages': completed, 'f1_closed': False, 'scientific_success_claimed': False,
            'automatic_retry_permitted': False,
            'note': 'Reports verified; F1 disposition and scientific interpretation require review.'}
    except BaseException as exc:
        terminal = {'state': 'ERROR', 'started_utc': started, 'ended_utc': utc_now(),
            'error_type': type(exc).__name__, 'error': str(exc), 'stages': completed,
            'automatic_retry_permitted': False, 'f1_closed': False, 'scientific_success_claimed': False}
        write_new(runtime / 'watcher_terminal.json', terminal)
        raise
    write_new(runtime / 'watcher_terminal.json', terminal)
    return terminal


def fixed_plan(inputs):
    stages = []
    for name, folder, script, sha256, status in AUDITORS:
        source = RUN / folder / script
        output = source.with_name('postterminal_' + name + '_audit_20261018_r1.json')
        stages.append({'name': name, 'expected_status': status, 'output': str(output),
            'command': [PYTHON, '-B', str(source), '--output', str(output)]})
    return {'runtime': str(RUN / 'terminal_audit_watcher_runtime_20261018_r1'),
        'terminal': str(RUN / 'final_continuation_runtime_20261018_r1/controller_terminal.json'),
        'inputs': dict(inputs), 'stages': stages, 'production': True, 'poll_seconds': 60}


def production_plan(registration_sha256):
    if os.name != 'posix' or Path(__file__).absolute().parent != SUPPORT or sys.executable != PYTHON:
        raise RuntimeError('production watcher restricted to registered Rack location/interpreter')
    raw, record = capture(REGISTRATION)
    if record['sha256'] != registration_sha256:
        raise RuntimeError('watcher registration hash mismatch')
    doc = json.loads(raw)
    if (doc.get('schema') != 'brphm-f1-terminal-audit-watcher-registration-v1'
            or doc.get('fixed_plan') != fixed_plan({})):
        raise RuntimeError('registered watcher commands differ from fixed read-only plan')
    inputs = {row['path']: row['sha256'] for row in doc['inputs']}
    if len(inputs) != len(doc['inputs']) or inputs.get(str(Path(__file__).absolute())) != capture(__file__)[1]['sha256']:
        raise RuntimeError('watcher source binding mismatch')
    for _, folder, script, expected, _ in AUDITORS:
        if inputs.get(str(RUN / folder / script)) != expected:
            raise RuntimeError('registered independent auditor identity mismatch')
    inputs[str(REGISTRATION)] = registration_sha256
    return fixed_plan(inputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--registration-sha256', required=True)
    args = parser.parse_args()
    plan = production_plan(args.registration_sha256)
    result = preflight(plan) if args.check else run(plan)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
