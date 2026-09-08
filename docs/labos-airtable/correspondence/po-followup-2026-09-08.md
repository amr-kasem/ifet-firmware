# Product owner follow-up — WhatsApp draft, 2026-09-08

**Status: DRAFT, NOT SENT.** A short second message, after
`sent/2026-09-08-po-five-test-approval-request.md`. Copy the block below.

**Why there is a second message at all.** Three things, and none of them can wait for his reply to the
first:

1. The first message told him **Airtable receives deflection data**. It does not and cannot — and the
   Airtable team is being told the opposite in the change document, so the two statements would meet.
2. It asked for *"four small workflow decisions"* and listed three: the list is numbered 2, 3, 4, so
   **ANSI ordering and `STATIC_PROGRAMME` never got asked.**
3. It said Impact was *"implemented"* before the per-impact shape existed. It exists now, which makes the
   correction cheap to state — but he read "implemented" a day before it was true, and he should hear that
   from us.

Keep it short. He reads on a phone, he has already been sent a sheet, and a long correction reads as a
problem rather than as tidiness.

---

Two corrections to what I sent you, and two questions I left out by accident.

**Corrections.** I said Airtable receives deflection data for Static Load — it doesn't, and it can't yet.
The gauges on the rigs were never calibrated to a real unit, so we'd be sending numbers we can't stand
behind. The readings are recorded and kept in LabOS; they just don't go to Airtable until the gauges are
calibrated, which needs bench time. Same story for max pressure, for a different reason — we can read it but
nothing stores it yet. The sheet I sent you says this correctly on the Static Load page; my summary didn't.

And I said the Impact workflow was implemented. The version you specified — one attempt per impact — is
built now, but it wasn't when I wrote that. It's built and tested and not yet deployed, like everything else
in this piece of work.

**The two questions I missed.** My list jumped from 1 to 2, so these never reached you:

**ANSI Z97.1 ordering.** It's normally the first test performed on a specimen. LabOS records that
expectation but doesn't block the other tests if it hasn't been done. Is that right, or do you want it
enforced? A hard block has no override, so it will eventually stop legitimate work.

**The static programme.** Proposals carry a `Static / Type` value — *Full* in the ones we've seen. LabOS
reads it, checks it, and then runs the same six-stage programme regardless. If *Full* is the only one in
practice, that's fine as it stands. If it isn't, tell me and I'll make LabOS refuse the others out loud
rather than quietly run the full one.

Nothing here changes the sheet or blocks your review of it.

---

## Notes for us, not for sending

**The deflection correction is the load-bearing one.** `Deflection Value` and `Deflection Unit` are
`UNMET-UNCALIBRATED`: the envelope refuses them in the columns *and* the JSON, and §4 of the Airtable change
document tells their team *"we would rather send nothing than send a number we cannot stand behind"*. If he
repeats "Airtable receives deflection data" to anyone at IFET, the two statements collide in public. That is
the reason this message goes now rather than waiting.

**Max pressure is included deliberately**, even though the first message did not mention it. It is the other
half of the same sentence in the sheet, and the honest distinction — we can read it, nothing stores it, and
validating what we store needs bench time — is easier to make once than to unpick later. Note the
distinction has already been narrowed once: the change document used to call it "software work, already
scheduled" against deflection's hardware dependency, and the delivery plan has M7 hardware-bound too.

**"Implemented" is corrected rather than defended.** The claim was made a day before the per-impact shape
existed, and it is the kind of thing that costs credibility precisely because it turned out fine.

**Questions 2, 3, 4 are not repeated here.** They were asked and they stand; repeating them invites him to
re-answer what he may already have decided, and makes this message look like the first one failed.

**Six questions are now on the record**, and the approval document tracks answers inline as they arrive —
question 6 is already marked confirmed there. When 1 and 5 come back, they go the same way, and
`check_register.py` check 7 fails if the document drifts from the code it is generated from.
