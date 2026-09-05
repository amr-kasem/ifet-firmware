# Design decisions awaiting your approval

**Date:** 2026-09-06 · **Status:** `implementation PAUSED pending this review`
**Source:** `integration-design-2026-09-05.md` · `field-register-2026-09-05.csv`

> Eight decisions. **A1 is the one to read first** — it is structural, it revises work already built, and
> every uniqueness constraint depends on it. A2–A4 are consequential and reversible-but-costly. A5–A8 are
> judgement calls where I have a recommendation and no strong stake.
>
> Nothing further is being implemented until these are settled. The outbox commits stand as groundwork; see
> §"What is already built" below for exactly what that commits us to, which is less than it looks.

---

## A1 — Programme run vs stage: what an Airtable attempt row *is* ⚠️ **structural**

**The decision.** One Airtable row per **programme run**, not per stage — via a new `test_programme_runs`
entity. `labos_test_id` identifies the programme, `labos_attempt_id` one run of it.

**Why it came up.** A LabOS `StaticTest` / `CyclicTest` row is not a test, it is a **stage** of a derived
programme. Verified in production 2026-09-05:

| | min | avg | max | `preset` |
|---|---|---|---|---|
| static stages per project | **6** | 6.43 | 9 | 498 / 508 |
| cyclic stages per project | **8** | 8.03 | 9 | 632 / 634 |

One `DP (+) (PSF)` Protocol Section expands into **six** stages. So section : stage is 1 : 6.

**Why I recommend it.** Their `Protocol Section` carries a *singular* `LabOS Attempt ID` and a
`Latest LabOS Attempt Number` — the table is shaped for one result per requirement line. Six stage rows would
answer none of the operational questions Airtable exists to answer without obliging them to build a roll-up,
and roll-ups are theirs by agreement. It is also the same call already made for impact shots: one attempt,
many children, detail in the JSON valve.

**What it costs.** It **revises P1's mapping** — `envelope_values()` would map from the run, not from a trial.
Cheap now (nothing deployed), expensive after. It also adds an entity and a migration.

**The alternative,** for completeness: one row per stage trial, which is what P1 currently builds. Keeps P1
untouched; produces ~7× the rows; makes `Attempt Number` ambiguous between stage index and retry; leaves
Airtable unable to answer "did static load pass" without work on their side.

**Needs your call because** it is the only decision here that invalidates existing work, and because it
changes what our counterparty sees per test.

---

## A2 — `Max Pressure Achieved` and `Measured Value` are omitted (gate G4)

**The decision.** Both are left out of the payload; the envelope raises if anything populates them.

**Why.** The firmware → Management trial payload is *exactly one field*, `deflections[]` — no pressure, no
duration, no cycles, no timestamps. And static pressure is driven **open-loop from a browser slider**, so the
configured setpoint is not an achieved value.

**The alternatives you could direct instead:** (a) a firmware change to report achieved pressure — real work,
needs a rig; (b) an agreed derivation, e.g. send the setpoint and label it as such; (c) accept the omission
indefinitely.

**My recommendation: (c) now, (a) when a rig is available.** Publishing a setpoint under a field named
"Achieved" is the kind of quiet inaccuracy that survives into a report.

**Needs your call because** it is a visible gap in what we deliver, and the customer may expect that field.

---

## A3 — Deflection stays entirely local (gate G1)

**The decision.** `Deflection Value` and `Deflection Unit` omitted, and the per-gauge readings are **not**
carried in the JSON valve either, under any name.

**Why.** `max_deflection` spans −1280.91 → 1288.86. The values have already been multiplied by 0.0393701 and
rounded, so they are neither calibrated deflections nor raw counts — I tried two names for them and both were
wrong. Publishing a number we cannot describe is worse than not publishing it.

**The alternative:** carry them in the JSON valve under an explicitly hedged key, preserving evidence in their
base at the cost of putting an untrusted number on the wire.

**My recommendation: keep it local.** But this is genuinely arguable and you have already ruled once in this
direction — flagging it so the ruling is on the record rather than inherited.

---

## A4 — Corrections are immutable; a correction is a new attempt

**The decision.** A recorded verdict is never edited — `verdict_at` set once, enforced in the database. A
correction mints a **new attempt** carrying `Corrects Attempt ID`, and the corrected row is unchanged
afterwards. **No grace window** for a mis-click.

**Why no grace window.** A rule that depends on how long ago something happened, or on whether a network call
had completed, is a rule nobody can audit.

**What it costs.** An operator who mis-clicks a verdict creates a permanent extra row. In exchange, no
recorded result is ever silently altered.

**Needs your call because** it is a lab-workflow cost, not only an engineering one.

---

## A5 — Requirements completeness warns; execution is what blocks

**The decision.** `Cyclic present ∧ DP absent` surfaces a warning at specimen selection, but the actual
safeguard is that the backend **refuses to start a pressure-driven test** without an inward/outward pair whose
provenance is `proposal` or `operator`. An Airtable-sourced pair is display-only while §10.19 is open.

**Recommendation: as stated.** Blocking selection outright would stop testing on a defect upstream of us;
blocking *execution* stops the thing that actually matters.

---

## A6 — Unrecognised shapes are non-executable

**The decision.** An unknown `Section Name`, or a `Requirement Kind` we do not implement, is displayed and
recorded but cannot start a test. No best-effort parsing.

**Recommendation: as stated** — this is your rule and I think it is the right one. Noted here only so it is
approved rather than assumed.

---

## A7 — Vocabulary at the API boundary

**The decision.** Keep the database names (`ProjectParent`, `Project`) and speak Airtable's vocabulary at
every API path: `/airtable/projects` returns ProjectParents, `/airtable/specimens` returns Projects.

**Recommendation: as stated.** Renaming the tables is a migration plus UI churn for no functional gain; the
collision is vocabulary, and the boundary is the cheapest place to fix it. The risk is a future reader
confusing the two, which is why the mapping is stated at the top of the register.

---

## A8 — Water infiltration stays out of scope

**The decision.** `Water (PSF)` is a TAS-202 section and LabOS already runs it as a 900 s static hold at
0.15 × inward DP — but it is **not one of the five test types** and is excluded from this expansion.

**Recommendation: confirm the exclusion explicitly**, so it is a decision rather than an oversight. It is a
sixth workflow and would widen the milestone.

---

## What is already built, and what it commits us to

`ifet-management` `d61f6f5` — `app/sync/{outbox,state,worker}.py` and 23 tests. **Not wired into `main.py`,
no migration, no container, nothing deployed.**

It is safe groundwork because it depends on none of the decisions above. Its full import list is
`sqlalchemy`, `data.models.Base`, and `airtable.errors` — no `envelope`, no `mapping`, no `contract`, no
`TestResult`. The payload is opaque JSON and `attempt_id` is an opaque string, so **A1 does not reach it**:
whether that id names a stage trial or a programme run, the queue behaves identically.

What it *does* assume, and what you are therefore also approving by letting it stand:

- the four-phase write model — `create` → `terminal` → `verdict` → `attachment`;
- per-attempt FIFO ordering with head-of-line blocking scoped to one attempt;
- park-never-drop on repeated failure;
- status served by report-api from persisted state, with queue depth counted at read time.

**The sequencing rule I would adopt going forward:** the transport layer can be built against open gates;
nothing that reads the field register can. `test_programme_runs`, the envelope changes, the mirror and the
endpoints all sit above the register and wait for this review.

---

## Also awaiting your review, not a decision

`../correspondence/airtable-team-questions-2026-09-06.md` — **drafted, not sent.** Our three answers, ten
questions that need them, and a paste-ready reply. The 2026-08-31 draft is marked superseded with its text
preserved.

Sending it is what starts G2, G3 and G5 moving; nothing external progresses until it goes.
