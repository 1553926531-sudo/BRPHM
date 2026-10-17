"""Deploy the audit-only waiter to a new folder; do not launch it here."""
from __future__ import annotations

import base64
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).absolute().parent
NAMES = ('leo900_terminal_audit_watcher_20261018_r1.py',
         'test_leo900_terminal_audit_watcher_20261018_r1.py',
         'terminal_audit_watcher_local_20261018_r1.json')
REMOTE = r'''
import base64,hashlib,importlib.util,json,os,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
p=json.load(sys.stdin)
run=Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
support=run/'terminal_audit_watcher_support_20261018_r1'
runtime=run/'terminal_audit_watcher_runtime_20261018_r1'
def now():return datetime.now(timezone.utc).isoformat()
def record(path):
 if not path.is_file() or path.is_symlink() or path.resolve()!=path:raise RuntimeError('unsafe input '+str(path))
 raw=path.read_bytes()
 return {'path':str(path),'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,doc):
 with path.open('x',encoding='utf-8',newline='\n') as h:
  json.dump(doc,h,sort_keys=True,indent=2,allow_nan=False);h.write('\n');h.flush();os.fsync(h.fileno())
 path.chmod(0o444)
if run.resolve()!=run or not run.is_dir():raise RuntimeError('run identity mismatch')
if support.exists() or support.is_symlink() or runtime.exists():raise FileExistsError('preserve existing watcher support/runtime; never repeat deploy')
names={'leo900_terminal_audit_watcher_20261018_r1.py','test_leo900_terminal_audit_watcher_20261018_r1.py','terminal_audit_watcher_local_20261018_r1.json'}
if set(p['files'])!=names:raise RuntimeError('unexpected transfer membership')
raws={n:base64.b64decode(row['base64'],validate=True) for n,row in p['files'].items()}
if sum(map(len,raws.values()))>64000:raise RuntimeError('small-code transfer budget exceeded')
for n,raw in raws.items():
 if hashlib.sha256(raw).hexdigest()!=p['files'][n]['sha256']:raise RuntimeError('transfer hash mismatch')
green=json.loads(raws['terminal_audit_watcher_local_20261018_r1.json'])
if green['exit_code']!=0 or green['test_count']!=9 or not green['sources_unchanged'] or 'skipped' in green['stderr']:raise RuntimeError('local test gate incomplete')
for n,h in green['code_sha256'].items():
 if p['files'][n]['sha256']!=h:raise RuntimeError('source changed since local tests')
affinity=sorted(os.sched_getaffinity(0));nice=os.getpriority(os.PRIO_PROCESS,0)
available=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M).group(1))*1024
if affinity!=[4] or nice<15 or available<1024**3:raise RuntimeError('reserved resource budget not satisfied')
environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}}
os.environ.update(environment)
support.mkdir(exist_ok=False)
for n,raw in raws.items():
 with (support/n).open('xb') as h:h.write(raw)
 (support/n).chmod(0o444)
started=now()
command=[sys.executable,'-B','-m','unittest','-v','test_leo900_terminal_audit_watcher_20261018_r1']
r=subprocess.run(command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=120)
count=re.search(r'Ran (\d+) tests? in',r.stderr)
count=int(count.group(1)) if count else None
passed=r.returncode==0 and count==9 and 'skipped' not in r.stderr
verification={'status':'PASS' if passed else 'FAIL','started_utc':started,'ended_utc':now(),
 'command':command,'exit_code':r.returncode,'test_count':count,'stdout':r.stdout,'stderr':r.stderr,
 'deployed_files':[record(support/n) for n in sorted(names)],
 'resources':{'cpu_affinity':affinity,'nice':nice,'mem_available_bytes':available,'numeric_threads':1},
 'real_final_data_read':False,'simulation_or_controller_modified':False,'evaluator_invoked':False,
 'raw_code_and_receipt_bytes_uploaded':sum(map(len,raws.values())),'tensor_transfer_bytes':0}
write(support/'verification.json',verification)
if not passed:
 print(json.dumps({'status':'FAIL','verification':verification}));raise SystemExit(1)
spec=importlib.util.spec_from_file_location('leo900_watcher_registration',support/'leo900_terminal_audit_watcher_20261018_r1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
inputs={str(support/'leo900_terminal_audit_watcher_20261018_r1.py'):record(support/'leo900_terminal_audit_watcher_20261018_r1.py')}
for _,folder,script,expected,_ in module.AUDITORS:
 directory=run/folder
 if record(directory/script)['sha256']!=expected:raise RuntimeError('existing registered auditor hash mismatch')
 for path in sorted(directory.glob('*.py')):
  inputs[str(path)]=record(path)
 publication=directory/'leo900_external_commitment_rest_publication_20261017T193909Z.json'
 inputs[str(publication)]=record(publication)
registration={'schema':'brphm-f1-terminal-audit-watcher-registration-v1','created_utc':now(),
 'scope':'Audit-only operational dispatch; no scientific candidate/protocol change',
 'fixed_plan':module.fixed_plan({}),'inputs':list(inputs.values()),
 'verification':record(support/'verification.json'),'automatic_retry_permitted':False,
 'f1_closed':False,'scientific_success_claimed':False,'simulation_or_controller_modified':False}
write(support/'terminal_audit_watcher_registration.json',registration)
registration_record=record(support/'terminal_audit_watcher_registration.json')
check_command=[sys.executable,'-B',str(support/'leo900_terminal_audit_watcher_20261018_r1.py'),
 '--check','--registration-sha256',registration_record['sha256']]
check=subprocess.run(check_command,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=60)
check_receipt={'command':check_command,'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr}
write(support/'prelaunch_read_only_check.json',check_receipt)
for n in names:
 if record(support/n)['sha256']!=p['files'][n]['sha256']:raise RuntimeError('deployed source drift')
print(json.dumps({'status':'PASS' if check.returncode==0 else 'FAIL','verification':verification,
 'verification_record':record(support/'verification.json'),'registration':registration,
 'registration_record':registration_record,'prelaunch_check':check_receipt,
 'prelaunch_check_record':record(support/'prelaunch_read_only_check.json'),
 'watcher_launched':False,'runtime_exists':runtime.exists()}))
raise SystemExit(check.returncode)
'''


def main():
    green = json.loads((HERE / NAMES[-1]).read_text())
    if green['exit_code'] or green['test_count'] != 9 or not green['sources_unchanged']:
        raise RuntimeError('nine passing local tests required')
    files = {}
    for name in NAMES:
        raw = (HERE / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if name in green['code_sha256'] and green['code_sha256'][name] != digest:
            raise RuntimeError('local source hash drift')
        files[name] = {'sha256': digest, 'base64': base64.b64encode(raw).decode()}
    if sum((HERE / name).stat().st_size for name in NAMES) > 64000:
        raise RuntimeError('small-code transfer budget exceeded')
    code = 'import base64;exec(base64.b64decode(' + repr(base64.b64encode(REMOTE.encode()).decode()) + '))'
    remote = shlex.join(['/usr/bin/taskset', '-c', '4', '/usr/bin/nice', '-n', '15',
        '/mnt/data/BRPHM/rul-space/.venv-fm/bin/python', '-B', '-c', code])
    command = ['ssh', '-i', r'C:\Users\Administrator\Documents\id_ed25519',
        '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
        'first@10.123.100.40', remote]
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(command, input=json.dumps({'files': files}), capture_output=True,
            text=True, encoding='utf-8', timeout=240)
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError:
            document = {'status': 'ERROR', 'stdout': result.stdout}
        document.update(ssh_exit_code=result.returncode, ssh_stderr=result.stderr)
    except subprocess.TimeoutExpired:
        document = {'status': 'SSH_TIMEOUT', 'retry_allowed': False,
            'reason': 'Inspect exclusive support directory before any further action.'}
    document.update(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
        deployer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256={name: row['sha256'] for name, row in files.items()}, transfer_budget_bytes=64000)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = HERE / ('leo900_terminal_audit_watcher_deployment_' + stamp + '.json')
    with output.open('x', encoding='utf-8', newline='\n') as h:
        json.dump(document, h, sort_keys=True, indent=2, allow_nan=False)
        h.write('\n')
    print(json.dumps({'receipt': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'status': document.get('status'), 'test_count': document.get('verification', {}).get('test_count'),
        'registration': document.get('registration_record'), 'prelaunch_check': document.get('prelaunch_check'),
        'diagnostic': document.get('stdout'), 'ssh_stderr': document.get('ssh_stderr')}))
    return 0 if document.get('status') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
