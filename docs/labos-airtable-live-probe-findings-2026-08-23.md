# LabOS ↔ Airtable — first live probe against both bases

**Date:** 2026-08-23 · **Author:** Abdelrahman · **Contract:** `v0.3 DRAFT` → this document supplies §10 deltas
**Trigger:** the Airtable team delivered both PATs on 2026-08-23 and invited us to read the original base.

> **Status of this document.** It is the *evidence record* for the probe run. Contract
> `labos-airtable-write-contract-v0.3.md` §10 stays authoritative for open-item status; this file is what §10
> cites. Everything below was produced by GETs only.

---

## 1. What ran, and what it was allowed to touch

| | |
|---|---|
| Command | `python3 -m app.airtable.probe --snapshot …`, then a read-only record dump |
| Bases | `app4oXS3Kd5IKWgJ7` (LabOS Testing) **and** `app0OCunbmuXl7Hc9` (IFET production) |
| HTTP verbs issued | **`GET` only.** No `POST`, `PATCH`, `PUT` or `DELETE` was sent to either base |
| Write guards during the run | `AIRTABLE_SYNC_ENABLED=false`, `AIRTABLE_ALLOW_PRODUCTION_WRITE=false`, client write-allowlist = `tblnc9SsbXU0C0FWh` only |
| Their instruction | *"nothing will change in original base except LabOS Raw Data Table"* — **honoured; nothing changed in either base, including the raw table** |

Both PATs resolve to the same Airtable user (`usr3MpxrOLIMTI8Rv`) and each is scoped to exactly one base, which
matches what they described.

**Secret handling.** Both tokens went straight into the gitignored `.env` in `ifet-management` (mode `600`) and
appear in no commit, no document and no browser-served config. The production token is deliberately **not**
named `AIRTABLE_TOKEN` — `config.py` reads that name, so reaching production requires a conscious override
rather than an inherited default.

> ⚠️ **Rotate both tokens after acceptance testing.** They arrived as plaintext in an email thread — the second
> time credentials have travelled that way on this project (the v1 guide PDF was the first). Nothing has been
> misused, and this is a process note rather than an incident, but a token in a mail thread is a token with an
> unknown blast radius.

---

## 2. The environment checks out

All eight table IDs transcribed from their PDF into contract §0.1 are **confirmed live in both bases**, with
matching names. `Wall Positions Calendar` (`tbly6A3GB1GHdGocq`) is absent from both — it is presumably an
interface-only view. Contract §0.2 said every ID except the production base was single-sourced from a PDF;
that caveat can now be **dropped**.

**The testing base is a structural clone of production.** Table IDs *and* field IDs are identical across the
two bases, so the base is a duplicate rather than a parallel build. Two consequences worth keeping:

- The field-ID snapshot contract §9 requires is **portable across both environments** — one binding covers
  testing and production, and a cutover cannot silently re-point at different fields.
- The testing base contains **zero records** in all five LabOS-relevant tables. It is schema-only, so every
  finding about *data* below comes from the production base, which is where they populated the proposal.

---

## 3. Open items this run closes

| Item | Question | Answer from the live base | Now |
|---|---|---|---|
| **§10.1** | Is `Photos` an Attachment field? | `url` — matches what the contract §7 requires | ✅ closed (type half; reachability still a human answer) |
| **§10.2** | Are the four `Airtable … ID` fields text or link-to-record? | All four are `singleLineText` — **exactly what LabOS proposed** | ✅ closed |
| **§10.5** | Is `Impact Result` a fixed option set or free text? | `singleLineText` — free text | ✅ closed |
| **§10.10** | Rotated PAT delivered out-of-band | Both PATs delivered 2026-08-23 | ✅ closed |
| **§10.11** | Verify the §5 null/blank table against the live base | Probe run, snapshot committed | ✅ closed |
| **§10.16** | Is the `Test Result` option `Pass` or `Passed`? | **`Passed`.** Their v2 example was right and **this contract was wrong** | ✅ closed — LabOS changed |

Also confirmed: `LabOS Attempt ID` is `singleLineText`, so it is legal as the upsert merge key (contract §2
requires a plain-text field — a formula or rollup would have made `performUpsert` impossible). All 28 fields
v2 promised are present. One undocumented field exists, `Raw Modified Time` (`lastModifiedTime`), which is
Airtable-computed and needs nothing from LabOS.

---

## 4. Open items this run creates

### §10.17 — `Test Type` offers only `Static Load`. **Blocking.**

The live single-select holds exactly one option:

```
Test Type: ['Static Load']
```

Contract §4.3 defines five: `Static Load`, `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1`. **Four of the five
test types LabOS runs have no option to land in**, and a single-select rejects an unknown value. This is not a
naming quibble — the very proposal they sent as the worked example (IFET-26-0066) contains TAS-201 impact
testing, TAS-202 forced entry, TAS-203 cyclic and ANSI Z97.1. **Only the static-load portion of that job could
be written back today.**

The four missing options must be added to the select, in both bases.

### §10.18 — `Test Status` spells it `Abborted`

```
Test Status: ['Not Started', 'In Progress', 'Completed', 'Abborted']
```

A typo, but a load-bearing one: a single-select will not accept `Aborted`, so LabOS must send `Abborted`
verbatim or every aborted test 422s. LabOS has implemented their spelling (§6 below) and will keep it as long
as the base holds it. **Preferred fix: correct the option to `Aborted`** — an option rename in Airtable
preserves existing cell values, so this is safe on their side. LabOS will follow whichever spelling they
settle on; what it cannot do is guess.

`Test Result` and `Test Status` also carry `Pending` / `Not Applicable` and `Not Started`, which LabOS never
sends — those are theirs for pre-population, and LabOS leaving them alone is correct.

### §10.19 — **the proposal data in Airtable does not match the proposal PDF.** Blocking, and the most serious finding here.

See §5. This is the headline.

### §10.20 — `Test Date` is a `date`, not a `dateTime`

Contract §10.13 already objects to collapsing start and end into one field. The live type makes it sharper:
`Test Date` is a **`date`**, so it cannot hold a time of day at all. Test *duration* is therefore not merely
un-modelled, it is unrepresentable in any column. LabOS already mirrors start, end and computed `duration_s`
into `Complete LabOS JSON Response`, so nothing is lost from the payload — but nothing in Airtable can filter,
sort or roll up on it. This strengthens the §10.13 request rather than replacing it.

### §10.21 — confirm who writes the LabOS fields on `Protocol Sections`

`Protocol Sections` already carries `LabOS Attempt ID`, `Latest LabOS Attempt Number`, `LabOS Report Link`,
`LabOS Retest Required`, `Excel File Link`, `Result`, `Status`, `Testing Date` and `Notes`, and their sample
row `rec5d5BStH7z5h7NJ` has them **populated** (`LabOS Attempt ID: "001"`, `Latest LabOS Attempt Number: "1"`,
`Result: Passed`).

LabOS's read of this — which needs confirming, because the whole write model depends on it — is that **LabOS
writes only `LabOS Raw Data Table`, and their automation rolls those raw rows up into `Protocol Sections`.**
That is consistent with v2 §5/§7 and with their instruction that only the raw table changes. If instead LabOS
is expected to write `Protocol Sections` directly, that contradicts both, and the client's allowlist would
have to be widened deliberately.

### §10.22 — `LabOS Attempt ID` format

Their populated sample uses `"001"`. Contract §3 specifies a **UUID**, because attempt IDs must be unique
across every job, rig and year — a zero-padded counter collides the moment two jobs run concurrently, which is
the normal case with two rigs. LabOS will keep sending UUIDs; their automation must not assume a short numeric
form. `Latest LabOS Attempt Number` is the field that should carry `1`, `2`, `3`.

---

## 5. §10.3 answered — the read side, and a defect in it

**§10.3 has been the critical path since 2026-07-23 and it is now answered**, in both halves: what the
structure is, and whether it is usable.

### 5.1 The structure

`Protocol Sections` is one record per requirement line, keyed by `Section Name`, with the requirement in
`Value`:

| Protocol | `Section Name` | `Value` |
|---|---|---|
| TAS-201 | `LMI (impacts)` | `9` |
| TAS-201 | `SMI (impacts)` | `10` |
| TAS-202 | `# Dials` | `Full` |
| TAS-202 | `Static / Type` | `+60/60` |
| TAS-202 | `DP (+) (PSF)` | `9` |
| TAS-202 | `Water (PSF)` | *(blank)* |
| TAS-202 | `Forced Entry (*)` | *(blank)* |
| TAS-203 | `Cyclic (PSF)` | `+60/60` |
| ANSI Z97.1 | `Impact` | *(blank)* |

So it is **row-per-parameter, not discrete typed fields and not versioned JSON** — the third option, which
neither side had proposed. It is *addressable*: LabOS can find "the DP requirement for this protocol" by
matching `Section Name`. That is enough to build against, and **W3 is unblocked on structure.**

What it is not is *typed*. `Value` is `singleLineText` holding `9`, `Full` and `+60/60` interchangeably — a
magnitude, an enum and a pressure pair in one untyped column, with the unit encoded in the `Section Name`
string rather than in a field. LabOS will need a per-`Section Name` parser, and that parser is a hazard: it
turns a free-text edit in Airtable into a silent misread in the test sequencer. This is gap I from the internal
plan, now confirmed rather than suspected. **LabOS's ask stands: `Required Value` + `Required Unit` as typed
fields**, with `Value` retained as the human-facing display string.

### 5.2 The defect — values are shifted by one column

Cross-checking their populated record against the source PDF they sent (`IFET-26-0066.pdf`), **the values are
offset by one position across the TAS-201/TAS-202 span.** The PDF's rate table was read by glyph coordinate,
so this is column-position evidence rather than an eyeball of a text dump:

| Column (PDF header x-position) | **PDF says** | **Airtable holds** | |
|---|---|---|---|
| `LMI (impacts)` @ 229 | `9` | `9` | ✅ |
| `SMI (impacts)` @ 259 | *(blank)* | `10` | ❌ |
| `# Dials` @ 283 | `10` | `Full` | ❌ |
| `Static / Type` @ 308 | `Full` | `+60/60` | ❌ |
| `DP (+) (PSF)` @ 354 | `+60/60` | `9` | ❌ |
| `Water (PSF)` @ 396 | `9` | *(blank)* | ❌ |
| `Forced Entry (*)` @ 424 | *(blank)* | *(blank)* | ✅ |
| `Cyclic (PSF)` @ 469 | `+60/60` | `+60/60` | ✅ |
| `Impact` @ 507 | *(blank)* | *(blank)* | ✅ |

The pattern is unambiguous: **the blank `SMI` cell was dropped instead of being preserved as a positional
blank**, so every value from `# Dials` onward slid one column to the left until the run of blanks at
`Water` / `Forced Entry` re-anchored it. The extractor is reading *values in order* rather than *values by
column*.

**Why this matters more than a bad demo record.** These are the numbers LabOS reads to *drive the rig*. Taken
at face value, this record instructs LabOS to run the TAS-202 structural test at **9 PSF instead of +60/60** —
roughly a seventh of the specified design pressure — and, if the specimen holds, to write back `Passed`. That
is a false pass on a hurricane-rated sliding glass door, produced by a system working exactly as built. The
same shift also loses the water-infiltration requirement entirely.

**This is not a LabOS-side bug and LabOS cannot defend against it**, because every shifted value is
individually plausible: `9` is a perfectly legal DP. Only the PDF proves it wrong.

Requests to the Airtable team, in priority order:

1. **Fix the extractor to be column-positional**, so a blank cell consumes its slot.
2. **Re-extract IFET-26-0066** and any other job already loaded this way, and tell us how many are affected.
3. **Add a validation pass** before a job is released to testing — at minimum, unit-plausibility bounds on the
   pressure fields, which would have caught `DP = 9`.
4. Until 1–3 land, **LabOS should not read requirements from Airtable for a live test.** W3 can be *built*
   against this structure; it must not be *trusted* with a rig until the extraction is corrected.

---

## 6. What changed on the LabOS side today

All in `ifet-management` @ `feature/labos-airtable`. Still stdlib-only, still no production image rebuild.

| Change | Why |
|---|---|
| `contract.py` — `Field` gains `option_wire` + `wire_option()` | Option **values** now translate at the wire boundary exactly as field **names** already did via `wire_name`. LabOS keeps one internal vocabulary; the base's spelling wins on the wire. |
| `Test Result`: `Pass`→`Passed`, `Fail`→`Failed` | §10.16, closed against the live base |
| `Test Status`: `Aborted`→`Abborted` | §10.18 — their spelling, verbatim, because a single-select accepts nothing else |
| `envelope.py` — `_check_option` validates twice | LabOS option → translate → live option. A caller cannot pass *their* spelling (one direction only, so there is one vocabulary inside LabOS), and an option the base lacks fails **locally** rather than as a 422. |
| `tests/fake_schema.py` — the three select sets transcribed verbatim from the live base | The fixture now encodes reality, including both surprises |
| tests: 95 → **98**, all passing | Adds §10.17 as an executable fact: four of five test types are refused against the live `Test Type` set |

Schema snapshots for both bases are committed under `docs/airtable-schema/` for the §9 deploy-time diff.

---

## 7. What we need on Monday's call

Ordered by what blocks the most:

1. **The extraction shift (§10.19)** — confirm, fix, re-extract, and tell us the blast radius. Nothing that
   reads requirements from Airtable can go live until this is closed.
2. **`Test Type` options (§10.17)** — add `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1`. Without them only
   static load can be written back at all.
3. **`Corrects Attempt ID` + `Correction Reason` (§10.14)** — still absent; still the two fields the JSON valve
   cannot rescue, because automations must *branch* on them.
4. **`Required Value` + `Required Unit` on `Protocol Sections` (§5.1)** — typed requirements, so LabOS is not
   parsing `+60/60` out of free text to decide what pressure to apply.
5. **`Test Date` (§10.13 / §10.20)** — a `date` field cannot express duration. Either restore the start/end
   pair, or confirm `Test Date` means *start* and duration lives in JSON.
6. **Confirm the write model (§10.21)** — LabOS writes only `LabOS Raw Data Table`; their automation rolls up
   into `Protocol Sections`.
7. **`Abborted` (§10.18)** and **attempt-ID format (§10.22)** — small, but both cause silent breakage.

Once 1 and 2 are settled, LabOS runs verification stages 2–3 (a live upsert round-trip into the testing base),
which is the last thing standing between here and W2.

---

## 8. The message that goes out

> **Status:** ✅ **SENT 2026-08-28** — see the *Sent* stamp at the end of this section. What actually went
> out was a formalised version of this wording:
> **`docs/sent/2026-08-28-labos-airtable-live-base-verification-report.docx`**, kept in the repo as the
> sent record. This section remains the authoritative *wording*; the docx is the authoritative *artifact*.
>
> **Previously:** Written 2026-08-23 for the Monday 2026-08-25 session;
> that slot lapsed without the message going out. Re-framed below for a direct send — the four asks and their
> ordering are unchanged, and were re-verified against both live bases on 2026-08-28 (all four still open).
> This section is the **authoritative wording** — contract §10 owns the item *statuses*, this owns what we
> actually say. Sent record to be stamped below.

**To:** Luis Macias (IFET) · **Cc:** Airtable team
**Subject:** LabOS ↔ Airtable — we've read both bases; one issue to flag before anything goes live

---

Hi Luis,

Thanks for the tokens and for pointing us at the populated proposal data — that was exactly what we needed.
Both tokens work, and we've now connected to both bases and read them end to end.

Apologies for not getting this to you before the slot we'd pencilled in — that one is on me. Everything below
still stands; I re-checked it against both bases this morning.

To be clear about what we did: **we only read.** Every request was a `GET`. We wrote nothing to either base,
including the LabOS Raw Data Table, so nothing has changed on your side. We'll keep it that way until you give
us the go-ahead for the write test described at the end.

Almost everything checked out, and several open questions closed on the spot. But we found one thing that we
think you'll want to look at before anything goes live, so I'll lead with that.

### 1. The requirement values in Airtable don't match the proposal PDF

We cross-checked the IFET-26-0066 records against the proposal PDF you sent. The values are **shifted by one
column**:

| Requirement | Your proposal PDF | Airtable currently holds |
|---|---|---|
| SMI (impacts) | *(blank)* | 10 |
| # Dials | 10 | Full |
| Static / Type | Full | +60/60 |
| **DP (+) (PSF)** | **+60/60** | **9** |
| Water (PSF) | 9 | *(blank)* |

The pattern is consistent: where the proposal has a **blank** cell, the extractor appears to skip it rather
than hold its position, so every value after it moves one column to the left. The blank SMI cell is what
starts it here; the run of blanks at Water/Forced Entry is where it re-aligns.

**Why we're flagging it rather than just working around it.** These are the numbers LabOS reads to drive the
test rig. Taken at face value, this record tells LabOS to run the TAS-202 structural test at **9 PSF instead
of +60/60** — roughly a seventh of the specified design pressure — and, if the door holds, to record it as
Passed. The water requirement disappears entirely.

We can't defend against this from our side, because every shifted value is individually plausible: 9 is a
perfectly legal design pressure. Nothing short of comparing against the original proposal reveals it.

**One more thing worth knowing: this has already reached a completed record.** On this same job, the
`SMI (impacts)` section holds `Value = 10` with `Result = Passed` and `Status = Completed` — but the proposal
has no SMI value at all; the 10 belongs to `# Dials`. So it isn't only a risk to future tests: there is a
result already recorded as passed against a requirement that isn't in the source document. That's why we'd
like to know the scope of the re-extraction rather than just the fix.

What we'd ask:

1. Make the extraction **column-positional**, so a blank cell keeps its slot.
2. **Re-extract IFET-26-0066**, and let us know how many other jobs were loaded the same way — including any
   where testing has already been marked complete, since those may need their results reviewed.
3. Add a **sanity check** before a job is released for testing — even simple range limits on the pressure
   fields would have caught `DP = 9`.

Until that's done, we won't read requirements from Airtable to drive a live test. We'll keep building against
the structure — that part is fine, see item 3 — but we won't put it in front of a rig.

### 2. Test Type only has one option

The `Test Type` field in the LabOS Raw Data Table currently offers only **Static Load**. Airtable rejects any
value that isn't in the list, so at the moment we can only write back static-load results.

The IFET-26-0066 job itself needs four more: TAS-201 impact, TAS-202 forced entry, TAS-203 cyclic, and
ANSI Z97.1. Could you add these options to the field, in both bases?

- `Cycles`
- `Impact`
- `Forced Entry`
- `ANSI Z97.1`

### 3. The read side — good news, plus one request

We now understand how requirements are structured: one Protocol Section record per requirement, with the name
in `Section Name` and the value in `Value`. **That works for us** and unblocks the requirements-reading work.

One request that would make it considerably safer: `Value` is free text, so it holds `9`, `Full` and `+60/60`
in the same column, and the unit is carried in the section's *name* rather than in a field. That means we have
to parse the numbers back out of text, and a small wording change on your side could silently change how a
test runs.

If you could add two fields to Protocol Sections — **`Required Value`** (number) and **`Required Unit`**
(text or single-select) — we'd read those and treat `Value` purely as the human-readable display string.
Nothing you do today would need to change.

### 4. Smaller items

- **`Test Status` is spelled `Abborted`** in both bases. We're sending your spelling so nothing breaks, but if
  you rename the option to `Aborted` we'll follow — renaming in Airtable keeps existing values intact.
- **`Test Result`** — your guide was right and our spec was wrong. We've changed our side to send
  `Passed` / `Failed`.
- **`Corrects Attempt ID` and `Correction Reason`** (from our earlier list) are still the two fields we most
  need. Without them, a corrected result and a genuine retest look identical in the data, so any roll-up that
  counts attempts or works out a pass rate will be wrong in one of the two cases — and it will look right.
- **`Test Date` is a date-only field**, so a test's start and end time can't both be recorded and duration
  can't be derived. We're keeping both in the JSON field for now; flagging it in case you want it reportable.
- **Attempt IDs** — your sample row uses `001`. Ours are UUIDs, because two rigs running at once would collide
  on a simple counter. The sequence number lives in `Latest LabOS Attempt Number` instead.
- **Please rotate both tokens** once we're through acceptance testing. They came through email, so it's worth
  replacing them as a matter of routine.

### What we need from you next

We're ready for the last verification step: **a single test write** into the LabOS Raw Data Table in the
**testing** base (`app4oXS3Kd5IKWgJ7`) — one record, written and then updated, to confirm the round-trip and
the duplicate-prevention behave as expected. We won't touch the production base. **We just need your OK to run
it** — a one-line reply is enough, it doesn't have to wait for a call.

Could we also put a new slot in the diary for the testing session, since the last one lapsed? Any time that
suits you works for us.

Suggested order when we do talk, most-blocking first:

1. The extraction issue (item 1) — the only one that affects test results
2. Test Type options (item 2) — blocks writing back anything but static load
3. Approval for the test write
4. The field requests in items 3 and 4

Happy to walk through any of it live, or send the detailed findings if your Airtable developers would like
them.

Best,
Abdelrahman
LabOS

---

> **Sent:** ✅ **2026-08-28**, as *LabOS – Airtable Integration: Live Base Verification, Data Integrity
> Findings, and Requested Actions* (`docs/sent/2026-08-28-labos-airtable-live-base-verification-report.docx`),
> to the IFET / Airtable integration team.
>
> **What the sent version added over the wording above** — all improvements, recorded so the contract and the
> next message stay consistent with what they actually received:
>
> 1. **A P0/P1/P2 priority table with a *Requested from* column**, separating the two integration blockers
>    from the contract-hardening items and naming who each is asked of.
> 2. **`Test Type` options requested in *both* bases**, not just testing — this section had not said so.
> 3. **A new ask: how is `+60/60` represented** once `Required Value` is numeric? Now contract **§10.23**.
>    It is the one genuinely new item, and it is blocking: unresolved, we are back to parsing pressures out
>    of free text.
> 4. **Confirmation that testing and production share table *and* field IDs**, so one field-ID binding
>    carries across environments — a real cutover-risk reduction that was in the probe data but had not been
>    stated as a conclusion.
> 5. **Explicit asks** to confirm Airtable automation owns the roll-up into `Protocol Sections` (§10.21) and
>    that `LabOS Attempt ID` is opaque UUID text (§10.22).
> 6. **"~15% of the required pressure"** rather than "roughly a seventh" — same number, stated the way the
>    reader will check it.
>
> **Also sent, separately:** the project-status page for IFET management —
> *📌 LabOS × Airtable — Project Status & Revised Timeline (2026-08-28)*,
> `3ca57bad43d581e5b28ece91494a45a7`.
