# F2 Processed-Tensor Replay Addendum

**Audit date:** 2026-10-02 (UTC)  
**Purpose:** Append-only update to the earlier revision-binding addendum. This records a current deterministic replay that was not available when the earlier addendum was written.  
**Scope:** BAT/RWA train/validation interim Parquets and their preprocessing outputs only. The pipeline read holdout membership metadata, but no holdout telemetry or labels, raw MAT payload, A1/B1 data, or sealed payload.

## Determination

The current released train/validation Parquet inputs, current Rack preprocessing code, and the checked-in BAT/RWA preprocessing configurations deterministically reproduce the canonical processed BAT/RWA tensor values. A reader trace saw exactly the 275 train/validation Parquets per component and zero holdout Parquet reads. Every feature and label tensor checked was bitwise equal to the canonical payload. The initial replay `.pt` file hashes differed because `meta.norm_stats` contained the scratch output path; changing only that metadata string to the canonical relative path and serializing with the production `_save_pt` function yielded exact canonical SHA-256 matches for both tensors.

This closes the current raw/interim-to-processed reproducibility link for the existing data files, code, and configs. It does **not** create a contemporaneous receipt for the original canonical files' July 2026 creation event: the original operator, time, and exact historical code/config state remain unverified. The two inspected ModelScope commits have different root manifests but the complete-tier tree and manifest are identical. DOI disclosure and commit-specific license applicability remain unresolved at the repository level; the date-qualified live API license observation is recorded in the machine manifest.

## Replay Contract

- Rack root: `/mnt/data/BRPHM/rul-space`; source package `.venv-fm/bin/python`, Python 3.10.20, NumPy 1.26.4, pandas 2.3.3, PyTorch 2.3.1+cu121, PyYAML 6.0.3.
- Entry point: `src.datasets.preprocess.run` routes `split.policy=cell_tail` to `run_target`.
- Configurations: `configs/preprocess/bat_target.yaml` SHA-256 `a9fb5a6c22e1de4364dd44d160de9cff93d446453b90d32b839f4f86f35ab095`; `configs/preprocess/rwa_target.yaml` SHA-256 `95d4fc52a5de90a7fb4513fad58d6f6edcb72aa7a2460f1b325940a3e1a76457`.
- Code: `src/datasets/preprocess.py` `5d6720d486a9c2cb7ef580881462492490b705311a69f7688487d2bda5868463`; `windows.py` `0bb61ab593272c18177a33724f29bbc2f0b45595d55913c12686d2635db50945`; `labels.py` `08a5aaf74e9cb1f97f035e815da86ccd4d88485a675d0c02e64cc3451c9943d2`; `sim_loader.py` `05afe14c78200be6523c5e23802d0c4c1298f693d5dbe580a4d478d58090dd06`; `scripts/_serveropt.py` `62e20910ecb866ef950b2a601d0ca0d54050d922f1fe864f57613cf78936f267`; `scripts/validate_tree.py` `b6eeb5e501140ca99802d2199c4d1394856c7374e83a565cb9a84a0424c6818f`.
- Only the five `out.*` paths were overridden. Scratch outputs were written to `work/paper/review/f2_tensor_replay_20261002/{bat,rwa}`. Existing split CSVs and `data/holdout/holdout_manifest.csv` were read-only. Canonical tensors and normalization files were not written.
- The existing per-unit ModelScope hash audit matched all 550 train/validation raw MAT files and all 550 train/validation interim Parquets to the published manifest: 1,100/1,100 matching hashes, zero mismatch. That report is `f2_modelscope_raw_hash_binding_20261002.json`, SHA-256 `a7c995973d122c0084ec0d65f02de053c407330fce068b23b4d7daa4a11a3fb95`.

Replay invocation was through the repository's Python API to redirect outputs safely:

```python
from pathlib import Path
from src.datasets import preprocess as p

root = Path(".").resolve()
cfg = p.load_config("configs/preprocess/bat_target.yaml")  # repeat with rwa_target.yaml
cfg["out"].update({
    "pt": "work/paper/review/f2_tensor_replay_20261002/bat/bat_target.pt",
    "pt_train": "work/paper/review/f2_tensor_replay_20261002/bat/bat_target_train.pt",
    "pt_val": "work/paper/review/f2_tensor_replay_20261002/bat/bat_target_val.pt",
    "norm_stats": "work/paper/review/f2_tensor_replay_20261002/bat/bat_target_norm_stats.json",
    "stats_doc": "work/paper/review/f2_tensor_replay_20261002/bat/bat_target_stats.md",
})
result = p.run(cfg, root=root, workers=1)
```

For the read trace, `_read_parquet` was wrapped to record each requested basename while delegating to the original reader. The read-unit set was compared to train/validation IDs in the frozen split CSV and to holdout IDs in the holdout manifest. After value comparison, only `payload["meta"]["norm_stats"]` was reset to the canonical relative path before calling `_save_pt(payload, scratch_path)` for the final byte-hash comparison.

## Results

| Component | Read calls / train-val IDs | Holdout reads | Windows (train / val) | Tensor shape | Tensor field equality | Canonical / normalized replay SHA-256 |
|---|---:|---:|---:|---|---|---|
| BAT | 275 / 275, exact set | 0 | 2,364 / 1,317 | `[3681,60,4]` | `x`, `y_rul`, `y_hi`, `mask.y_hi`: bitwise equal | `9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` |
| RWA | 275 / 275, exact set | 0 | 4,884 / 2,167 | `[7051,30,13]` | `x`, `y_rul`, `y_hi`, `mask.y_hi`: bitwise equal | `9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595` |

The sorted read-unit ID set SHA-256 is `f11eb56134f9bf6239802591b5101dfd757d8bb76c3999fad71da728b5b7c85f` for BAT and `b9ebc781752afa3ed1174fcdca67ccca1db801f19d4d204e70387a568499deed` for RWA. The replay-generated norm-stat JSON differed bytewise because `created_utc` changed; after excluding only `created_utc`, every remaining field matched the canonical norm-stat file. Canonical/replay norm-stat hashes are BAT `2d85f3a241a343f8ac18d0ba2c0e3d09019cfb13c913869bf2d72743fc547796` / `28af79a0fd4815ee2be3442bb43a9e94539a86c610c3b6af18d26842af2c5b7b`, and RWA `b65cc7be29a372748188550250dfd65ce1483b01a5796fabfc36ba1a586be0e4` / `fced96e199488d5a9cbc32edc3f78d94e9ab0e98047eed5a041a4bbeb46e6203`.

Two transient tooling mistakes were retried and logged in the JSON addendum: one remote inline command failed shell parsing before the preprocessing process started, and one hash-check call passed `_save_pt` arguments in reverse order and raised before writing. Neither attempt read or changed canonical data; the corrected trace and serialization checks passed.

## Evidence and Limits

- Canonical tensor SHA-256 was independently checked on Rack and matches the frozen formal receipt; exact replay serialization also matches those same hashes.
- ModelScope historical commit `85ebba12f3ec132dc9e0ea8ae49012f57505ccf1` and current head `cfe0a27a99fa776d6e464649576432c871992771` share complete-tier tree `f0b07bea4a1d2eb9286b26f7c91f34b951391da3` and complete-tier manifest SHA-256 `ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062`. Their root manifests differ; the report does not claim full repository revision identity.
- Confidence is high for current train/validation file-to-tensor derivation, current split adherence, and holdout exclusion. Confidence is not asserted for the original July 2026 creation event's operator or runtime because no contemporaneous receipt was found.
- The live dataset-detail API reported `CC-BY-4.0` on 2026-10-02, but neither inspected Git commit includes a versioned license file. No DOI was disclosed by the inspected API/README, and exact-name DataCite/Crossref searches returned no result on that date. These are explicit remaining source metadata issues for publication.

The machine-readable record is [f2_tensor_replay_addendum_20261002.json](f2_tensor_replay_addendum_20261002.json). It provides exact file hashes, read-set hashes, and comparison outcomes.

