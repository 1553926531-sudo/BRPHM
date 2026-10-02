# Venue rules evidence package (2026-10-03)

This directory is the auditable evidence package for `venue_rules_verified_20261003.md`. It contains copies of the official responses captured during the venue audit, normalized text extracts, exact quote selections, and a machine-readable `manifest.json`. Hashes are SHA-256 over the saved artifact bytes.

## Interpretation boundary

- IEEE venue rules are official publisher/society instructions and are usable as venue-specific submission constraints.
- The general IEEE peer-review and accessibility pages are corroboration only. The accessibility page concerns general IEEE web accessibility guidance; it is not an article-PDF compliance rule.
- Clarivate API attempts returned HTTP 401 with empty bodies, and no public dated CAS partition record was obtained. Therefore no current JCR/CAS Q1 claim is made for RESS, MSSP, or AST.
- `trel_rs.html` says three independent reviewers for each published article; the separate 2026 review-policy PDF says at least two, with three preferred. Both statements are preserved and the difference is reported in the note.

## Files

- `raw/`: source captures and binary documents.
- `extracts/`: normalized HTML/PDF text and exact quote selections.
- `manifest.json`: URL, status, final URL, capture time, size, and SHA-256 for each artifact.

The package was written only under `work/paper/review/venue_rules_evidence_20261003/`.
