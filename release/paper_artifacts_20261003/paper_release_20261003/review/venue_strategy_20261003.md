# Multi-venue IEEE submission strategy

**Date:** 2026-10-03 (Asia/Shanghai)  
**Purpose:** maintain three independent IEEE submission paths while the author metadata and final venue are pending. This is a routing strategy, not a claim of acceptance or of a current SCI quartile.

## Hard constraint

The user allows either an IEEE venue or a non-IEEE journal that is demonstrably SCI Q1. The IEEE basket below is therefore the immediately eligible set. A second, independent SCI-Q1 basket is maintained in [`q1_venue_research_20261003.md`](q1_venue_research_20261003.md), but its quartile is marked `Q1_VERIFICATION_REQUIRED` until the target year's Clarivate JCR or CAS record is captured. No public Scopus/SCImago signal is silently treated as proof of SCI Q1.

## Ranked basket

| Rank | IEEE venue | Working article type | Paper framing | Why it is in the basket | Main screening risk | Switch condition |
|---:|---|---|---|---|---|---|
| 1 | **IEEE Transactions on Instrumentation and Measurement (TIM)** | Regular paper, provisional | Measurement-derived telemetry and an auditable source-label-only evaluation protocol | Official IMS scope was fetched and hashed; recent TIM papers establish direct RUL/domain-shift precedent; the current six-page IEEEtran manuscript can be adapted without inventing results | The contribution must read as measurement science/protocol work, not only a predictive-model comparison | Use as primary after the abstract, contributions, and discussion explicitly center measurement-derived telemetry, auditability, and reproducibility |
| 2 | **IEEE Transactions on Reliability (T-Rel)** | Regular paper, provisional | Reliability credibility, provenance control, and risk-aware RUL evaluation under source-only transfer | Recent T-Rel records include RUL reliability assessment, credibility evaluation, and unseen-domain generalization; topical fit is strong | Current evidence is deterministic and small; probabilistic reliability/uncertainty content is limited, and official author pages were not readable in this audit | Promote to primary only if a reliability/credibility section and uncertainty treatment are added and the official submission rules are verified |
| 3 | **IEEE Transactions on Aerospace and Electronic Systems (TAES)** | Regular paper, provisional | Spacecraft telemetry and cross-orbit prognostics evaluation | Official AESS scope and author information were fetched and hashed; spacecraft prognostics precedent exists | LEO600 has 5 usable BAT units and 1 RWA observation; the simulator period differs from the model tile by about 79 s/608 km; application evidence is narrow | Use only with an aerospace-system narrative, explicit seam limitation, and stronger spacecraft validation or a clearly bounded methods paper |

## Independent SCI-Q1 fallback basket

| Rank | Journal | Working framing | Why it is retained | Gate before submission |
|---:|---|---|---|---|
| 1 | **Reliability Engineering & System Safety (RESS)** | Auditable reliability/prognostics evaluation under source-only transfer | Best non-IEEE fit for provenance, credibility, and risk-aware RUL evaluation | Verify current JCR/CAS Q1; add reliability/credibility framing and preserve the small-sample bound |
| 2 | **Mechanical Systems and Signal Processing (MSSP)** | Signal-processing and temporal-feature audit for cross-condition RUL | Strongest non-IEEE signal/RUL precedent | Verify current JCR/CAS Q1; add a defensible signal-processing ablation and larger validation if available |
| 3 | **Aerospace Science and Technology (AST)** | Spacecraft telemetry and bounded cross-orbit prognostics | Aerospace domain fit and separate editor pool | Verify current JCR/CAS Q1; resolve or explicitly bound the 79-second period seam and expand aerospace evidence |

These three are evidence-backed candidates, not claims of current Q1 status. Their source records, hashes, scope risks, and the exact verification procedure are in `q1_venue_research_20261003.md`.

## Evidence ledger

- Scope and recent-paper evidence are in [`venue_research_20261002.md`](venue_research_20261002.md), with Crossref and Semantic Scholar metadata checks and DOI links.
- TIM official IMS response hash: `f8b8d3ff31fd37656a3a8989c057ac28c0a58f3df2e827c22e8a8b73fa82329d` (fetched 2026-10-02).
- TAES official scope response hash: `f0e4891bc7d6880e0b21d41de6140cd1204345afc8faa6f7fc628d9bc5063f9a` (fetched 2026-10-02).
- TAES author-information response hash: `8bf300d6ff64a0abc65ba448b86dce560653b4a718c2532e1ba92fc8a1c2c41a` (fetched 2026-10-02).
- T-Rel official pages were identified but returned HTTP 418/202 without usable body in this environment; no T-Rel page limit, review model, or PDF checker is claimed.
- IEEE Author Center returned HTTP 403 in the same audit; PDF eXpress, accessibility, article type, and metadata rules remain venue-specific checks.

## Shared package and venue-specific branches

The evidence package remains shared: F1–F10 ledgers, the machine manifest, reproduction scripts, statistics, figures, and the locally verified PDF. Venue branches may change title/abstract/emphasis, references, page layout, and declarations, but may not change the registered split, frozen candidate, receipt, gate arithmetic, or historical outer-fold disposition. Each branch must carry its own source hash and PDF hash.

The current working default is TIM because its official scope is directly verified and the required reframing is smaller. T-Rel and TAES remain ready IEEE fallbacks; RESS, MSSP, and AST remain independent SCI-Q1 candidates pending the dated JCR/CAS check. No branch is declared submission-ready until author metadata, funding/COI, article type, current template, and venue checker requirements are confirmed.

## Decision record

The author requested a high-probability basket rather than a single venue. Therefore the audit keeps three IEEE routes active and does not convert the shortlist into a single-venue compliance claim. The next venue-dependent action is to prepare the TIM branch first, then clone the shared evidence package into T-Rel and TAES variants if the primary scope check or editorial prescreen fails.
