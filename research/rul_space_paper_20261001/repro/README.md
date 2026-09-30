# BRPHM RUL source-only reproduction bundle

This bundle accompanies the audited source-only temporal TCN paper. It contains the evidence summary, formal-fold table, candidate matrix, immutable receipts, and the isolated runner sources used for the final route.

## Final route

- Model: unit-first relative temporal TCN with dilations `(1, 2, 4)`, width 16, kernel 3, dropout 0.05.
- Input: source-standardized telemetry concatenated with each unit's earliest-window relative trajectory.
- Loss: unit-balanced SmoothL1 on normalized RUL.
- Ensemble: fixed seeds `(17, 42, 73)`, median aggregation.
- Residual correction: source-fit residual median with shrinkage `0.25`.
- Alpha catalog: `17^3 = 4913` target-orbit routes.
- BAT route: `(1e-5, 1e-5, 1e-5)` for `(LEO500, LEO550, LEO700)`.
- RWA route: `(0.02, 1e-5, 1e-5)` for `(LEO500, LEO550, LEO700)`.

## Verification contract

Selection uses six directed source transfers and three residual-KS pairs. Formal evaluation is six outer folds and runs once after source-only handoff. The frozen reference SHA-256 is:

`b708df9c448a051b8669c29789f00d282aa7907784e6f99d7e20ef1fb96b6733`

The receipts record that canonical data and the competition line were not modified, sealed/A1/B1 holdouts were not read, holdout and outer labels were not used for training or selection, and population-wide generalization is not verified by this controlled experiment.

## Reproduction inputs

The registered ModelScope-backed data root is intentionally not copied into this bundle. It must already be present in the project environment. The final receipt records the input tensor hashes, source folds, numerical tolerance, and execution metadata. Use the isolated runner copies in `runners/` and keep the source/resource contract from the parent project:

```text
taskset -c 0
nice -n 15
ionice -c 3
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
```

Do not read sealed, A1, B1, or any true holdout while reproducing source diagnostics. Do not overwrite an existing receipt; write a new receipt identity for any new run.

## Contents

- `evidence/`: machine-readable summary, formal folds, and method matrix.
- `receipts/`: seven immutable source-gate receipts, including the promoted route and retained failures.
- `runners/`: candidate runner sources copied from the isolated research tree.
- `../en/main.tex`, `../zh/main.tex`: English and Chinese LaTeX sources.
- `../en/main.pdf`, `../zh/main.pdf`: compiled three-page PDFs.
- `../en/paper_en.docx`, `../zh/paper_zh.docx`: generated Word documents.

The DOCX files were structurally validated with the repository Office validator under UTF-8 mode. A local LibreOffice/Word executable was not available for DOCX-to-PDF rendering in this environment; the LaTeX PDFs and all embedded DOCX image/table counts were checked instead.
