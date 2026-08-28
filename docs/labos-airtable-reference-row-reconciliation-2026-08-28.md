# Reconciling our envelope against the Airtable team's own sample row

**Author:** Abdelrahman · **Date:** 2026-08-28 · **Method:** read-only
**Trigger:** the question *"should we wait for real Airtable writes so we have data consistency?"*

**Short answer: the concern is right, the remedy is not to wait.** A real Airtable-team write already
exists. Comparing our envelope against it finds two genuine inconsistencies that no test on our side would
ever have caught, because the fields involved are free text and would have accepted our values silently.

---

## 1. What is actually in the two bases

Record counts, read-only, 2026-08-28:

| Table | Testing `app4oXS3Kd5IKWgJ7` | Production `app0OCunbmuXl7Hc9` |
|---|---|---|
| IFET Projects | **0** | 1 |
| Mock-Ups/Specimens | **0** | 1 |
| Tests Protocols | **0** | 4 |
| Protocol Sections | **0** | 9 |
| **LabOS Raw Data Table** | **0** | **1 — their own sample write** |
| Walls & Positions | **0** | 5 |

**The testing base is completely empty.** And production's raw table already holds one record,
`recxZWiVa5Wuy0ZV6`, created **2026-08-10** — written by the Airtable team, not by us. That row is the
reference we were missing, and it has been available for eighteen days.

---

## 2. Our envelope vs. their row — the diff that matters

| Field | Live type | **Their row** | **Our envelope** | |
|---|---|---|---|---|
| `Deflection Unit` | `singleLineText` | **`Inches`** | **`in`** | 🔴 **divergent** |
| `Complete LabOS JSON Response` | `multilineText` | `gauges` is a **list of objects** — `{gauge, deflection, unit}` — plus `design_pressure`, `hold_time_seconds`, `observations` | `gauges` is a **dict** — `{"g1": 0.42}` — plus `load_steps`, `labos_extra` | 🔴 **structurally divergent** |
| `Schema Version` | `singleLineText` | `1.0` | `0.3` (our contract version) | 🟠 different meaning |
| `Test Date` | `date` | `2026-08-05` — date only | full ISO datetime `…T14:03:00Z` | 🟠 unverified |
| `LabOS Attempt ID` | `singleLineText` | `001` | UUID | 🟠 known — §10.22 |
| `Unit` | `singleLineText` | `PSF` | `PSF` | ✅ |
| `Test Result` | `singleSelect` | `Passed` | `Passed` | ✅ |
| `Retest Required` · `Testing Continued` | checkbox · text | **absent** | sent | 🟠 they treat as optional |

### 2.1 Why `Deflection Unit` is the serious one

The contract models `Deflection Unit` as a **single select** with options `in` / `mm`
(`contract.py:117`). **The live field is `singleLineText`.**

That difference changes everything about the failure mode:

- A single select would have **rejected** `Inches`, or rejected `in` — either way, loudly, at the first write.
- Free text **accepts both**. So the column ends up holding `Inches` on their rows and `in` on ours,
  meaning the same physical unit in two spellings, with nothing anywhere to notice.

Every downstream consumer — a roll-up, a filter, a report, a conversion — then has to know both. This is
exactly the class of defect that is cheap now and expensive after a hundred rows.

**The same applies to `Unit`** (`PSF`/`PSI`/`in`/`mm`/…), also modelled as a select and also live as free
text. It happens to agree today at `PSF`. That is luck, not agreement.

**And it is worse than cosmetic — verified today.** `envelope.build` **refuses** `Deflection Unit = "Inches"`
outright:

```
EnvelopeError: 'Deflection Unit': 'Inches' is not an allowed option ['in', 'mm'].
Contract §5 — LabOS never invents a select option at runtime.
```

So their current spelling is not merely untidy, it is **unsendable by our client**. §10.24 has to be
answered before any real sync, not tidied up afterwards.

**Why we did not simply adopt `Inches`.** It was tried and deliberately reverted. Their row is a
hand-written sample rather than a stated vocabulary, and switching only this field would leave `Unit`
accepting `in` while `Deflection Unit` demanded `Inches` — internally inconsistent, which is worse than
being consistently different from them. The probe therefore keeps our vocabulary, which is safe because
probe rows are tagged `LABOS-PROBE` and purged. The decision belongs to them.

### 2.2 The JSON shape is a real interoperability question

Contract §6 defines our shape. Their sample defines theirs. Both are reasonable; they are not the same:

```
theirs:  "gauges": [ {"gauge": "G1", "deflection": 0.18, "unit": "Inches"}, … ]
ours:    "gauges": { "g1": 0.11, "g2": 0.19, "g3": 0.12 }
```

Theirs carries the unit **per reading**; ours carries gauges as a map and the unit as a sibling column.
If anything on their side parses this field, our shape breaks it. If nothing parses it, it is documentation
only and the shape matters less — **but we do not know which, and that is the question to ask.**

---

## 3. So: wait, or not?

**Do not wait. Reconcile now, then proceed.** Waiting was the right instinct for the wrong reason — the
reference data is not missing, it has simply not been compared against until today.

Three separate things were being conflated:

| Concern | Verdict |
|---|---|
| **"We need a real Airtable write to compare against"** | ✅ **Valid — and satisfied.** `recxZWiVa5Wuy0ZV6` is that write. Reconciliation is §2 above and should land before we write anything |
| **"Stage 3 into an empty testing base is meaningless"** | ❌ **Not so.** All four ID fields are `singleLineText`, so Airtable enforces **no referential integrity** — a fabricated `rec…` is exactly as valid to Airtable as a real one. Upsert de-duplication, blank handling, `0`, JSON round-trip and option translation are all properties of the write path, not of the surrounding data |
| **"We can't verify their roll-up automations"** | ✅ **Correct, and unfixable today.** Rolling a raw row up into `Protocol Sections` needs a real Project→Mock-Up→Protocol→Section chain to roll into, and the testing base has none. This is a **separate stage**, not a reason to delay stage 3 |

### The sequencing that follows

1. **Now** — align the envelope to the reference row where the reference is the only evidence we have
   (`Deflection Unit`), and raise the two open questions (§10.24, §10.25).
2. **Stage 3** — proceeds into the empty testing base on their approval. It tests write mechanics, which
   need no surrounding data. **But it must not run before step 1**, or it writes the first inconsistent row
   itself and we have manufactured the very problem this document is about.
3. **Stage 4 (new)** — linkage and roll-up. Needs the testing base seeded with a real job chain.
   **Ask them to seed it**, ideally with `IFET-26-0066` *after* the extractor is fixed, so the same request
   serves two purposes.

---

## 4. What goes to the Airtable team

Additions to the open-items list. Both are cheap for them to answer and expensive for us to guess.

- **§10.24 — unit vocabulary.** `Unit` and `Deflection Unit` are free text, and their sample row writes
  `Inches` where our contract says `in`. Agree one vocabulary and we will send it verbatim. Our preference
  is the short form (`in`, `mm`, `PSF`) as the stored value, with display left to the interface — but
  **their existing row is the incumbent, so we will match `Inches` unless they say otherwise.** Best fix is
  to make both fields single selects, which turns this class of drift into an error instead of a silent
  divergence.
- **§10.25 — `Complete LabOS JSON Response` shape.** Does anything on their side parse this field? If yes,
  we adopt their sample's shape (per-reading `unit`, `gauges` as a list). If it is for human reading only,
  we keep the contract §6 shape and say so explicitly, so nobody later builds an automation against an
  assumption.

Also worth confirming, lower priority: `Schema Version` semantics (their `1.0` vs our contract version),
and whether `Retest Required` / `Testing Continued` are genuinely optional, since their row omits both
while §4.5 makes them terminal-required.
