"""Verify package membership and immediate R10 evidence without running research."""
import ast, hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
files=manifest['files']
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
assert actual==set(files)|{'SHA256_MANIFEST.json'},'unexpected package membership'
for name,expected in files.items():
 p=root/name
 assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),name
 assert sha(p)==expected,name
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8'),filename=name)
ledger=json.loads((root/'release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R10.json').read_text(encoding='utf-8'))
fields=('location','original','problem','modification','evidence','source','date','hash','command','result','cross_validation','confidence','remaining_risk','status')
assert ledger['f1_closed'] is False and ledger['goal_status']=='active'
assert len(ledger['findings'])==4
for row in ledger['findings']:
 assert all(row.get(k) for k in fields)
 assert all(name in ledger['artifact_sha256'] for name in row['evidence'])
for name,expected in ledger['artifact_sha256'].items():
 assert files[name]==expected and sha(root/name)==expected,name
graph=json.loads((root/'INTEGRITY_GRAPH.json').read_text(encoding='utf-8'))
assert graph['r10_sha256']==sha(root/'release/f1_audit_20261010/F1_LEO900_PREFLIGHT_EVIDENCE_20261018R10.json')
assert graph['immediate_r10_evidence']==ledger['artifact_sha256']
print(json.dumps({'status':'IMMEDIATE_R10_PACKAGE_VERIFIED','files':len(files)+1,'immediate_evidence_files':len(ledger['artifact_sha256']),'python_sources_parsed':sum(n.endswith('.py') for n in files),'prior_history_recursively_verified':False,'f1_closed':False,'scientific_success_claimed':False}))
