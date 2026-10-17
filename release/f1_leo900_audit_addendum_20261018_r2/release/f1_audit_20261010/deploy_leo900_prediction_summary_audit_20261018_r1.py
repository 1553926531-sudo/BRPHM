"""Install the prediction-summary auditor once in a new isolated support folder.

Only synthetic tests and the read-only auditor run; existing simulation,
controller, freeze, candidate, evaluator and statistical analysis are untouched.
"""
from __future__ import annotations

import base64
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).absolute().parent
GREEN = 'prediction_summary_audit_local_20261018_r2.json'
PUBLICATION = 'leo900_external_commitment_rest_publication_20261017T193909Z.json'
RUN = '/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1'
SUPPORT = RUN + '/prediction_summary_audit_support_20261018_r1'
REMOTE = r'''
import base64,hashlib,json,os,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
p=json.load(sys.stdin)
run=Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
support=run/'prediction_summary_audit_support_20261018_r1'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def record(path):return {'path':str(path),'sha256':digest(path),'size':path.stat().st_size}
def write(path,value):
 with path.open('x',encoding='utf-8',newline='\n') as h:
  json.dump(value,h,sort_keys=True,indent=2,allow_nan=False);h.write('\n');h.flush();os.fsync(h.fileno())
 path.chmod(0o444)

if not run.is_dir() or run.resolve()!=run or support.parent!=run:raise RuntimeError('run/support identity mismatch')
if support.exists() or support.is_symlink():raise FileExistsError('support exists; inspect it, never overwrite or repeat deploy')
names={'leo900_prediction_summary_audit_20261018.py','test_leo900_prediction_summary_audit_20261018.py',
 'leo900_terminal_evidence_20261018_r2.py','test_leo900_terminal_evidence_20261018_r2.py',
 'prediction_summary_audit_local_20261018_r2.json','leo900_external_commitment_rest_publication_20261017T193909Z.json'}
if set(p['files'])!=names:raise RuntimeError('support file membership mismatch')
decoded={name:base64.b64decode(row['base64'],validate=True) for name,row in p['files'].items()}
if sum(map(len,decoded.values()))>240000:raise RuntimeError('small-code transfer budget exceeded')
for name,raw in decoded.items():
 if hashlib.sha256(raw).hexdigest()!=p['files'][name]['sha256']:raise RuntimeError('transfer hash mismatch')
green=json.loads(decoded['prediction_summary_audit_local_20261018_r2.json'])
if green['exit_code']!=0 or not green.get('sources_unchanged') or green.get('test_count')!=12 or not re.search(r'Ran 12 tests in',green['stderr']) or 'skipped' in green['stderr']:raise RuntimeError('local 12-test gate incomplete')
for name,expected in green['code_sha256'].items():
 if p['files'][name]['sha256']!=expected:raise RuntimeError('source changed after local tests')
affinity=sorted(os.sched_getaffinity(0));nice=os.getpriority(os.PRIO_PROCESS,0)
available=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M).group(1))*1024
if affinity!=[4] or nice<15 or available<1024**3:raise RuntimeError('reserved resource budget not satisfied')
support.mkdir(exist_ok=False)
for name,raw in decoded.items():
 with (support/name).open('xb') as h:h.write(raw)
 (support/name).chmod(0o444)
environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
 'MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
started=datetime.now(timezone.utc).isoformat()
command=[sys.executable,'-B','-m','unittest','-v','test_leo900_prediction_summary_audit_20261018']
test=subprocess.run(command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=300)
count=re.search(r'Ran (\d+) tests? in',test.stdout+test.stderr)
count=int(count.group(1)) if count else None
passed=test.returncode==0 and count==12 and 'skipped' not in test.stderr
verification={'schema':'brphm-f1-independent-prediction-summary-auditor-rack-tests-v1',
 'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
 'status':'PASS' if passed else 'FAIL','command':command,'exit_code':test.returncode,
 'test_count':count,'stdout':test.stdout,'stderr':test.stderr,
 'deployed_files':[record(support/name) for name in sorted(decoded)],
 'resources':{'cpu_affinity':affinity,'nice':nice,'mem_available_bytes_before':available,
 'numeric_threads':{key:environment[key] for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}},
 'raw_code_and_receipt_bytes_uploaded':sum(map(len,decoded.values())),
 'tensor_transfer_bytes':0,'real_final_labels_read_by_tests':False,
 'simulation_or_configuration_modified':False,'controller_or_evaluator_invoked':False,
 'candidate_or_route_modified':False,'deployer_sha256':p['deployer_sha256']}
write(support/'verification.json',verification)
if not passed:
 print(json.dumps({'status':'FAIL','verification':verification,'verification_file':record(support/'verification.json')}));raise SystemExit(1)
audit_command=[sys.executable,'-B',str(support/'leo900_prediction_summary_audit_20261018.py'),
 '--output',str(support/'first_read_only_prediction_summary_audit.json')]
check=subprocess.run(audit_command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=300)
output=support/'first_read_only_prediction_summary_audit.json'
audit={'command':audit_command,'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr,
 'report':json.loads(output.read_text()) if output.is_file() else None,
 'record':record(output) if output.is_file() else None}
write(support/'first_read_only_prediction_summary_audit_execution.json',audit)
for name in decoded:
 if digest(support/name)!=p['files'][name]['sha256']:raise RuntimeError('deployed input drift')
print(json.dumps({'status':'PASS' if check.returncode==0 else 'FAIL','verification':verification,
 'verification_file':record(support/'verification.json'),'read_only_audit':audit,
 'audit_execution_file':record(support/'first_read_only_prediction_summary_audit_execution.json')}))
raise SystemExit(check.returncode)
'''


def main():
    green = json.loads((HERE / GREEN).read_text(encoding='utf-8'))
    if (green['exit_code'] != 0 or not green.get('sources_unchanged') or green.get('test_count') != 12
            or 'Ran 12 tests in' not in green['stderr'] or 'skipped' in green['stderr']):
        raise RuntimeError('12 passing local tests and unchanged sources required')
    names = (*green['code_sha256'], GREEN, PUBLICATION)
    files = {}
    for name in names:
        if Path(name).name != name:
            raise RuntimeError('support input must be a basename')
        raw = (HERE / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if name in green['code_sha256'] and green['code_sha256'][name] != digest:
            raise RuntimeError('source drift since local test receipt')
        files[name] = {'sha256': digest, 'base64': base64.b64encode(raw).decode()}
    if sum((HERE / name).stat().st_size for name in names) > 240000:
        raise RuntimeError('small-code transfer budget exceeded')
    payload = {'files': files, 'deployer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    encoded = base64.b64encode(REMOTE.encode()).decode()
    remote = shlex.join(['/usr/bin/taskset', '-c', '4', '/usr/bin/nice', '-n', '15',
                        '/mnt/data/BRPHM/rul-space/.venv-fm/bin/python', '-B', '-c',
                        'import base64;exec(base64.b64decode(' + repr(encoded) + '))'])
    command = ['ssh', '-i', r'C:\Users\Administrator\Documents\id_ed25519',
               '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               'first@10.123.100.40', remote]
    started = datetime.now(timezone.utc).isoformat()
    try:
        run = subprocess.run(command, input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', timeout=650)
        try:
            document = json.loads(run.stdout)
        except json.JSONDecodeError:
            document = {'status': 'ERROR', 'stdout': run.stdout}
        document.update(ssh_exit_code=run.returncode, ssh_stderr=run.stderr)
    except subprocess.TimeoutExpired:
        document = {'status': 'SSH_TIMEOUT', 'retry_allowed': False,
                    'reason': 'Inspect the new support directory before subsequent action; do not duplicate deploy.'}
    document.update(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
                    deployer_sha256=payload['deployer_sha256'], run=RUN, support=SUPPORT,
                    input_sha256={name: row['sha256'] for name, row in files.items()},
                    transfer_budget_bytes=240000)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = HERE / ('leo900_prediction_summary_audit_deployment_' + stamp + '.json')
    with output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(document, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
    audit = document.get('read_only_audit', {})
    print(json.dumps({'receipt': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                      'status': document.get('status'), 'test_count': document.get('verification', {}).get('test_count'),
                      'read_only_audit_status': audit.get('report', {}).get('status'),
                      'read_only_audit_record': audit.get('record'),
                      'diagnostic': document.get('stdout'), 'ssh_stderr': document.get('ssh_stderr')}))
    return 0 if document.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
