# TA7 live probe — the Impact classification pair, on the real wire, 2026-09-11

**Result: 64/64 assertions passed, in one clean run — `20260910T223938Z`.**
Read `probe-results-20260910T223938Z.json`; it is the authoritative artifact.

Run by `ifet-management` `src/management_service/tests/ta7_probe_live.py` against the **Testing** Base
`app4oXS3Kd5IKWgJ7`. Production `app0OCunbmuXl7Hc9` was read for comparison and never written.

## Why this exists at all

Every local suite injects a transport that accepts any payload. That is right for testing the queue, and it
is exactly how a sender that would have rejected *every photograph* once passed 270 tests. This probe uses
the real chain and no substitutes:

```
Airtable records -> mirror.refresh -> importer -> HTTP routes
  -> sync.publish -> sync_outbox -> worker.drain
  -> service.make_sender(AirtableClient) -> Airtable
```

## The four runs, and which one counts

| Run | Score | What it was |
|---|---|---|
| `223048Z` | 51/53 | **Superseded.** Two probe defects, described below |
| `223217Z` | 62/63 | **Superseded.** One probe defect |
| `223313Z` | 63/64 | **Superseded.** One false assertion |
| **`223938Z`** | **64/64** | **The result.** All defects corrected, nothing skipped or loosened |

The intermediate runs are kept because **all three failures were defects in the probe, and two of them are
the system refusing to do something wrong.** That is worth an audit trail:

1. **`223048Z` — LMI-E published nothing.** The probe created a test carrying an Airtable *section* id but
   no *protocol* id. `mapping.py` refused to publish a half-finished binding rather than write a row that
   attaches to nothing (contract §4.1). Correct behaviour; the probe was wrong.
2. **`223048Z` — `record_phase` returned `None` on re-publish.** Also correct: it declines a phase already
   delivered. That is idempotency one layer *earlier* than the upsert. The assertion was inverted to test
   for it, and the wire-level upsert proven separately.
3. **`223217Z` — direct re-upsert refused.** The probe rebuilt a *terminal* envelope for an attempt that had
   already been reviewed, and the envelope refused a verdict on a terminal write (contract §4, §6). Correct;
   the probe now uses `build_verdict`.
4. **`223313Z` — "withdrawn values absent from the JSON" failed.** A false alarm and the only one that was
   never a real refusal: the check was `"999" in text`, which matched the **microseconds in a timestamp**
   (`22:33:27.464999`). Replaced with a structural walk comparing actual values. Re-verified across all rows
   before the final run, and clean in it.

**None of the four was a wire mismatch.** No assertion was weakened to make the run pass.

## What was proved

**Impact Classification** — `SMI`, `LMI Level D` and `LMI Level E` each published the exact expected value,
onto the row matching that attempt's `LabOS Attempt ID`.

**Target Impact Velocity** — published from the LabOS-stored value, arrived as an Airtable **number and not
text**, and **fractional values survived**: 50.25 and 55.5 round-tripped exactly. That is what the
`precision: 2` assertion in preflight is protecting; precision 0 would have silently truncated them.

**Existing behaviour intact** — `Impact Number` 1 on every row, `Impact Result` carrying its impact's line,
photographs delivered through the real attachment channel, `Complete LabOS JSON Response` valid JSON.

**Idempotency, both layers** — the queue declines an already-delivered phase, and a direct re-upsert of the
identical payload returned the **same record id** with `createdRecords` empty. Across the whole probe:
8 rows, 8 distinct attempt ids, no duplicate logical attempt.

**The inbound withdrawal, tested positively.** The probe populated `Missile Type`, `Missile Weight` and
`Impact Velocity` on its own Protocol Sections with values designed to be recognisable
(`PROBE-SHOULD-NOT-BE-READ`, 999, 888). None reached the mirror, the requirement snapshot, the domain model
or the published JSON. The count *did* arrive, so the section was genuinely read — the absence is a
withdrawal, not a failed read.

**Write boundary** — the four hierarchy tables were snapshotted before and after the sync phase and compared
by record id. No unexpected write to any of them. The probe's own hierarchy records are setup, not LabOS
sync writes, and are listed below.

**Production** — schema 142 before and after, byte-identical JSON, record count unchanged, neither new field
present. Production was only ever read.

## Records left in the Testing Base — DO NOT DELETE YET

`probe-records-inventory.txt` has the full list with ids, classification, velocity and timestamps.
Everything is tagged `Operator Name = LABOS-PROBE-TA7`, and each hierarchy carries its run in its job number
(`IFET-PROBE-TA7-0001-<run>`).

They stay for human review by us and by the Airtable team. **Cleanup is a separate, explicit, recorded
operation** — LabOS never deletes, and purging is an ask, not a side effect.

## Files

`probe-results-*.json` — every assertion with pass/fail and detail, per run.
`imported-project-*.json` — the LabOS project as the importer built it, showing the un-prefilled fields.
`production-before-*.json` / `production-after-*.json` — production schema around every run.
`probe-records-inventory.txt` — what to review, and what to delete when cleanup is approved.
