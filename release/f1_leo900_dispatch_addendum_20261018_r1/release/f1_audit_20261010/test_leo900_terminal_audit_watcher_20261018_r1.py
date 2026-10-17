"""Exercise dispatch safety using real disposable subprocesses, never final data."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

try:
    watcher = importlib.import_module('leo900_terminal_audit_watcher_20261018_r1')
except ModuleNotFoundError as exc:
    if exc.name != 'leo900_terminal_audit_watcher_20261018_r1':
        raise
    watcher = None

STATES = ('EXECUTION_CHAIN_VERIFIED', 'PREDICTION_SUMMARIES_VERIFIED',
          'NUMERICAL_STATISTICS_VERIFIED')
CHILD = '''import json,sys
from pathlib import Path
output,trace,name,status,exitcode=sys.argv[1:]
with Path(trace).open('a',encoding='utf-8') as h:h.write(name+'\\n')
if int(exitcode):raise SystemExit(int(exitcode))
with Path(output).open('x',encoding='utf-8') as h:
 json.dump({'status':status,'f1_closed':False,'scientific_success_claimed':False},h)
'''


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(watcher, 'terminal audit watcher implementation is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.trace = self.root / 'child_invocations.txt'
        self.terminal = self.root / 'controller_terminal.json'
        self.runtime = self.root / 'watcher_runtime'
        self.inputs, self.steps = {}, []
        for name, status in zip(('chain', 'predictions', 'statistics'), STATES):
            script = self.root / (name + '.py')
            script.write_text(CHILD, encoding='utf-8')
            self.inputs[str(script)] = hashlib.sha256(script.read_bytes()).hexdigest()
            output = self.root / (name + '_audit.json')
            self.steps.append({'name': name, 'expected_status': status,
                'output': str(output), 'command': [sys.executable, '-B', str(script),
                str(output), str(self.trace), name, status, '0']})
        self.plan = {'runtime': str(self.runtime), 'terminal': str(self.terminal),
            'inputs': self.inputs, 'stages': self.steps, 'production': False,
            'poll_seconds': 60}

    def finish_controller(self, state='EVALUATION_AND_STATISTICS_COMPLETED'):
        self.terminal.write_text(json.dumps({
            'schema': 'brphm-f1-final-continuation-terminal-v1', 'state': state,
            'formal_gate_passes': False}), encoding='utf-8')
        if os.name == 'posix':
            self.terminal.chmod(0o444)

    def test_pending_check_creates_nothing_and_does_not_invoke_auditors(self):
        self.assertEqual(watcher.preflight(self.plan)['state'], 'WAITING_FOR_CONTROLLER_TERMINAL')
        self.assertFalse(self.runtime.exists())
        self.assertFalse(self.trace.exists())
        self.assertTrue(all(not Path(s['output']).exists() for s in self.steps))

    def test_wait_then_runs_three_audits_once_in_order_without_claiming_f1(self):
        waits = []
        def wait(seconds):
            waits.append(seconds)
            self.assertFalse(self.trace.exists())
            self.finish_controller()
        report = watcher.run(self.plan, wait_fn=wait)
        self.assertEqual(waits, [60])
        self.assertEqual(self.trace.read_text().splitlines(), ['chain', 'predictions', 'statistics'])
        self.assertEqual(report['state'], 'AUDIT_REPORTS_VERIFIED')
        self.assertIs(report['formal_gate_passes'], False)
        self.assertIs(report['f1_closed'], False)
        self.assertIs(report['scientific_success_claimed'], False)
        self.assertEqual(len(report['stages']), 3)
        for row in report['stages']:
            self.assertEqual(row['exit_code'], 0)
            self.assertEqual(row['output']['sha256'], hashlib.sha256(Path(row['output']['path']).read_bytes()).hexdigest())
        self.assertEqual(report['controller_terminal']['sha256'], hashlib.sha256(self.terminal.read_bytes()).hexdigest())

    def test_error_controller_preserves_evidence_without_running_an_audit(self):
        self.finish_controller('ERROR')
        original = self.terminal.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'controller'):
            watcher.run(self.plan)
        self.assertFalse(self.trace.exists())
        self.assertEqual(self.terminal.read_bytes(), original)
        self.assertEqual(json.loads((self.runtime / 'watcher_terminal.json').read_text())['state'], 'ERROR')

    def test_duplicate_start_cannot_repeat_any_audit(self):
        self.finish_controller()
        watcher.run(self.plan)
        original = self.trace.read_bytes()
        with self.assertRaises(FileExistsError):
            watcher.run(self.plan)
        self.assertEqual(self.trace.read_bytes(), original)

    def test_nonzero_exit_stops_chain_without_retry(self):
        self.finish_controller()
        self.steps[0]['command'][-1] = '7'
        with self.assertRaisesRegex(RuntimeError, 'exit code 7'):
            watcher.run(self.plan)
        self.assertEqual(self.trace.read_text().splitlines(), ['chain'])
        terminal = json.loads((self.runtime / 'watcher_terminal.json').read_text())
        self.assertEqual(terminal['stages'][0]['exit_code'], 7)
        self.assertFalse(terminal['automatic_retry_permitted'])
        self.assertFalse(Path(self.steps[1]['output']).exists())

    def test_exit_zero_with_pending_report_cannot_advance(self):
        self.finish_controller()
        self.steps[0]['command'][-2] = 'PENDING_TERMINAL'
        with self.assertRaisesRegex(RuntimeError, 'status'):
            watcher.run(self.plan)
        self.assertEqual(self.trace.read_text().splitlines(), ['chain'])
        self.assertEqual(json.loads((self.runtime / 'watcher_terminal.json').read_text())['state'], 'ERROR')

    def test_existing_report_is_preserved_and_blocks_first_stage(self):
        self.finish_controller()
        output = Path(self.steps[2]['output'])
        output.write_bytes(b'existing report must survive')
        with self.assertRaises(FileExistsError):
            watcher.run(self.plan)
        self.assertEqual(output.read_bytes(), b'existing report must survive')
        self.assertFalse(self.trace.exists())

    def test_input_drift_while_waiting_blocks_all_audits(self):
        def wait(seconds):
            Path(next(iter(self.inputs))).write_bytes(b'changed registered code')
            self.finish_controller()
        with self.assertRaisesRegex(RuntimeError, 'input hash'):
            watcher.run(self.plan, wait_fn=wait)
        self.assertFalse(self.trace.exists())
        self.assertEqual(json.loads((self.runtime / 'watcher_terminal.json').read_text())['state'], 'ERROR')

    def test_controller_drift_after_first_audit_stops_later_stages(self):
        self.finish_controller()
        script = Path(self.steps[0]['command'][2])
        script.write_text(CHILD + '''\np=Path(sys.argv[7]);p.chmod(0o644)
p.write_text('{"schema":"brphm-f1-final-continuation-terminal-v1","state":"ERROR"}')
''', encoding='utf-8')
        self.inputs[str(script)] = hashlib.sha256(script.read_bytes()).hexdigest()
        self.steps[0]['command'].append(str(self.terminal))
        # The child intentionally changes a protected input after producing a valid audit.
        self.steps[0]['command'][2] = str(script)
        raw = script.read_text().replace('output,trace,name,status,exitcode=sys.argv[1:]',
                                         'output,trace,name,status,exitcode=sys.argv[1:6]')
        raw = raw.replace('p=Path(sys.argv[7])', 'p=Path(sys.argv[6])')
        script.write_text(raw, encoding='utf-8')
        self.inputs[str(script)] = hashlib.sha256(script.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, 'controller.*changed'):
            watcher.run(self.plan)
        self.assertEqual(self.trace.read_text().splitlines(), ['chain'])
        self.assertFalse(Path(self.steps[1]['output']).exists())


if __name__ == '__main__':
    unittest.main()
