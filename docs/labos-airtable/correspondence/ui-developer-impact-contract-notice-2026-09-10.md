# UI developer — Impact contract is changing, 2026-09-10

**Status: DRAFT, NOT SENT.** Send today. The Impact screen is the developer's current piece of work,
which is what makes this urgent rather than tidy.

**Why it goes now and why it is worded as it is.** The change is *decided*, not *built* — the finish-gate
refusal is TA7. We have just had to correct the product owner for calling Impact "implemented" a day
before it was. The same sentence must not be written to the UI developer. So this says **decided, not yet
live**, and `MANUAL_TESTS_API.md` carries the same framing: the current behaviour stays documented as
current, and the coming fields are in a clearly-marked forward notice that is deleted when TA7 lands.

Nothing in the API has changed today. No route behaves differently.

---

## The message

Quick heads-up before you go further on the Impact screen — the requirement model changed yesterday and
I'd rather you heard it now than rebuilt the form later.

**What changed.** Impact requirements were going to arrive from Airtable as *Missile Type*, *Missile
Weight* and *Impact Velocity*. The product owner has withdrawn all three. Instead the operator picks one
**Impact Classification** in LabOS, and that gets published back to Airtable with the result.

**Two new fields on the impact test:**

- **Impact Classification** — exactly three values: `SMI`, `LMI Level D`, `LMI Level E`
- **Target Impact Velocity** — a number in ft/s, entered by the operator

**Both are required before an Impact attempt can be completed** — not when the test is created. So
`POST /projects/{pid}/impact-tests/` stays valid with `{}`, and the form needs a way to set both before
the operator reaches finish. Aborting an attempt won't require them.

**Careful with the two velocities.** Target Impact Velocity is a per-*test* value the operator enters.
`shots.velocity` is the achieved velocity of an individual impact, recorded per shot — that one is
unchanged and stays where it is. They are different fields and shouldn't share a control.

**Nothing else about Impact moves.** Two-step start-then-finish, one attempt per impact, `shot_number`,
`Impact Result`, the photograph requirement, and impact location on the shot are all exactly as they are.

**None of this is live yet** — no route behaves differently today, and there's no new validation error to
handle. It's the next change coming, not something to code around now. I've put the detail in
`MANUAL_TESTS_API.md` under §7 as a marked "not yet implemented" notice, and I'll tell you when it lands
and delete the notice.

The one thing worth doing now is leaving room for the two fields, so the layout doesn't have to be redone.

---

## Notes for us, not for sending

**Line 223 of `MANUAL_TESTS_API.md` was actively wrong** — it told them `missile` / `missile_weight` come
from `Missile Type` / `Missile Weight`. Struck through rather than deleted, so a developer who already
read it sees that it changed rather than wondering whether they misremembered.

**The `null`-handling bullet in §8 was extended rather than replaced.** `missile` and `missile_weight`
were nullable "now"; they are nullable **permanently** after TA7, as history-only fields. That is a
different statement and it affects whether they write a fallback.

**No `400` is documented.** It does not exist yet. Documenting it would be the "implemented" mistake in
miniature, and they would build error handling for a response the server cannot currently produce.
