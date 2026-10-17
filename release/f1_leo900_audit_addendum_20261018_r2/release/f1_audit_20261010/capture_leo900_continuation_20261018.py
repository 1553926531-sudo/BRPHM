"""Capture read-only controller evidence without accessing MAT files or tensors."""
from __future__ import annotations

import base64
import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
root=Path('/mnt/data/BRPHM/rul-space/work/f1_leo900_formal_20261017_r1')
runtime=root/'final_continuation_runtime_20261018_r1'
launch=root/'final_continuation_launch_20261018_r1'
def capture(path,kind='json'):
 if not path.exists():return {'path':str(path),'exists':False}
 if path.is_symlink() or not path.is_file():raise RuntimeError('not a regular evidence file: '+str(path))
 before=path.stat();data=path.read_bytes();after=path.stat()
 if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
  raise RuntimeError('evidence changed during capture: '+str(path))
 result={'path':str(path),'exists':True,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
  'mtime_ns':after.st_mtime_ns,'mode':oct(after.st_mode&0o777)}
 if kind=='json':result['document']=json.loads(data)
 elif kind=='text':result['text']=data.decode('utf-8')
 elif kind=='tail':result['tail']=data[-6000:].decode('utf-8',errors='replace')
 return result
pid_record=capture(launch/'controller_pid.json')
pid=pid_record['document']['pid']
events=[capture(p) for p in sorted((runtime/'events').glob('*.json'))]
previous=None
for index,row in enumerate(events,1):
 document=row['document']
 if document['sequence']!=index or document['previous_event_sha256']!=previous:
  raise RuntimeError('broken controller event chain')
 previous=row['sha256']
process=subprocess.run(['ps','-p',str(pid)+',4138426,4141867,4141869,4141871,4141873',
 '-o','pid,ppid,lstart,ni,psr,pcpu,pmem,etime,stat,comm'],capture_output=True,text=True)
live={}
proc=Path('/proc')/str(pid)
if proc.exists():
 live={'cmdline':(proc/'cmdline').read_bytes().replace(b'\x00',b' ').decode(),
  'stat':(proc/'stat').read_text(),'cpu_affinity':sorted(os.sched_getaffinity(pid)),
  'nice':os.getpriority(os.PRIO_PROCESS,pid)}
documents={}
for key,path in {
 'launch_intent':launch/'launch_intent.json','launch_receipt':launch/'launch_receipt.json',
 'controller_plan':runtime/'controller_plan.json','terminal':runtime/'controller_terminal.json',
 'guard':root/'leo900_final_label_access_guard.json',
 'seal_receipt':root/'metadata_seal_execution_20261018_r1/seal_receipt.json',
 'freeze_manifest':root/'formal_output_execution_r1/freeze_manifest.json',
 'gate':root/'formal_output_execution_r1/same_partition_performance_gate.json',
 'final_receipt':root/'formal_output_execution_r1/final_receipt.json',
 'statistics_receipt':root/'formal_statistics_20261018_r1/statistics_receipt.json',
 }.items():documents[key]=capture(path)
logs={str(p.relative_to(root)):capture(p,'tail') for p in
 [launch/'controller.stdout.log',launch/'controller.stderr.log',
  *(runtime/(stage+suffix) for stage in ('seal','freeze','evaluate','statistics') for suffix in ('.stdout.log','.stderr.log'))]}
simulation={name:capture(root/'simulation_logs'/name,'text')
 for name in ('start_utc.txt','end_utc.txt','exit_status.txt')}
print(json.dumps({'schema':'brphm-f1-leo900-controller-observation-v1',
 'observed_utc':datetime.now(timezone.utc).isoformat(),'root':str(root),'pid_record':pid_record,
 'processes':process.stdout,'controller_process':live,'events':events,'event_chain_valid':True,
 'event_chain_last_sha256':previous,'documents':documents,'logs':logs,'simulation':simulation,
 'remote_writes':False,'mat_contents_read':False,'raw_or_tensor_labels_read':False,
 'simulation_or_configuration_modified':False,'candidate_modified':False,'controller_restarted':False}))
'''


def main():
    code = "import base64;exec(base64.b64decode(" + repr(base64.b64encode(REMOTE.encode()).decode()) + "))"
    remote = shlex.join(["python3", "-B", "-c", code])
    command = ["ssh", "-i", r"C:\Users\Administrator\Documents\id_ed25519",
               "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2",
               "first@10.123.100.40", remote]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60)
    if result.returncode:
        raise RuntimeError(f"read-only SSH capture failed ({result.returncode}): {result.stderr}")
    document = json.loads(result.stdout)
    document["capture_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = HERE / f"leo900_continuation_observation_{stamp}.json"
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"output": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "observed_utc": document["observed_utc"], "processes": document["processes"],
        "event_types": [row["document"]["event_type"] for row in document["events"]],
        "event_chain_valid": document["event_chain_valid"],
        "terminal": document["documents"]["terminal"],
        "guard_exists": document["documents"]["guard"]["exists"],
        "stderr": document["logs"][str(Path('final_continuation_launch_20261018_r1/controller.stderr.log').as_posix())]}))


if __name__ == "__main__":
    main()
