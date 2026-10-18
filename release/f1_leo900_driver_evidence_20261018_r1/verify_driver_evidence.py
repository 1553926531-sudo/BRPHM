"""Check captured evidence and driver arithmetic without connecting or running research."""
import ast, hashlib, json, math
from pathlib import Path, PurePosixPath
root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((root/'SHA256_MANIFEST.json').read_bytes())
files=manifest['files']
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
assert actual==set(files)|{'SHA256_MANIFEST.json'},'package membership differs'
for name,expected in files.items():
 p=PurePosixPath(name)
 assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name
 path=root/name
 assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
 raw=path.read_bytes()
 assert sha(raw)==expected,name
 if name.endswith('.py'):ast.parse(raw.decode('utf-8'),filename=name)
directory=root/'release/f1_audit_20261010'
doc=json.loads((directory/'F1_LEO900_PERIODIC_DRIVER_EVIDENCE_20261018R1.json').read_bytes())
fields=('location','original','problem','modification','evidence','source','date','hash','command','result','cross_validation','confidence','remaining_risk','status')
assert all(doc['fields'].get(k) for k in fields)
assert doc['f1_closed'] is False and doc['goal_status']=='active'
assert doc['scientific_success_claimed'] is False and doc['semantic_final_labels_read'] is False
assert doc['simulation_or_candidate_modified'] is False
assert doc['manuscript_and_f2_f10_substantive_edits_frozen'] is True
for name,expected in doc['fields']['hash']['input_sha256'].items():
 assert sha((directory/name).read_bytes())==expected,name
assert sha((directory/'audit_leo900_periodic_environment_20261018_r1.py').read_bytes())==doc['fields']['hash']['analysis_program_sha256']
v=doc['mathematical_cross_check']
period=2*math.pi*math.sqrt(v['semimajor_axis_km']**3/v['gravitational_parameter_km3_s2'])
assert period==v['semimajor_period_s']
assert (period-5740)/period==v['fractional_period_shortening']
assert period/5740-1==v['relative_repeat_rate_increase']
assert len(doc['driver_diagnostics'])==3 and len(doc['static_model_bindings'])==2
for row in doc['driver_diagnostics']:
 count=row['tile_period_s']//10
 assert row['duty_percent_recomputed']==100*row['umbra_samples']/count
 assert row['charge_current_recomputed_a']==-2*row['umbra_samples']/(count-row['umbra_samples'])
graph=json.loads((root/'INTEGRITY_GRAPH.json').read_bytes())
assert graph['periodic_driver_record_sha256']==sha((directory/'F1_LEO900_PERIODIC_DRIVER_EVIDENCE_20261018R1.json').read_bytes())
assert graph['immediate_input_sha256']==doc['fields']['hash']['input_sha256']
print(json.dumps({'status':'DRIVER_EVIDENCE_PACKAGE_VERIFIED','files':len(files)+1,'immediate_input_files':8,'f1_closed':False,'scientific_success_claimed':False,'runtime_or_model_predictions_reexecuted':False}))
