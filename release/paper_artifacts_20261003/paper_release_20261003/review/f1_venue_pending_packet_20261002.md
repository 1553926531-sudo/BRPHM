# Target Venue Pending Packet

**Status:** `VENUE_NOT_CONFIRMED`  
**Reason:** the reviewed materials name no IEEE journal/conference, track, article type, or submission mode. Venue-specific compliance is therefore not asserted.

## Required confirmation fields

| Field | Current value | Evidence required before venue checks can close |
|---|---|---|
| Venue | `TBD` | Official venue URL and scope page |
| Track / section | `TBD` | Official CFP or submission portal |
| Article type | `TBD` | Author instructions |
| Submission mode | `TBD` | Double-blind or author-identified policy |
| Edition / deadline | `TBD` | Official CFP or portal |

## Checks intentionally still open

- Scope match with 2-3 recent papers from the named venue.
- Official template, page limit, column format, font, and reference rules.
- Review model, anonymization, author metadata, ORCID, acknowledgements, and funding fields.
- PDF eXpress or other venue checker identity and submission-window rules.
- Accessibility requirements: embedded fonts, tagged PDF, reading order, and figure text.
- Data/code/supplement and artifact DOI requirements.
- COI, funding, privacy, ethics applicability, and data-license declarations.

## Candidate venues researched (shortlist only)

The existing research note `venue_research_20261002.md` records official-page hashes and access dates for:

1. IEEE Transactions on Instrumentation and Measurement (TIM).
2. IEEE Transactions on Reliability (T-Rel).
3. IEEE Transactions on Aerospace and Electronic Systems (TAES).

This shortlist is not a venue confirmation. TIM and TAES scope pages were readable and hashed on 2026-10-02; T-Rel scope/author pages were not readable in that capture. No page-limit, PDF-checker, or acceptance claim may be inferred for any venue until the user supplies the target.

## User confirmation needed

Provide the target IEEE venue, track or section, article type, and whether the submission is double-blind. Until those fields are fixed, the IEEE checklist item 1.1 and all venue-specific items remain `pending`, not `pass`.


