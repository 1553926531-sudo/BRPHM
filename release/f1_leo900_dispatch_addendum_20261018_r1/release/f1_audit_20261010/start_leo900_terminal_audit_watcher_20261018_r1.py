"""Launch only the new audit waiter once, using its verified Rack registration."""
from __future__ import annotations

import base64
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).absolute().parent
DEPLOYMENT = HERE / 'leo900_terminal_audit_watcher_deployment_20261017T212856Z.json'
DEPLOYMENT_SHA = '7ad1cc4ec56a0289606bd49823448d818b0f6ac26ad241994c99c69b64bf126e'
REMOTE = r'''
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
p=json.load(sys.stdin)
run=Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
support=run/'terminal_audit_watcher_support_20261018_r1'
launch=run/'terminal_audit_watcher_launch_20261018_r1'
runtime=run/'terminal_audit_watcher_runtime_20261018_r1'
def now():return datetime.now(timezone.utc).isoformat()
def record(path):
 if not path.is_file() or path.is_symlink() or path.resolve()!=path:raise RuntimeError('unsafe launch evidence')
 raw=path.read_bytes();return {'path':str(path),'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,doc):
 with path.open('x',encoding='utf-8',newline='\n') as h:
  json.dump(doc,h,sort_keys=True,indent=2);h.write('\n');h.flush();os.fsync(h.fileno())
 path.chmod(0o444)
if run.resolve()!=run or support.resolve()!=support:raise RuntimeError('run/support path mismatch')
if launch.exists() or launch.is_symlink() or runtime.exists():raise FileExistsError('existing launch/runtime; never launch a duplicate')
registration=support/'terminal_audit_watcher_registration.json'
verification=support/'verification.json'
if record(registration)['sha256']!=p['registration_sha256'] or record(verification)['sha256']!=p['verification_sha256']:raise RuntimeError('deployed registration/verification drift')
v=json.loads(verification.read_bytes())
if v['status']!='PASS' or v['test_count']!=9 or v['exit_code']!=0:raise RuntimeError('Rack nine-test gate incomplete')
for row in v['deployed_files']:
 if record(Path(row['path']))!=row:raise RuntimeError('deployed input drift')
environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1',**{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}}
prefix=['/usr/bin/taskset','-c','4','/usr/bin/nice','-n','15','/mnt/data/BRPHM/rul-space/.venv-fm/bin/python','-B',str(support/'leo900_terminal_audit_watcher_20261018_r1.py')]
check=prefix+['--check','--registration-sha256',p['registration_sha256']]
checked=subprocess.run(check,cwd=support,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=60)
if checked.returncode:raise RuntimeError('prelaunch audit-only check failed: '+checked.stderr)
state=json.loads(checked.stdout)
if state['state'] not in ('WAITING_FOR_CONTROLLER_TERMINAL','WAITING_FOR_AUDIT_RESOURCES','READY_FOR_READ_ONLY_AUDITS'):raise RuntimeError('unexpected dispatch preflight state')
launch.mkdir(exist_ok=False)
command=prefix+['--run','--registration-sha256',p['registration_sha256']]
intent={'schema':'brphm-f1-terminal-audit-watcher-launch-intent-v1','created_utc':now(),
 'command':command,'registration':record(registration),'verification':record(verification),
 'preflight_command':check,'preflight':state,'audit_only':True,'automatic_retry_permitted':False,
 'simulation_or_controller_modified':False,'candidate_modified':False,'evaluator_invoked':False}
write(launch/'launch_intent.json',intent)
with (launch/'watcher.stdout.log').open('xb') as out,(launch/'watcher.stderr.log').open('xb') as err:
 child=subprocess.Popen(command,cwd=support,env=environment,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
pid={'pid':child.pid,'launched_utc':now(),'command':command,'launch_intent':record(launch/'launch_intent.json')}
write(launch/'watcher_pid.json',pid)
receipt={'schema':'brphm-f1-terminal-audit-watcher-launch-receipt-v1','created_utc':now(),
 'state':'LAUNCHED_UNCONFIRMED','pid':child.pid,'intent':record(launch/'launch_intent.json'),
 'pid_record':record(launch/'watcher_pid.json'),'audit_only':True,'f1_closed':False,
 'scientific_success_claimed':False,'simulation_or_controller_modified':False}
write(launch/'launch_receipt.json',receipt)
print(json.dumps({'launch_receipt':receipt,'launch_receipt_record':record(launch/'launch_receipt.json'),
 'launch_intent':intent,'pid_record':pid,'run':str(run)}))
'''


def main():
    if hashlib.sha256(DEPLOYMENT.read_bytes()).hexdigest() != DEPLOYMENT_SHA:
        raise RuntimeError('deployment receipt hash mismatch')
    deployment = json.loads(DEPLOYMENT.read_text())
    if deployment['status'] != 'PASS' or deployment['verification']['test_count'] != 9:
        raise RuntimeError('verified Rack deployment required')
    payload = {'registration_sha256': deployment['registration_record']['sha256'],
               'verification_sha256': deployment['verification_record']['sha256']}
    code = 'import base64;exec(base64.b64decode(' + repr(base64.b64encode(REMOTE.encode()).decode()) + '))'
    remote = shlex.join(['python3', '-B', '-c', code])
    command = ['ssh', '-i', r'C:\Users\Administrator\Documents\id_ed25519',
        '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
        'first@10.123.100.40', remote]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, input=json.dumps(payload), capture_output=True,
        text=True, encoding='utf-8', timeout=90)
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        document = {'stdout': result.stdout}
    document.update(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
        ssh_exit_code=result.returncode, ssh_stderr=result.stderr,
        launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        deployment_receipt_sha256=DEPLOYMENT_SHA)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = HERE / ('leo900_terminal_audit_watcher_launch_' + stamp + '.json')
    with output.open('x', encoding='utf-8', newline='\n') as h:
        json.dump(document, h, sort_keys=True, indent=2);h.write('\n')
    print(json.dumps({'receipt': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'ssh_exit_code': result.returncode, 'launch_receipt': document.get('launch_receipt'),
        'diagnostic': document.get('stdout'), 'ssh_stderr': result.stderr}))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
