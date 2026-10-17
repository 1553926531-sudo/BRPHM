"""Offline byte verification of this pre-final commitment; no datasets or network."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
doc=json.loads((root/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
for name,expected in doc['files'].items():
 p=root/name
 assert p.is_file() and not p.is_symlink(),name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,name
actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
assert actual==set(doc['files'])|{'SHA256_MANIFEST.json'},'unlisted or missing file'
print(json.dumps({'status':'PASS','files_verified':len(doc['files']),'f1_closed':False}))
