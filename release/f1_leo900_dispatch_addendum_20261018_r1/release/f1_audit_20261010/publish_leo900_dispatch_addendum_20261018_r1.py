"""Publish one small R10 addition to a fresh BRPHM branch; preserve prior branches."""
from pathlib import Path

import publish_leo900_audit_addendum_20261018_r2 as publisher

publisher.PACKAGE = publisher.REPO / 'release/f1_leo900_dispatch_addendum_20261018_r1'
publisher.BRANCH = 'f1-leo900-dispatch-addendum-20261018-r1'
publisher.BASE = '523619aed9dfb8f5622332acfe26363ffd682b2c'
publisher.ORIGINAL_BRANCH = 'f1-leo900-audit-addendum-20261018-r2'
publisher.TRANSACTION = publisher.HERE / 'leo900_dispatch_addendum_transaction_20261018_r1.json'
publisher.MESSAGE = ('Record existing LEO900 terminal audit dispatch and R10 evidence\n\n'
    'Append the small operational evidence package after R9. Preserve the original '
    'candidate, analysis, simulation, controller and manuscript. F1 remains open.\n')
# The preserved publisher records the current entry point's hash in its receipt.
publisher.__file__ = str(Path(__file__).resolve())

if __name__ == '__main__':
    publisher.main()
