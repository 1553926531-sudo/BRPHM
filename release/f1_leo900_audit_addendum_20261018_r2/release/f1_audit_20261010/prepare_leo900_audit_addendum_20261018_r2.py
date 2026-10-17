"""Prepare R9 as a new audit bundle, preserving the original and R8 bundles."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import prepare_leo900_audit_addendum_20261018_r1 as prior

HERE, REPO = prior.HERE, prior.REPO
PACKAGE = REPO / 'release/f1_leo900_audit_addendum_20261018_r2'
R9_SHA = '6de13be7865f3b603933ccf2aece3d97297d7dd01fe98a61bac0b3ee56695ca1'


def collect():
    payload, edges = prior.collect()
    if prior.sha((HERE / 'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json').read_bytes()) != R9_SHA:
        raise RuntimeError('preserved R9 differs')
    todo = [HERE / name for name in (
        'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.json',
        'F1_LEO900_PREFLIGHT_EVIDENCE_20261018R9.md',
        'prepare_leo900_audit_addendum_20261018_r2.py',
        'publish_leo900_audit_addendum_20261018_r2.py')]
    allowed = (HERE.resolve(), prior.PREVIOUS.resolve())
    while todo:
        path = todo.pop()
        target = path.resolve(strict=True)
        if path.is_symlink() or not any(target.is_relative_to(a) for a in allowed):
            raise RuntimeError('artifact outside the two approved text directories')
        name = target.relative_to(REPO).as_posix()
        if name in payload:
            if payload[name] != path.read_bytes():
                raise RuntimeError('artifact changed during closure traversal')
            continue
        data = path.read_bytes()
        if len(data) > 512_000 or prior.SECRET.search(data) or data.decode('utf-8').encode('utf-8') != data:
            raise RuntimeError('unsafe/non-text/oversized artifact')
        payload[name] = data
        if path.suffix != '.json':
            continue
        doc = json.loads(data)
        for key, expected in doc.get('artifact_sha256', {}).items():
            prior.safe_name(key)
            matches = []
            for candidate in (REPO / key, path.parent / key, HERE / key, prior.PREVIOUS / key):
                if candidate.is_file() and not candidate.is_symlink():
                    resolved = candidate.resolve()
                    if any(resolved.is_relative_to(a) for a in allowed) and prior.sha(resolved.read_bytes()) == expected:
                        matches.append(resolved)
            if not matches:
                raise RuntimeError('unresolved artifact hash edge: ' + key)
            resolved = matches[0]
            edges.append(dict(source=name, key=key, target=resolved.relative_to(REPO).as_posix(), sha256=expected))
            todo.append(resolved)
    if len(payload) > 150 or sum(map(len, payload.values())) > 3_000_000:
        raise RuntimeError('small-text traffic budget exceeded')
    return payload, edges


def main():
    if PACKAGE.exists():
        raise FileExistsError('new bundle already exists; preserve it')
    payload, edges = collect()
    now = datetime.now(timezone.utc).isoformat()
    payload['INTEGRITY_GRAPH.json'] = prior.encoded(dict(
        schema='brphm-f1-addendum-artifact-graph-v2', created_utc=now,
        artifact_edges=sorted(edges, key=lambda e:(e['source'],e['key'])),
        original_commit=prior.ANCHOR, r8_sha256=prior.R8_SHA, r9_sha256=R9_SHA,
        original_manifest_sha256=prior.PREVIOUS_MANIFEST_SHA,
        goal_status='active', f1_closed=False, scientific_success_claimed=False,
        stale_goal_objective_note='Retained15/15-closed wording is obsolete. R5-R9 maintain F1 OPEN pending actual complete final evidence.'))
    payload['README.md'] = f'''# LEO900 audit evidence through R9

This new bundle adds an independent prediction-to-summary auditor, its retained RED/failed/passing artificial test receipts, a separate Rack support deployment and R9 evidence ledger. It also retains the R5-R8 evidence closure and byte-exact original small text commitment. **F1 remains OPEN; the F1-F10 goal remains active; substantive manuscript/F2-F10 edits remain frozen.**

The original candidate/analysis commitment is [BRPHM commit {prior.ANCHOR}](https://github.com/1553926531-sudo/BRPHM/commit/{prior.ANCHOR}). The earlier R8 audit package remains [BRPHM commit b8ad940e5779692f25643cdaa2fac346e4385760](https://github.com/1553926531-sudo/BRPHM/commit/b8ad940e5779692f25643cdaa2fac346e4385760). This package changes neither commitment, candidate, gate, statistical estimand, analysis, simulation nor controller.

Run `python -B verify_addendum.py` here to verify exact member hashes, all included `artifact_sha256` edges, membership and Python syntax. Source paths and historic relative references are preserved and mapped in `INTEGRITY_GRAPH.json`. This offline verifier does not execute the included publisher/deployer/evaluator/controller programs.

From the included `release/f1_audit_20261010`, the artificial prediction suite is `python -B -m unittest -v test_leo900_prediction_summary_audit_20261018` (NumPy). Its saved records show12/12 local and12/12 Rack passing; both real audits defer prediction decoding until complete terminal. The independent statistics suite is `python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018` (NumPy/SciPy), with16/16 saved local/Rack passes. Reproducing either artificial suite requires no real final inputs. Production auditor CLIs remain locked to their registered Rack root. Never re-run a deployed evaluator, controller launcher or deployment to reproduce these artificial tests.

The three prepared audit layers check provenance and exact original gate arithmetic; original saved predictions versus per-unit/pooled summaries; and saved summaries versus bootstrap draws, intervals, SD, paired tests and Holm. The two descriptive arithmetic auditors allow64 ULP at their stated comparison scales; this is never a new gate tolerance. They do not independently regenerate raw labels/window eligibility or model/projection outputs. R9 bridges R8's previously stated saved-summary assumption only when run successfully on the eventual real terminal evidence; currently it is prepared and tested.

Latest included capture:2026-10-17T21:14:39Z, BAT25/48,RWA0/48, existing simulation/controller running, no final-label guard or terminal yet. Observations can become stale and imply no completion time. Synthetic test success and public availability do not establish scientific superiority. Seed17/42/73 are ensemble constituents, not independent repetitions. Previous outer/LEO800 feedback remains development/diagnostic evidence. One new held-out orbit cannot establish population-wide generalization.

Local timestamps are self-recorded. GitHub readbacks corroborate byte availability by observed server-response time, not immutable notarization or global historic non-access. Audit additions cannot be backdated or substituted for the original commitment. No dataset, model tensor or simulation output is copied here.

Prepared UTC:{now}. Operations are confined to BRPHM; ModelScope remains read-only; no IEEE upload/submission/email/contact is performed.
'''.encode()
    payload['verify_addendum.py'] = prior.VERIFIER.encode()
    manifest = dict(schema='brphm-f1-audit-addendum-manifest-v2', created_utc=now,
        kind='additive audit evidence; no new candidate registration',
        files={name:prior.sha(data) for name,data in sorted(payload.items())},
        f1_closed=False, scientific_success_claimed=False)
    payload['SHA256_MANIFEST.json'] = prior.encoded(manifest)
    if sum(map(len,payload.values())) > 3_000_000:
        raise RuntimeError('complete small-text budget exceeded')
    for name,data in payload.items():
        prior.safe_name(name)
        prior.write_new(PACKAGE / name,data)
    print(json.dumps(dict(package=str(PACKAGE),files=len(payload),bytes=sum(map(len,payload.values())),
        artifact_edges=len(edges),manifest_sha256=prior.sha(payload['SHA256_MANIFEST.json']),f1_closed=False)))


if __name__ == '__main__':
    main()
