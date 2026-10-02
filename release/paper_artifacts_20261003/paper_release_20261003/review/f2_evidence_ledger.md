# F2 Evidence Ledger: Dataset, Split, and Label Contract

**Audit date:** 2026-10-02 (Asia/Singapore)  
**Finding:** F2 is **current-derivation and manuscript-patch closed for the registered project split contract**. The remaining publication items are explicitly bounded: commit-level license authentication, DOI status, author declarations, and a paper-specific immutable release.  
**Scope boundary:** The initial manifest/split audit used metadata and split CSVs only. The later replay opened only train/validation interim Parquets and train/validation tensor values for exact derivation checks; it did not read holdout telemetry/labels, sealed/A1/B1 assets, or rerun an evaluation.

## Finding

The manuscript's sentence “previously registered BAT and RWA tensors from the ModelScope-backed project data root” is not reproducible by itself. The project now has a machine-readable unit manifest and an independently checked split reconstruction. The paper still needs to publish the manifest contract, exact dataset version, license/source-data notices, and the distinction between the registered three-orbit experiment and the separate LEO600 F1 final partition.

## Location and original text

- **Manuscript:** `work/paper/en/main.tex:30`
- **Original:** “The experiment consumes the previously registered BAT and RWA tensors from the ModelScope-backed project data root. BAT contains 13 channels and RWA contains 13 channels in the temporal input used by the final receipt; windows have length 30. Three orbit identifiers are parsed from unit identifiers: LEO500, LEO550, and LEO700. Source and validation units are disjoint by construction.”
- **Related manuscript text:** `work/paper/en/main.tex:133` repeats an undocumented ModelScope-backed data dependency.

## Problem

1. No dataset version, immutable commit, DOI, license, access date, or machine-readable URL/hash is attached to the sentence.
2. Unit/window counts, per-orbit counts, split membership, stride, overlap, missing-value handling, label construction, and sensor semantics are absent.
3. The stated BAT input dimension is contradicted by the final source receipt: BAT input shape is `[3681, 60, 4]`, while RWA is `[7051, 30, 13]`. The four BAT channels are listed in the target preprocessing card.
4. The public ModelScope repository has a current head different from the historical verification commit. A paper must bind itself to one immutable version instead of silently mixing them.

## Evidence and hashes

| Artifact | Result | SHA-256 / value |
|---|---|---|
| `sim_manifest_remote.csv` (Rack `sim/logs/manifest.csv` copy) | 648 registered units: 324 BAT + 324 RWA; 216 per orbit | `93710e01e18684e6296d52c4ae8ea98491841440db8f2b9798e0139901fccbc8` |
| `f1_holdout_manifest.csv` | 98 units: 49 per product line | `ee1e2f760e...` (full hash in F2 JSON) |
| `unit_split_membership.csv` | 648 rows, one row per unit | `f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0` |
| `f2_dataset_split_manifest.json` | Contract and summary; replay status updated 2026-10-02 | `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2` |
| Rack `bat_target_split.csv` | 324 rows, 49 holdout / 194 train / 81 val | `3b6ad1bbb5a8df5da9ab35dd044e69576bae9bf9b08867b0d109c252314e5e6` |
| Rack `rwa_target_split.csv` | 324 rows, 49 holdout / 194 train / 81 val | `969590b62f250ea7ecb632520e4ad8da312f8f4fbe381b1a198d692d175efa16` |
| Promoted source receipt | BAT `[3681,60,4]`, RWA `[7051,30,13]`; `rmax` 150 and 0.2 | `b99ed8...` (full hash in F1/evidence bundle) |
| ModelScope current `master` | Read-only `git ls-remote` on 2026-10-02 | `cfe0a27a99fa776d6e464649576432c871992771` |
| ModelScope historical independent verification | `PUBLIC_HTTP=200`, complete 67,539 files / 107,243,597,734 bytes on 2026-08-31 | commit `85ebba12f3ec132dc9e0ea8ae49012f57505ccf1`; root manifest `0f8d21b05eb0168ad36a070e1beb22421c962fcbbb46f65ff6cc6bba9bc3d697` |

Full hashes and all 648 membership rows are in [f2_dataset_split_manifest.json](/C:/Users/Administrator/Documents/Codex/2026-09-26/new-chat/work/paper/review/f2_dataset_split_20261002/f2_dataset_split_manifest.json) and [unit_split_membership.csv](/C:/Users/Administrator/Documents/Codex/2026-09-26/new-chat/work/paper/review/f2_dataset_split_20261002/unit_split_membership.csv).

## Split reconstruction

The Rack source is `first@10.123.100.40:/mnt/data/BRPHM/rul-space`. The holdout contract is read from `configs/holdout.yaml`: `frac=0.15`, nearest rounding, seed `20260715`, DOE-cell stratification, and at most one unit per cell. The target train/validation contract is read from `src/datasets/preprocess.py::assign_splits_cell_tail` and the two target preprocessing cards:

```text
holdout membership first;
for each (product_line, doe_cell) among non-holdout units:
    key = sha256(f"0:{unit_id}")
    order ascending by key
    n_val = clamp(floor(n * 0.2), 1, n - 1), with n=1 => 0
    assign the final n_val units to validation; assign the rest to train
```

The local reconstruction matches both Rack split CSVs by `unit_id`, `split`, and `strata`: **648/648 rows match, 0 differences**.

## Label, window, and missing-value contract

- Raw main telemetry is documented as 0.1 Hz on a 10 s grid; event detail is 1 Hz in bounded windows.
- BAT processed input is 4 channels, `L=60`, stride `5`, `rmax=150` cycles, `drop_negative`, and `impute_mean`; `bat.ir_proxy_ohm` is explicitly absent-allowed and has identity statistics.
- RWA processed input is 13 channels, `L=30`, stride `1`, `bin_s=574.0` seconds, `rmax=0.2` days, `drop_negative`, and `impute_mean`; singleton-bin standard deviations are imputed from training statistics.
- Raw labels are `rul_days = Tf - t`; `fail` is zero before failure and monotone one after failure; right-censored units have no failure time, NaN raw RUL, and `fail=0`.
- Normalization statistics are fit on the train split and reused for validation/holdout.
- The F1 LEO600 partition is a separate untouched final test with its own partition manifest and is not assigned to the 648-unit train/validation membership.

## Commands and results

1. `ssh -i C:/Users/Administrator/Documents/id_ed25519 first@10.123.100.40 '... sed/grep configs/holdout.yaml src/datasets/preprocess.py configs/preprocess/{bat_target,rwa_target}.yaml docs/data_dictionary.md'`  → rules and label/window contract recorded.
2. `git ls-remote https://www.modelscope.cn/datasets/modelscope1553926531/BRPHM-datasets.git HEAD refs/heads/master refs/heads/main` → current `master/HEAD=cfe0a27a99fa776d6e464649576432c871992771`.
3. `python work/paper/repro/build_f2_dataset_split_manifest.py --root .` → 648 membership rows and the F2 JSON.
4. `scp ... data/processed/splits/{bat_target,rwa_target}_split.csv ...` followed by a unit-level PowerShell comparison → 648/648 matches, zero split or strata differences.

## Cross-validation

- **Primary source:** Rack configuration/code and manifests.
- **Independent computational check:** local pure-Python reconstruction from the copied raw manifest and holdout manifest.
- **Independent artifact check:** Rack's persisted BAT/RWA split CSVs.
- **Public-data check:** ModelScope Git remote head and the historical remote verification JSON in the prior release evidence tree.
- **Confidence:** high for the 648-unit split contract and the receipt input dimensions; medium for the public repository's license because the paper/project does not yet bind a single license statement for the assembled complete tier.

## Required manuscript modification

Replace the current one-sentence data description with a dataset table and a pointer to the hash-linked manifest. Correct BAT from 13 channels to 4 channels for the receipt used in this study, and state the exact ModelScope commit selected for publication. Add access date, license/source-data attribution, unit/window counts, split algorithm, label and missing-value contract, and the separate LEO600 final-test declaration.

## Remaining risk and status

- **Remaining risk:** the target venue is still unspecified; venue-specific data/code supplement and license wording cannot be checked yet. The current ModelScope head moved after the historical verified commit, so the manuscript must select and freeze one version before release.
- **Status:** `CURRENT_DERIVATION_AND_MANUSCRIPT_PATCH_CLOSED_PUBLIC_RELEASE_LICENSE_DOI_LIMITS_EXPLICIT`.

## Current-Turn Revalidation (2026-10-02)

> **Historical snapshot marker.** This subsection records the state observed at the
> 2026-10-02 revalidation boundary, before the subsequent tensor replay/addendum
> and manuscript reconciliation. Statements below that say the manuscript was
> unedited or that version binding was unresolved describe that earlier snapshot;
> they are not the status of the current artifact tree.

### Finding record

- **Position:** `main.tex:30` and `main.tex:133`. The current `main.tex` SHA-256 is `4dc54e2a8ccd3aa087344ae52737b5f9f1bc5bb97faa9926c1d0aa6cf5d33621` (the pre-reconciliation source was `d99e2023bd8f665e040bcb66b2c107b35076f0f7b514ec04aadf6873705f7dc9`).
- **Original text:** “The experiment consumes the previously registered BAT and RWA tensors from the ModelScope-backed project data root. BAT contains 13 channels and RWA contains 13 channels in the temporal input used by the final receipt; windows have length 30.”
- **Problem:** the sentence misstates BAT dimensions and omits the exact repository revision, the registered unit/window counts, public DOI status, commit-specific license status, and the distinction between registered holdout units and units represented in the train/validation tensors.
- **Evidence-backed correction (at that historical boundary):** BAT is `[N,60,4]` with stride 5; RWA is `[N,30,13]` with stride 1. The machine-readable manifest then reported 648 registered units (324 per component; 216 per orbit), 388 train, 162 validation, and 98 holdout units (49 per component). It also recorded the verified processed-window counts and corrected LEO600 cross-reference fields. The manuscript had not yet been edited at that time; the current source/addendum records the later reconciliation.
- **ModelScope license and DOI:** the official live ModelScope dataset-detail API declared `CC-BY-4.0` on 2026-10-02. No versioned license file was found in either inspected commit, and the README's publisher authorization sentence is not a license instrument. No DOI was disclosed by the API/README; DataCite had zero exact-name records and Crossref had no exact-title match. Record the observed platform metadata with its date and explicitly state the commit-level license limitation; do not assign this license to unrelated collection partitions.
- **Version binding (at that historical boundary):** unresolved. The historical verified commit was `85ebba12f3ec132dc9e0ea8ae49012f57505ccf1`; the current head observed on 2026-10-02 was `cfe0a27a99fa776d6e464649576432c871992771`. The input hashes did not yet prove which complete-tier release the paper consumed. The two README hashes differed, so commit payload equivalence could not be assumed. The later replay/addendum and current manifest must be read for the post-boundary status.

### Processed windows and split membership

The audit loaded `data/processed/{bat,rwa}_target.pt` with `map_location='meta'` and read only `meta.index`; no feature/label tensor values or `data/holdout` files were inspected. Every represented `(unit_id, split)` matched the hashed target split CSV. No payload unit was assigned to `holdout`; no represented unit crossed splits.

| Component | Registered units train/val/holdout | Represented train/val units | Windows train/val | Windows by orbit (train / val) | Train/val units with zero usable windows |
|---|---|---|---|---|---:|
| BAT | 194 / 81 / 49 | 146 / 57 | 2,364 / 1,317 = 3,681 | LEO500 954 / 423; LEO550 803 / 375; LEO700 607 / 519 | 72 |
| RWA | 194 / 81 / 49 | 169 / 71 | 4,884 / 2,167 = 7,051 | LEO500 1,610 / 742; LEO550 1,664 / 660; LEO700 1,610 / 765 | 35 |

The older generated `docs/rwa_target_stats.md` (SHA-256 `6e143578e78c148133f8f907aba0025a62b63df07b445b6978f52c8336794315`) says “holdout units ... 0.” This wording is ambiguous and conflicts with the hashed 324-row RWA split, which contains 49 holdout units. The processed tensor index independently confirms 240 represented RWA units (169 train, 71 validation), zero holdout, and 35 non-holdout units with no windows. Correct publication wording is therefore **49 registered RWA holdout units, zero holdout units in the processed tensor**. Do not copy the old `0` as the registered holdout count.

### Evidence, commands, and cross-checks

| Artifact/source | Date and result | SHA-256 |
|---|---|---|
| `unit_split_membership.csv` | 648 rows; one unit-level membership per unit | `f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0` |
| `f2_dataset_split_manifest.json` | Valid JSON; 648 registered units, 3,681 BAT / 7,051 RWA windows, non-null LEO600 cross-reference, and current tensor replay status | `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2` |
| Rack `bat_target.pt` / `rwa_target.pt` | Input tensors hash-bind to the frozen candidate receipt | `9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` / `9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595` |
| Rack `bat_target_split.csv` / `rwa_target_split.csv` | Each is 324 rows; train 194, validation 81, holdout 49 | `3b6ad1bbb5a8df5da9ab35dd044e69576bae9bf9b08867b0d109c252314e5e6` / `969590b62f250ea7ecb632520e4ad8da312f8f4fbe381b1a198d692d175efa16` |
| ModelScope current detail API | HTTP 200; `License=CC-BY-4.0`; modified `2026-10-02T13:38:33Z`; no DOI fields | `61f2c24187366406f4b26df31b52434d90e9afaaffa9b7ac41ad4a50f16c1902` |
| `f2_modelscope_provenance_20261002.md` | Primary-source research memo; access date 2026-10-02 | `2f7f7026e503845d22704eb72bc4a596becd96d7b2f8663e74bc1be9fd096f3e` |

Audit commands on 2026-10-02:

```powershell
Get-FileHash -LiteralPath <artifact> -Algorithm SHA256
ssh -i C:\Users\Administrator\Documents\id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=yes first@10.123.100.40 sha256sum -- <tensor and split paths>
ssh -i C:\Users\Administrator\Documents\id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=yes first@10.123.100.40 /mnt/data/BRPHM/rul-space/.venv-fm/bin/python -
```

The Python audit passed with `membership_mismatch=0`, `unknown=0`, `multi_split_units=0`, `payload_holdout_units=0`; train/validation unit shortfalls were exactly 72 BAT and 35 RWA zero-window units. Independent cross-checks were: (1) 648-row local membership reconstruction versus both persisted Rack split CSVs; (2) metadata-only tensor index versus those split CSVs; (3) tensor SHA-256 values versus the frozen candidate receipt; (4) the historical and current ModelScope commit trees versus the live ModelScope API and README/provenance sources. The manifest JSON parsed with `ConvertFrom-Json -Depth 100`; its SHA-256 was recomputed after the last manifest edit as `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2`, and the membership CSV recomputed as `f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0`. Confidence is **high** for split membership, window totals and current platform metadata; **medium** for applying the live license metadata to any one historical commit; **unresolved** for exact ModelScope payload revision binding.

### Remaining work and status

F2 was **partially evidenced, not publication-closed** at the time of this audit section. The append-only follow-up below records the subsequent train/validation-only deterministic replay and supersedes the earlier unresolved raw-to-processed link for current reproducibility.

## Superseding Replay Evidence (2026-10-02)

The current processed tensor derivation is now verified from the hash-matched ModelScope interim files using Rack's current preprocessing code and the checked-in target configs. See [f2_tensor_replay_addendum_20261002.md](f2_dataset_split_20261002/f2_tensor_replay_addendum_20261002.md) and its machine-readable companion. The reader trace recorded exactly 275 train/validation Parquet reads per component; both read sets equaled the frozen train/validation unit sets, with zero holdout Parquet reads. `x`, `y_rul`, `y_hi`, and `mask.y_hi` were bitwise equal to the canonical tensors; after restoring only the canonical `meta.norm_stats` path before serialization, replay SHA-256 exactly matched BAT `9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` and RWA `9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595`.

The two inspected ModelScope commits have different root manifests, but the complete-tier tree and manifest are identical. The current byte-level derivation is therefore reproducible from the same complete-tier payload. The historic July 2026 creation event remains unreceipted: the replay cannot recover the original operator, timestamp, or historical code/config state. The live API's CC-BY-4.0 declaration is date-qualified and lacks a versioned license file in either inspected commit; no DOI was disclosed by the checked API/README or exact-name DataCite/Crossref queries. Venue/article type and permanent artifact publication remain pending; the current manuscript patch is present in `en/main.tex` and its local PDF rebuild is recorded in `review/pdf_build_verification_20261003.json`.

**Current F2 status:** current split and tensor derivation evidence is closed; manuscript publication patch and source metadata declarations remain pending. The machine ledger is `f2_evidence_ledger.json`; the machine manifest is `f2_dataset_split_20261002/f2_dataset_split_manifest.json`.




## Post-freeze hash reconciliation (2026-10-03)

The machine ledger and manifest were reconciled after a read-only consistency check. The replay addendum JSON remains `c6c177ac93fad6cffd47244e3dfbdfd919f898a48b7113244be5e087e8131a1c`; the replay addendum Markdown remains `074bea858318d2572b77f660a56361357a7b536ccc3c626d57333b93096483b1`; the updated split manifest is `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2`; and the updated F2 JSON ledger is `7d99a6fd78885c89791a6493d36c767ce3d50b90ea691701a76eaaf056fa287a`. The previous ledger bindings (`61842ba3...`, `9128647d...`, and `96507e32...`) are retained in the JSON ledger's `historical_hash_bindings_20261002_pre_reconciliation` field and are historical only. The manifest's embedded addendum digest now equals the replay JSON hash. The current consistency report JSON is `e5299342a2c39451926c2488d673cad68189d62e530cbfda191b45dfed0d104d`, with Markdown companion `746429fb629cc56bb97157184063988b7f947701ef6b2331e5fc2c65a6a43598`.

The same consistency check identified and records one superseded sentence in the ModelScope provenance memo that said complete-tier equality had not been proved. The subsequent revision comparison and replay prove equality of the complete-tier subtree/manifest at the two inspected commits while the root repository manifests differ; the paper therefore pins one immutable commit and does not claim whole-repository identity.

**Current status:** split membership, label/window contract, train/validation replay, manuscript patch, and artifact hash bindings are closed. DOI, commit-authenticated license text, historical canonical-creation receipt, author declarations, and paper-specific public release remain explicitly pending.
