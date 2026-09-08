# Product owner update — WhatsApp draft, 2026-09-08

**Status: DRAFT, NOT SENT.** Two parts, sent together:

1. **The message** — written to be pasted into WhatsApp as-is: short paragraphs, no formatting, scannable on
   a phone. Copy the block below.
2. **The sheet** (§"The sheet to confirm") — the three new tests field by field, with four questions that
   need a yes or no. Send it as its own message or a one-page PDF; it is not WhatsApp-shaped and must not be
   pasted into the block.

---

Hi — quick update on LabOS ↔ Airtable.

The backend for the three manual tests you asked for is built and tested: Impact, Forced Entry and ANSI Z97.1. The API documentation our UI developer needs to start the screens is written and in the repository — the screens themselves are their next piece of work, not done yet.

Impact records each impact separately — impact 1, 2, 3 — each with its own pass/fail and its own photos. Forced Entry and ANSI are pass/fail with notes and photos. None of them touch the rig hardware, so there's no firmware change and no risk to the two production systems.

I'm sending a one-page sheet alongside this with the exact fields for each of the three — what comes from the proposal automatically, what the operator types, and what reaches Airtable. Worth ten minutes of your time to confirm before the UI screens get built, because changing a field after the screens exist costs a lot more than changing it now. There are four specific questions on it.

On the Airtable side: we've made all the schema changes in the Testing base only — 17 fields, production untouched. The document explaining every change and why is ready to go to the Airtable team, along with answers to the three questions they raised this week.

Two things worth flagging early rather than at demo:

1. Loading sequences don't need to come from Airtable — LabOS already calculates all 14 stages from the design pressures. That's less work for everyone, but it's different from the flow you described.
2. We're not sending deflection readings or max pressure yet. The gauges aren't calibrated to a real unit, so we'd be sending numbers we can't stand behind. Fixable, but it needs bench time.

One ask: can we get the test rig back online? It's been down since late July. It isn't blocking us right now — the manual test backend is built and tested against a local database, and the Airtable schema work is verified against the live Testing base — but the piece that actually sends results to Airtable is still being built, and before any of it goes to the production systems we need to prove it against real sensors and real gauges. Getting the rig back now means the go-live is a scheduled window rather than a first attempt.

Nothing is deployed yet. Happy to walk through any of it whenever suits.

---

## The sheet to confirm — the three new tests, field by field

**Send this with the update, as its own message or a one-page PDF. Not part of the WhatsApp block.** The
point is confirmation before the UI screens are built: every field below is already in the database and the
API, so a correction now is a schema edit, and a correction after the screens exist is a schema edit plus a
UI rewrite plus a migration against real rows.

Three columns matter throughout: **from the proposal** means LabOS fills it in and the operator cannot
mistype it; **operator** means it is typed at the rig; **to Airtable** means it leaves LabOS.

---

### 1. Impact — LMI and SMI

Requirement codes `IMPACT_LMI` and `IMPACT_SMI`. **One test type, not two** — large and small missile are
the same procedure with a different missile, so the missile is a field and not a separate test.

| Field | Where it comes from | Notes |
|---|---|---|
| Missile | **From the proposal** (`Missile Type`) | e.g. *Large Missile D*. Free text — the standard's set is open, so LabOS does not invent a dropdown |
| Missile weight | **From the proposal** (`Missile Weight`) | pounds. A requirement, never a measurement: LabOS never writes an achieved weight back |
| How many impacts | **From the proposal** (`Required Value`) | e.g. 2 impacts. Blank is never read as zero |
| Target velocity | **From the proposal** (`Impact Velocity`) | ft/s. **See question 3 — the operator does not currently see this** |
| Impact number | LabOS | 1, 2, 3 — the ordinal you would say out loud, allocated by LabOS and unique within the attempt |
| Pass or fail, per impact | **Operator** | **Required.** An impact without an outcome is not an impact |
| Photographs, per impact | **Operator** | Attached to that specific impact, not to the test as a whole |
| Achieved velocity, per impact | **Operator, optional** | The protocol normally fixes it; requiring it per impact was retyping, not data capture |
| Location on the specimen | **Operator, optional** | Recorded per impact. **We deliberately did not create an Airtable field for it** — see question 4 |
| Note, per impact | **Operator, optional** | "the third impact cracked the corner" is a sentence someone will need to write |

**What reaches Airtable:** one roll-up `Impact Result`, the overall `Test Result`, and the photographs. The
per-impact breakdown travels in the JSON response, not as separate Airtable columns — Airtable has one row
per attempt, not one row per impact.

**A retest is a new attempt with its own impacts,** numbered from 1 again, linked to the same test. The
previous attempt is never overwritten.

---

### 2. Forced Entry

Requirement code `FORCED_ENTRY`. Pass/fail against a named grade.

| Field | Where it comes from | Notes |
|---|---|---|
| Grade judged against | **From the proposal** (`Required Option`) | e.g. *ASTM F588 Grade 40*. Free text, so an unrecognised grade is displayed and the test is non-executable rather than guessed |
| Pass or fail | **Operator** | The verdict for the attempt |
| Notes | **Operator** | Where failure detail goes — see question 2 |
| Photographs | **Operator** | Attached to the attempt |

**What reaches Airtable:** `Test Result` (Passed / Failed / Inconclusive) and `Notes`. There is no separate
`Forced Entry Result` column — question 2.

---

### 3. ANSI Z97.1

Requirement code `ANSI_IMPACT`. Same shape as Forced Entry, judged against a class.

| Field | Where it comes from | Notes |
|---|---|---|
| Class judged against | **From the proposal** (`Required Option`) | e.g. *Class A* |
| Pass or fail | **Operator** | |
| Notes, photographs | **Operator** | |

**This is not the missile impact test.** ANSI Z97.1 is a bag-drop safety-glazing test and it is kept as a
separate requirement code for exactly that reason — a reader who assumed "impact" meant one thing would
otherwise route it to the wrong procedure.

**What reaches Airtable:** `Test Result` and `Notes`, as above.

---

### Common to all three

| | |
|---|---|
| Attempt number | LabOS. Every attempt is numbered and kept; a retest never overwrites its predecessor |
| Operator name | Declared at the session, snapshotted onto each attempt. **No authentication behind it** — it is a declaration, not a login |
| Start and end time | LabOS, in UTC |
| Verdict, who gave it, when | **Reviewer**, recorded separately from the operator even when it is the same person |
| Requirement snapshot | LabOS freezes what the proposal required onto the attempt, so a later Airtable edit cannot change what a finished test was judged against |
| Rig hardware | **None of the three touch it.** No firmware change, no risk to the two production systems |

---

### Four questions we need a yes or no on

**1. ANSI ordering is not enforced.** ANSI Z97.1 is normally performed first on a specimen. LabOS records
that expectation but does not block the others if it has not been done. A hard block would eventually stop
legitimate work and there is no override in the design. *Is informational-only correct, or do you want it
enforced?*

**2. Forced Entry and ANSI have no dedicated result columns in Airtable.** Both verdicts land in the shared
`Test Result` column, with detail in `Notes` and the JSON. `Test Type` and `Test Result` are both
single-select, so Airtable can still filter and group by them natively. *Is that enough, or does a named
report need `Forced Entry Result` and `ANSI Result` as their own columns?*

**3. The target impact velocity is read but never shown.** It comes across from the proposal and is frozen
onto the attempt, so it is in the record — but it does not appear on the test the operator is looking at.
*Does the operator need to see the target velocity at the rig?*

**4. Impact location has no Airtable field, deliberately.** LabOS records where each impact landed, but we
did not create an `Impact Locations` field on the Airtable side: location is an observation per impact, not a
requirement, and the shared Airtable view is becoming the schema production is built from — an unwanted
field there is much harder to remove than to add. *Confirm location stays a LabOS-side observation.*

**One more, from the requirement side rather than these three tests:** the proposal's `Static / Type` value
(`STATIC_PROGRAMME`, e.g. *Full*) is read and validated but changes nothing — LabOS derives the same
six-stage static programme regardless. If a proposal ever specifies a different programme, LabOS would run
the full one anyway without saying so. *Is `Full` the only static programme in practice?* If it is not, we
should make LabOS refuse the others out loud rather than ignore them.

## Notes for us, not for sending

**Why the test node ask is framed this way.** It is genuinely not blocking Track A or Track B — the
disposable Postgres harness and the simulated rig harness cover everything up to a real deploy. Claiming it
blocks us would be false and would also invite "so what have you been doing". Framing it as *needed before
go-live* is both true and a stronger request.

**One thing to settle when the node comes back:** its config points at the **production** broker and API
(`10.1.10.185`), so a rig on the fleet is not an isolated environment — its trials land in the production
database unless the route is gated. That needs deciding before it is switched on, not after.

**The two divergences are deliberately one line each.** Both are engineering decisions with reasons, and
neither is a WhatsApp conversation. The point of raising them here is only that he hears them from us first.

**Why the sheet exists, and why now.** Every field on it is already in the database and the API, and the UI
developer's next piece of work is the screens for exactly these three tests. So this is the last moment when
a correction is a schema edit rather than a schema edit plus a UI rewrite plus a migration against real
rows — `missile_impact_tests` alone already carries 39 tests and 114 shots in production.

**The four questions are the ones where we made a call he may not want.** Not a survey: ANSI ordering is
unenforced, the two manual verdicts share `Test Result`, the target velocity is invisible to the operator,
and impact location is deliberately absent from Airtable. Each is defensible and each is reversible now.
The `STATIC_PROGRAMME` one is added last because it is about the requirement side rather than these three
tests, and the honest answer is that LabOS currently ignores a value it reads.
