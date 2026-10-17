# LEO900 additive audit evidence

This package appends R5-R8 audit corrections, the independent statistical numerical verifier, the retained failed/successful synthetic test receipts, and read-only execution observations. **F1 remains OPEN.** The overall F1-F10 goal remains active and manuscript/F2-F10 substantive edits remain frozen.

This is an audit addendum. The original candidate and analysis commitment remains [commit 846cdaac03beab2bacb9834bde1ed8fff1c77141](https://github.com/1553926531-sudo/BRPHM/commit/846cdaac03beab2bacb9834bde1ed8fff1c77141). No new candidate, tuning decision, evaluation or statistical protocol is introduced. The original small text commitment is copied byte-for-byte inside this bundle to make the historical artifact hash edges verifiable offline; no simulation, model tensor or dataset is copied.

Run `python -B verify_addendum.py` here. It checks all member SHA256 values, resolves every included `artifact_sha256` edge, and checks Python syntax without executing those modules. Historic bare paths are resolved explicitly in `INTEGRITY_GRAPH.json`. Published source paths are preserved underneath this package root.

The independent numerical verifier's synthetic suite can be run in `release/f1_audit_20261010` with `python -B -m unittest -v test_leo900_statistics_numerical_audit_20261018`. It needs NumPy and SciPy; the verifier itself imports NumPy plus the separate provenance verifier. Production CLIs are fixed to the registered Rack root. Do not run production evaluators, deployers, controller launchers or package publishers to reproduce synthetic tests.

The latest included observation at 2026-10-17T21:00:04Z reports BAT23/48 and RWA0/48 with the existing controller awaiting simulation. Observations can become stale. Synthetic test success, a valid hash chain and a running process do not establish a final result or scientific superiority. The final candidate must not be revised after observing this final test.

The saved-unit-summary numerical audit does not independently derive those summaries from raw truth/prediction arrays. It is a different arithmetic implementation of the registered statistics, conditional on those saved summaries and the same NumPy RNG contract. The three model seeds are ensemble constituents, not independent experiments. Historical outer/LEO800 outcomes remain development evidence. One new final orbit is not population-wide replication.

All timestamps inside local receipts are self-recorded. GitHub server readback records observed availability, and Git history can be changed; neither proves global historical non-access. Later audit publication cannot be backdated or substituted for the original candidate commitment.

Prepared UTC: 2026-10-17T21:03:05.823526+00:00. Repository authorization applies only to BRPHM. This package performs no ModelScope write, IEEE upload/submission/contact, or competition-asset operation.
