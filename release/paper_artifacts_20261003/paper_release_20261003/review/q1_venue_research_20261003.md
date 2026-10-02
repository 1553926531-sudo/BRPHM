# SCI-Q1 fallback venue research (verification ledger)

**Date:** 2026-10-03 (Asia/Shanghai)  
**Purpose:** maintain non-IEEE fallbacks that are plausibly SCI Q1 and technically aligned with the registered RUL/domain-shift evidence. This note does **not** claim a current JCR or Chinese Academy of Sciences (CAS) quartile without an authoritative year/category lookup.

## Eligibility rule

The user permits a venue that is either IEEE or at least SCI Q1. The three IEEE routes remain the immediately eligible basket because they satisfy the IEEE requirement independently of quartile. A non-IEEE route is submission-eligible only after the authors check the target year's Clarivate JCR and/or CAS partition for the exact subject category and record a dated screenshot/export or institutional report. SCImago/Scopus quartiles are useful screening signals but are not treated as proof of SCI Q1.

## Candidate basket

| Rank | Journal | Publisher / ISSN | Evidence captured | Fit to this paper | Main desk-risk | Required promotion gate |
|---:|---|---|---|---|---|---|
| 1 | **Reliability Engineering & System Safety (RESS)** | Elsevier; 0951-8320 / 1879-0836 | Elsevier serial record confirms title, publisher, ISSNs and Scopus source 13853; Crossref and OpenAlex independently resolve the same title/ISSN | Strongest non-IEEE match for provenance-controlled RUL evaluation, reliability credibility, and risk-aware transfer assessment | Current final partition is tiny (5 BAT units, 1 RWA window), deterministic rather than probabilistic, and simulation-only | Confirm current JCR/CAS Q1; add a reliability/credibility framing and make the small final partition a formal scope bound |
| 2 | **Mechanical Systems and Signal Processing (MSSP)** | Elsevier / Academic Press; 0888-3270 / 1096-1216 | Elsevier serial record confirms title, publisher, ISSNs and Scopus source 21080; Crossref and OpenAlex independently resolve the same title/ISSN | Strong RUL, condition-monitoring, temporal-feature and signal-processing precedent | The present contribution is mainly an audit protocol; MSSP reviewers may require a stronger signal-processing or algorithmic contribution and larger validation | Confirm current JCR/CAS Q1; add signal-processing ablations and keep claims limited to the registered protocol |
| 3 | **Aerospace Science and Technology (AST)** | Elsevier Masson; 1270-9638 (eISSN not returned by the captured serial record) | Elsevier serial record confirms title, publisher, ISSN and Scopus source 12507; Crossref and OpenAlex independently resolve the same title/ISSN | Aerospace RUL/telemetry route that can reuse the spacecraft component narrative | LEO600 has only 5 usable BAT units and 1 RWA observation, with the recorded 79 s simulator/tile-period mismatch | Confirm current JCR/CAS Q1; resolve or explicitly bound the orbital-period seam and expand aerospace validation if available |

## Primary-source records

The following machine endpoints were fetched on 2026-10-03 with `Invoke-WebRequest -UseBasicParsing` and a `BRPHM-audit/2026-10-03` user agent. SHA-256 is over the UTF-8 response text.

| Source | HTTP | SHA-256 |
|---|---:|---|
| [Elsevier serial record, RESS](https://api.elsevier.com/content/serial/title/issn/0951-8320) | 200 | `ace6544dc2e19ab0caab54ea5f8ff9b71aa3b5f8fe39b052770a52524c3cfea8` |
| [Elsevier serial record, MSSP](https://api.elsevier.com/content/serial/title/issn/0888-3270) | 200 | `a6a2fbff42c757182815cd8b69a46c36ff4d5760c2ce1c4fc77b739133aac100` |
| [Elsevier serial record, AST](https://api.elsevier.com/content/serial/title/issn/1270-9638) | 200 | `8eb295294e23081f1fa9850043daa2feacd937023d4736f0918aeda8d45eaa4b` |
| [OpenAlex source, RESS](https://api.openalex.org/sources/issn:0951-8320) | 200 | `0e1a8c24b64024adad0e40c33c911562ddaba8a77bc986bccdba6323e0ee8905` |
| [OpenAlex source, MSSP](https://api.openalex.org/sources/issn:0888-3270) | 200 | `fc734cc36d14b1912cb29f142f058d8be9be767033c322bcd93580d111740e60` |
| [OpenAlex source, AST](https://api.openalex.org/sources/issn:1270-9638) | 200 | `a10de98644abada07a8b34a1780d8d26bd890f1fe2a75b6aaff8fe6a7e597f3c` |

Official journal landing pages to verify at submission time:

- [RESS](https://www.sciencedirect.com/journal/reliability-engineering-and-system-safety)
- [MSSP](https://www.sciencedirect.com/journal/mechanical-systems-and-signal-processing)
- [AST](https://www.sciencedirect.com/journal/aerospace-science-and-technology)

The publisher landing pages returned HTTP 403 in this environment, so no article-type, word/page limit, review model, or supplementary-material rule is inferred from them. A 403 is an access observation, not a claim that the journal lacks a rule; the rules must be rechecked through the institutional publisher portal or the journal's Editorial Manager page.

## Quartile and indexing status

- The captured Elsevier records identify the journals and their Scopus source IDs. They do not expose Clarivate SCIE membership or JCR quartile.
- OpenAlex supplies independent source metadata and citation statistics, but it is not a JCR/CAS quartile authority.
- Therefore the ledger deliberately records `Q1_VERIFICATION_REQUIRED` for all three. Before using any one as a non-IEEE submission route, capture the current year's Clarivate JCR category and quartile or the institution's current CAS partition entry, with access date and report hash. If that lookup fails, retain the route as a research fallback only and use an IEEE basket route.

## Route-specific paper work

The same hash-linked evidence package can be reused. A branch may alter title, abstract, related-work emphasis, figures, and declarations, but it may not alter F1 chronology, the 648-unit split, the frozen LEO600 receipt, source-gate arithmetic, or the statistical limits. RESS needs the strongest reliability/credibility framing; MSSP needs the strongest signal-processing ablation; AST needs a defensible aerospace validation story. None of these branches may claim statistical significance, practical superiority, or population generalization from the current LEO600 sample.

## Cross-validation and confidence

- **High confidence:** title, publisher, ISSN and endpoint response facts; each is corroborated by two machine sources (Elsevier serial metadata plus Crossref/OpenAlex).
- **Medium confidence:** topical fit, because it is an editorial judgment grounded in the manuscript's registered evidence and the existing F7 literature ledger.
- **Open / no claim:** current SCI indexing and Q1 quartile. Those require a dated authoritative JCR/CAS record for the target year and category.

