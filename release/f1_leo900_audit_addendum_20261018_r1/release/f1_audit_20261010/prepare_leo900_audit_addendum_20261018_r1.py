"""Prepare an additive, offline-verifiable F1 audit package; no remote access."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREVIOUS = REPO / 'release/f1_leo900_pre_final_commitment_20261018_r1'
PACKAGE = REPO / 'release/f1_leo900_audit_addendum_20261018_r1'
ANCHOR = '846cdaac03beab2bacb9834bde1ed8fff1c77141'
R8_SHA = '7ace7afcbb8756f681134975fc999865745086d8b62db751977c73a138de2f29'
PREVIOUS_MANIFEST_SHA = '7a489927d3cb6001fff91b7b9af77d9da0468f6721a053fa90be8d8025ca9490'
SECRET = re.compile(rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,}')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(doc):
    return (json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def safe_name(name):
    p = PurePosixPath(name)
    if not isinstance(name, str) or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise RuntimeError('unsafe artifact path')
    return name


def collect():
    """Resolve historic local/package-relative hash edges before writing anything."""
    seeds = [
        'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.json',
        'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R8.md',
        'test_leo900_terminal_evidence_20261018_r2.py',
        'prepare_leo900_audit_addendum_20261018_r1.py',
        'publish_leo900_audit_addendum_20261018_r1.py',
        'publish_leo900_external_commitment_rest_20261018.py',
        'publish_leo900_external_commitment_20261018.py',
        'capture_leo900_metadata_20261018.py',
        'capture_leo900_continuation_20261018.py',
        'leo900_generation_metadata_20261017T210004Z.json',
        'leo900_continuation_observation_20261017T210004Z.json',
    ]
    r8 = HERE / seeds[0]
    if sha(r8.read_bytes()) != R8_SHA:
        raise RuntimeError('R8 ledger differs from the preserved anchor')
    if sha((PREVIOUS / 'SHA256_MANIFEST.json').read_bytes()) != PREVIOUS_MANIFEST_SHA:
        raise RuntimeError('original pre-final manifest differs')
    todo = [HERE / n for n in seeds]
    todo.extend(p for p in PREVIOUS.rglob('*') if p.is_file())
    payload, edges = {}, []
    allowed = (HERE.resolve(), PREVIOUS.resolve())
    while todo:
        path = todo.pop()
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not any(resolved.is_relative_to(a) for a in allowed):
            raise RuntimeError('artifact is outside the two approved text directories')
        name = resolved.relative_to(REPO).as_posix()
        if name in payload:
            continue
        data = path.read_bytes()
        if len(data) > 512_000 or SECRET.search(data):
            raise RuntimeError('oversized or credential-like artifact: ' + name)
        if data.decode('utf-8').encode('utf-8') != data:
            raise RuntimeError('artifact is not byte-exact UTF-8: ' + name)
        payload[name] = data
        if path.suffix != '.json':
            continue
        doc = json.loads(data)
        for key, expected in doc.get('artifact_sha256', {}).items():
            safe_name(key)
            candidates = (REPO / key, path.parent / key, HERE / key, PREVIOUS / key)
            matches = []
            for candidate in candidates:
                if candidate.is_file() and not candidate.is_symlink():
                    target = candidate.resolve()
                    if any(target.is_relative_to(a) for a in allowed) and sha(target.read_bytes()) == expected:
                        matches.append(target)
            if not matches:
                raise RuntimeError('unresolved artifact hash edge: ' + key)
            target = matches[0]
            edges.append({'source': name, 'key': key, 'target': target.relative_to(REPO).as_posix(), 'sha256': expected})
            todo.append(target)
    if len(payload) > 150 or sum(map(len, payload.values())) > 3_000_000:
        raise RuntimeError('package exceeds the fixed small-text traffic budget')
    return payload, edges


VERIFIER = '''"""Verify this additive F1 package offline; no network, models or data."""
import hashlib,json
from pathlib import Path,PurePosixPath
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256_MANIFEST.json').read_bytes())
for name,expected in manifest['files'].items():
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or ':' in name or '\\\\' in name: raise RuntimeError('unsafe manifest path')
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
'''


def main():
    if PACKAGE.exists():
        raise RuntimeError('preserve existing additive package; do not replace it')
    payload, edges = collect()
    now = datetime.now(timezone.utc).isoformat()
    payload['INTEGRITY_GRAPH.json'] = encoded({
        'schema': 'brphm-f1-addendum-artifact-graph-v1', 'created_utc': now,
        'artifact_edges': sorted(edges, key=lambda e: (e['source'], e['key'])),
        'original_commit': ANCHOR, 'r8_sha256': R8_SHA,
        'original_manifest_sha256': PREVIOUS_MANIFEST_SHA,
        'goal_status': 'active', 'f1_closed': False,
        'stale_goal_objective_note': 'The old objective says F1 passed15/15. R5-R8 supersede this implication; F1 remains OPEN until the real terminal evidence is assessed.',
        'scientific_success_claimed': False,
    })
    payload['README.md'] = f'''# LEO900 additive audit evidence

This package appends R5-R8 audit corrections, the independent statistical numerical verifier, the retained failed/successful synthetic test receipts, and read-only execution observations. **F1 remains OPEN.** The overall F1-F10 goal remains active and manuscript/F2-F10 substantive edits remain frozen.

This is an audit addendum. The original candidate and analysis commitment remains [commit {ANCHOR}](https://github.com/1553926531-sudo/BRPHM/commit/{ANCHOR}). No new candidate, tuning decision, evaluation or statistical protocol is introduced. The original small text commitment is copied byte-for-byte inside this bundle to make the historical artifact hash edges verifiable offline; no simulation, model tensor or dataset is copied.

Run `python -B verify_addendum.py` here. It checks all member SHA256 values, resolves every included `artifact_sha256` edge, and checks Python syntax without executing those modules. Historic bare paths are resolved explicitly in `INTEGRITY_GRAPH.json`. Published source paths are preserved underneath this package root.

The independent numerical verifier's synthetic suite can be run in `release/f1_audit_20261010` with `python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018`. It needs NumPy and SciPy; the verifier itself imports NumPy plus the separate provenance verifier. Production CLIs are fixed to the registered Rack root. Do not run production evaluators, deployers, controller launchers or package publishers to reproduce synthetic tests.

The latest included observation at 2026-10-17T21:00:04Z reports BAT23/48 and RWA0/48 with the existing controller awaiting simulation. Observations can become stale. Synthetic test success, a valid hash chain and a running process do not establish a final result or scientific superiority. The final candidate must not be revised after observing this final test.

The saved-unit-summary numerical audit does not independently derive those summaries from raw truth/prediction arrays. It is a different arithmetic implementation of the registered statistics, conditional on those saved summaries and the same NumPy RNG contract. The three model seeds are ensemble constituents, not independent experiments. Historical outer/LEO800 outcomes remain development evidence. One new final orbit is not population-wide replication.

All timestamps inside local receipts are self-recorded. GitHub server readback records observed availability, and Git history can be changed; neither proves global historical non-access. Later audit publication cannot be backdated or substituted for the original candidate commitment.

Prepared UTC: {now}. Repository authorization applies only to BRPHM. This package performs no ModelScope write, IEEE upload/submission/contact, or competition-asset operation.
'''.encode()
    payload['verify_addendum.py'] = VERIFIER.encode()
    manifest = {'schema': 'brphm-f1-audit-addendum-manifest-v1', 'created_utc': now,
                'kind': 'additive audit evidence; no new candidate registration',
                'files': {name: sha(data) for name, data in sorted(payload.items())},
                'f1_closed': False, 'scientific_success_claimed': False}
    payload['SHA256_MANIFEST.json'] = encoded(manifest)
    for name, data in payload.items():
        safe_name(name)
        write_new(PACKAGE / name, data)
    print(json.dumps({'package': str(PACKAGE), 'files': len(payload),
                      'bytes': sum(map(len, payload.values())), 'artifact_edges': len(edges),
                      'manifest_sha256': sha(payload['SHA256_MANIFEST.json']), 'f1_closed': False}))


if __name__ == '__main__':
    main()
