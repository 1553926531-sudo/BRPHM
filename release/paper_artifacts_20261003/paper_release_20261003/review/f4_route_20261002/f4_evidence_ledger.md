# F4 Evidence Ledger: Alpha Route and Source-Only Rules

**Audit date:** 2026-10-03 UTC  
**Status:** `EVIDENCE_CLOSED_320_ROUTE_CONTRACT`

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

Each family has 64 masks over the six directed transfers `(LEO500->LEO550, LEO500->LEO700, LEO550->LEO500, LEO550->LEO700, LEO700->LEO500, LEO700->LEO550)`, producing route IDs `family{index}_mask{mask:02d}`. The promoted uniform-floor variant requires every target alpha to be at least `1e-5` before the registered conservative source-gate selector is applied.

## Information set

- Source labels are used for model fitting, source residual correction, and the pre-freeze source gate.
- Target RUL labels are never used for fitting, route choice, correction, thresholding, or final candidate freezing.
- Target orbit identity is read from unit metadata and the earliest target window is consumed as unlabeled sensor input for the relative representation.
- The implemented deployment regime is label-free target-input/transductive. Pure inductive transfer is not implemented or evaluated.

## Direct evidence and hashes

| Artifact | SHA-256 |
|---|---|
| `temporal_tcn_route_sweep_source_gate.py` | `41e505e4f1ff7de050d86efe8766b64d96b0239e6436e7b0496f085ccb91cc7b` |
| `temporal_tcn_source_gate.py` | `0a50fe3839fdb804903cf8ece5e6191e1cb4dd9bf6b8e23938ae13ab946b1d74` |
| `temporal_tcn_relative_blend_source_gate.py` | `f9fa246661793ad098231efeb45f5967f33cd83f35f80aa179453e53d1cacc09` |
| `temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001.py` | `3f24394e16e58a49ceaef99448a690e13143356918aed45f1ea50f3d7b8dd126` |
| `candidate_v15_receipt.json` | `54b628a565e47ccae95f630ec7db933b0e091aa53dc96aee3a1496ff9a3c66c7` |
| `final_receipt.json` | `49c7e9da240842a6095f06358a0e318a4da2357b94da25611dedbbce5962bba5` |
| `selection_decision.json` | `53e2cd76f8aec7c4ded0fbb7857533e64ccb48fd5fd042a23caee904018ef7c2` |
| `main.tex` | `4dc54e2a8ccd3aa087344ae52737b5f9f1bc5bb97faa9926c1d0aa6cf5d33621` |

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
