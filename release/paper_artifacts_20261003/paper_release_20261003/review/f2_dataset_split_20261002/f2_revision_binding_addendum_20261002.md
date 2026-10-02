# F2 ModelScope Revision-Binding Addendum

**Access date:** 2026-10-02 (Asia/Shanghai)  
**Scope:** Read-only comparison of public ModelScope Git/manifests and local registration/split metadata. No raw telemetry, held-out labels, A1/B1 data, or sealed payloads were opened. No dataset payload was downloaded in this comparison.

## Determination

At the released source-record level, the paper's 550 non-holdout `SIM_bat`/`SIM_rwa` unit IDs map one-to-one to the same 550 raw records in both inspected ModelScope revisions. The historical complete-tier tree and current complete-tier tree are identical Git objects, and the complete-tier manifest is byte-identical. Therefore the public source records may be version-pinned to either commit without changing the declared released data tier.

This does **not** establish a byte-level provenance link from those raw MAT records to the formal processed input tensors. The registration CSV has paths and design metadata but no per-file raw SHA-256. The formal receipt has one aggregate input-tensor SHA-256 per component but no dataset commit, raw-manifest hash, per-unit raw hashes, or preprocessing receipt mapping those raw hashes and the preprocessing implementation to the aggregate tensor digest. Thus the existing formal tensor bytes cannot yet be cryptographically attributed to either commit. A paper may identify the source record set and commit, but should not claim the recorded tensor hashes were reproducibly derived from that commit until this missing link is supplied.

## Version and Manifest Comparison

Repository: [ModelScope BRPHM-datasets](https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets)  
Git URL: `https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets.git`

| Artifact | Historical verified commit | Current head at access | Comparison |
|---|---|---|---|
| Commit | `85ebba12f3ec132dc9e0ea8ae49012f57505ccf1` | `cfe0a27a99fa776d6e464649576432c871992771` | `git ls-remote` returned the current hash for `HEAD` and `refs/heads/master`; historical commit raw files resolve over HTTPS. |
| Root `MANIFEST.json` SHA-256 | `0f8d21b05eb0168ad36a070e1beb22421c962fcbbb46f65ff6cc6bba9bc3d697` | `27701f270180dd00fb35c835a62bb0583102fb950f22981199c7dd6bdf56cba1` | Root manifests differ. Historical/current Git blob IDs: `1667f724b6f2d55f30c8b892bc9cd5cd9e304f20` / `c86cea05d65f566fbfbc0aef45e600bb0a4af7e4`. |
| Root manifest metadata | generated `2026-08-31T01:54:28+00:00` | generated `2026-09-05T14:03:14+00:00` | `packages`, `published_tiers`, and `tier_status` are identical. The only `root_files` SHA difference is `README.md` (`767aded6...7810d` vs. `0fb8af75...3a01`); all other root file hashes match. |
| `BRPHM_RUL_complete` package record | 67,539 files; 107,243,597,734 bytes; manifest SHA-256 `ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062` | Same values | Identical package metadata in both root manifests. |
| `BRPHM_RUL_complete` Git tree | `f0b07bea4a1d2eb9286b26f7c91f34b951391da3` | `f0b07bea4a1d2eb9286b26f7c91f34b951391da3` | Entire tier subtree is the same Git tree object, including paths and tracked LFS pointer blobs. |
| `BRPHM_RUL_complete/MANIFEST.json` | Git blob `5fbb843ed576b746c547250a0e9a4cd4546ed7f1`; 23,922,408 bytes; SHA-256 `ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062` | Same Git blob, size, and SHA-256 | 67,539 manifest records and all SIM raw record hashes are identical across the two commits. |

Historical remote-integrity cross-check: local [verification receipt](C:/Users/Administrator/Documents/Codex/2026-07-21/host-rack-linux-hostname-10-123/work/frontend_20260806_redesign/results/research/modelscope_complete_remote_verify_20260831_fix14/verification.json), SHA-256 `DB52292024356F86EB2D5D6A3641DD6A9F96332FBA9AE6A0C02DD5CE4B2E8E72`, records `REMOTE_HEAD_MATCH=true`, root manifest SHA-256 above, `BRPHM_RUL_complete_VERIFY=PASS files=67539 bytes=107243597734`, and `PUBLIC_HTTP=200` at commit `85ebba12...` on 2026-08-31.

## Exact Unit-Set Reconciliation

| Set / artifact | Count | SHA-256 |
|---|---:|---|
| Registration `sim_manifest_remote.csv` | 648 total; `SIM_bat=324`, `SIM_rwa=324` | `93710e01e18684e6296d52c4ae8ea98491841440db8f2b9798e0139901fccbc8` |
| Split `unit_split_membership.csv` | 648 total; train 388, validation 162, holdout 98 | `f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0` |
| Recorded holdout manifest | 98 units | `ee1e2f760ebc69319d3dc0625744a602114a5dc249ebe8b283f0d9cb53d0c981` |
| Public complete-tier SIM raw records | 550 total; `SIM_bat=275`, `SIM_rwa=275` | Encoded by complete-tier manifest SHA-256 above; canonical filtered-record digest below. |
| Non-holdout unit-ID set (`train ∪ val`) | 550 | `538c33e36678f443591a62983237360dea94dce569b6458c58298d33a815335f` |
| Public SIM raw unit-ID set | 550 | `538c33e36678f443591a62983237360dea94dce569b6458c58298d33a815335f` |
| Holdout unit-ID set | 98 | `128a53ff720f2f9e8ac2323525c3f573fbbc529f64000be5769e7e87eefe60f3` |
| Full registration unit-ID set | 648 | `a038bcd2410f61894fb044c9e975ce0d7f92109d1c4fdc02d0a66108ad5c9952` |
| Canonical filtered public SIM raw manifest records | 550 records | `2ad5d1c281741e86c439d4cd208391a63cd72de91436f74b311cc93df778ca9b` |

Set reconciliation result:

- `public_SIM_raw_IDs == registration_train_val_IDs`: **true**, 550/550.
- `public_SIM_raw_IDs ∩ registration_holdout_IDs`: **empty**.
- `registration_IDs - public_SIM_raw_IDs`: **98**, exactly the local membership manifest's holdout set.
- Public IDs missing from the registration: **0**; extra public IDs beyond non-holdout registration: **0**.
- Basename-normalized raw paths and `source_family`/`dataset_id` matched for all 550 public records: **0 mismatches**.
- Each of the 550 public raw records has a manifest `bytes` value and a syntactically valid 64-hex SHA-256. There is no corresponding per-file SHA column in the local 648-row registration CSV to compare against.

Set-hash algorithm: collect the specified IDs, sort lexicographically, join with one LF after every ID, encode as UTF-8, then SHA-256. The filtered-record digest uses the 550 complete-tier manifest rows where `layer == "raw"` and `source_family in {"SIM_bat", "SIM_rwa"}`, sorted by `path`, serialized with Python `json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`, ASCII-encoded, then SHA-256.

The local F2 manifest digest recorded by this 2026-10-02 addendum was `5ce4f9733dbf858df49e469545a0c8dcaa212e372a7b98bf20ada56c5b58f79d`; this is a historical snapshot, not the current file. The earlier `f2_evidence_ledger.json` value `7bf5e5b040ab09c7025de937950635ee210b44406b36dc4db15566a1760d9524` is also retained as historical evidence. The post-freeze 2026-10-03 rebinding produced current manifest SHA-256 `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2`; the current ledger and consistency record carry that value.

## Formal-Tensor Provenance Check

| Artifact | Evidence |
|---|---|
| Current frozen formal receipt | `work/paper/review/f5_unit_metrics_20261002/frozen_candidate_receipt.json`, 6,138,349 bytes, SHA-256 `b99ed8a3d2f168483f1072e7363fe1793a08708c16693ea6ba59e29bf03631f1`. Recursive key audit found no `raw_manifest_sha256`, `input_manifest_sha256`, `raw_sha256`, `source_raw_sha256`, `dataset_commit`, `modelscope_commit`, or `dataset_revision` field. |
| BAT formal input tensor | `input_tensor_sha256=9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` |
| RWA formal input tensor | `input_tensor_sha256=9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595` |
| Fold evidence summary | `work/paper/evidence/evidence_summary.json`, SHA-256 `24666999c05051435e5ffcf418ddab428e709b797b8c06f947a2b7fcada91417`; repeats the same component-level tensor hashes across folds. |
| Missing deterministic link | No receipt binds the public per-unit raw SHA list and preprocessing code/config/version/command to the two aggregate tensor hashes. The local registration CSV identifies MAT paths and units only; it has no file checksum column. |

Therefore the data-source **unit membership and expected public raw digests** are version-pinned to the same complete tier at both commits. The formal tensors' derivation from those raw digests is not established by the inspected evidence. The missing link is a hash-bound preprocessing receipt containing the input revision, per-unit raw SHA list (or its canonical list digest), preprocessing code/config hashes and deterministic command, and resulting BAT/RWA tensor hashes.

## Reproducible Read-Only Commands

Commands and checks executed on 2026-10-02:

```powershell
git ls-remote https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets.git HEAD refs/heads/master refs/heads/main
git -c protocol.version=2 clone --filter=blob:none --depth=1 --no-checkout https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets.git <temporary-metadata-clone>
git -C <temporary-metadata-clone> fetch --filter=blob:none origin 85ebba12f3ec132dc9e0ea8ae49012f57505ccf1
git -C <temporary-metadata-clone> ls-tree --long 85ebba12f3ec132dc9e0ea8ae49012f57505ccf1 MANIFEST.json BRPHM_RUL_complete/MANIFEST.json
git -C <temporary-metadata-clone> ls-tree --long cfe0a27a99fa776d6e464649576432c871992771 MANIFEST.json BRPHM_RUL_complete/MANIFEST.json
git -C <temporary-metadata-clone> rev-parse 85ebba12f3ec132dc9e0ea8ae49012f57505ccf1:BRPHM_RUL_complete
git -C <temporary-metadata-clone> rev-parse cfe0a27a99fa776d6e464649576432c871992771:BRPHM_RUL_complete
```

The metadata comparison used Python 3.12 standard-library `json`, `csv`, `hashlib`, and `subprocess`: `git show <commit>:BRPHM_RUL_complete/MANIFEST.json`, filter only SIM raw manifest rows, compare `Path(out_mat).name` / `unit_id` to each public record's basename and family, and compare public IDs against `split != "holdout"`. Only manifest metadata were parsed; no MAT, Parquet, held-out label, A1, or B1 payload was read.

## Confidence and Remaining Risk

**High confidence:** current/historical complete-tier tree identity; root/tier manifest hashes; exact equality of the 550 public SIM raw IDs with registered train+validation IDs; exact 98-unit holdout exclusion; path/family mapping.  
**High confidence that the linkage is absent from the checked receipts:** formal aggregate input hashes are recorded, but the inspected receipt/registration artifacts have no source raw SHA, source manifest hash, or dataset commit.  
**Remaining risk:** the source record set can be cited to either commit, but the existing formal tensor byte stream is not cryptographically tied to per-unit raw records by the available receipts. The earlier F2 manifest values are retained as dated historical snapshots; post-freeze rebinding now records the current manifest digest `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2` in the current ledger and consistency record.
