"""Read only the running LEO900 job's metadata; never load simulation labels."""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REMOTE = r'''
import hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
root = Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
files = {}
for directory in (root/'project/generated', root/'project/data/raw/sim'):
    if directory.exists():
        for path in directory.rglob('*.mat'):
            if path.name.startswith(('BAT_LEO900_', 'RWA_LEO900_')):
                info = path.stat()
                files[str(path.resolve())] = {'name': path.name, 'size': info.st_size,
                    'mtime_ns': info.st_mtime_ns}
logs = {}
for name in ('start_utc.txt', 'end_utc.txt', 'exit_status.txt', 'matlab_stdout.log', 'matlab_stderr.log'):
    path = root/'simulation_logs'/name
    if path.exists():
        info = path.stat()
        logs[name] = {'size': info.st_size, 'mtime_ns': info.st_mtime_ns}
        if name in ('start_utc.txt', 'end_utc.txt', 'exit_status.txt'):
            logs[name]['value'] = path.read_text().strip()
code = {}
for directory in (root/'protocol_inputs', root/'evidence'):
    if directory.exists():
        for path in directory.glob('*.py'):
            code[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
memory = {}
for line in Path('/proc/meminfo').read_text().splitlines():
    key, value = line.split(':', 1)
    if key in ('MemTotal','MemAvailable','SwapFree'):
        memory[key] = value.strip()
process = subprocess.run(['ps','-p','4138426,4141867,4141869,4141871,4141873',
    '-o','pid,ppid,ni,pcpu,pmem,etime,comm'], capture_output=True, text=True)
usage = shutil.disk_usage('/mnt/data')
print(json.dumps({'observed_utc':datetime.now(timezone.utc).isoformat(),
    'root':str(root), 'files':sorted(files.values(), key=lambda item:item['name']),
    'counts':{c:sum(item['name'].startswith(c.upper()+'_') for item in files.values()) for c in ('bat','rwa')},
    'logs':logs, 'code_sha256':code, 'processes':process.stdout, 'memory':memory,
    'disk_free_bytes':usage.free, 'semantic_labels_read':False, 'mat_contents_read':False,
    'simulation_or_configuration_modified':False, 'remote_writes':False}))
'''


def main():
    encoded = base64.b64encode(REMOTE.encode()).decode('ascii')
    command = "python3 -B -c \"import base64;exec(base64.b64decode('" + encoded + "'))\""
    result = subprocess.run(['ssh', '-i', r'C:\Users\Administrator\Documents\id_ed25519',
        '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
        'first@10.123.100.40', command], capture_output=True, text=True, timeout=55)
    if result.returncode:
        raise RuntimeError(f'SSH metadata query failed ({result.returncode}): {result.stderr.strip()}')
    document = json.loads(result.stdout)
    document['schema'] = 'brphm-f1-leo900-generation-metadata-progress-v1'
    document['capture_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = Path(__file__).with_name(f'leo900_generation_metadata_{stamp}.json')
    with output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(document, handle, ensure_ascii=True, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'output':str(output), 'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'counts':document['counts'], 'observed_utc':document['observed_utc'],
        'processes':document['processes'], 'logs':document['logs']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
