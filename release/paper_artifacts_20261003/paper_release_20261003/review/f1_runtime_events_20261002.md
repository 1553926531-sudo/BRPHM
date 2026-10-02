# F1 Runtime Events: 2026-10-02

This append-only companion log records the clean-test continuation after the
old outer-fold chain was rejected. It does not promote any result to a final
claim and does not replace the primary ledger.

## Environment and hashes

- Rack: `first@10.123.100.40`, project `/mnt/data/BRPHM/rul-space`.
- SSH key: `C:/Users/Administrator/Documents/id_ed25519`.
- Rack clock in command output: `2026-10-01T18:32:47Z`; local clock: `2026-10-02T02:35:20.4278020+08:00`. The offset is recorded rather than silently normalized.
- `run_f1_generator_v8_bat_20261002.m`: `0cd020b8413eb3ab1002fd481b64f7baac1b7735cc641e46ec18b7eb4ae5a4d2`.
- `build_f1_generator_v8_20261002.py`: `09b7be0bf75c3d5ee017b79b6e7aa6bc845ec0d793a052d66d0a93b814b1cf53`.
- `build_f1_final_partition_v8_20261002.py`: `a19be6291e04b71d7b48f515bf0646c9a3e08155412277cb755c360814e20db6`.
- `build_f1_raw_partition_v8_20261002.py`: `d6839d3b2ef6179157d74f8a6c78cfd8d78bd694586e8ca4ae60019bf0c01ad4`.
- `f1_clean_final_test_20261001_v2.py`: `7cf9be5fc5d19859955f71384afcfd27533dbd098369e0767fac73c0715f2482`.

## Event 1: raw-pool census command failure and repair

The first invocation attempted to use the Rack default `/usr/bin/python3` and
failed with `ModuleNotFoundError: No module named 'torch'`. The surrounding
PowerShell command also expanded the remote `$out` variable before SSH, so its
`[ -e ]` guard was malformed. No output manifest was written and no final
label was read.

Repair: locate the project runtime and use an absolute output path. The
working runtime is `/mnt/data/BRPHM/rul-space/.venv-fm/bin/python`.

## Event 2: raw-pool candidate manifest created

Command (Rack, metadata-only):

```text
/mnt/data/BRPHM/rul-space/.venv-fm/bin/python
  /mnt/data/BRPHM/rul-space/work/paper/repro/build_f1_raw_partition_v8_20261002.py
  --root /mnt/data/BRPHM/rul-space
  --output /mnt/data/BRPHM/rul-space/work/f1_raw_candidate_manifest_v8_20261002.json
```

Result: exit code `0`, elapsed `0:25.22`, CPU `41%`, max RSS `375992KB`.
The manifest has six rows, one per component×orbit cell. Eligible counts were
BAT `(21,24,25)` and RWA `(10,11,13)` for LEO500/550/700. Exclusions were
recorded in the manifest; `semantic_labels_read=false`.

- Manifest SHA-256: `8381021c60703f0cdf6cb163a2d4df9b06f2a20ebc06857cfeaad6e08cf86326`.
- Sidecar SHA-256: `6294d4e06557063a520e1b8d20a20c97738250379ff61d0896018e864900fbbd`.
- Disposition: **备用候选清单，仅元数据；未冻结、未读 final labels、未评估。**

## Event 3: v8 BAT generation remains active

At Rack UTC `2026-10-01T18:32:47Z`, PID `2902630` was present with:

```text
etime=01:12:32  cputime=01:07:45  pcpu=93.4  pmem=1.3  stat=SNl
```

The wrapper log was still in the S984 initialization block at that poll. No
generated BAT `.mat`, summary, or exitcode existed **at that timestamp**. The
process was not interrupted, restarted, or duplicated. Its resource contract
remains one CPU with low priority (`taskset -c 0 nice -n 15 ionice -c 3`),
leaving Rack capacity for normal use.

## Event 4: S984 completed; same PID moved to S985

At Rack UTC `2026-10-01T18:43:33Z`, the same PID was still active. S984 had
completed with log code `0`, `N=80935`, `K=282`, and wall time `4401.2 s`.
The generated file is:

```text
/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v8_bat/generated/bat/BAT_LEO500_B00_H2_L3_S984.mat
size=2376431 mode=664
sha256=75b38245b947ffcd8c178e2ed1c868a1e8d0532000b1239d1f76a089a52b77bd
```

The same MATLAB PID then entered S985 (`StopTime=1.09634e+06 s`). No second
MATLAB process was started and no final-label access occurred.

## Event 5: S985 completed; same PID moved to S986

At Rack UTC `2026-10-01T20:14:53Z`, S985 completed with log code `0`,
`N=109635`, `K=382`, and wall time `5800.1 s`. The generated file is:

```text
/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v8_bat/generated/bat/BAT_LEO550_B30_H2_L3_S985.mat
size=3179040 mode=664
sha256=f8a17ae95ed87efa0666a4cad986311630df3757fdf9990704efd94a7eec901e
```

The same MATLAB PID then entered S986 (`StopTime=706020 s`). No second MATLAB
process was started and no final-label access occurred.

## Promotion rule

The v8 BAT tree is not a final partition until all three generated files have
passed file/hash checks, the final partition manifest is created, and an
immutable candidate-freeze event precedes any final-label access. A performance
metric or paper decision cannot be made from the running process or the raw
candidate manifest.

## Event 6: v11 source-binding and inherited-output failures

The first single-tree builder call failed before generation because its source
ID argument was in the wrong position (`RuntimeError: source contract drift:
BAT_LEO550_B30_H0_L2_S187`). It wrote no config, raw file, or label output.

The corrected retry initially used `BAT_LEO550_B30_H0_L2_S149` for S915 and
`BAT_LEO700_B30_H2_L1_S279` for S916. Both trees were copied from the mixed
tree, which already contained three RWA files. This violated the single-source
tree contract. S915 (PID 3417128) and S916 (PID 3417126) were stopped before a
fresh BAT file was produced; both IDs and trees are burned and cannot enter a
final partition. No semantic or final labels were read.

The manifest check then confirmed that the intended LEO550 source is
`BAT_LEO550_B60_H0_L2_S187`; the earlier B30 choice was a binding error, not a
data result.

## Event 7: clean single-source retry trees

The builder was changed to remove any inherited `generated/` directory after
copying the model tree. Fresh trees were created:

```text
/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v11_s917
/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v11_s918
```

Bindings and source-card hashes:

| Unit | Source unit | Seed | Source-card SHA-256 |
|---|---|---:|---|
| `BAT_LEO550_B60_H0_L2_S917` | `BAT_LEO550_B60_H0_L2_S187` | 891917 | `533a6add4fb9815867338dd19f84d85cb300e9d7ac8fff6565468b7c41e908f4` |
| `BAT_LEO700_B30_H2_L1_S918` | `BAT_LEO700_B30_H2_L1_S279` | 891918 | `50a0caff2ecf378591b49f75780b23302632904da0e6c4984939ef2ced672fff` |

The post-build generated-file count was zero for both trees. Builder, runner,
and source-card hashes are recorded in the JSON ledger. The source cards state
`semantic_labels_read=false`.

## Event 8: v11 BAT generation running

At observed Rack time `2026-10-01T22:51:38Z`, the two new MATLAB processes were:

```text
PID 3424547  CPU 1  BAT_LEO550_B60_H0_L2_S917  seed 891917  stop_time_max_s 1500000
PID 3424543  CPU 2  BAT_LEO700_B30_H2_L1_S918  seed 891918  stop_time_max_s 1500000
```

S914 remains the only process on CPU 0. The two new logs show the expected
B60/H0/L2/S187 and B30/H2/L1/S279 configuration cards; no fresh BAT file had
appeared at that observation. This is generation evidence only. No partition
freeze, final-label access, feasibility probe, or metric evaluation has been
performed.

## Event 9: S917 generation completed

`BAT_LEO550_B60_H0_L2_S917` completed with MATLAB exit code `0`, simulation
code `11`, `N=33293`, `K=117`, `Tf=3.72545 d`, and wall time `1792.3 s`.
The raw file is `1126473` bytes with SHA-256
`2a8641557bab826e2f733231fe9395fed8282cd43021f8543692c33f8e6fb9c7`.
This is still a diagnostic unit: no semantic label access has occurred, and it
is excluded from the eventual v13 final partition.

## Diagnostic promotion boundary

The current diagnostic IDs are S911--S913, S917, S918, and S925. After generation completes,
the v12 metadata manifest will be read once by
`probe_f1_partition_feasibility_v12_20261002.py`; that operation reads
`label.rul`, records finite/nonnegative/kept window counts, and burns every
touched unit. The diagnostic manifest and probe output cannot be passed to the
freeze evaluator.

Only after the probe will a new, unprobed batch S919--S924 be generated and
bound into the final partition. The final freeze command will hash those raw
files before its first semantic label access. No S911--S918 ID may appear in
the final manifest.

## Event 10: mixed-tree S914 queue abort and clean replacement

The S914 MATLAB process was stopped after log inspection showed that its
six-row mixed manifest was executing the historical BAT queue. No file named
`BAT_LEO500_B60_H2_L3_S914.mat` was written and no semantic label was read.
S914 is burned and cannot be reused.

A clean single-row tree was built for `BAT_LEO500_B60_H2_L3_S925`, bound to
source `BAT_LEO500_B60_H2_L3_S106`, seed `891925`, and stop time `1500000 s`.
The post-build generated directory was empty; source-card SHA-256 is
`406c2038025cc9aa82bbd40eb12562028e453cd0acba3d23493a038473832790` and the
single-row manifest SHA-256 is
`3900ae0c9a9f0ac3bb6a2a4ff4e304ecd57088b75d26519240bbee13ed5e1752`.
PID `3526285` runs on CPU 0 at low priority.

## Event 11: v11 BAT stop-time contract failure and repair

`BAT_LEO700_B30_H2_L1_S918` completed the long MATLAB simulation but failed
before atomic output because the requested `stop_time_max_s=1500000` is not an
integer multiple of the 5740-second orbit period. The log reports
`make_dataset:stop` at `run_one_sample:608`, wall time `7888.6 s`, and zero
fresh MAT files. Log SHA-256 is
`13b2661c7404d07eab30d09fcb55a4a28efc4ccf25612ed96a8e9641a6af6599`.
No semantic or final label was read. S918 is burned.

S925 used the identical invalid stop ceiling. After S918 established the
deterministic contract failure, S925 was terminated with SIGTERM at Rack UTC
`2026-10-02T01:09:03Z`, before output and before any label access. Its log
SHA-256 is `729813068c1ea6d9e225c7995c95421ee8ffc63dc9c644f847e5b457ee543e52`.
S925 is burned and cannot enter a partition.

The repair is isolated in `build_f1_single_generator_v12_20261002.py`: BAT
stop ceilings are deterministically floored to an integer orbit, recording
requested `1,500,000 s` and effective `1,498,140 s = 261*5740 s` in the
source card and manifest. New IDs S926/S927 were built from fresh trees with
empty generated directories; their source-card hashes are
`7ae77b70089d60e58f7055aed1fdc60cf3b2549f37bb43c22a732ac64c0fbc8a` and
`9b5e213a8530730aa23100454f57c0bfa54ecafd7adb2fbee695d75e8a208417`.

At Rack UTC `2026-10-02T01:10:10Z`, S926 (PID 3652511, CPU 2) and S927
(PID 3652516, CPU 0) started under the same one-process low-priority resource
contract. Both remain unprobed and label-free. The v12 partition builder now
accepts the v2 stop-time cards and binds S917/S926/S927 plus the three RWA
diagnostic units; failed S918/S925 are excluded.

The first v12 start command then failed before entering `make_dataset`: the
nested SSH quoting changed the MATLAB directory to
`/home/first/ /mnt/data/BRPHM/rul-space/work/paper/repro`. Logs contain no
simulation banner, no output, and no label access. S926/S927 are therefore
burned as runner failures. The replacement is pre-registered as S928/S929
with the same source bindings and orbit-aligned `1,498,140 s` ceiling, and it
will invoke the uploaded file-based `.sh` runner to remove the shell quoting
failure mode.

S928/S929 were then created from fresh trees and started through the uploaded
file-based runners. At the first post-start check, MATLAB command lines showed
the correct `/mnt/data/BRPHM/rul-space/work/paper/repro` directory and both
PIDs remained alive; no semantic labels or final labels have been read.

## Event 12: repaired BAT diagnostic outputs and metadata manifest

S929 completed with simulation code 11, `N=117671`, `K=411`,
`Tf=13.08708 d`, wall time `6505.1 s`, and raw MAT SHA-256
`151969b33490752d7b4672edb036025afe30ff5a6c6b823b2ab6fedc967e264a`.
S928 completed as a censored BAT run with code 0, `N=149815`, `K=522`,
no finite failure time, wall time `8017.9 s`, and raw MAT SHA-256
`5cbba9d844f988a22322deda9d6e3cb5d4cf8450d1b158a3a6ed329dbafaec5b`.
Both outputs were generated with effective `StopTime=1,498,140 s`, and neither
has been opened by the Python label-processing path.

The metadata-only v12 partition manifest contains the three existing RWA
diagnostic units plus S917/S928/S929. It has SHA-256
`6cb683245434874c114eda84c286cacbf067f868903af064e7829a8aa01fa767` and
declares `semantic_labels_read=false`; it is eligible only for the one-time
feasibility probe.

## Event 13: diagnostic feasibility probe completion

The v12 partition was probed once to test preprocessing-window feasibility.
This was a development/diagnostic operation, not a final evaluation. The probe
read semantic RUL labels, did not perform final-label access, and permanently
burned every touched unit.

- Probe: `/mnt/data/BRPHM/rul-space/work/f1_diagnostic_probe_v12_20261002.json`
- Probe SHA-256: `a3998d1ad99e539cad05c7b4153b6b5664d291d639666aef547d1cf8c9fb36b8`
- Input manifest SHA-256: `6cb683245434874c114eda84c286cacbf067f868903af064e7829a8aa01fa767`
- Probe interval: `2026-10-02T03:38:29.508916Z` to `2026-10-02T03:38:33.746720Z`
- `semantic_labels_read=true`; `final_label_access=false`; `diagnostic_only=true`
- `all_touched_units_excluded_from_future_final_partitions=true`

| Unit | Raw windows | Finite labels | Kept | Status |
|---|---:|---:|---:|---|
| BAT LEO500 S929 | 30 | 30 | 28 | feasible |
| BAT LEO550 S917 | 0 | 0 | 0 | zero windows after label filter |
| BAT LEO700 S928 | 41 | 0 | 0 | zero windows after label filter |
| RWA LEO500 S911 | 57 | 57 | 3 | feasible |
| RWA LEO550 S912 | 57 | 57 | 11 | feasible |
| RWA LEO700 S913 | 57 | 57 | 8 | feasible |

All six units (`S911`, `S912`, `S913`, `S917`, `S928`, `S929`) are excluded
from every future final partition. Only predeclared fresh IDs `S919`--`S924`
remain eligible for the F1 final chain.

## Event 14: S922 builder permission failure and replacement

The first BAT final-tree build for `BAT_LEO500_B60_H2_L3_S922` failed before
MATLAB was invoked. The copied v12 diagnostic base retained a mode `0444`
`single_source_card.json`; the builder attempted to replace that file and
raised `PermissionError`. No raw output, semantic label, or final label was
read. S922 is therefore burned as a failed build and will never enter a final
manifest.

The repair is to use the v11 mixed base only as a code/template source (the
builder removes inherited `generated/` output and writes a new single-source
card), while keeping the source ID, orbit, seed and stop-time contract
pre-registered. A fresh `BAT_LEO500_B60_H2_L3_S930` replaces S922. The final
eligible set is now `S919`, `S920`, `S921`, `S930`, `S923`, `S924`.

## Event 15: S923 completed; S930 remains active

S923 (`BAT_LEO550_B60_H0_L2_S923`, seed `891923`, CPU 2, MATLAB PID `3918683`)
completed successfully according to the MATLAB `make_dataset` completion row.
The output was written at `2026-10-02T04:30:32.594595Z` (Rack file mtime) and
observed complete at `2026-10-02T04:33:09Z`. MATLAB reported simulation code
11, `N=33,293`, `K=117`, `Tf=3.72545 d`, and wall time `1792.9 s`.

- MAT: `/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v12_s923/generated/bat/BAT_LEO550_B60_H0_L2_S923.mat`
- MAT size/SHA-256: `1,126,605` bytes / `c701a9762c2cd55c28501a15216b4b2786dae96a069b43c487d41c7bace9dc92`
- `run.log` SHA-256: `c05d0f8c0eeabd17b68f8b074f395ac90830c8852c99aea49ff0fd3b0510462e`
- MATLAB output: `make_dataset` reports one product, zero failures, and status `ok`.
- `semantic_labels_read=false`; `final_label_access=false`.
- Limitation: the detached shell exit status was not retained independently; the MATLAB completion row and output/log hashes are the retained completion evidence.

At observation time S930 remained active as PID `3918684`, with no generated MAT.

## Event 16: S930 active; S921 started

S930 (`BAT_LEO500_B60_H2_L3_S930`, seed `891930`) started at
`2026-10-02T03:59:51Z` on CPU 1 under `nice 15` and `ionice -c 3`. Its MATLAB
PID `3918684` remains active. Runner SHA-256 is
`9b7d1f61c7c86735879322b12a1289409d381e30c8e8279922b6964b41d0ba6b`; MATLAB
script SHA-256 is
`0762cc1b3443f764296d6d9c6b1413cdb2b6372ba94a0f2cc6f6a6a31aab47c7`; source
card SHA-256 is
`8acc511d4783e231aab871ebeba49b0eca1b20f797abb18b38d82984035b9afd`.
No final MAT or semantic/final label access was observed as of
`2026-10-02T04:35:16Z`.

S921 (`RWA_LEO700_B60_H0_L1_S921`, seed `891921`) started at
`2026-10-02T04:35:04Z` on CPU 2 under `nice 15` and `ionice -c 3`; MATLAB PID is
`3968538`. At first verification (`04:35:16Z`), it was active and its generated
directory was empty. Runner SHA-256 is
`8151dc44f1604664b90ca5401fe3fb472cb6bd4abd1e87097da078f617c7b895`; MATLAB
script SHA-256 is
`c205d8d845126e5b22e0c90ce5c8f5588b99a3ff9f95900d974e8f1b1567101b`; source
card SHA-256 is
`bcb535187001a2297546d3d63d205fe64fb4d3e1d28eae1624b611419d0bea44`.
The inherited source-card manifest hash is
`3dad01245a82d997399476a192054cbaa916cc3cf8ebb2bac8e0b142f54677f2` for both
fresh trees. No semantic or final labels have been read.

## Event 17: S921 RWA raw generation completed

S921 (`RWA_LEO700_B60_H0_L1_S921`, seed `891921`, PID `3968538`) completed at
`2026-10-02T04:41:16.833391Z` by Rack output mtime. MATLAB reported simulation
code 2, `N=4,919`, `K=17`, `Tf=0.24965 d`, wall time `275.84 s`, one product,
zero failures, and `status=ok`.

- MAT: `/mnt/data/BRPHM/rul-space/work/f1_generator_20261002_v12_s921/generated/rwa/RWA_LEO700_B60_H0_L1_S921.mat`
- MAT size/SHA-256: `298,119` bytes / `b00f5fe10360a2efda13b81beb61c0815b86dfb38ac3d8a48f19b7530f1bcaee`
- `run.log` SHA-256: `dec1b4c9a68e52f60297b17d593f13ffadcb89612e2ce477b5707af202eeff76`
- `semantic_labels_read=false`; `final_label_access=false`.

## Event 18: verified GMAT R2026a package installed in tool cache

The host copy of the official SourceForge Linux package was transferred once
to `/mnt/data/BRPHM/tool-cache` and verified against official release metadata
before extraction. Package size is `401,664,992` bytes, MD5 is
`ec496a0319657fa2c079d7e996b9b1ed`, and SHA-256 is
`fe124b4a606b2e3b704a6fbb1c37b87598d5df0d18cb661c304b5f60074a7754`. The
official metadata listed the same size and MD5. The extracted runtime is
`/mnt/data/BRPHM/tool-cache/GMAT/R2026a`; no package was fetched from the
internet during this transfer.

## Event 19: first GMAT R2026a script rejected before propagation

GMAT R2026a started successfully and parsed the new-orbit script, then rejected
the legacy list form `EclipseEvents.Spacecraft = {DefaultSC}` during script
validation. Exit code was `1`; no propagation, CSV, eclipse report, raw
simulation, or label access occurred. The full log SHA-256 is
`55c7271e95af5da7b096769b88042ff4dea2dd4adc750e2daf9d75dbda78b04f`; the v1
script SHA-256 is
`112036458f3fd2626befc966bf3b9a9f704b33a7a6188bc3a882a299a20c63ce`.

The cause is a GMAT resource-field syntax difference. R2026a's bundled
`samples/Ex_EclipseLocation.script` assigns a single spacecraft object without
braces. The repair is an immutable v2 script with only that field corrected;
the failed script and log are retained.

## Event 20: GMAT R2026a produced the LEO600-B30 environment

The v2 script completed successfully with GMAT's own `Integration test
(Console version) successful` message and `Total Run Time: 7.125 seconds`.
GMAT propagated the new 600 km orbit for 30 days and produced both report
files. The CSV has `43,201` data rows, an exact `2,592,000 s` span from
`01 Jan 2026 00:00:00.000` to `31 Jan 2026 00:00:00.000`; the eclipse table has
445 sequential positive-duration Earth umbra events. This was independently
checked with PowerShell `Import-Csv` and whitespace-field parsing.

- v2 script SHA-256: `ca5644bb8d29bb31698d1b5a813429f4b6422c91187c01c649272a4135b629f6`
- GMAT run log SHA-256: `fbe7c706634d57591d1b78691b112551eb294627f0d2e0b3d579bbf3fbf3ef2d`
- Orbit CSV size/SHA-256: `6,656,072` bytes / `db5c99f14ebc3582d57ee76a3bb955c4cc51c9f0b11eaad3ee22a7bdc1b22c77`
- Eclipse report size/SHA-256: `57,716` bytes / `c9bda562da4b8eff4209a1b183b48f1e8524463036f39804af565c6913c89331`
- `semantic_labels_read=false`; `final_label_access=false`.

The console reported that optional Python 3.12 and MATLAB interface plugins did
not load because their shared libraries are absent. GMAT core initialization,
propagation, eclipse location, and the integration test completed; neither
optional plugin is used by this orbit-generation script.

## Event 21: LEO600 fixed-period tile boundary audit

The isolated generator reports the GMAT LEO600 period as approximately
`5819 s` while the registered model contract fixes each environment tile and
BAT orbit period at `5740 s`. Its startup diagnostic reports a `-79 s`
difference and `608 km` seam. The independent GMAT V1-V8 import manifest passes
for B00/B30/B60, but those checks validate time grid, eclipse geometry and beta
and do not test periodic spatial closure. The mismatch is retained as a
physical-model validity limitation; no final label was read to investigate it.

- `sat_params.m` SHA-256: `22644a6feecca2f692db325621c2f244a4b2213174f1f3f0793138b3116bea48`
- `import_gmat.m` SHA-256: `3d13d8f3488e9d0a4bd94389d9cc350e5007d29dc4c7950960602a8665730f6d`
- LEO600 validation manifest SHA-256: `c57cdaf3d0ace5a0c9e09c1c8000a281b58909eb48a0becfc5dab19941e6370f`

## Event 22: LEO600 run restarted with measured resource allocation

The first 2-worker run (launcher PID `4160191`, workers `4163311/4163313`)
remained active after 22 minutes with zero raw outputs. At `2026-10-02T07:00:48Z`,
Rack had 208 logical CPUs, 89% idle in a 1-second `vmstat` sample, `132 GiB`
available memory, and zero swap-in/out. After rechecking the output directory
and exact process identities, SIGTERM was sent to those three PIDs. They were
absent by `07:08:38Z`; output remained absent and the original log hash was
`5ab6de68faaf29fc9257ddb6bd646a7dd7ca321c692660900c584ac29b9fa07a`. The
detached process did not retain an OS exit code.

An 8-worker run was launched at PID-file mtime
`2026-10-02T07:09:10.545858157Z`, with affinity `0-7`, `nice 15`, and
`ionice -c 3`. The MATLAB log confirms an 8-worker pool. By
`2026-10-02T07:19:16Z`, it had written three RWA units, each reported `status=ok`
and zero failures. Raw file sizes/hashes and the contemporaneous generator log
hash are in `f1_leo600_run1_20261002/execution_snapshot_20261002T071916Z.json`
(SHA-256 `f71baba6cc406290d1d1e6d0171b22e60aabebd24b7c4be8ee5dd8522c48d105`).
The W8 runner captures MATLAB's return code in `generator_w8.exitcode`.

A 12-worker plan was prepared from measured idle capacity, but a fresh output
check found completed files before any existing process was stopped. The plan
was cancelled; W8 continues as the only active generator. The unused amendment
record has SHA-256
`13c0f43387391617243d5519e8b2618f90daa7c362801a2ea6cf1723210c2131`.

No semantic labels, final labels, preflight, final freeze, or evaluation have
been accessed or started as of this event.

## Event 23: all six LEO600 RWA raw units completed

At `2026-10-02T07:28:38Z`, MATLAB had completed manifest positions 7-12,
covering all six registered RWA units S946-S951. Each was reported `status=ok`
with zero failures. Their exact byte sizes, Rack mtimes and SHA-256 values are
in `f1_leo600_run1_20261002/execution_snapshot_20261002T072838Z.json`, whose
SHA-256 is `eb5bcbf325f5a1bffa47d7b51a388604e7ececf2e2a94ec082807147cd0786ce`.
The snapshot and checksum sidecar are mode `0444` on Rack. The contemporaneous
generator log SHA-256 is
`eef44b1f19e2a07a30ce390c719b4e385d7f563954c9727bf9fc589411aa817f`.

The six BAT units S940-S945 remain in progress. The 8-worker MATLAB run is
still active, and the host reported about `123 GiB` available RAM and no swap
I/O at this observation. No semantic/final labels, partition seal, candidate
freeze, or evaluation have started. Local tests passed: 10 wrapper tests and
6 partition-builder tests; the relevant JSON files parse successfully.

## Event 24: evaluator fit-label boundary statically verified

Before final-label access, the Rack evaluator and both fit implementations were
read with numbered source output and hashed. The candidate path uses
`data["x"][train]` and `data["y"][train]` for source fitting and normalization;
`data["x"][valid]` is used only for prediction. The fixed HGB/MLP control path
also fits only on `x_train/y_train` and uses `x_valid` for prediction. Its
metrics/residual reporting reads `y[valid]` after prediction; in the final
runner this happens only after `final_label_access_started`, and these values
are not fed back into fitting or route selection.

- Fallback module SHA-256:
  `facca14f7abc9b78956245be102b131100f73a29988562766237f293b6a6f65d`
- Relative-blend module SHA-256:
  `f9fa246661793ad098231efeb45f5967f33cd83f35f80aa179453e53d1cacc09`
- Relative model module SHA-256:
  `386de2a1a2a2073215ccf7b526e2f7bb20cffd00c6366a83e08391e3830c1cbf`
- Base TCN module SHA-256:
  `0a50fe3839fdb804903cf8ece5e6191e1cb4dd9bf6b8e23938ae13ab946b1d74`
- HGB/MLP control module SHA-256:
  `658b99fecc31689ef624e0726b330b07bccf377ce7f0977d1814331a728f6bf7`

The wrapper order is `verify_freeze` -> append
`final_label_access_started` -> construct evaluation payload -> fit/predict ->
report metrics and receipt. This is a static audit, not yet a runtime event;
the final receipt must confirm these dependency hashes and event order.

## Event 25: LEO600 raw generation completed

At `2026-10-02T10:22:09Z`, the sole W8 generator exited with code `0`. MATLAB
reported 12/12 completed units, zero failures, and one censored BAT trajectory
(`BAT_LEO600_B60_H1_L3_S944`, code `0`). The six BAT and six RWA raw files were
then sealed by a metadata-only partition builder; no semantic/final labels were
read during generation or seal.

- Partition manifest SHA-256: `910c0582bc7e451385faccc48987f1cdb5b5684ba2b105efa240a1e8f5ce3123`.
- Partition sidecar SHA-256: `cabfffc3a2c9f61ceee9bdb86227c2a5e9316b46850c6bc3282476d6dd84d0f0`.
- Final generator log SHA-256: `69735acb97691b71335239210d9ba5f1befa13af6a12a1bdeb6987623d9ee9bb`.
- Exit-code file SHA-256: `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.
- Resource amendment SHA-256: `01f2475767b4d1d052aa4715c5ab1428e48e6205195b35870e20771f26ae366d`.
- Seal result: `status=sealed_metadata_only`, `unit_counts={bat:6,rwa:6}`.

The raw hashes and unit-level statuses are in the local machine-readable final
verification artifact. The MATLAB command remained the preregistered simulation
command; W8 changed only compute allocation and exit-status capture.

## Event 26: first LEO600 evaluation attempt retained as environment failure

The first output directory `/mnt/data/BRPHM/rul-space/work/f1_leo600_final_20261002`
was frozen successfully, then its `final_label_access_started` event was appended
at `2026-10-02T10:23:53.912804Z` (event SHA-256
`8c0d457e703ab0b0d5138e1251654f7c1f048f9773f1c46cc8d907fa33f2256d`). The
evaluator failed immediately at `ModuleNotFoundError: No module named 'src'`.
No payload, receipt, metric, or completed-evaluation event was written, and the
failure amendment records that semantic labels were not read. The failed
directory is retained and not reused.

## Event 27: retry freeze and final evaluation completed

The only repair was setting `PYTHONPATH=/mnt/data/BRPHM/rul-space`; candidate,
routes, partition, thresholds and dependencies were unchanged. A new immutable
retry directory was frozen before label access:

- Freeze manifest SHA-256: `0e13d131ecf28d9f867e823a9387fd3ed3af398144d90c6afaf5cda2d1f04e69`.
- Selection decision SHA-256: `65fcbd77c2c16a1da0cb2bb93e8bab24818d78ca98282d0214cd6052944ded58`.
- Final receipt SHA-256: `3eff57fe0703fc851e8a96c0016660034fc72c30d2e20b3c3de220c6893ce459`.
- Same-partition performance gate SHA-256: `1f7be0be1ef4761e37b311f3f764094bfac4cd26871c497e9576617585e3bc5b`.

The retry event chain is immutable and ordered as `preflight_recorded` ->
`candidate_frozen` -> `final_label_access_started` ->
`final_evaluation_completed` -> `same_partition_reference_gate_completed`.
The receipt reports exactly-once evaluation after freeze, no holdout use for
training/selection, no sealed/A1/B1 read, and no canonical/competition mutation.

The same-partition gate uses unrounded metrics and tolerance `1e-12`:

| Component | Candidate RMSE | Reference RMSE | Delta | Candidate MAE | Reference MAE | Delta | Units/windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| BAT | `1.1142871129918521` | `1.1142966431138528` | `-9.530122000667163e-06` | `0.673842205479741` | `0.6738513384014369` | `-9.132921695798046e-06` | 5/125 |
| RWA | `0.005497685074806214` | `0.005497685074806214` | `0.0` | `0.005497685074806214` | `0.005497685074806214` | `0.0` | 1/1 |

Gate result: `passes=true`, `strict_gain=true`, `regressions=[]`. BAT supplies
the strict gain; RWA is non-inferior but has one usable unit and one window.
This closes F1 provenance and performance. Old outer results remain diagnostic.

