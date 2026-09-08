# Product owner update — WhatsApp draft, 2026-09-08

**Status: DRAFT, NOT SENT.** Written to be pasted into WhatsApp as-is: short paragraphs, no formatting,
scannable on a phone. Copy the block below.

---

Hi — quick update on LabOS ↔ Airtable.

The backend for the three manual tests you asked for is built and tested: Impact, Forced Entry and ANSI Z97.1. The API documentation our UI developer needs to start the screens is written and in the repository — the screens themselves are their next piece of work, not done yet.

Impact records each impact separately — impact 1, 2, 3 — each with its own pass/fail and its own photos. Forced Entry and ANSI are pass/fail with notes and photos. None of them touch the rig hardware, so there's no firmware change and no risk to the two production systems.

On the Airtable side: we've made all the schema changes in the Testing base only — 17 fields, production untouched. The document explaining every change and why is ready to go to the Airtable team, along with answers to the three questions they raised this week.

Two things worth flagging early rather than at demo:

1. Loading sequences don't need to come from Airtable — LabOS already calculates all 14 stages from the design pressures. That's less work for everyone, but it's different from the flow you described.
2. We're not sending deflection readings or max pressure yet. The gauges aren't calibrated to a real unit, so we'd be sending numbers we can't stand behind. Fixable, but it needs bench time.

One ask: can we get the test rig back online? It's been down since late July. It isn't blocking us right now — the manual test backend is built and tested against a local database, and the Airtable schema work is verified against the live Testing base — but the piece that actually sends results to Airtable is still being built, and before any of it goes to the production systems we need to prove it against real sensors and real gauges. Getting the rig back now means the go-live is a scheduled window rather than a first attempt.

Nothing is deployed yet. Happy to walk through any of it whenever suits.

---

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
