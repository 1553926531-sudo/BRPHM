"""Install/test the independent auditor in a NEW support directory only.

Never starts/restarts the controller or simulation; never calls an evaluator.
The only production audit invocation is the auditor's fixed read-only CLI.
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
GREEN = 'terminal_evidence_local_green_attempt_20261018_r6.json'
PUBLICATION = 'leo900_external_commitment_rest_publication_20261017T193909Z.json'
RUN = '/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1'
SUPPORT = RUN + '/terminal_evidence_support_20261018_r1'
REMOTE = r'''
import base64,hashlib,json,os,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
p=json.load(sys.stdin)
run=Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
support=run/'terminal_evidence_support_20261018_r1'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def record(path):return {'path':str(path),'sha256':digest(path),'size':path.stat().st_size}
def write(path,value):
 with path.open('x',encoding='utf-8',newline='\n') as h:
  json.dump(value,h,sort_keys=True,indent=2,allow_nan=False);h.write('\n');h.flush();os.fsync(h.fileno())
 path.chmod(0o444)
if not run.is_dir() or run.resolve()!=run or support.parent!=run:raise RuntimeError('run/support identity mismatch')
if support.exists() or support.is_symlink():raise FileExistsError('new independent support already exists; never overwrite')
names={'leo900_terminal_evidence_20261018.py','test_leo900_terminal_evidence_20261018.py',
 'terminal_evidence_local_green_attempt_20261018_r6.json','leo900_external_commitment_rest_publication_20261017T193909Z.json'}
if set(p['files'])!=names:raise RuntimeError('independent auditor membership mismatch')
decoded={name:base64.b64decode(row['base64'],validate=True) for name,row in p['files'].items()}
if sum(map(len,decoded.values()))>180000:raise RuntimeError('transfer budget exceeded')
for name,raw in decoded.items():
 if hashlib.sha256(raw).hexdigest()!=p['files'][name]['sha256']:raise RuntimeError('transfer hash mismatch')
green=json.loads(decoded['terminal_evidence_local_green_attempt_20261018_r6.json'])
if green['exit_code']!=0 or not re.search(r'Ran 32 tests in',green['stderr']):raise RuntimeError('local test gate incomplete')
for name,expected in green['code_sha256'].items():
 if p['files'][name]['sha256']!=expected:raise RuntimeError('source changed after local tests')
support.mkdir(exist_ok=False)
for name,raw in decoded.items():
 with (support/name).open('xb') as h:h.write(raw)
 (support/name).chmod(0o444)
environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
 'MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
started=datetime.now(timezone.utc).isoformat()
command=[sys.executable,'-B','-m','unittest','-v','test_leo900_terminal_evidence_20261018']
test=subprocess.run(command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=300)
count=re.search(r'Ran (\d+) tests? in',test.stdout+test.stderr)
count=int(count.group(1)) if count else None
passed=test.returncode==0 and count==32 and 'skipped' not in test.stderr
verification={'schema':'brphm-f1-independent-terminal-auditor-rack-tests-v1',
 'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
 'status':'PASS' if passed else 'FAIL','command':command,'exit_code':test.returncode,
 'test_count':count,'stdout':test.stdout,'stderr':test.stderr,
 'deployed_files':[record(support/name) for name in sorted(decoded)],
 'resources':{'cpu_affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),
 'numeric_threads':{k:environment[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}},
 'network_bytes_uploaded':sum(map(len,decoded.values())),'tensor_transfer_bytes':0,
 'real_final_labels_read_by_tests':False,'simulation_or_configuration_modified':False,
 'controller_or_evaluator_invoked':False,'candidate_or_route_modified':False,
 'deployer_sha256':p['deployer_sha256']}
write(support/'verification.json',verification)
if not passed:
 print(json.dumps({'status':'FAIL','verification':verification,'verification_file':record(support/'verification.json')}));raise SystemExit(1)
audit_command=[sys.executable,'-B',str(support/'leo900_terminal_evidence_20261018.py'),
 '--output',str(support/'first_read_only_audit.json')]
check=subprocess.run(audit_command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=300)
output=support/'first_read_only_audit.json'
audit={'command':audit_command,'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr,
 'report':json.loads(output.read_text()) if output.is_file() else None,
 'record':record(output) if output.is_file() else None}
write(support/'first_read_only_audit_execution.json',audit)
for name in decoded:
 if digest(support/name)!=p['files'][name]['sha256']:raise RuntimeError('deployed file drift')
print(json.dumps({'status':'PASS' if check.returncode==0 else 'FAIL','verification':verification,
 'verification_file':record(support/'verification.json'),'read_only_audit':audit,
 'audit_execution_file':record(support/'first_read_only_audit_execution.json')}))
raise SystemExit(check.returncode)
'''


def main():
    green = json.loads((HERE / GREEN).read_text(encoding='utf-8'))
    if green['exit_code'] != 0 or 'Ran 32 tests in' not in green['stderr'] or 'skipped' in green['stderr']:
        raise RuntimeError('complete local 32-test suite required')
    names = ('leo900_terminal_evidence_20261018.py', 'test_leo900_terminal_evidence_20261018.py', GREEN, PUBLICATION)
    files = {}
    for name in names:
        raw = (HERE / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if name in green['code_sha256'] and green['code_sha256'][name] != digest:
            raise RuntimeError('auditor/test changed since local test receipt')
        files[name] = {'sha256': digest, 'base64': base64.b64encode(raw).decode()}
    payload = {'files': files, 'deployer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    encoded = base64.b64encode(REMOTE.encode()).decode()
    command = ['/usr/bin/taskset', '-c', '4', '/usr/bin/nice', '-n', '15',
               '/mnt/data/BRPHM/rul-space/.venv-fm/bin/python', '-B', '-c',
               'import base64;exec(base64.b64decode(' + repr(encoded) + '))']
    ssh = ['ssh', '-i', r'C:\Users\Administrator\Documents\id_ed25519',
           '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
           'first@10.123.100.40', shlex.join(command)]
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(ssh, input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', timeout=650)
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError:
            document = {'status': 'ERROR', 'stdout': result.stdout}
        document.update(ssh_exit_code=result.returncode, ssh_stderr=result.stderr)
    except subprocess.TimeoutExpired:
        document = {'status': 'SSH_TIMEOUT', 'retry_allowed': False,
                    'reason': 'Inspect the new support directory before any subsequent action; no duplicate deploy.'}
    document.update(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
                    deployer_sha256=payload['deployer_sha256'], run=RUN, support=SUPPORT,
                    input_sha256={name: row['sha256'] for name, row in files.items()})
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = HERE / ('leo900_terminal_evidence_deployment_' + stamp + '.json')
    with output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'receipt': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                      'status': document.get('status'), 'test_count': document.get('verification', {}).get('test_count'),
                      'audit': document.get('read_only_audit'), 'diagnostic': document.get('stdout'),
                      'ssh_stderr': document.get('ssh_stderr')}))
    return 0 if document.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
