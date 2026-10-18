"""Append only the driver evidence package to a new BRPHM branch."""
from pathlib import Path

import publish_leo900_audit_addendum_20261018_r2 as publisher

publisher.PACKAGE = publisher.REPO / "release/f1_leo900_driver_evidence_20261018_r1"
publisher.BRANCH = "f1-leo900-driver-evidence-20261018-r1"
publisher.BASE = "1646c1097f4e66e0c2217ccfadc37a6dde587d87"
publisher.ORIGINAL_BRANCH = "f1-leo900-dispatch-addendum-20261018-r1"
publisher.TRANSACTION = publisher.HERE / "leo900_driver_evidence_transaction_20261018_r1.json"
publisher.MESSAGE = ("Record pre-outcome LEO900 periodic-driver evidence\n\n"
                     "Append captured diagnostics, registered model connections and mathematical "
                     "cross-checks. Preserve simulation, candidate, gates and manuscript. F1 remains open.\n")
publisher.__file__ = str(Path(__file__).resolve())

if __name__ == "__main__":
    publisher.main()
