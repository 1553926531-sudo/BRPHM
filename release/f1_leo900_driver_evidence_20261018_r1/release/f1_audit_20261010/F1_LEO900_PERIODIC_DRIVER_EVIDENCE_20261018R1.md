# F1 LEO900 periodic-driver evidence

F1 remains OPEN; the F1-F10 goal remains active. This is a pre-outcome evidence addition, with no change to the frozen simulation, candidate, gates, access policy or manuscript.

The declared analytic orbit has a reference Kepler period of 6179.328127714831 s. The actual frozen generator repeats a5740s tile. The period is7.109642321% shorter, giving7.653800134% more repetitions per unit time. These are driver quantities, not prediction improvements. A circular-reference seam is3224.265338km; runtime diagnostics report3222-3228km. The circular calculation does not reproduce a full eccentric/interpolated orbit.

| Environment | Logged period, rounded s | Tile s | Logged seam, rounded km | Recomputed umbra duty % | Recomputed charging A |
|---|---:|---:|---:|---:|---:|
| LEO900_B00 | 6179 | 5740 | 3222 | 36.585365854 | -1.153846153846 |
| LEO900_B30 | 6180 | 5740 | 3227 | 33.623693380 | -1.013123359580 |
| LEO900_B60 | 6180 | 5740 | 3228 | 9.581881533 | -0.211946050096 |

The registered serialized model and build source both connect the environmental position to solar heat and the thermal model to BAT and RWA. Therefore the seam has a possible physical influence. No sensitivity simulation, final RUL labels or model outcomes were inspected; this record does not estimate that influence or declare the experiment valid/invalid by a new threshold. The import PASS is not evidence that a30-day continuous orbit drove the model.

The accompanying JSON contains all14 finding fields, exact input hashes, formulas and verified model edges. Read-only capture programs are embedded in the referenced observations. This analysis can be reviewed or rerun in a disposable copy; its output writer refuses to overwrite existing evidence. The original run and registered terminal auditors continue automatically.

JSON SHA256: `c7ecff47242b4f642423a87fbb79a848b11f2e83431e495f26d24229f5162c4f`. Created UTC: 2026-10-18T00:40:41.950086+00:00.
