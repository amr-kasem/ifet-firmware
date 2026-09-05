# Design closure verification — 2026-09-06

**Author:** Abdelrahman · **Scope:** documentation closure only.
**Authority:** `../contract/write-contract-v0.4.md`; A1–A8 decided under the instruction to close the design.

## Completed

- Finalized v0.4, the implementation design, decision record, 66-row field register and unsent change notice.
- Preserved the pre-closure v0.3 specification under evidence; `contract/` contains exactly one specification.
- Reconciled the index and status views. Earlier dated assessments are explicitly historical, including
  obsolete field gaps, permission waits and the October 9 target, which has not been revalidated.
- Corrected register inconsistencies: programme identity belongs to the programme entity and includes
  specimen/section/type uniqueness; pressure output uses PSF; initial Test Result is Pending; reviewer
  fields require schema support; unavailable deflection rejection is required behavior, not delivered code.
- Marked the local FIFO metadata row LOCAL_ONLY so schema setup cannot mistake it for an Airtable field.

## Checks performed

Parsed the CSV with Python's standard CSV reader and compared field names/types to **both saved September 5
schema baselines**. These are offline checks against recorded evidence, not fresh Airtable probes.

| Check | Result |
|---|---|
| Register rows / unique direction-table-field keys | 66 / 66 |
| Decision state | All 66 DECIDED |
| Delivery states | 44 BASELINE, 15 PLANNED, 4 CONDITIONAL, 3 OMITTED |
| Actual planned Airtable fields | 14: eight Protocol Sections, six LabOS Raw Data Table |
| Other planned row | One local queue-metadata row; never create it in Airtable |
| Existing wire fields | Names and types match both saved baselines |
| Planned wire fields | All 14 absent in both saved baselines |
| Active contract files | Exactly one, v0.4 |
| Whitespace validation | `git diff --check` passed |

BASELINE records field existence, including intrinsic record-ID metadata; it does not assert that v0.4
mapping or runtime code exists. No application tests were rerun for this documentation-only change.

## Notion reconciliation

Fetched these pages before editing, added the current closure above their preserved historical content,
then fetched each again to verify the new sections. The schema page now includes all 66 current register
rows with direction, table, field, type and delivery state.

| Page | Update |
|---|---|
| [Project Status & Revised Timeline](https://app.notion.com/p/3ca57bad43d581e5b28ece91494a45a7) | Decisions, actual delivery limits, next milestones and unvalidated prior dates |
| [Airtable Schema Reference](https://app.notion.com/p/3a357bad43d581c68ea1c85411429cac) | Current v0.4 decisions and 66-row mapping; previous tables retained as history |
| [Internal Engineering Plan](https://app.notion.com/p/3a657bad43d581fa9778e5c361abd190) | Current scope, dependencies and M1–M5 sequence |
| [LabOS architecture hub](https://app.notion.com/p/3a357bad43d5818cb726d24c5e803c69) | Closure summary and links to current owner-facing status and mapping |

The technical verification record, archived roadmap and original five-week baseline retain their historical
roles. No implementation task was marked delivered by this documentation reconciliation.

## Scope and handoff

No runtime code, schema, Airtable records or production containers changed. No rig was contacted or driven.
The correspondence remains **NOT SENT**. Existing outbox code remains groundwork; new PostgreSQL migrations,
programme/run APIs, v0.4 envelope behavior and acceptance are implementation work.

Next is M1 Testing Base diff/linked synthetic fixtures, followed by M2 local PostgreSQL import/run/offline
replay. The design defines subsequent implementation; closing it does not silently perform those milestones.
Measurement calibration/acquisition, extractor remediation, automation acceptance and production cutover
retain the checks and fallback behavior in contract §§3–10.
