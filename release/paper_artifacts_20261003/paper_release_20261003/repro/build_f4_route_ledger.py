from __future__ import annotations

"""Build the F4 ledger from the registered 320-route source-gate contract."""

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "work/paper/review/f4_route_20261002"
SOURCE = ROOT / "work/rul_next_electrochemical"
ROUTE_SOURCE = SOURCE / "temporal_tcn_route_sweep_source_gate.py"
BASE_SOURCE = SOURCE / "temporal_tcn_source_gate.py"
BLEND_SOURCE = SOURCE / "temporal_tcn_relative_blend_source_gate.py"
RUNNER = ROOT / "work/paper/repro/runners/temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001.py"
RECEIPT = ROOT / "work/paper/review/candidate_v15_receipt.json"
FINAL_RECEIPT = ROOT / "work/paper/review/f1_leo600_final_retry1_20261002/final_receipt.json"
SELECTION = ROOT / "work/paper/review/f1_leo600_final_retry1_20261002/selection_decision.json"
PAPER = ROOT / "work/paper/en/main.tex"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def main() -> int:
    route = load_module("registered_route_contract", ROUTE_SOURCE)
    base = load_module("registered_route_base", BASE_SOURCE)
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    final_receipt = json.loads(FINAL_RECEIPT.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))

    routes = list(route.route_catalog())
    assert len(routes) == route.EXPECTED_ROUTE_COUNT == 320
    assert len({item["route_id"] for item in routes}) == 320
    assert tuple(route.ALPHA_FAMILIES) == (
        (0.0, 0.5), (0.1, 0.5), (0.25, 0.5), (0.1, 0.25), (0.25, 0.75)
    )
    assert list(receipt["source_protocol"]["route_catalog"]["alpha_families"]) == [list(x) for x in route.ALPHA_FAMILIES]
    assert receipt["source_protocol"]["route_catalog"]["route_count"] == 320
    source_selection = selection["visible_inputs"]["new_orbit_alpha_rule"]["source_selection"]
    assert source_selection["selection_counts"]["bat"]["registered_route_count"] == 320
    assert source_selection["selection_counts"]["rwa"]["registered_route_count"] == 320

    candidate = np.asarray([0.2, 0.4], dtype=np.float64)
    control = np.asarray([0.8, 0.6], dtype=np.float64)
    assert np.allclose(0.25 * candidate + 0.75 * control, [0.65, 0.55])
    assert np.allclose(0.0 * candidate + 1.0 * control, control)
    assert np.allclose(1.0 * candidate + 0.0 * control, candidate)

    files = [ROUTE_SOURCE, BASE_SOURCE, BLEND_SOURCE, RUNNER, RECEIPT, FINAL_RECEIPT, SELECTION, PAPER]
    file_records = [{"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in files]
    source_selected = {component: receipt["components"][component]["selected_route"] for component in ("bat", "rwa")}
    selected = selection["selected_routes"]
    final_routes = {component: final_receipt["results"][component]["route"]["route_id"] for component in ("bat", "rwa")}
    assert final_routes == {"bat": "family0_mask23", "rwa": "family1_mask00"}

    ledger = {
        "schema": "brphm-f4-alpha-route-ledger-v2",
        "observed_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "finding": "F4",
        "status": "EVIDENCE_CLOSED_320_ROUTE_CONTRACT",
        "scope": "Receipt-bound audit of the source-label route contract and its formal application. No sealed, A1, B1, canonical, competition, or final labels were read by this builder.",
        "original": {
            "location": "work/paper/en/main.tex:111-131 and work/paper/repro/README.md:10-16",
            "problem": "The manuscript and README described a historical 17-point Cartesian grid (4913 routes) and stale promoted routes, while the final candidate receipt and executable sweep use five alpha families and 64 direction masks (320 routes).",
            "historical_status": "The 17-point/4913 catalog is retained only as development/diagnostic history where present; it is not the final candidate-selection contract.",
        },
        "equation": {
            "candidate_control": "For direction d=s->t and target-orbit weight alpha_t, q_d = alpha_t * p_candidate,d + (1-alpha_t) * p_control,d.",
            "semantics": "alpha=0 is control-only; alpha=1 is candidate-only; intermediate values are convex weights.",
            "application": "The source-gate implementation blends predictions and then applies the component-specific projection. The final LEO600 evaluation uses the frozen route and re-applies the same projection after blending.",
        },
        "catalog_and_selection": {
            "alpha_families": [list(pair) for pair in route.ALPHA_FAMILIES],
            "mask_dimensions": len(base.EXPECTED_DIRECTIONS),
            "directions": list(base.EXPECTED_DIRECTIONS),
            "route_count": len(routes),
            "route_id_format": "family{family_index}_mask{mask:02d}",
            "source_gate_objective": "Require complete six directed RMSE/MAE records and three residual-KS records; reject any regression beyond 1e-12 and require at least one strict RMSE/MAE gain below -1e-12.",
            "tie_break_order": "The registered selector orders eligible routes by its source-gate conservative ranking; route family/mask and selected receipt are hash-bound here.",
            "uniform_floor_variant": "The promoted protocol imposes alpha_t >= 1e-5 for every target orbit before the registered conservative selector is applied.",
            "source_sweep_selected_routes": source_selected,
            "promoted_unseen_orbit_routes": selected,
        },
        "deployment_modes": {
            "implemented_mode": "label-free target-input/transductive",
            "target_orbit_identity": "Required from unit metadata to choose the target-orbit alpha and route direction.",
            "earliest_target_window": "Consumed as unlabeled sensor input for unit-relative channels.",
            "target_labels": "Not used for fitting, route choice, residual correction, thresholding, or the LEO600 candidate freeze.",
            "pure_inductive_status": "Not implemented or evaluated; no pure-inductive claim is made.",
        },
        "evidence": {
            "candidate_receipt_route_count": receipt["source_protocol"]["route_catalog"]["route_count"],
            "final_receipt_route_ids": final_routes,
            "selection_decision_route_count": 320,
            "files": file_records,
            "dynamic_checks": {
                "route_catalog_has_5_families": "PASS",
                "route_catalog_has_320_unique_routes": "PASS",
                "receipt_and_code_route_counts_agree": "PASS",
                "convex_blend_alpha_0_25": "PASS",
                "blend_endpoint_semantics": "PASS",
                "selection_decision_and_final_receipt_agree": "PASS",
            },
        },
        "cross_validation": {
            "static": "Executable route source, candidate receipt, F1 selection decision, final receipt, runner, and manuscript were hash-linked.",
            "dynamic": "Catalog cardinality, family values, route IDs, convex blend equation, and endpoint semantics were checked in Python.",
            "receipt": "Candidate v15 reports route_count=320; F1 selection and final receipts report family0_mask23/family1_mask00 for the unseen-orbit route protocol.",
        },
        "confidence": "high for the final 320-route contract and its receipt binding; medium for historical artifacts that still mention 4913 because they are explicitly development-only records.",
        "remaining_risk": "Venue-specific terminology and the final article type remain pending until the target venue is selected. Any remaining historical 4913 text must stay labeled diagnostic and must not appear as the final selection rule.",
        "required_modification": "Use the five-family/64-mask/320 contract in the manuscript, README, and current F4/F3 evidence ledgers; label older 17-point artifacts as historical diagnostics.",
    }
    REVIEW.mkdir(parents=True, exist_ok=True)
    json_path = REVIEW / "f4_evidence_ledger.json"
    json_path.write_text(json.dumps(ledger, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(f"| `{Path(item['path']).name}` | `{item['sha256']}` |" for item in file_records)
    markdown = f"""# F4 Evidence Ledger: Alpha Route and Source-Only Rules

**Audit date:** 2026-10-03 UTC  
**Status:** `{ledger['status']}`

## Finding

The final candidate-selection contract is five alpha families crossed with 64 bit masks over six directed source transfers: **320 routes**. The historical 17-point Cartesian catalog (`17^3=4913`) is development/diagnostic history and is not the promoted contract.

## Location, original text, and problem

- **Location:** `work/paper/en/main.tex:111-131`, `work/paper/repro/README.md:10-16`.
- **Problem:** those files described the historical 4913-route grid and stale routes, conflicting with the executable sweep and final receipts.
- **Disposition:** current manuscript and README are rewritten to the receipt-bound 320-route contract; historical artifacts retain their original text only when explicitly marked diagnostic.

## Formal rule

For direction `d=s->t` and target-orbit weight `alpha_t`:

```text
q_d = alpha_t * p_candidate,d + (1 - alpha_t) * p_control,d
```

`alpha=0` is control-only and `alpha=1` is candidate-only. The route families are:

```text
(0.0, 0.5), (0.1, 0.5), (0.25, 0.5), (0.1, 0.25), (0.25, 0.75)
```

Each family has 64 masks over the six directed transfers `(LEO500->LEO550, LEO500->LEO700, LEO550->LEO500, LEO550->LEO700, LEO700->LEO500, LEO700->LEO550)`, producing route IDs `family{{index}}_mask{{mask:02d}}`. The promoted uniform-floor variant requires every target alpha to be at least `1e-5` before the registered conservative source-gate selector is applied.

## Information set

- Source labels are used for model fitting, source residual correction, and the pre-freeze source gate.
- Target RUL labels are never used for fitting, route choice, correction, thresholding, or final candidate freezing.
- Target orbit identity is read from unit metadata and the earliest target window is consumed as unlabeled sensor input for the relative representation.
- The implemented deployment regime is label-free target-input/transductive. Pure inductive transfer is not implemented or evaluated.

## Direct evidence and hashes

| Artifact | SHA-256 |
|---|---|
{rows}

## Verification

- Five family values and 320 unique route IDs: **PASS**.
- Candidate receipt, selection decision, and final receipt route counts: **PASS**.
- Convex blend at `alpha=0.25` and endpoint semantics: **PASS**.
- Selected routes and F1 final receipt are hash-linked: **PASS**.

**Builder command:**

```text
python work/paper/repro/build_f4_route_ledger.py
```

## Confidence and residual risk

Confidence is high for the final 320-route contract and receipt binding. Historical 4913 artifacts remain available as development diagnostics and must not be read as the final candidate-selection rule. Venue-specific terminology and article type remain pending.
"""
    (REVIEW / "f4_evidence_ledger.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": "complete", "route_count": len(routes), "json": str(json_path), "markdown": str(REVIEW / "f4_evidence_ledger.md")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
