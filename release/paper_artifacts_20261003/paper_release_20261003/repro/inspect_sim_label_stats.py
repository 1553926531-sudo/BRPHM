#!/usr/bin/env python3
from pathlib import Path
import sys
import numpy as np
from src.datasets import sim_loader

root = Path('/mnt/data/BRPHM/rul-space')
component = sys.argv[1]
uid = sys.argv[2]
base = root / ('data/holdout' if sys.argv[3] == 'holdout' else 'data/raw/sim') / component
raw = base / (uid + '.mat')
_, _, frame = sim_loader.convert_one(raw, 'SIM_' + component, root / 'data/interim' / ('SIM_' + component), root=root, lenient=False, write=False)
rul = np.asarray(frame['label.rul'], float)
fail = np.asarray(frame['label.fail'], int)
finite = np.isfinite(rul)
print({'uid': uid, 'rows': len(frame), 'finite_rul': int(finite.sum()), 'rul_min': float(np.nanmin(rul)) if finite.any() else None, 'rul_max': float(np.nanmax(rul)) if finite.any() else None, 'fail_values': {str(k): int(v) for k, v in zip(*np.unique(fail, return_counts=True))}})
