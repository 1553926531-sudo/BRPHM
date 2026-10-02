# F6 Reconciled Statistical Evidence

**Audit date:** 2026-10-02 UTC  
**Status:** `RECONCILED_DIAGNOSTIC_STATISTICS_REFERENCE_PAIRING_UNAVAILABLE`

## Frozen Fold Benchmark

The exact frozen-reference fold values are hash-bound and compared with candidate unit-cluster bootstrap intervals. The reference fold score is held fixed because its per-unit historical predictions are absent; this is not a paired-reference analysis.

| Component | Orbit | Units | RMSE delta | RMSE 95% CI | RMSE FWER upper | MAE delta | MAE 95% CI | MAE FWER upper |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BAT | LEO500 | 70 | -3.65677083e-06 | -0.375625882, 0.464573741 | 0.623395048 | -1.34589163e-06 | -0.204968476, 0.250158011 | 0.340894198 |
| BAT | LEO550 | 68 | -9.59349712e-06 | -0.249132424, 0.256226681 | 0.354742626 | -3.93200562e-06 | -0.137873002, 0.155683725 | 0.219573143 |
| BAT | LEO700 | 65 | -3.0063243e-05 | -0.422591658, 0.39914464 | 0.537663541 | -1.85915687e-05 | -0.290119212, 0.312046432 | 0.432439811 |
| RWA | LEO500 | 78 | -2.51649128e-05 | -0.00238410377, 0.00234329416 | 0.00318478311 | -5.20892448e-07 | -0.00205661593, 0.0021010845 | 0.00283756294 |
| RWA | LEO550 | 79 | -1.33370106e-08 | -0.00258232531, 0.00240754679 | 0.00322575077 | -1.48879367e-09 | -0.0020103901, 0.00206718683 | 0.00276071953 |
| RWA | LEO700 | 83 | -2.93752957e-08 | -0.00215016645, 0.00207186902 | 0.00282699793 | -2.16716214e-08 | -0.00194912949, 0.00203261976 | 0.00278490159 |

Units are resampled as clusters with all windows retained, then window-weighted RMSE/MAE are recomputed. Simultaneous one-sided upper bounds use Bonferroni over 12 fold-metric comparisons.

## Replay Sensitivity

The paired bootstrap and one-sided Wilcoxon below compare candidate unit errors with a newly refitted current control. The replay is not the frozen historical reference, and these tests are diagnostic only.

| Component | Orbit | Units | Mean RMSE delta | RMSE CI | Wilcoxon p | Adjusted p | Mean MAE delta | MAE CI | Wilcoxon p | Adjusted p |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BAT | LEO500 | 70 | -3.20563151e-06 | -5.22949997e-06, -1.13378819e-06 | 0.000438986 | 0.00526783 | -1.64589138e-06 | -3.43675139e-06, 1.55570659e-07 | 0.0225149 | 0.270178 |
| BAT | LEO550 | 68 | -4.97419116e-06 | -7.29427113e-06, -2.63769536e-06 | 0.000101564 | 0.00121876 | -2.0456798e-06 | -4.14698036e-06, 7.77594161e-08 | 0.0225245 | 0.270294 |
| BAT | LEO700 | 65 | -1.10132989e-05 | -1.73485944e-05, -5.80346344e-06 | 2.50161e-06 | 3.00193e-05 | -8.91718165e-06 | -1.4264249e-05, -4.35472898e-06 | 7.32827e-05 | 0.000879392 |
| RWA | LEO500 | 78 | -2.68360473e-05 | -6.98949471e-05, 1.55478708e-05 | 0.125471 | 1 | -1.84997267e-05 | -5.89733508e-05, 2.19144137e-05 | 0.229759 | 1 |
| RWA | LEO550 | 79 | -1.0478709e-08 | -3.11664062e-08, 1.02060469e-08 | 0.124384 | 1 | -4.88048139e-09 | -2.43247006e-08, 1.45243978e-08 | 0.231761 | 1 |
| RWA | LEO700 | 83 | -3.22948191e-08 | -4.98374459e-08, -1.51689988e-08 | 0.000674527 | 0.00809433 | -2.67953483e-08 | -4.28280964e-08, -1.11331762e-08 | 0.00202715 | 0.0243259 |

## Seed Sensitivity

The three fixed seeds are reported descriptively with fold-wise mean, sample SD, and range. They are not treated as independent replications.

| Component | Orbit | RMSE mean +/- SD | RMSE range | MAE mean +/- SD | MAE range |
|---|---|---:|---:|---:|---:|
| BAT | LEO500 | 1.94580425 +/- 4.9e-07 | 1.94580381, 1.94580478 | 1.29659757 +/- 3.11e-07 | 1.29659721, 1.29659779 |
| BAT | LEO550 | 1.79447909 +/- 1.45e-06 | 1.79447825, 1.79448076 | 1.18893597 +/- 8.73e-07 | 1.18893512, 1.18893686 |
| BAT | LEO700 | 2.39080876 +/- 4.23e-06 | 2.39080477, 2.3908132 | 1.55829205 +/- 2.74e-06 | 1.55828897, 1.55829422 |
| RWA | LEO500 | 0.0207255455 +/- 5.38e-06 | 0.0207196843, 0.0207302617 | 0.0155862788 +/- 3.82e-06 | 0.0155818729, 0.0155885783 |
| RWA | LEO550 | 0.020271667 +/- 1.49e-08 | 0.020271651, 0.0202716804 | 0.0150540654 +/- 8.31e-09 | 0.015054057, 0.0150540737 |
| RWA | LEO700 | 0.021490302 +/- 6.56e-09 | 0.0214902945, 0.0214903067 | 0.0167122689 +/- 5.01e-09 | 0.0167122631, 0.0167122723 |

## Interpretation

The deterministic six-fold gate remains separate from statistical and engineering conclusions. The original paired CSV cannot establish frozen-reference unit uncertainty. The candidate-only cluster bootstrap is conditional on the registered orbit sample and a fixed benchmark score; replay-control tests are not substitutes. No practical-significance threshold was pre-registered.

**Reproduction command:** `python work/paper/repro/build_f6_statistics_20261002.py`
