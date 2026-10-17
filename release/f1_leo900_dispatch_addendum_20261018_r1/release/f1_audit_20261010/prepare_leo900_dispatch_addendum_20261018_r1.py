"""Prepare only the immediate R10 evidence, without copying earlier closures."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import prepare_leo900_audit_addendum_20261018_r1 as support

HERE, REPO = support.HERE, support.REPO
PACKAGE = REPO / 'release/f1_leo900_dispatch_addendum_20261018_r1'
BASE = '523619aed9dfb8f5622332acfe26363ffd682b2c'
LEDGER_SHA = '72246da233fedb8eacbfb53dd544e0dab113a51229309042d18a9d2d00569e69'

VERIFIER = r'''"""Verify package membership and immediate R10 evidence without running research."""
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
'''


def main():
    if PACKAGE.exists():
        raise FileExistsError('dispatch package already exists; preserve it')
    ledger_path = HERE / 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R10.json'
    assert support.sha(ledger_path.read_bytes()) == LEDGER_SHA
    ledger = json.loads(ledger_path.read_bytes())
    payload = {}
    names = set(ledger['artifact_sha256']) | {
        'release/f1_audit_20261010/' + name for name in (
            ledger_path.name, ledger_path.with_suffix('.md').name, Path(__file__).name,
            'publish_leo900_dispatch_addendum_20261018_r1.py',
            'publish_leo900_audit_addendum_20261018_r2.py',
            'publish_leo900_external_commitment_20261018.py',
            'publish_leo900_external_commitment_rest_20261018.py',
            'dispatch_package_preparation_failure_20261018_r1.json')}
    for name in sorted(names):
        support.safe_name(name)
        path = REPO / name
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(HERE.resolve())
        data = path.read_bytes()
        assert data.decode('utf-8').encode('utf-8') == data and not support.SECRET.search(data), name
        if name in ledger['artifact_sha256']:
            assert support.sha(data) == ledger['artifact_sha256'][name], name
        payload[name] = data
    now = datetime.now(timezone.utc).isoformat()
    payload['INTEGRITY_GRAPH.json'] = support.encoded(dict(
        schema='brphm-f1-r10-immediate-evidence-graph-v1', created_utc=now,
        base_commit=BASE, r10_sha256=LEDGER_SHA,
        immediate_r10_evidence=ledger['artifact_sha256'],
        prior_history_recursively_included=False,
        prior_history_bundle='release/f1_leo900_audit_addendum_20261018_r2',
        prior_history_manifest_sha256='204714677d70194eb42dc7f6bc7d856270e5ce9e2681f929d9f8308890aeaf9e',
        f1_closed=False, scientific_success_claimed=False))
    payload['verify_dispatch.py'] = VERIFIER.encode('utf-8')
    payload['README.md'] = f'''# LEO900 R10 audit dispatch evidence

F1 remains OPEN. The F1-F10 goal remains active. Substantive manuscript/F2-F10 edits remain frozen pending actual final review.

This small additive package records the already launched audit-only watcher, its retained artificial RED/GREEN tests, Rack deployment, single launch and read-only observations. It changes no candidate, simulation, existing controller, evaluation or registered statistical analysis. Do not rerun a launcher, deployment, freeze or evaluator. The watcher will automatically run the three existing auditors once after completed evaluation/statistics.

Run `python -B verify_dispatch.py` from this package to check exact member hashes, Python syntax, the four complete14-field records and all17 immediate R10 evidence edges. This command does not execute included research or operational programs and requires only Python's standard library. It deliberately does not recursively reverify earlier ledger history or real final data. Earlier history is preserved in [BRPHM commit {BASE}](https://github.com/1553926531-sudo/BRPHM/commit/{BASE}), package `release/f1_leo900_audit_addendum_20261018_r2`; its manifest SHA256 is `204714677d70194eb42dc7f6bc7d856270e5ce9e2681f929d9f8308890aeaf9e`. Original candidate/analysis commitment remains commit `846cdaac03beab2bacb9834bde1ed8fff1c77141`.

Latest included generation/controller observation:2026-10-17T21:35:14Z,BAT26/48,RWA0/48. Watcher observation:2026-10-17T21:36:16Z,PID792920,sleeping,one thread,CPU4,nice15,RSS17192kB,stderr0bytes,no audit stages started. These are point-in-time observations and give no completion-time guarantee. Recorded artificial tests:local9/9,Rack9/9; passing them establishes neither F1 closure nor scientific superiority.

After normal terminal, inspect controller_terminal, watcher_terminal, three independent reports, original-precision gate, physical-unit effects and registered uncertainty. Preserve every output if an audit fails; resolve audit issues without repeating evaluation or revising the candidate against this final. Seeds17/42/73 are ensemble constituents. Historical outer counts and LEO800 feedback are development/diagnostic evidence. One held-out orbit cannot establish population-wide generalization. Raw-data/window-eligibility reconstruction and independent model replication remain outside the prepared auditors' coverage.

Self-recorded timestamps and hash links do not prove global historical non-access. A GitHub publication/readback supplies corroborating availability evidence, not immutable notarization. Only BRPHM is writable; ModelScope is read-only. No IEEE upload, submission, email or contact is performed.

The first preparation attempt stopped before writing because the immediate evidence alone is278449bytes, exceeding its operational256000-byte package budget. Its failure receipt is retained. The complete text package now has a512000-byte cap; no scientific threshold, protocol, input or existing package was changed.

Prepared UTC:{now}.
'''.encode('utf-8')
    payload['SHA256_MANIFEST.json'] = support.encoded(dict(
        schema='brphm-f1-r10-dispatch-package-manifest-v1', created_utc=now,
        files={name:support.sha(data) for name,data in sorted(payload.items())},
        base_commit=BASE, f1_closed=False, scientific_success_claimed=False))
    total = sum(map(len,payload.values()))
    assert total <= 512000, 'small evidence traffic budget exceeded'
    for name,data in payload.items():
        support.write_new(PACKAGE / name, data)
    print(json.dumps({'package':str(PACKAGE),'files':len(payload),'bytes':total,
        'manifest_sha256':support.sha(payload['SHA256_MANIFEST.json']),
        'immediate_evidence_files':len(ledger['artifact_sha256']),'f1_closed':False}))


if __name__ == '__main__':
    main()
