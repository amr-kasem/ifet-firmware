# Live write proof — Testing base, 2026-09-08

**Approved by:** gad, 2026-09-08 · **Base:** Testing `app4oXS3Kd5IKWgJ7` ·
**Table:** `LabOS Raw Data Table` `tblnc9SsbXU0C0FWh` ·
**Production:** untouched, refused unconditionally by both tools.

Everything else about the sync path is proven with an **injected transport**,
which tests the queue and can never test the wire. That distinction is not
academic: it hid a defect that would have parked every photograph on first
contact with Airtable (see below). So the wire now has its own proof.

## Stage 3 — the mechanism · **15/15**

`tests/stage3_live_write.py --live`. One Static Load attempt, fourteen original
checks plus a new one for the verdict phase.

| # | Check | Result |
|---|---|---|
| 1, 15 | terminal and verdict payloads build and carry the merge key | PASS |
| **2** | **first upsert creates exactly one record** | **`recj07Jtx6wHcCFIk`** |
| **3** | **identical re-send updates, does not create** | **same record id** |
| **4** | **replayed retry leaves exactly one row** | **1 row** |
| 5–7 | empty string to a number / date / select field | all rejected 422 |
| 8 | omitting the key instead is accepted | PASS |
| 9 | unknown select option fails loudly, no stray option created | 422 |
| 10 | a genuine `0` stores as `0`, not blank | read back `0` |
| 11 | batch over 10 refused before sending | PASS |
| 12 | client throttles under Airtable's 5 req/s | 6 requests in 5.23 s |
| 13 | structured JSON survives the round trip | `g3=0.0`, 2 load steps |
| 14 | UTC timestamps round-trip, duration derivable | `duration_s=1680` |

**Checks 2–4 are the ones that mattered.** Upsert on `LabOS Attempt ID` via
`performUpsert` / `fieldsToMergeOn` had never executed against Airtable. The
entire three-phase design rests on it — if Airtable would not merge on that
field, every phase would have become a separate row and the design would have
had to change. It merges.

**Two findings beyond a pass.** Airtable's own rejection text for check 9 is
*"Insufficient permissions to create new select option"* — so the token
**cannot** invent options, which is a stronger guarantee than `typecast=False`
being set correctly on our side. And the throttle has real headroom: 6 requests
took 5.23 s, roughly 1.15 req/s against a 5 req/s ceiling, so the earlier
concern that `MIN_REQUEST_INTERVAL = 0.2` left none was wrong.

## Stage 4 — all five workflows · **5/5**

`tests/stage4_five_types_live.py --live`. Each type driven through
`create → terminal → verdict` with the same envelope builders `sync.publish`
uses, validated against the **live** option sets rather than a snapshot.

| Test type | Phases | Rows | Read back |
|---|---|---|---|
| Static Load | 3 | **1** — `recZGnkBp49L4adeO` | `Passed` · `Completed` |
| Cycles | 3 | **1** — `rec6U5pffTLOMMrdy` | `Passed` · `Completed` |
| Impact | 3 | **1** — `recmACcwM6xqlgB0s` | `Passed` · `Completed` |
| Forced Entry | 3 | **1** — `recqLohi16ck2vrcp` | `Passed` · `Completed` |
| ANSI Z97.1 | 3 | **1** — `recdpXVeGvrSyIV7f` | `Passed` · `Completed` |

Three writes, one row, every type. Until this morning three of these five could
not resolve their Airtable identity at all, so "the sync works" had been
demonstrated for two workflows out of five.

## Live option sets, read from the base

| Field | Type | Options |
|---|---|---|
| `Test Type` | singleSelect | `Static Load` · `Cycles` · `Impact` · `Forced Entry` · `ANSI Z97.1` |
| `Test Status` | singleSelect | `Not Started` · `In Progress` · `Completed` · **`Abborted`** |
| `Test Result` | singleSelect | `Pending` · `Passed` · `Failed` · `Not Applicable` · `Inconclusive` |

**All five `Test Type` options already exist**, which retires a concern carried
in the tooling: an older note said the live set held only `Static Load`, which
would have blocked four of the five types. It does not. `Abborted` — their
spelling — is confirmed live, and every value the envelope translates to is
present.

## What this does NOT prove

- **Attachments.** `LabOS Photos` has no upload path: no preview generation, no
  direct upload, no recording of returned attachment ids. Stage 4 deliberately
  omits it rather than pretending. The production sender now refuses an
  attachment entry with a truthful reason instead of PATCHing a `photo` object
  as record fields — which is what it did until today, and which Airtable would
  have rejected as an unknown field, parking every photograph permanently.
- **The read half.** No mirror table, no import path, so pre-fill is unproven
  end to end. The largest remaining gap; business I/O reconciliation, 2026-09-08.
- **Their automations.** The Meta API returns 403 for automations, so whether
  ours writes disturb an unfiltered trigger needs the Airtable team's eyes.
- **Volume.** Five attempts is not a load test.
- **Production.** Untouched. Live alembic head is still `3a65a83e0463`, before
  P1 — and that must be confirmed **on the node**, not from this repo.

## Housekeeping

Every row is tagged `Operator Name = LABOS-PROBE`, with `LabOS Test ID` values
prefixed `probe-` or `probe4-`. **LabOS never deletes**, so purging them is an
ask for the Airtable team. Six rows in total: one from stage 3, five from stage 4.
