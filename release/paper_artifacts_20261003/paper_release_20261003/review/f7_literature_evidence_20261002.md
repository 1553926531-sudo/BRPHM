# F7 Literature Evidence Ledger

**Finding:** F7 literature-source verification.  
**Manuscript location:** Section II (Related Work), `work/paper/en/main.tex`; the section currently contains five references dated 1964, 2010, 2018, and 2019. The Introduction has no numbered contribution list.  
**Review report location:** F7 in `C:/Users/Administrator/Documents/Codex/2026-10-01/ni-d/outputs/IEEE_Review_Report_English.md`.  
**Access date:** 2026-10-02 (UTC).  
**Scope boundary:** Bibliographic and abstract-level verification only. No manuscript edits, full-text claims, personal-profile searches, affiliations, student records, or admissions information were collected.

## F7 Finding

**Original problem:** The present Related Work is too narrow and dated to establish the position of an RUL cross-orbit/domain-shift study. It contains no recent direct RUL/domain-adaptation work, no recent IEEE work, and the manuscript provides no explicit contribution bullets or evidence-linked comparison against relevant methods.

**Action from this audit:** The four DOI candidates in the IEEE review report all resolve to real, directly relevant RUL/domain-adaptation papers. Three additional direct original studies from 2021–2023 were identified and cross-checked. These records support strengthening the literature review; they do not, by themselves, establish novelty, prove that any method is a fair benchmark for this dataset, or support a claim of superiority. Their target-data assumptions differ and must be compared explicitly before choosing performance baselines.

**Manuscript change and timing:** At the initial 2026-10-02 literature capture, no manuscript edit had yet been made. The subsequent reconciled source added the verified recent references and contribution bullets described below; this timestamped ledger remains the evidence record for that later revision.

## Retrieval and Integrity Method

For each DOI, the following APIs were queried over HTTPS:

```text
GET https://api.crossref.org/works/{doi}
GET https://api.openalex.org/works/https://doi.org/{doi}
GET https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url
GET https://doi.org/{doi}                 # redirect resolution to publisher landing page
GET https://ieeexplore.ieee.org/document/{IEEE document id}/
```

The following command shape was used for API retrieval and response hashing (hashes below are SHA-256 of the raw HTTP response body):

```python
import hashlib, requests
r = requests.get(url, timeout=20, headers={"User-Agent": "F7 literature audit/1.0"})
print(r.status_code, r.url, hashlib.sha256(r.content).hexdigest())
```

The DOI resolver returned HTTP 302 with an IEEE Xplore document URL for each of the seven IEEE records below. Direct IEEE Xplore document-page GETs returned HTTP 202 with a zero-byte body for all seven (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). This is recorded as a page-content retrieval limitation, not as evidence that the publication does not exist. An IEEE REST metadata probe returned HTTP 418 with an anti-automation page; the public IEEE API returned HTTP 403 `Developer Inactive`. Metadata and abstracts were therefore cross-checked against three independently maintained bibliographic services. Crossref is the publisher-deposited registration record; OpenAlex and Semantic Scholar provide separately indexed metadata/abstracts. No assertion is made that these API records replace full-text review.

All Crossref, OpenAlex, and Semantic Scholar requests returned HTTP 200 for the seven items below. API response hashes bind the exact responses observed on the access date. DOI-resolver response hashes bind the 302 redirect responses. Exact endpoint URLs are included in the source rows.

## Four DOI Candidates From the Review Report

The metadata fields below use Crossref for author/title/issue citation details, checked against OpenAlex and Semantic Scholar. Year disagreements are called out rather than silently normalized. Abstract quotations are short verbatim fragments returned by the named abstract-indexing source; ellipses indicate editorial omission.

### F7-A1 — IEEE Access 2024

- **Exact title:** “Supervised Domain Adaptation for Remaining Useful Life Prediction Based on AdaBoost With Long Short-Term Memory”
- **Authors:** Seunghwan Seo; Jungwoo Hwang; Moonkyung Chung.
- **Year / venue / locator:** 2024; *IEEE Access*, vol. 12, pp. 96757–96768.
- **DOI / publisher page:** [10.1109/ACCESS.2024.3426909](https://doi.org/10.1109/ACCESS.2024.3426909); [IEEE Xplore document 10595096](https://ieeexplore.ieee.org/document/10595096/).
- **Relevance evidence:** Semantic Scholar abstract says the work addresses “domain adaptation (DA) problems in remaining useful life prediction” and “proposes a supervised DA method based on AdaBoost with long short-term memory (LSTM).” This is a direct RUL/domain-adaptation method, not a general time-series citation.
- **Independent metadata cross-check:** Crossref and OpenAlex agree on exact title, ordered full author names, year 2024, and IEEE Access. Semantic Scholar agrees on title, venue, DOI and author order (first author abbreviated as “S. Seo”). No material bibliographic conflict found.
- **Sources, retrieval result, and SHA-256:**
  - Crossref, [DOI record](https://api.crossref.org/works/10.1109/access.2024.3426909), HTTP 200, SHA-256 `edd7aef18355328a3203f75d75b6d01ce2deb1dffead11c5de67a8d6823bb836`.
  - OpenAlex, [DOI record](https://api.openalex.org/works/https://doi.org/10.1109/access.2024.3426909), HTTP 200, SHA-256 `031822c681ae0e5768e0d26a484be592fa6cdf8d8cc8d98d8509d43f5fb0b79f`.
  - Semantic Scholar, [DOI record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/ACCESS.2024.3426909?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), HTTP 200, SHA-256 `128875d01c54e85ebf0388c9dc5a60c57f12af7921d064088719c33856c02a23`.
  - DOI resolver, HTTP 302 to the IEEE Xplore URL above, redirect-body SHA-256 `c8fff5aa4214ea2c5ddcc4dd453610e5a54ef1173b6b03efdee90112e1cf8384`; Xplore page GET HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including in the Related Work as a recent supervised RUL domain-adaptation method. Do not imply direct comparability without matching its target-label/data-access regime to this paper's deployment claim.
- **Confidence / residual risk:** High for existence, identity, citation metadata, and topical relevance; medium for whether it is a fair experimental baseline until its complete information regime and benchmark setup are compared from the article itself.

### F7-A2 — IEEE Internet of Things Journal, online/issue-year discrepancy

- **Exact title (Crossref/OpenAlex):** “Uncertainty Estimation Pseudo-Labels Guided Source-Free Domain Adaptation for Cross-Domain Remaining Useful Life Prediction in IIoT.” Semantic Scholar hyphenates “Pseudo-Label-Guided”; title substance otherwise matches.
- **Authors:** Zhuohang Chen; Jinglong Chen; Tongyang Pan; Jingsong Xie. Semantic Scholar uses “Zhuo Chen,” “Tong-Yang Pan,” and “Jing-Song Xie.”
- **Year / venue / locator:** Crossref and OpenAlex record 2024; Semantic Scholar records publication year 2025. Crossref has not supplied volume/issue/pages (`1-1` placeholder). **Do not finalize the bibliography year or issue locator from this ledger alone; verify the current IEEE issue record before camera-ready citation.**
- **DOI / publisher page:** [10.1109/JIOT.2024.3464854](https://doi.org/10.1109/JIOT.2024.3464854); [IEEE Xplore document 10684608](https://ieeexplore.ieee.org/document/10684608/).
- **Relevance evidence:** OpenAlex abstract begins: “Domain adaptation (DA) enhances the scalability of remaining useful life (RUL) prediction technologies…” and says traditional DA approaches require simultaneous access to source and target data. The title and abstract directly concern cross-domain RUL and source-free adaptation.
- **Independent metadata cross-check:** Crossref and OpenAlex agree on exact title, author order and IEEE Internet of Things Journal. Semantic Scholar matches the DOI and venue but reports year 2025 and minor title/author-name normalization differences. The date conflict remains visible and unresolved against Xplore because the page body was blocked by HTTP 202.
- **Sources, retrieval result, and SHA-256:**
  - Crossref, [DOI record](https://api.crossref.org/works/10.1109/jiot.2024.3464854), HTTP 200, SHA-256 `516e89a79ef75d7745c0b79943cd8163d4efa4f0a2eae65fd24318e26bc1b428`.
  - OpenAlex, [DOI record](https://api.openalex.org/works/https://doi.org/10.1109/jiot.2024.3464854), HTTP 200, SHA-256 `2bb5ad125e27a73ff5cfc67f836c36df9ae757e7cdfa6f99a39f1f7586408931`.
  - Semantic Scholar, [DOI record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/jiot.2024.3464854?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), HTTP 200, SHA-256 `446763309ed1de94eda8062f9c704ddf26ad0febe21a4beb06ef91c6f6c437c5`.
  - DOI resolver, HTTP 302 to the IEEE Xplore URL above, redirect-body SHA-256 `53db554bd2c5241ff5f71c219646350dcae9514a2afa1edc07579bafe50308dc`; Xplore page GET HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as direct source-free/cross-domain RUL literature, with its label-free target-data assumption stated. Do not present it as evidence for a strictly inductive source-only deployment unless the manuscript defines and justifies that comparison.
- **Confidence / residual risk:** High for paper identity and relevance; medium for the exact publication year and final issue citation because Crossref/OpenAlex and Semantic Scholar disagree and the publisher page content did not load.

### F7-A3 — IEEE/ASME Transactions on Mechatronics 2024

- **Exact title:** “Partial Domain Adaptation in Remaining Useful Life Prediction With Incomplete Target Data.”
- **Authors:** Xiang Li; Wei Zhang; Xu Li; Hongshen Hao. OpenAlex displays the second author as “Zhang We”; Crossref and Semantic Scholar give “Wei Zhang.”
- **Year / venue / locator:** 2024; *IEEE/ASME Transactions on Mechatronics*, vol. 29, no. 3, pp. 1903–1913. OpenAlex reports 2023, while Crossref and Semantic Scholar report the 2024 issue/publication year. Use 2024 for issue citation; retain the discrepancy in provenance.
- **DOI / publisher page:** [10.1109/TMECH.2023.3325538](https://doi.org/10.1109/TMECH.2023.3325538); [IEEE Xplore document 10303731](https://ieeexplore.ieee.org/document/10303731/).
- **Relevance evidence:** Semantic Scholar abstract states that current algorithms assume “training and testing entities are operating under identical condition,” then frames this as unrealistic for real PHM applications; the title explicitly proposes partial DA for RUL with incomplete target data.
- **Independent metadata cross-check:** Crossref and Semantic Scholar match on title, author list after name normalization, venue, DOI, and 2024 publication. OpenAlex matches title/DOI/venue/authorship set but records 2023 and reverses the second author's name tokens. Final volume, issue, and pages are present in Crossref.
- **Sources, retrieval result, and SHA-256:**
  - Crossref, [DOI record](https://api.crossref.org/works/10.1109/tmech.2023.3325538), HTTP 200, SHA-256 `d66d15cafa1d333b34921469f659cedb884dfe9c02a0b386c6ec5c061f191e8c`.
  - OpenAlex, [DOI record](https://api.openalex.org/works/https://doi.org/10.1109/tmech.2023.3325538), HTTP 200, SHA-256 `fe4c760cd56e6f85fc4dfa1455146ccdd6159385d2db93753d22f34421b53563`.
  - Semantic Scholar, [DOI record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tmech.2023.3325538?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), HTTP 200, SHA-256 `440f61bb2e58d9340449e11a793ac5fa406321d99a69aef005ce7628122b7731`.
  - DOI resolver, HTTP 302 to the IEEE Xplore URL above, redirect-body SHA-256 `43449c0f7e1223061d3a6c0d9c1ac7f4192ccff9b12d29f65d6a54b4a71c7892`; Xplore page GET HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as direct RUL partial-domain-adaptation work. Its explicit incomplete-target-data setting is relevant context, but that target-data access must be distinguished from this manuscript's source-only selection claim.
- **Confidence / residual risk:** High for identity, 2024 issue citation, and relevance; moderate for author-name rendering due OpenAlex token reversal. No full-text comparison performed.

### F7-A4 — IEEE Transactions on Instrumentation and Measurement 2022

- **Exact title:** “Weighted Adversarial Domain Adaptation for Machine Remaining Useful Life Prediction.”
- **Authors:** Kangkai Wu; Jingjing Li; Lin Zuo; Ke Lu; Heng Tao Shen. Semantic Scholar abbreviates the last author as “H. Shen”; OpenAlex has a corrupted display string for Ke Lu, while Crossref gives full names.
- **Year / venue / locator:** 2022; *IEEE Transactions on Instrumentation and Measurement*, vol. 71, pp. 1–11.
- **DOI / publisher page:** [10.1109/TIM.2022.3212525](https://doi.org/10.1109/TIM.2022.3212525); [IEEE Xplore document 9913497](https://ieeexplore.ieee.org/document/9913497/).
- **Relevance evidence:** Semantic Scholar abstract describes RUL prediction and says methods often assume source and target data have similar distributions, whereas real-world source/target domains differ. The title identifies a weighted adversarial DA method for machine RUL.
- **Independent metadata cross-check:** Crossref and Semantic Scholar agree on title, DOI, 2022, venue, and authors (with initials/hyphenation differences); OpenAlex agrees on title, DOI, year, venue, and author sequence, although one name is character-corrupted in its response.
- **Sources, retrieval result, and SHA-256:**
  - Crossref, [DOI record](https://api.crossref.org/works/10.1109/tim.2022.3212525), HTTP 200, SHA-256 `819e162a068a7f501109b1b455a1bca46d621eef0c711ae0fff07cd088b78abc`.
  - OpenAlex, [DOI record](https://api.openalex.org/works/https://doi.org/10.1109/tim.2022.3212525), HTTP 200, SHA-256 `cd54d09d6cbfdc48d4fb9c8d69e667d77df5838ceb243855c56a5790d39241fa`.
  - Semantic Scholar, [DOI record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tim.2022.3212525?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), HTTP 200, SHA-256 `7fe87ce7c7405e547bc2035dfec9297f757bf7aff7746946d3605197d42bf86e`.
  - DOI resolver, HTTP 302 to the IEEE Xplore URL above, redirect-body SHA-256 `5a7eddd8fba6a766b2e296b00652c8a3a9d938d09fdc5ed4e0a57bbf35fa1e4d`; Xplore page GET HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as direct adversarial DA for RUL literature. It is a method-family reference, not an automatic baseline; target-data assumptions and benchmark protocol must be checked before making performance comparisons.
- **Confidence / residual risk:** High for identity, issue citation, and topic; medium-high for exact last-author display (use Crossref full form); no full-text comparison performed.

## Three Additional Direct Original Studies (2020–2026 Search Window)

These are additional to the four DOI candidates above. They were found through the OpenAlex query `search="remaining useful life domain adaptation"`, filtered to journal articles published 2020–2026; each was then independently resolved by DOI and checked through Crossref, OpenAlex, and Semantic Scholar. The query response SHA-256 was `d88fed7c599b9de7c14163bc3403c001b35fc33e3e60bd777ae25e47a5bc8be1` at `https://api.openalex.org/works?search=remaining+useful+life+domain+adaptation&filter=from_publication_date%3A2020-01-01%2Cto_publication_date%3A2026-12-31%2Ctype%3Aarticle&per-page=25&select=id%2Cdoi%2Ctitle%2Cpublication_year%2Cauthorships%2Cprimary_location%2Cabstract_inverted_index`. Search results were screened for direct RUL/domain adaptation in title/abstract, then checked individually; DOI year was not treated as publication year.

### F7-B1 — IEEE Transactions on Industrial Informatics 2021

- **Exact title:** “Contrastive Adversarial Domain Adaptation for Machine Remaining Useful Life Prediction.”
- **Authors:** Mohamed Ragab; Zhenghua Chen; Min Wu; Chuan-Sheng Foo; Chee Keong Kwoh; Ruqiang Yan; Xiaoli Li. Crossref uses “Chuan Sheng Foo”; Semantic Scholar varies hyphenation/initial forms.
- **Year / venue / locator:** 2021; *IEEE Transactions on Industrial Informatics*, vol. 17, no. 8, pp. 5239–5249. Crossref and Semantic Scholar indicate the 2021 issue; OpenAlex reports 2020, so record that as an online-first/indexing-year discrepancy, not the volume year.
- **DOI / publisher page:** [10.1109/TII.2020.3032690](https://doi.org/10.1109/TII.2020.3032690); [IEEE Xplore document 9234721](https://ieeexplore.ieee.org/document/9234721/).
- **Relevance evidence:** OpenAlex/Semantic Scholar abstract says RUL methods “usually assume that the training and testing data are collected from the same condition”; title identifies contrastive adversarial DA for machine RUL.
- **Independent metadata cross-check:** Crossref and Semantic Scholar agree on the full issue citation, title and author order; OpenAlex agrees on title/venue/DOI/author set but reports year 2020. Use the Crossref volume/issue/year citation and disclose the difference if discussing online availability.
- **Sources and SHA-256:** Crossref [record](https://api.crossref.org/works/10.1109/tii.2020.3032690), `f69493b6726d4aee1275af9881030f54f9a41459695a053c8d07a987f17d0af3`; OpenAlex [record](https://api.openalex.org/works/https://doi.org/10.1109/tii.2020.3032690), `1637782d8a85cde0bce1a6252d3f94c93a45e55779ec5d77aa7320cac221ba2d`; Semantic Scholar [record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tii.2020.3032690?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), `d2f1738d8e81503ba7727249866c0afded917633562c82364841dd490b6bf104`. All HTTP 200. DOI resolver HTTP 302 body SHA-256 `27da995cd5cec4f9e381497532ca259c9d352a7895af601932cf44e73c11f055` to the publisher page above; page HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as a core recent RUL cross-domain method. It is a plausible family-level baseline candidate, subject to benchmark and target-information compatibility.
- **Confidence / residual risk:** High for title, issue citation, and relevance; medium for online-first year and for baseline comparability pending full-text protocol review.

### F7-B2 — IEEE/ASME Transactions on Mechatronics 2022

- **Exact title:** “Transfer Learning for Remaining Useful Life Prediction Across Operating Conditions Based on Multisource Domain Adaptation.”
- **Authors:** Yifei Ding; Peng Ding; Xiaoli Zhao; Yudong Cao; Minping Jia.
- **Year / venue / locator:** 2022; *IEEE/ASME Transactions on Mechatronics*, vol. 27, no. 5, pp. 4143–4152.
- **DOI / publisher page:** [10.1109/TMECH.2022.3147534](https://doi.org/10.1109/TMECH.2022.3147534); [IEEE Xplore document 9723508](https://ieeexplore.ieee.org/document/9723508/).
- **Relevance evidence:** Semantic Scholar abstract states that many existing prognostic methods use single-source adaptation and “ignor[e] the domain-shift within source domain”; the title directly concerns RUL across operating conditions and multisource DA.
- **Independent metadata cross-check:** Crossref, OpenAlex, and Semantic Scholar agree on title, full author order, 2022, and IEEE/ASME Transactions on Mechatronics; Crossref and Semantic Scholar agree on volume/issue/pages.
- **Sources and SHA-256:** Crossref [record](https://api.crossref.org/works/10.1109/tmech.2022.3147534), `057457d83d2b809b53706321a4e575d59ffa9a1243e8994da2756d31849f92d8`; OpenAlex [record](https://api.openalex.org/works/https://doi.org/10.1109/tmech.2022.3147534), `d7357b5042e8e58361f98718d875ac13620e7eaf6134287a27371f90fbc9d6e7`; Semantic Scholar [record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tmech.2022.3147534?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), `79cc4e0b2a41807ef25f63499325791f1a5a699d7feacccf48c3b893da4d13db`. All HTTP 200. DOI resolver HTTP 302 body SHA-256 `47eba0bd0c19095ce86c947222eb141a31caca22761d8543b78767240f30301e` to the publisher page above; page HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as directly relevant multisource RUL adaptation across operating conditions. Consider it for a recent comparison only if its access to multiple source domains and target data can be reproduced under the registered protocol.
- **Confidence / residual risk:** High for bibliographic identity and relevance; medium for experimental-baseline fit pending protocol/full-text review.

### F7-B3 — IEEE Transactions on Industrial Informatics 2023

- **Exact title:** “Self-Supervised Deep Domain-Adversarial Regression Adaptation for Online Remaining Useful Life Prediction of Rolling Bearing Under Unknown Working Condition.”
- **Authors:** Wentao Mao; Jiaxian Chen; Jing Liu; Xihui Liang. Semantic Scholar uses hyphenation/initial variants for some names.
- **Year / venue / locator:** 2023; *IEEE Transactions on Industrial Informatics*, vol. 19, no. 2, pp. 1227–1237. OpenAlex records 2022 while Crossref and Semantic Scholar give the 2023 issue/publication date; use 2023 for the final issue citation.
- **DOI / publisher page:** [10.1109/TII.2022.3172704](https://doi.org/10.1109/TII.2022.3172704); [IEEE Xplore document 9769904](https://ieeexplore.ieee.org/document/9769904/).
- **Relevance evidence:** Semantic Scholar abstract calls it an “online remaining useful life (RUL) approach for rolling bearings under unknown working condition” and describes condition drift and limited early-fault observations. The title and abstract directly connect online adaptation, working-condition shift, and RUL.
- **Independent metadata cross-check:** Crossref and Semantic Scholar agree on title, author order, 2023 final issue, and venue. OpenAlex agrees on title/venue/DOI/authors but reports 2022. Crossref's final volume/issue/pages support the 2023 issue citation.
- **Sources and SHA-256:** Crossref [record](https://api.crossref.org/works/10.1109/tii.2022.3172704), `4e34a9021ab1fc6af69ac6f2091a73024c0f95601b1ab45c069e2bffcfa781e7`; OpenAlex [record](https://api.openalex.org/works/https://doi.org/10.1109/tii.2022.3172704), `ab1d8fe1c54750dd7fda1939bfda903da3bedc48fd99dc4be29301ebe51a30b9`; Semantic Scholar [record](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/tii.2022.3172704?fields=title,authors,year,venue,publicationDate,abstract,externalIds,url), `1db879a75320cceda1f95f3f28d87fb1516c9ea407eb8d50bf57f2e85ef41e4f`. All HTTP 200. DOI resolver HTTP 302 body SHA-256 `4ec7bca24fe81d718d3487c7f53b3c33b70d7181487c0a8deac058cade73d9d2` to the publisher page above; page HTTP 202 / zero bytes.
- **Inclusion decision:** Recommend including as a recent online/unknown-condition RUL adaptation method. It may motivate the target-telemetry distinction required by F4; do not treat it as an inductive, source-only comparator without matching its online target inputs.
- **Confidence / residual risk:** High for paper identity, issue citation, and topic; medium for baseline fit pending full-text review.

## Decision and Cross-Validation Summary

| Evidence group | Records checked | Bibliographic agreement | Relevance | Proposed action |
|---|---:|---|---|---|
| Review-report DOI candidates | 4 | Titles/author sets/venue/DOI agree across Crossref and OpenAlex; S2 agrees substantively. Three year/display nuances are explicitly recorded. | All four directly address RUL domain adaptation. | Add all four to the literature map; state information-regime differences; verify A2 issue/year from current publisher record before final bibliography. |
| Additional search results | 3 | Crossref and S2 issue citations agree; OpenAlex differs on online/indexing year for B1 and B3. | All three directly address cross-condition/domain-adaptive RUL. | Add all three to Related Work; treat as candidate baselines only after full-text method/data access review. |

At least two independent metadata sources were consulted for every article, and a third abstract-indexing source was available for all seven. Publisher DOI resolution was confirmed for all seven, but the IEEE Xplore HTML itself did not return article content in this environment (HTTP 202, zero body). Abstract-level relevance is supported by OpenAlex and/or Semantic Scholar records; no full-text validation is claimed. Article relevance confidence is high because the exact titles and returned abstracts directly name RUL plus domain adaptation/cross-domain or operating-condition transfer. Novelty confidence is not assessed: a seven-paper targeted set is not a systematic review or an exhaustive novelty search.

## Remaining F7 Work Before Manuscript Revision

1. Compare each paper's source/target data access, labels, target telemetry, datasets, splits, and metrics against the registered source-only contract; only then nominate fair baselines.
2. Retrieve and inspect full texts or authoritative publisher abstracts once the IEEE Xplore access path serves content; reconcile A2's 2024/2025 year and other online-first/issue-year differences against the live publisher issue records.
3. Expand the search beyond the single OpenAlex query before making any novelty or completeness claim. A focused search across IEEE Xplore, Crossref, OpenAlex, Semantic Scholar, and direct references/citations should include RUL forecasting, domain generalization, condition transfer, and source-only/inductive protocols.
4. Draft 3–5 contribution bullets only after the evidence supports them. These references establish relevant prior art; they do not establish that the present candidate is novel, superior, or fairly compared.

**F7 status:** Literature identity and topical relevance evidence assembled; manuscript revision and baseline fairness remain open. This status is separate from experimental findings F1–F6 and does not imply a positive novelty verdict.

