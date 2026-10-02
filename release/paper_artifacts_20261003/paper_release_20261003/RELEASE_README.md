# BRPHM paper artifact release (2026-10-03)

This archive contains the isolated paper evidence package for the source-label-only cross-orbit RUL manuscript. It includes the English LaTeX source/PDF, figures, F1-F10 review ledgers, machine-readable manifests, reproduction scripts, and immutable receipts.

## Scope boundary

- The ModelScope dataset is referenced by URL and pinned commit; it is not duplicated here.
- No `sealed`, `A1`, `B1`, `canonical`, `production`, or competition data are included.
- Cached bytecode and transient build files are excluded.
- The historical six-fold outer results are marked diagnostic/development evidence; the frozen LEO600 receipt is the final controlled evaluation.

## Reproduce

Read `repro/README.md` first. Reproduction must use the registered ModelScope commit and must write a new receipt identity.

## Venue routing

The evidence package supports an IEEE basket (TIM primary, T-Rel and TAES fallbacks) and an independent SCI-Q1 basket (RESS, MSSP, AST) whose current JCR/CAS quartile still requires dated authoritative verification.

## Integrity

`checksums.sha256` covers every release file except the checksum manifest itself (a self-hash would be circular).
