# F3 Evidence Ledger: Method and Input Dimensionality

**Audit date:** 2026-10-02 (UTC)  
**Status:** `EVIDENCE_CLOSED_320_ROUTE_CONTRACT`  
**Scope:** Read-only audit of isolated electrochemical source-gate implementation and promoted receipt; no training and no sealed/A1/B1/canonical/competition access.

## Finding

The manuscript's statement that both components use 13 channels and length 30 is false for the promoted receipt. The registered tensors are BAT `[3681, 60, 4]` and RWA `[7051, 30, 13]`; the unit-first representation concatenates standardized raw channels with earliest-window residual channels, so the TCN receives 8 channels for BAT and 26 for RWA. The complete train/forward/postprocess/blend contract is now executable and hash-bound below.

## Location and original text

- **Location:** `work/paper/en/main.tex:30,49-59`
- **Original:** “BAT contains 13 channels and RWA contains 13 channels in the temporal input used by the final receipt; windows have length 30.”
- **Problem:** raw tensor channels, transformed model channels, and component-specific window lengths are conflated; optimization, initialization/termination, complexity, edge cases, and operation order are not specified.

## Direct evidence

| Artifact | Result | SHA-256 |
|---|---|---|
| `temporal_tcn_source_gate.py` | 26589 bytes | `0a50fe3839fdb804903cf8ece5e6191e1cb4dd9bf6b8e23938ae13ab946b1d74` |
| `temporal_tcn_unit_first_source_gate_20261001.py` | 3648 bytes | `9c8c433adc1c592584e2467956f67432b635ac8f6dca51f22c4f03f0aaa70b20` |
| `temporal_tcn_unit_first_residual_centered_source_gate_20261001.py` | 6695 bytes | `04ff3b984e1bbed8510986f10812bb8643dee85fc46ad16b38cf6f75395ad453` |
| `temporal_tcn_route_sweep_source_gate.py` | 11130 bytes | `41e505e4f1ff7de050d86efe8766b64d96b0239e6436e7b0496f085ccb91cc7b` |
| `temporal_tcn_global_inner_route_source_gate.py` | 11179 bytes | `9f82f37eb8bc02eb670de4062d4102d7aa33f8cc0ce458fd32e8ce917c6d0749` |
| `temporal_tcn_fine_global_inner_route_source_gate.py` | 1925 bytes | `3e8d66db4f0c7adfe7a6d123be931eadf3eedf6925180434a62716311276cd90` |
| `temporal_tcn_unit_first_residual_centered_uniform_alpha_floor_source_gate_20261001.py` | 3328 bytes | `3f24394e16e58a49ceaef99448a690e13143356918aed45f1ea50f3d7b8dd126` |
| `main.tex` | 35197 bytes | `4dc54e2a8ccd3aa087344ae52737b5f9f1bc5bb97faa9926c1d0aa6cf5d33621` |
| `candidate_v15_receipt.json` | 322307 bytes | `54b628a565e47ccae95f630ec7db933b0e091aa53dc96aee3a1496ff9a3c66c7` |

Promoted receipt dimensions: BAT `[3681, 60, 4]`, `rmax=150`; RWA `[7051, 30, 13]`, `rmax=0.2`.

## Formal specification

For component c, each window is X_i in R^(L_c x C_c) with unit u_i, end time t_i and normalized label y_i=RUL_i/rmax_c in [0,1]. For every ordered orbit pair s != t, fit only rows with orbit s and evaluate only rows with orbit t; source and validation unit sets must be disjoint.

### Notation and representation

- `C_c`: BAT 4, RWA 13; `L_c`: BAT 60, RWA 30; transformed input `C'=2C_c` gives BAT 8 and RWA 26.
- Source-only standardization uses channel mean and standard deviation over source windows; scales below `1e-6` are floored.
- For each unit, choose the row with minimum `t_end`; concatenate the standardized sequence and its difference from that unit's earliest-window first sample.

### Network and training

Conv1d(2C_c -> 16, k=1), then three residual blocks with dilations 1,2,4. Each block has Conv1d(16->16,k=3,padding=dilation,dilation=dilation), GroupNorm(1,16), SiLU, Dropout(0.05), repeated twice, then residual addition. Pool last hidden state and temporal mean (32 values); concatenate age features (a,a^2,sqrt(max(a,0))) to 35 values; Linear(35->16), SiLU, Linear(16->1), sigmoid.

For each fixed seed in (17,42,73), seed Python/NumPy/PyTorch, use AdamW(lr=0.002, weight_decay=1e-4), batch=min(256,n), shuffled DataLoader with a seeded generator, 90 epochs, SmoothL1(beta=1.0 default) weighted by inverse unit window count and rescaled so weights sum to n, gradient norm clip 1.0, no early stopping. Ensemble is the elementwise median of the three seed predictions.

Nominal temporal receptive field: With two k=3 convolutions at each dilation (1,2,4), the nominal temporal receptive field is 1 + 2*(k-1)*(1+2+4) = 29 samples. Symmetric padding is used; this is not a causal TCN.

### Operation order

1. Fit source-only standardization and transform raw windows.
2. Append unit-first residual channels.
3. Fit three fixed-seed TCNs and take the median prediction.
4. Add source-fit correction `-0.25 median(pred_source-y_source)`.
5. Apply BAT isotonic non-increasing or RWA causal running-min projection and clip to `[0,1]`.
6. Blend with the frozen control using `alpha*candidate+(1-alpha)*control`.
7. Reapply the component projection/clipping; multiply by `rmax` only for physical-unit metrics.

### Route, complexity, and boundary conditions

Pseudocode:

1. Fit the source-only scaler and append per-unit earliest-window relative channels.
2. Fit the three fixed seeds for 90 epochs; compute the source-fit median-residual correction and apply it to candidate predictions.
3. Project candidate predictions, enumerate the 320 family/mask routes, blend with the frozen control, reproject, and evaluate the source gate.
4. Select the registered conservative minimum among eligible routes, with every promoted target alpha at least `1e-5`.
5. Freeze the route; refit on two source orbits and evaluate each held-out orbit once.

- The current catalog has five alpha families crossed with 64 masks over six directed transfers, producing 320 routes. Selection is source-gate-only with the registered conservative ranking; the promoted uniform-floor variant first requires every target alpha to be at least `1e-5`. The historical 17-point/4913 catalog is retained as diagnostic-only.
- For N windows, length L, raw channels C, width W=16, B=3 blocks, kernel k=3, one epoch costs O(N*L*(2CW + 2B*W^2*k)); the three-seed 90-epoch fit multiplies this by 270, and memory is O(min(256,N)*L*2C + parameters). Parameter count is 32C+5505: 5633 for BAT (C=4) and 5921 for RWA (C=13).
- Initialization is PyTorch default module initialization after deterministic seed setup. Training terminates after exactly max(1, epochs)=90 epochs; no validation-based early stopping or adaptive termination is implemented.
- Every fitted source set is nonempty and every unit has at least one window.; Input arrays are rank-3, finite, and channel-compatible; nonfinite arrays raise before fitting.; A constant source channel uses scale 1e-6; tmax uses denominator floor 1e-9.; No source/validation unit overlap is permitted; empty or incomplete direction grids raise/fail the source gate.; One-window units are valid; their monotonic projection has no adjacent pair and their upward fraction is null.

## Verification

The deterministic checks passed: shape doubling and relative-channel shift invariance, unit-balanced weights, finite unit-interval model outputs for BAT/RWA dimensions, monotone bounded projections, a complete 320-route family/mask catalog, and a selector code check with no `outer` dependency. The promoted receipt independently confirms the raw tensor shapes, three-seed median ensemble, unit-balanced SmoothL1 contract, and 320-route count.

**Commands:**

```text
python work/paper/repro/build_f3_method_ledger.py
python -m pytest work/rul_next_electrochemical/test_temporal_tcn_source_gate.py -q
```

## Cross-validation, confidence, and residual risk

- **Cross-validation:** static line inspection and hashes; dynamic representation/model/projection/route invariants; independent candidate receipt comparison; manuscript Eq. (2) comparison.
- **Confidence:** high for implementation, input dimensions, and the current 320-route contract; medium for venue-specific supplement and metadata requirements.
- **Remaining risk:** historical 17-point artifacts remain in the evidence tree as development diagnostics; venue-specific page and supplement constraints remain unconfirmed.
- **Required modification:** preserve the component-specific tensor table, formal problem definition, pseudocode, full network/training contract, complexity, edge cases, and operation order in the manuscript or supplement; label the historical catalog diagnostic-only.

**Result:** F3 evidence is closed for the current implementation contract; venue-specific production constraints remain pending.
