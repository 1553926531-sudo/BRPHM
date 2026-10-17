"""Verify this additive F1 package offline; no network, models or data."""
import hashlib,json
from pathlib import Path,PurePosixPath
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256_MANIFEST.json').read_bytes())
for name,expected in manifest['files'].items():
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name: raise RuntimeError('unsafe manifest path')
 f=root/name
 if f.is_symlink() or not f.is_file(): raise RuntimeError('missing/nonregular member: '+name)
 if hashlib.sha256(f.read_bytes()).hexdigest()!=expected: raise RuntimeError('hash mismatch: '+name)
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
if actual!=set(manifest['files'])|{'SHA256_MANIFEST.json'}: raise RuntimeError('membership differs')
graph=json.loads((root/'INTEGRITY_GRAPH.json').read_bytes())
for edge in graph['artifact_edges']:
 doc=json.loads((root/edge['source']).read_bytes())
 if doc['artifact_sha256'][edge['key']]!=edge['sha256']: raise RuntimeError('source hash edge differs')
 if hashlib.sha256((root/edge['target']).read_bytes()).hexdigest()!=edge['sha256']: raise RuntimeError('target hash edge differs')
for name in manifest['files']:
 if name.endswith('.py'): compile((root/name).read_bytes(),name,'exec')
print(json.dumps({'status':'PASS','files_verified':len(manifest['files']), 'artifact_edges_verified':len(graph['artifact_edges']), 'python_syntax_checked':True, 'f1_closed':False,'scientific_success_claimed':False}))
