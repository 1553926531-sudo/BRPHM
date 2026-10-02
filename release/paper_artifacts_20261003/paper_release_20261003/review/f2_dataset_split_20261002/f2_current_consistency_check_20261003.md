# F2 Current Consistency Check — 2026-10-03

## Scope and status

This is a read-only reconciliation of the F2 dataset/split/provenance records. It does not read or modify sealed, A1, B1, canonical, production, or competition assets, and it does not modify `en/main.tex`. The check was run against the files currently on disk on 2026-10-03 (Asia/Shanghai). The split and train/validation tensor replay evidence remains substantively reproducible. The first check found stale hash bindings and one superseded prose statement; those bindings were corrected in the post-freeze reconciliation below.

**Status:** `RECONCILED__PUBLIC_METADATA_LIMITS_REMAIN`

## Finding 1 — stale hash bindings in the F2 ledger

- **Position:** `review/f2_evidence_ledger.json`, `artifacts.manifest`, `artifacts.tensor_replay_addendum_json`, and `artifacts.tensor_replay_addendum_markdown`.
- **Original/current text:** The ledger records `61842ba3d1ee89e7180a29449365bd0e2ab9734a89ed0c96f0939bb596cbcb4c`, `9128647da2c9fab7c20c55ca18ff1d07e44092a8e51f07df4c73919c32629e85`, and `96507e32172b19db9bc32d3552377918a61cc61ed7ddd1739c9b57a94247fc9c`.
- **Problem:** These values do not match the bytes currently delivered at the paths. A reviewer following the machine ledger would verify a different artifact version.
- **Current evidence:**

  | Path | Current SHA-256 | Bytes |
  |---|---|---:|
  | `f2_dataset_split_manifest.json` | `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2` | 11790 |
  | `f2_tensor_replay_addendum_20261002.json` | `c6c177ac93fad6cffd47244e3dfbdfd919f898a48b7113244be5e087e8131a1c` | 9570 |
  | `f2_tensor_replay_addendum_20261002.md` | `074bea858318d2572b77f660a56361357a7b536ccc3c626d57333b93096483b1` | 7711 |

- **Correction:** Replace only the three ledger fields with the current values after the paper/source freeze. Recompute the F2 ledger hash and every downstream manifest that embeds it.
- **Command:**

  ```powershell
  Get-FileHash review/f2_dataset_split_20261002/f2_dataset_split_manifest.json,
    review/f2_dataset_split_20261002/f2_tensor_replay_addendum_20261002.json,
    review/f2_dataset_split_20261002/f2_tensor_replay_addendum_20261002.md -Algorithm SHA256
  ```

- **Cross-check:** Python `hashlib.sha256` and PowerShell `Get-FileHash` agree for the current files. The stale values are also present in `review/f2_evidence_ledger.md` and must be updated together.
- **Confidence:** High.
- **Residual risk:** Any concurrent regeneration can change the bytes again; perform this replacement only after the shared review tree is frozen.
- **Status:** `RECONCILED__LEDGER_REBOUND`.

## Finding 2 — stale self-reference inside the machine manifest

- **Position:** `review/f2_dataset_split_20261002/f2_dataset_split_manifest.json:175`, field `processed_window_summary.deterministic_train_validation_replay.addendum_json_sha256`.
- **Original/current text:** The field is `9128647da2c9fab7c20c55ca18ff1d07e44092a8e51f07df4c73919c32629e85`.
- **Problem:** The field points to the old bytes of the replay addendum while the delivered addendum hashes to `c6c177ac...`.
- **Correction:** Set the field to `c6c177ac93fad6cffd47244e3dfbdfd919f898a48b7113244be5e087e8131a1c`, then recompute the manifest SHA-256 and update all records that cite the manifest. This is an intentional two-step binding: the addendum hash is fixed first, then the manifest hash is computed.
- **Evidence/source/date:** Current addendum bytes and manifest bytes; local hash commands above; 2026-10-03.
- **Cross-check:** The addendum JSON's semantic claims (275 train/validation Parquet reads per component, zero holdout reads, bitwise tensor equality, canonical tensor hashes) agree with the current replay Markdown and F2 ledger; only the embedded digest is stale.
- **Confidence:** High.
- **Residual risk:** Do not use a self-referential hash of the manifest itself; the field binds the external addendum only.
- **Status:** `RECONCILED__SELF_REFERENCE_UPDATED`.

## Finding 3 — superseded prose in the provenance memo

- **Position:** `review/f2_dataset_split_20261002/f2_modelscope_provenance_20261002.md`, item 2 under “Same-Day Replay Update”.
- **Original/current text:** “The existing F2 manifest records both the verified historical revision and the later current head; it does not prove that their complete-tier payload manifests are identical.”
- **Problem:** The sentence is stale relative to the later revision comparison and replay records. The checked evidence now contains the complete-tier tree OID `f0b07bea4a1d2eb9286b26f7c91f34b951391da3`, byte-identical complete-tier manifest SHA-256 `ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062`, and `complete_tier_payload_identical=true`. Leaving both statements in one memo makes the conclusion ambiguous.
- **Correction:** Preserve the old sentence only inside a dated “superseded at 2026-10-02 replay” block, or replace it with: “The subsequent revision comparison and replay addendum establish equality of the complete-tier Git subtree and tier manifest at the two inspected commits; root repository manifests still differ, so the paper pins one immutable commit and does not claim whole-repository identity.”
- **Evidence/source/date:** `f2_revision_binding_addendum_20261002.md`, `f2_tensor_replay_addendum_20261002.md`, `f2_dataset_split_manifest.json`; 2026-10-03.
- **Cross-check:** Both machine addenda and the source manuscript (`en/main.tex:45`) state the same boundary: complete tier equal, root manifests different.
- **Confidence:** High.
- **Residual risk:** The result is limited to the two inspected commits and the complete tier; it does not authenticate the historical July tensor-creation event or unrelated collection partitions.
- **Status:** `RECONCILED__PROSE_UPDATED`.

## Finding 4 — old manifest hash retained as historical evidence without a current pointer

- **Position:** `f2_evidence_ledger.md:129`, `f2_modelscope_provenance_20261002.md:23`, and `f2_revision_binding_addendum_20261002.md:53`.
- **Original/current text:** These sections mention `5ce4f9733dbf858df49e469545a0c8dcaa212e372a7b98bf20ada56c5b58f79d` or the earlier ledger value `7bf5e5b040ab09c7025de937950635ee210b44406b36dc4db15566a1760d9524`.
- **Problem:** The values describe earlier file states, but the prose does not consistently label them as historical snapshots. A reader can mistake either value for the current manifest digest.
- **Correction:** Keep the values only as an append-only audit trail with explicit labels (`historical snapshot`, date, and purpose), and point to the current digest `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2`. Do not overwrite historical hashes in a way that destroys the chronology.
- **Evidence/source/date:** Current `Get-FileHash` output; revision-binding addendum; 2026-10-03.
- **Cross-check:** The current JSON manifest parses successfully and its split summary matches the 648-row membership file; the historical hashes are not equal to current bytes.
- **Confidence:** High.
- **Residual risk:** Historical addenda remain intentionally non-current; downstream scripts must select the current field rather than regex-matching the first digest in a prose file.
- **Status:** `RECONCILED__HISTORICAL_LABELS_EXPLICIT`.

## Substantive F2 cross-checks

The following claims were rechecked without reading restricted payloads:

1. `unit_split_membership.csv` has 648 rows and SHA-256 `f07ac79a69986b407b3af0458201be993a2a0956d59ba7af24abd028a14a24d0`.
2. The split manifest reports 648 registered units, 388 train, 162 validation, 98 holdout, and exact 648/648 split reconstruction.
3. Current processed tensor hashes remain BAT `9e2a7f3dbf22e99b4685ff2751c94e96312d380032270771f7e29a51e30057ab` and RWA `9dcbd45d668cc03089ef628068d1247eb2100f64b70c3d5b4aba8ff262813595`.
4. The replay addendum reports 275 train/validation Parquet reads per component, zero holdout reads, bitwise equality of checked fields, and exact canonical tensor serialization after the documented normalization-path restoration.
5. The pinned ModelScope commit `85ebba12f3ec132dc9e0ea8ae49012f57505ccf1` and observed head `cfe0a27a99fa776d6e464649576432c871992771` share complete-tier tree OID `f0b07bea4a1d2eb9286b26f7c91f34b951391da3` and complete-tier manifest SHA-256 `ba3aae4d5de48d9b1e1fcd78de219230bbf26cf3abb84f3d147a462f0bfe3062`; their root manifests differ.
6. The live ModelScope API license observation remains date-qualified `CC-BY-4.0` (2026-10-02) and neither inspected commit contains a versioned license file. This is metadata evidence, not a commit-authenticated license instrument.

## Post-reconciliation result

The pre-binding manifest snapshot was `09105491c34161fd3be9155478406950ce60d8f9f0c0f29491de8914f493fe97`; it is retained only as a historical byte snapshot. The current manifest is `3de92e0266a2555823dde6b04699db45d6f20f72414013c9eb153246f837d2e2`, and its embedded addendum digest equals the current replay JSON hash. The F2 JSON ledger was rebound to the current artifact hashes and historical values were retained in an explicit historical field.

## F2 disposition

The data/split/label contract and current train/validation replay are substantively evidenced, and the stale ledger pointers, manifest self-reference, and superseded provenance sentence have been reconciled in the post-freeze records. Public-metadata limits remain explicit: no DOI is claimed, the observed `CC-BY-4.0` value is live ModelScope metadata rather than a commit-authenticated license file, no license is assigned to unrelated collection partitions, and no historical canonical-creation event is inferred from the replay. The raw-to-processed tensor byte lineage remains an identified residual risk because the inspected receipts lack a per-unit raw-hash/preprocessing binding.
