# Airtable team's three questions — answer, and the agenda for tonight

**Author:** Abdelrahman · **Date:** 2026-08-31 · **Epic:** IFET-32 · **Status:** answer drafted, meeting tonight
**Trigger:** the Airtable team's reply to the 2026-08-28 verification report
(`correspondence/sent/2026-08-28-labos-airtable-live-base-verification-report.docx`).

> **What this document is.** The authoritative *wording* of our answer to their three questions, plus the
> agenda for tonight's call. Item **statuses** stay owned by contract §10 — this document is a view of it.
> The read-side field spec in §2 is a **proposal**, not yet agreed; when they accept it, it graduates into
> contract §9 and §10.3 / §10.15 / §10.23 close together.

---

## 0. The big picture in six lines

- **The five-day blocker cleared on 2026-08-28, and they replied within one working day.** Their response
  time has never been the problem; ours was.
- **Their message is better news than it looks.** Q1 hands us the read-side specification to write — the item
  that has been the critical path since 2026-07-23 (§10.3). They are asking us to define it.
- **Two of their three points we accept outright** (retest row model, `Test Date` → dateTime). Each closes an
  open item: §10.20 fully, §10.13 partially.
- **One point we have to push back on**, with the reason on the record: replacing `Corrects Attempt ID` with
  a shared `LabOS Test ID` does not carry the same information (§10.14). We already send the shared Test ID.
- **Their message does not touch the two P0 items** — the extraction shift (§10.19) and the missing
  `Test Type` options (§10.17). Tonight's job is to not let the schema conversation absorb them.
- **Nothing on our side is waiting on them except the one test write.** 132 tests green, stage-3 script
  dry-run verified, deploy runbook written. The build continues regardless (roadmap R1–R3).

---

## 1. Their message, verbatim

> **@Mariam**
> A few quick clarifications before we finalize the schema:
>
> 1. **Protocol Sections:** Please confirm how you want Required Value represented in a machine-readable
>    format, considering values may contain positive/negative numbers, ranges, symbols, and special
>    characters. Also, please specify the unit required for each protocol section.
> 2. **Retests:** Each attempt will create a new record with a unique LabOS Attempt ID and updated Attempt
>    Number, while Project ID, Mock-Up ID, Test Protocol ID, and Protocol Section ID remain the same. Instead
>    of Corrects Attempt ID, we'll use the same LabOS Test ID for re-attempts. Please confirm this works for
>    you.
> 3. **Test Date:** We'll change Test Date to include date and time, using the format:
>    `2026-08-04T19:00:00.000Z`
>
> Please confirm these points so we can proceed. Thanks!

### How it maps onto contract §10

| Their point | Contract items it touches | Our position |
|---|---|---|
| **1** — `Required Value` machine-readable + units | **§10.3** (read structure, longest-open) · **§10.15** (`Required Value`/`Required Unit`) · **§10.23** (`+60/60`) · **§10.24** (unit vocabulary) | **Accept the invitation and specify.** §2 below is the spec. Four items close together. |
| **2** — retest = new row, shared Test ID replaces `Corrects Attempt ID` | **§10.14** (blocking) · §2 / §3.1 of the contract | **Row model: confirmed, it is already what we do.** The substitution: **decline, with the cost stated.** |
| **3** — `Test Date` becomes a dateTime with ms, UTC | **§10.20** (date vs dateTime) · **§10.13** (start/end collapse) · §10.8 (two-write lifecycle) | **Accept.** Closes §10.20. §10.13 survives it — one instant still cannot hold both ends. |

---

## 2. Answer to Q1 — the read-side specification

Their framing is worth answering directly: *values may contain positive/negative numbers, ranges, symbols and
special characters.* That is true of the **display string**, and it is exactly why a single field cannot be the
machine-readable one. The principle:

> **Numbers go in number fields. Notation stays in `Value`. The shape is declared, never inferred from
> punctuation.**

`+60/60` is not a value with symbols in it — it is *two* values in one cell, rendered in proposal notation.
Any scheme that keeps them in one cell puts LabOS back to parsing text to decide what pressure to put on a
specimen, which is the failure mode §10.15 exists to remove.

### 2.1 Fields requested on `Protocol Sections` (`tblqpvuJlSdkeS9PS`)

`Value` is **unchanged** and stays the human-facing display string. Once these exist, **LabOS never parses
`Value` again.**

| Field | Type | Populated when | Notes |
|---|---|---|---|
| `Requirement Kind` | single select | always | `Magnitude` · `Directional Pair` · `Count` · `Enum` · `Not Applicable`. Declares which fields below to read. |
| `Required Value` | number | `Magnitude`, `Count` | Signed. A genuine zero is `0`; absent is **blank**. |
| `Required Value Inward` | number | `Directional Pair` | Positive magnitude, inward / positive pressure. `+60/60` → `60`. |
| `Required Value Outward` | number | `Directional Pair` | Positive magnitude, outward / suction. `+60/60` → `60`. |
| `Required Unit` | single select | any kind carrying a number | Vocabulary in §2.3. Blank for `Enum` / `Not Applicable`. |

Five fields, four of them numbers or selects. Nothing that exists today changes type or loses data.

**Why `Requirement Kind` earns its place.** It is the field that makes the data self-describing. Without it,
LabOS infers the shape from `Section Name` — so the day someone adds or renames a section, our parser is
guessing again, silently. With it, a mismatch between the declared kind and what the fields hold is a *loud*
validation failure on our side before a rig moves.

**Ranges.** We have not seen a true low/high range in the data — TAS-203 cyclic `+60/60` is the same
directional form as TAS-202 static, so `Directional Pair` covers it. If a real range appears, tell us and we
will add `Required Value Min` / `Max` rather than overload the pair.

**Blanks must stay blank.** A requirement that does not apply must be an empty field, distinguishable from
`0`. `Water (PSF)` blank and `Water (PSF) = 0` are different statements, and one of them is a test.

### 2.2 If they would rather add one field than five

Equivalent for us, cheaper for them, worse for them downstream: a single long-text
`Required Testing Parameters (JSON)` per section, shape supplied by us —
`{"kind":"directional_pair","inward":60,"outward":60,"unit":"PSF"}`. We will build against either.

**The trade-off to state plainly:** JSON in a long-text field cannot be filtered, sorted, grouped or rolled up
in Airtable, and their own interface pages cannot show it. The five typed fields serve their side as well as
ours. **Recommend the typed fields; accept the JSON if they prefer.**

### 2.3 The unit answer — kind and unit per section

Their second half asks us to state the unit for each protocol section. Read as: *one unit per section record,
determined by the parameter the section represents.* The table below is keyed on the `Section Name` values
observed live on 2026-08-23.

> **Safe to build on.** These names come from the proposal's column **headers**, which the extraction defect
> (§10.19) does not disturb — it shifted the **values**, not the headers. So the mapping is sound even though
> the sample data is not.

| `Section Name` | `Requirement Kind` | `Required Unit` | Example (correct, per the proposal PDF) |
|---|---|---|---|
| `LMI (impacts)` | `Count` | `impacts` | `9` |
| `SMI (impacts)` | `Count` | `impacts` | *(blank — no SMI requirement on this job)* |
| `# Dials` | `Count` | *(none)* | `10` |
| `Static / Type` | `Enum` | *(none)* | `Full` |
| `DP (+) (PSF)` | `Directional Pair` | `PSF` | inward `60`, outward `60` |
| `Water (PSF)` | `Magnitude` | `PSF` | `9` |
| `Forced Entry (*)` | `Enum` | *(none)* | *(blank)* |
| `Cyclic (PSF)` | `Directional Pair` | `PSF` | inward `60`, outward `60` |
| `Impact` (ANSI Z97.1) | `Enum` | *(none)* | *(blank)* |

**Unit vocabulary — the exact option list**, to be used identically for `Required Unit` here and for `Unit` /
`Deflection Unit` on the raw table:

```
PSF · PSI · in · mm · lbf · N · cycles · s · impacts
```

Stored value is the short form. Display (`Inches`, `pounds per square foot`) belongs to the interface, not the
column. **This is the moment to close §10.24:** their own sample row `recxZWiVa5Wuy0ZV6` writes
`Deflection Unit = "Inches"` where this vocabulary says `in`, and because both fields are live as free text
nothing errors — the column just quietly holds two spellings of one unit. Since they have now asked us to
specify, we specify `in`, and ask that `Unit` and `Deflection Unit` become **single selects** over this list.
That converts a silent divergence into a loud rejection.

> **Our own contract needs one addition:** `impacts` is not in §4.4's option list. Add it on ratification.

### 2.4 The connection they should hear us make

The typed fields also **contain** the extraction defect, partially. A `DP (+) (PSF)` section declared
`Directional Pair` that arrives holding a single magnitude of `9` is a structural mismatch, and LabOS rejects
it instead of loading a specimen to a seventh of its design pressure.

**Partially, not fully — and this matters.** A wrong number that lands in the right *shape* still passes every
check we can write. So this is a second line of defence, **not** a substitute for the column-positional
extractor fix (§10.19). Both are needed, and the extractor is still the one that gates go-live.

---

## 3. Answer to Q2 — retests

### 3.1 The row model: confirmed

*"Each attempt creates a new record with a unique `LabOS Attempt ID` and an updated `Attempt Number`, while
Project / Mock-Up / Protocol / Section IDs stay the same."*

**That is exactly contract §2 and §3.** No change on either side. And the shared `LabOS Test ID` they propose
is already in every payload we send — §2 defines it as the field that groups attempts of one test instance.
So there is nothing to negotiate there: it is confirmed, and it is not new.

### 3.2 The substitution: we have to decline, and here is the reason

The shared `LabOS Test ID` is not an alternative to `Corrects Attempt ID`. It answers a **different question**.

| Question | Answered by |
|---|---|
| Which attempts belong to the same test? | `LabOS Test ID` — shared. **Already sent.** |
| Is attempt 2 a second real test, or a fix to a mis-recorded attempt 1? | **Nothing, without `Corrects Attempt ID`.** |

Both cases produce the identical row shape their Q2 describes: same four Airtable IDs, same `LabOS Test ID`,
new `LabOS Attempt ID`, `Attempt Number` 2. The physical reality behind them is opposite:

| | **Retest** | **Correction** |
|---|---|---|
| What happened | The specimen **was tested twice**. Two real events. | **One** event, recorded wrongly. |
| Rows in Airtable | 2 rows, **both valid data** | 2 rows, **only the second is true** |
| A correct roll-up must | count both attempts | count **one** — and exclude row 1 |

**The consequence, stated for their side of the boundary.** Any automation that counts attempts, computes a
pass rate, or reports "tests performed" is wrong in one of the two cases — and it will look right. That is the
expensive kind of wrong: it does not fail, it reports.

**The real worked example from this project** (contract §3.1): on 2026-07-09 a rig's pressure sensors were
found to be logging PSI as PSF. A reading already written as `40 PSF` was actually `5760 PSF`. Editing the row
destroys the evidence a report has already cited; a bare new row leaves two contradictory `Passed` results with
no explanation. The only complete answer is a new row that **states what it supersedes** — which is a field, on
the row, that their automation can branch on.

**Also worth saying out loud:** we cannot mark the old row ourselves. It is terminal and locked to us by
contract §3. We can only write a new row declaring what it corrects; marking the old one `Superseded` is
theirs. That split is deliberate — the writer of a record never gets to retroactively alter one — and it is
precisely why the reference has to be a real column rather than something buried in our JSON.

### 3.3 The ask, and two fallbacks — in order of preference

1. **Preferred — two fields on `LabOS Raw Data Table`:** `Corrects Attempt ID` (**plain text**, not a
   computed field, not a link) and `Correction Reason` (long text). Blank on every retest; populated only on a
   correction. A correction of a correction references *its* predecessor, so the authoritative result is the
   row no other row supersedes.
2. **If they will not add a field — one formula field.** We already carry `corrects_attempt_id` inside
   `Complete LabOS JSON Response`. A single Airtable formula field (`REGEX_EXTRACT` over that text) surfaces it
   as something filterable, with no workflow change and no new LabOS work. **Honest caveat:** it is brittle to
   the JSON shape, which is itself unagreed (§10.25) — so this fallback depends on closing that item too.
3. **If neither** — then we record in the contract, and report to IFET, that attempt counts and pass rates
   derived from the raw table are **not trustworthy**, and that the distinction lives only in LabOS. That is a
   defensible decision for them to take with the cost visible; it is not defensible for us to leave implicit.

---

## 4. Answer to Q3 — `Test Date`

**Accepted, and it closes §10.20.** A date-only field could not express a time at all; `dateTime` in UTC with
milliseconds is what we already produce internally. We will send exactly their format
(`2026-08-04T19:00:00.000Z`).

Two things to settle alongside it, both small:

1. **§10.13 survives this change.** One instant cannot record both when a test started and when it finished,
   so duration remains unrepresentable in any column. Two ways forward, either is fine:
   - **Preferred:** add a second dateTime, `Testing End Date`. Duration then becomes filterable, sortable and
     roll-up-able on their side — which is the only reason we keep asking.
   - **Otherwise:** confirm `Test Date` means the **start** instant. We keep end time and `duration_s` in
     `Complete LabOS JSON Response`, and the payload loses nothing — only Airtable's ability to report on it.
2. **Confirm the two-write lifecycle (§10.8)** while we are here, because a single `Test Date` only works
   cleanly if it means *start*: LabOS upserts **twice** per attempt — once at start (`In Progress`, partial
   payload) and once at terminal state (`Completed` / `Abborted`, full payload), both on the same
   `LabOS Attempt ID`, so the second merges onto the first rather than creating a row. The first write is what
   gives them live visibility of a test in progress.
3. **Set the field's time zone explicitly, identically in both bases.** Airtable dateTime fields carry a
   display time zone. We store and send UTC; we would rather that be a stated setting than a default someone
   changes later.

---

## 5. What their message does *not* answer — the agenda for tonight

Their three questions are all schema-shaped. The two items that gate go-live are not, and neither appears in
their message. **Order the call by blast radius, not by their agenda.**

| # | Item | § | Owner | Why it leads |
|---|---|---|---|---|
| **P0** | **Extraction shift** — column-positional fix, re-extract `IFET-26-0066`, and the **blast radius including jobs already marked tested** | §10.19 | Airtable | The only item that can produce a false `Passed` on a hurricane-rated assembly. One already exists (`SMI (impacts)`, `Passed` / `Completed`, against a value the proposal does not contain). |
| **P0** | **`Test Type` options** — add `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1` **in both bases** | §10.17 | Airtable | Minutes of work. Until then four of five test types cannot be written back at all. |
| **P0** | **Approve one test write** into the **testing** base — one record, written then updated | — | Airtable / Luis | Script ready, dry-run verified, production base refused unconditionally. A one-line reply unblocks it. |
| **P1** | Make `Unit` + `Deflection Unit` **single selects** over §2.3's list; settle `in` vs `Inches` | §10.24 | Airtable | Both are free text today; their sample row and our envelope disagree, and neither side errors. Naturally closed by answering Q1. |
| **P1** | **Does anything on their side parse `Complete LabOS JSON Response`?** | §10.25 | Airtable | One yes/no. Decides whose JSON shape wins — and whether §3.3's fallback is viable at all. |
| **P1** | **Confirm the write model**: LabOS writes only `LabOS Raw Data Table`; their automation rolls up into `Protocol Sections` | §10.21 | Airtable | `Protocol Sections` already carries populated LabOS fields. If we are expected to write it, our client allowlist has to be widened deliberately. |
| **P2** | Rename `Abborted` → `Aborted` (a rename preserves cell values) | §10.18 | Airtable | We send their spelling today either way. |
| **P2** | Confirm `LabOS Attempt ID` is treated as **opaque UUID text** — their sample uses `001` | §10.22 | Airtable | A zero-padded counter collides the first time two rigs run at once, which is the normal case. |
| **P2** | `Schema Version` semantics; are `Retest Required` / `Testing Continued` genuinely optional? | §10.26 | Airtable | Decides whether their sample was incomplete or our required-set is wrong. |
| **P2** | **Seed the testing base** with one real job chain (ideally `IFET-26-0066` *after* the fix) | — | Airtable | The testing base is empty, so roll-up/linkage cannot be verified there at all. Same request serves both purposes. |
| **P2** | **Rotate both PATs** after acceptance testing | §10.10 | Airtable | They arrived as plaintext email. |

**Not Airtable's, and still ours to raise with IFET tonight if the room is right:**

- **A maintenance window** for the P0/P1 deploy — nothing is deployed, and the change set grows every week
  (runbook `runbooks/p0-p1-deploy-2026-08-28.md`, read §2 first).
- **The `test` node back online** — it is the only non-production rig. Without it the sync path is first
  exercised on production. Largest unmanaged risk in the plan.
- **Reviewing already-reported results** once the blast radius is known — a quality/business call for IFET,
  not an engineering one. We can supply the list.

---

## 6. What we commit to, so the exchange is not one-directional

- The §2 spec is ours and it is written — they can implement against it tonight.
- **The single test write runs within a day of their OK.** Testing base only; the client refuses the
  production base unconditionally.
- We bind to **field IDs**, not names, so anything they rename later is free; a removal or retype fails loudly
  at deploy rather than silently at test time.
- Results-out (roadmap R1–R3) needs nothing from them beyond that one approval, and continues regardless.
- Standing rule, unchanged and stated again: **no rig is driven from an Airtable requirement value, and no
  LabOS result is written against one, until §10.19 clears.**
- Pilot target **Friday 2026-10-09**. What moves it: the extractor fix past 18 Sep, or `Test Type` options
  past 25 Sep — see `status/revised-roadmap-2026-08-28.md` §2.

---

## 7. The reply — send as-is

> Hi — thanks, and thanks for turning this around so quickly. Answers to all three, and one push-back with the
> reasoning, so you can decide rather than take our word for it.
>
> **1. Protocol Sections — `Required Value`.**
> You are right that the values carry signs, pairs and notation, and that is exactly why we would rather not
> keep them in one cell: `+60/60` is not one value with symbols in it, it is two values in proposal notation.
> If we parse it back out of text, a small wording change on your side silently changes what pressure a rig
> applies. So: **numbers in number fields, notation left in `Value`, and the shape declared rather than
> inferred.**
>
> Five fields on `Protocol Sections`, with `Value` completely unchanged as the human-readable string:
>
> - `Requirement Kind` — single select: `Magnitude`, `Directional Pair`, `Count`, `Enum`, `Not Applicable`
> - `Required Value` — number (signed; for `Magnitude` and `Count`)
> - `Required Value Inward` — number (positive magnitude; `+60/60` → `60`)
> - `Required Value Outward` — number (positive magnitude; `+60/60` → `60`)
> - `Required Unit` — single select
>
> `Requirement Kind` is the one that does the real work: it makes each row self-describing, so when you add or
> rename a section later, we are not guessing at its shape. And please keep genuinely-absent requirements
> **blank** rather than `0` — a blank water requirement and a water requirement of zero are different
> statements.
>
> If five fields is more than you want to add, a single long-text `Required Testing Parameters (JSON)` per
> section works for us too and we will supply the shape. The only reason we prefer the typed fields is that
> they are filterable and roll-up-able on your side; JSON in long text is not.
>
> **Units per section** — one unit per section record, determined by the parameter. Using the section names as
> they are live today:
>
> | Section Name | Kind | Unit |
> |---|---|---|
> | `LMI (impacts)` | Count | `impacts` |
> | `SMI (impacts)` | Count | `impacts` |
> | `# Dials` | Count | — |
> | `Static / Type` | Enum | — |
> | `DP (+) (PSF)` | Directional Pair | `PSF` |
> | `Water (PSF)` | Magnitude | `PSF` |
> | `Forced Entry (*)` | Enum | — |
> | `Cyclic (PSF)` | Directional Pair | `PSF` |
> | `Impact` (ANSI Z97.1) | Enum | — |
>
> The full unit list, which we would use identically on both sides:
> `PSF`, `PSI`, `in`, `mm`, `lbf`, `N`, `cycles`, `s`, `impacts`. Short form as the stored value; long forms
> like "Inches" are a display choice for the interface.
>
> While you are in there — **could `Unit` and `Deflection Unit` on the raw table become single selects over
> that same list?** Both are free text today, and your sample row has `Deflection Unit = "Inches"` where our
> spec says `in`. Free text accepts both, so the column ends up holding two spellings of one unit and nothing
> ever errors. A single select turns that into an error at the first write, which is where we would rather
> find it.
>
> One connection worth naming: typed fields would also have caught the shifted `DP (+) (PSF) = 9` — a
> directional requirement arriving as a single number is a structural mismatch we can reject. It is a second
> line of defence, though, not a replacement for the extraction fix: a wrong number in the right shape still
> passes every check we can write.
>
> **2. Retests.**
> The row model is confirmed exactly as you describe it — new record, new `LabOS Attempt ID`, incremented
> `Attempt Number`, same four Airtable IDs. And the shared `LabOS Test ID` is already in every payload we
> send; that is what it is for, so nothing changes there.
>
> Where we would ask you to reconsider is treating it as a **replacement** for `Corrects Attempt ID`, because
> the two answer different questions. `LabOS Test ID` tells you which attempts belong to the same test.
> `Corrects Attempt ID` tells you whether attempt 2 was a **second real test** or a **fix to a mis-recorded
> attempt 1** — and both of those produce the identical row you described.
>
> That distinction decides how the data should be counted:
>
> - **Retest** — the specimen really was tested twice. Two rows, both valid data. Count both.
> - **Correction** — one test, recorded wrongly. Two rows, only the second is true. Count one, and exclude
>   the first.
>
> So any automation that counts attempts or works out a pass rate is wrong in one of the two cases — and it
> will look right, which is the part that concerns us.
>
> A real example from this project: in July we found a rig logging PSI as PSF, so a result already written as
> `40 PSF` was actually `5760`. We cannot edit the old row — it is terminal, and a report had already cited it
> — so the only honest fix is a new row that states what it supersedes and why. Marking the old row
> `Superseded` is then yours, from that field. We deliberately do not want the ability to alter a record we
> already wrote.
>
> Our ask is two plain fields on the raw table: **`Corrects Attempt ID`** (plain text — not a formula or link,
> since it is a merge/branch target) and **`Correction Reason`** (long text). Both blank on every retest;
> populated only on a correction, which is rare.
>
> If adding fields is awkward, there is a cheaper option: we already include `corrects_attempt_id` inside
> `Complete LabOS JSON Response`, so a single formula field on your side (`REGEX_EXTRACT` over that text)
> would surface it as something you can filter on, with no other change. That does depend on the JSON shape
> being settled — see the question below.
>
> **3. Test Date.**
> Yes — `dateTime` with `2026-08-04T19:00:00.000Z` is exactly right, and it is what we produce internally. Two
> small things to go with it:
>
> - A single instant still cannot hold both start and end, so test duration is not reportable in Airtable.
>   If you can add a second dateTime (`Testing End Date`) it becomes filterable and roll-up-able for you;
>   if not, we will treat `Test Date` as the **start** instant and keep end time and duration in the JSON
>   field. Either is fine — we would just like it decided rather than assumed.
> - Related, and worth confirming: we write **twice** per attempt on the same `LabOS Attempt ID` — once when a
>   test starts (`In Progress`, partial payload) and once when it finishes (`Completed` / `Abborted`, full
>   payload). The second merges onto the first rather than creating a second row. The first write is what gives
>   you live visibility while a test is running. Just confirm that suits you.
> - Could you also set the field's time zone explicitly, and identically in both bases? We store and send UTC,
>   and we would rather that be a stated setting than a default.
>
> **Still open from our side, in the order they matter:**
>
> 1. **The extraction shift** — the column-positional fix, the re-extract of `IFET-26-0066`, and how many other
>    jobs were loaded the same way, *including any already marked tested*. This is the only item that can
>    produce a result recorded as passed against a requirement the proposal does not contain, and one of those
>    already exists on that job.
> 2. **`Test Type` options** — `Cycles`, `Impact`, `Forced Entry`, `ANSI Z97.1`, in **both** bases. Until they
>    exist we can only write back static-load results, and that job needs all five.
> 3. **The go-ahead for one test write** into the **testing** base — one record, written then updated, to
>    confirm the round-trip and the duplicate-prevention. Production untouched; our client refuses it outright.
>    A one-line reply is all we need and it does not have to wait for the call.
> 4. **Does anything on your side read `Complete LabOS JSON Response`?** If yes we will adopt your sample's
>    shape; if it is for human reading only we will keep ours and note that so nobody builds an automation on
>    it later.
> 5. **Just to confirm the boundary:** we write only to `LabOS Raw Data Table`, and your automation rolls that
>    up into `Protocol Sections`. We ask because `Protocol Sections` already has LabOS fields populated on it.
> 6. Smaller ones: renaming `Abborted` → `Aborted` (a rename keeps existing values); treating
>    `LabOS Attempt ID` as opaque UUID text rather than the `001` form, since two rigs running at once would
>    collide on a counter; and — whenever it suits — **seeding the testing base with one real job chain**, since
>    it is currently empty and we cannot verify the roll-ups against it.
>
> Happy to go through any of this on the call.
>
> Best,
> Abdelrahman — LabOS

---

## 8. Sent record

> **Not yet sent.** Stamp here when it goes out, then close the affected items in contract §10 **first** and
> update the views. Per the filing rule, the artifact copy belongs in `correspondence/sent/` and is
> append-only once delivered.
