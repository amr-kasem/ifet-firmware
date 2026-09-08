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

---

# Stage 5 — the whole pipeline, live · **18/18**

Added after the three-layer verification framework was set out. Stages 3 and 4
push payloads the envelope built, with the client: **they prove the last two
links.** Stage 5 drives the chain end to end:

```
HTTP route → sync.publish → sync_outbox → worker.drain
           → service.make_sender(AirtableClient) → Airtable
```

with the **actual worker** and the **actual production sender** — not
imitations. That distinction is not pedantry: every unit suite injects a
transport that accepts any payload, which is how a sender that would have
rejected every photograph passed 270 tests.

To make it testable, the sender was extracted from `main()` as
`service.make_sender(client, settings)`. It had been a closure, so the only way
to check it was to keep a copy in the test and assert by source scan that the
copy still matched — a test of a resemblance. The copy is gone; the acceptance
suite and this probe call the same function.

## Per workflow, through the real routes

| | Forced Entry | ANSI Z97.1 | Impact |
|---|---|---|---|
| Queued by the routes | create · terminal · verdict + 1 attachment | same | same + 3 attachments |
| Airtable row | `reczx4aY8UTFxR4DX` | `recgIHlB…` | `recnbUx0…` |
| Identity round-trips | ✅ four rec ids · Test ID · Attempt ID · Attempt Number | ✅ | ✅ |
| Verdict and reviewer | ✅ `Passed` by `LABOS-PROBE-reviewer` | ✅ | ✅ |
| Timestamps | ✅ start · end · Test Date | ✅ | ✅ |
| **Withheld measurements** | ✅ **absent** | ✅ **absent** | ✅ **absent** |

## The three things a happy path cannot show

| Check | Result |
|---|---|
| **Retry** — re-delivering an attempt updates the same row | `reczx4aY8UTFxR4DX → reczx4aY8UTFxR4DX`, 1 row |
| **Retest** — a new attempt is a separate row, same Test ID, original untouched | attempt 1 `reczx4aY8UTFxR4DX` = `Passed` · attempt 2 `recoS8yhDqvnScfwx` = number 2 |
| **Attachments** park visibly without pinning the status | 3 parked · headline `Pending` · record-channel parked **0** |

That last row is the point of the two-channel split: a capability we have not
built cannot drag the headline to `Retry Required` and hide the next real
failure, while the stuck evidence stays visible in `attachment_parked`.

**One assertion of mine was wrong and is corrected rather than loosened.** I
expected all five attachment entries to park in one drain. `worker.drain` stops
when a cycle makes no progress and claims one head per attempt per channel, so
it parks each channel's head and leaves the rest pending — which is right, since
a channel whose head will never succeed should not be spun on every cycle. The
probe asserts the property now, not the count.

## This layer's honest limit

**Linkage is inserted directly.** Stage 5 proves the outbound path *given a
linked job*; it does not prove the importer, because the importer does not
exist. Proving that a requirement entered in Airtable reaches a rig and comes
back as a summary is layer 3 — and **layer 3 may not shortcut the linkage the
way this file deliberately does.**

Rig observations are synthetic. That proves data handling only; calibration and
hardware performance remain separate acceptance checks.

---

# Stage 5, second run — all five types, real hierarchy, photographs · **31/31**

The first stage 5 was 18/18 and three things about it were wrong. Recorded
because each was a way of passing without proving.

| Was | Now |
|---|---|
| Invented record ids (`recPROBE5project1`) | The real `IFET-FIXTURE-0001` records — project `reclD9DwtosvMGSI3`, mock-up `recclCv9R9AP5q9Vp`, protocol `recPqpWwDunfuXuL5` — and **the Protocol Section for each requirement code**, so a Cycles result cannot publish against the Forced Entry requirement |
| Three of five test types | **Five.** Static and Cycles through their real routes, posting `deflections` alone as production firmware does |
| A sender with no database access, so attachments could not deliver | The real `service.make_sender` with a session — the same function `main()` builds |

**Photographs now reach Airtable.** Preview generated, uploaded by value to
`content.airtable.com`, the returned attachment id recorded, and the file
verified present on the record.

## Two defects only a live run could find

Both invisible to a stubbed client, because a stub never builds a URL and never
returns Airtable's own response shape:

1. **`LabOS Photos` has a space in it.** A raw space in a request path is
   rejected before the request is made — `URL can't contain control
   characters`. Every upload failed on it.
2. **The upload endpoint returns the record keyed by field ID, not field name.**
   Looking the attachment up by name found nothing, so the upload *succeeded* —
   the file was on the record — and the returned id was never recorded. That is
   the quiet half of a working feature: without the id, a retry has nothing to
   reconcile against and would attach the photograph a second time.

The second is the more instructive. Nothing was visibly broken: entries went
`done`, the headline read `Synced`, and the photographs were on the records. Only
an assertion about the *recorded id* caught it.

## What this run asserts, per test type

identity round-trips (four record ids, Test ID, Attempt ID, Attempt Number) ·
the section matches the requirement code · verdict and reviewer land in their
spelling · timestamps present · **withheld measurements absent** · photographs
delivered with their returned ids and present on the record.

Then: **retry** re-delivers to the same row; **retest** is a separate row keeping
the same Test ID with the original untouched.

## Still not proven here

- **The importer.** Linkage is assigned directly. This proves the outbound path
  *given* a linked job and says nothing about how a job becomes linked — there
  is no mirror and no import path. **Layer 3 may not take this shortcut.**
- **Corrections**, `Max Pressure Achieved`, deflection calibration, rig
  `event_id` correlation, the operator UI, and their automations. Unchanged.
- Synthetic rig observations prove data handling only.

---

# Stage 6 — the full business flow · **14/14**

The target the epic was set, end to end, with **no shortcut on linkage**:

```
requirement in Airtable → mirrored (allowlisted) → hierarchy selected
  → imported through the SAME create path a typed project uses
  → parameters pre-filled → attempt run and reviewed, requirement frozen at start
  → published back on the section that specified it, with its photograph
```

| Check | Result |
|---|---|
| Requirements mirrored from the live base | 1 project · 1 specimen · 1 protocol · 6 sections |
| Every mirrored section reads unambiguously | 5 executable of 6 — `GAUGE_COUNT` is a parameter, not a test |
| Imported through the shared create path | project 1 · **6 static + 8 cyclic derived** |
| Parameters pre-filled | DP 60.0/45.0 · gauges 5 · impacts 2 |
| **Refresh then re-import** | 1 project, 6 static tests — no duplicate |
| **Airtable unreachable** | import serves the mirror; no call in the path |
| **Requirement frozen at start** | section `recVwSIEMXtezYa90` · `'ASTM F588 Grade 40'` |
| **Changed upstream requirement** | frozen value holds while the section now says `CHANGED-UPSTREAM` |
| Result reached Airtable, one row | `rec8hn6pJMqbbp8to` |
| **Published against the section that specified it** | `recVwSIEMXtezYa90` — the one the importer bound |
| Verdict, reviewer, dates | `Passed` by `LABOS-PROBE-reviewer` |
| Withheld measurements | **absent** |
| Photograph on the record | 1/1 delivered |

**Stage 5's shortcut is gone.** It assigned the Airtable record ids directly,
which proved the outbound path *given* a linked job. Here the linkage is
produced by the importer from requirements read out of the base.

## One defect found by running it

The field register's IN row for Mock-Ups/Specimens names **`Project Name`** as
the link to `IFET Projects`. It is not — that is a lookup of the job number's
*text*, and the real link field is **`IFET Job Number`**. The import simply
found no specimens. A register row naming a plausible neighbouring field is
exactly the kind of error that survives review, and only reading the live base
settles it.

## Still not proven, and the dependency for each

- **Corrections** — `corrects_attempt_id` has columns, a property and an
  envelope mapping, and no route sets them. Every attempt is a retest today.
- **`Impact Velocity`** — a target mapped to `shots.velocity`, an achieved
  observation. Needs its own column.
- **`GAUGE_COUNT`** — snapshotted as a programme parameter while firmware takes
  `selectedSensors[]` live at start; a mismatch has no defined behaviour.
- **`Max Pressure Achieved`** — on the bus, not persisted.
- **Deflection calibration** — bench time, hardware.
- **Rig `event_id` correlation** — a genuine firmware dependency, unlike
  operator identity.
- **The operator UI**, and **their automations** — Meta API returns 403.
- Synthetic rig observations prove data handling only.
