"""Prepare one bounded, additive package for the pre-outcome driver audit."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PACKAGE = REPO / "release/f1_leo900_driver_evidence_20261018_r1"
BASE = "1646c1097f4e66e0c2217ccfadc37a6dde587d87"
RECORD = "F1_LEO900_PERIODIC_DRIVER_EVIDENCE_20261018R1.json"
RECORD_SHA = "c7ecff47242b4f642423a87fbb79a848b11f2e83431e495f26d24229f5162c4f"
SECRET = re.compile(rb"-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,}")

VERIFIER = r'''"""Check captured evidence and driver arithmetic without connecting or running research."""
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
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(doc):
    return (json.dumps(doc, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def main():
    if PACKAGE.exists():
        raise FileExistsError("preserve existing driver evidence package")
    raw = (HERE / RECORD).read_bytes()
    assert sha(raw) == RECORD_SHA
    record = json.loads(raw)
    expected = dict(record["fields"]["hash"]["input_sha256"])
    expected[RECORD] = RECORD_SHA
    expected["audit_leo900_periodic_environment_20261018_r1.py"] = record["fields"]["hash"]["analysis_program_sha256"]
    names = set(expected) | {
        RECORD.replace(".json", ".md"),
        Path(__file__).name,
        "publish_leo900_driver_evidence_20261018_r1.py",
        "publish_leo900_audit_addendum_20261018_r2.py",
        "publish_leo900_external_commitment_20261018.py",
        "publish_leo900_external_commitment_rest_20261018.py",
    }
    payload = {}
    for name in sorted(names):
        assert Path(name).name == name and ":" not in name
        path = HERE / name
        assert not path.is_symlink() and path.resolve().is_relative_to(HERE.resolve())
        data = path.read_bytes()
        assert data.decode("utf-8").encode("utf-8") == data and not SECRET.search(data), name
        if name in expected:
            assert sha(data) == expected[name], name
        if name.endswith(".py"):
            ast.parse(data.decode("utf-8"), filename=name)
        payload["release/f1_audit_20261010/" + name] = data
    now = datetime.now(timezone.utc).isoformat()
    payload["INTEGRITY_GRAPH.json"] = encode(dict(
        schema="brphm-f1-leo900-periodic-driver-package-graph-v1",
        created_utc=now, base_commit=BASE,
        periodic_driver_record_sha256=RECORD_SHA,
        immediate_input_sha256=record["fields"]["hash"]["input_sha256"],
        original_candidate_and_analysis_commit="846cdaac03beab2bacb9834bde1ed8fff1c77141",
        transitive_history_recursively_included=False,
        f1_closed=False, scientific_success_claimed=False))
    payload["verify_driver_evidence.py"] = VERIFIER.encode()
    payload["README.md"] = f"""# LEO900 pre-outcome periodic-driver evidence

F1 remains OPEN and the F1-F10 goal remains active. Substantive manuscript and F2-F10 edits remain frozen.

This single additive package makes the captured periodic-driver diagnostics, generator source, registered model XML and mathematical cross-check available for review. It does not change the running simulation, candidate, scientific gates, controller, watcher or final-access policy. Do not launch any included operational program. Only `python -B verify_driver_evidence.py` is intended for package verification; it needs Python's standard library and performs no network access, training, simulation, final-label decoding or re-evaluation.

The recorded environment uses a5740-second repeated tile. Its reference Kepler period is6179.328127714831seconds, with whole-kilometre runtime seams3222-3228km. Solar-heat and thermal connections to both components exist in the captured model. These facts establish an approximation in the implemented driver. They do not measure its effect on temperature, component lifetimes, prediction error, or a comparison between models. The circular reference is not an independent simulator. One final orbit cannot establish generalization across an orbit population.

The JSON includes all14 finding fields and exact input/model/program hashes. The eight immediate input artifacts are included. Earlier ledgers' transitive references are not recursively copied; original candidate/analysis commitment is BRPHM commit846cdaac03beab2bacb9834bde1ed8fff1c77141. This package adds to commit{BASE}. No prior result, manuscript or package is replaced. The read-only observations and local timestamps establish their stated observation scope, not proof of global historical non-access. Publication/readback is evidence of availability and is not immutable notarization.

The analysis record was generated at{record['created_utc']}; its referenced observed final guard was absent at{record['final_guard_absent_at_observed_utc']}. The normal simulation and registered single evaluation continue independently. This package introduces no new scientific acceptance threshold and makes no success claim. Interpret final outcomes only with the original gate, physical-unit effects and registered uncertainty.

Only BRPHM is an authorized publication destination. ModelScope remains read-only; no IEEE upload, submission or external communication is performed. Raw payload budget is640000bytes. Prepared UTC:{now}.
""".encode()
    payload["SHA256_MANIFEST.json"] = encode(dict(
        schema="brphm-f1-leo900-periodic-driver-package-manifest-v1",created_utc=now,
        base_commit=BASE,files={n:sha(b) for n,b in sorted(payload.items())},
        f1_closed=False,scientific_success_claimed=False))
    total = sum(map(len, payload.values()))
    assert total <= 640000, "bounded evidence payload exceeded"
    for name, data in payload.items():
        path = PACKAGE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    print(json.dumps(dict(package=str(PACKAGE),files=len(payload),bytes=total,
                         manifest_sha256=sha(payload["SHA256_MANIFEST.json"]),f1_closed=False)))


if __name__ == "__main__":
    main()
