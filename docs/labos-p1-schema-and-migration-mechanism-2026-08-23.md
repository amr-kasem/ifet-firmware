# P1 — schema, identity, and how migrations actually reach production

**Date:** 2026-08-23 · **Author:** Abdelrahman · **Week:** 2 / P1 · **Epic:** IFET-32
**Code:** `ifet-management` @ `feature/labos-airtable` · **Contract:** `v0.3` §3, §4, §6

> **Why this document exists.** P1 was straightforward. Discovering *how a schema change reaches production*
> was not, and what it turned up changes how this project must handle migrations. That finding is the more
> important half of this document.

---

## 1. The correction that started it

P1 was built against `app/data/models.py` in a clone, on the assumption that the repository describes
production. On this project that assumption has a history of being wrong, so it was checked against the live
node before the migration was finalized.

**What held up:** `models.py` on `feature/labos-airtable` is byte-identical to `origin/latest`, the node's
working tree is **clean**, on `latest`, and its `models.py` matches `HEAD`. The production tables
`test_results` and `projects` match the model definitions exactly. So the code being extended is the code
production runs.

**What did not hold up:** everything about migrations.

| Assumed | Actually |
|---|---|
| The repo's `38f6ba7c1141` is the migration baseline | Production's `alembic_version` is **`3a65a83e0463`** — a revision that exists nowhere in git |
| Migrations are tracked in git | `**/alembic/versions/*` is **gitignored**. The repo has never tracked one |
| The repo has one migration, so production has ~one | Production has **29** |
| A migration file is an inert repo edit | `alembic/versions` is **bind-mounted** from the node, so a file dropped there is live at the next restart |

---

## 2. What is actually happening on the node

`startup.sh` runs on every container start:

```python
command.revision(config, message='Auto-generated migration', autogenerate=True)
command.upgrade(config, 'head')
```

Combined with `compose.yaml`:

```yaml
volumes:
  - ./src/management_service/alembic/versions:/app/alembic/versions   # bind-mounted
  - ./src/management_service/app:/app/app                             # bind-mounted
```

so:

1. Every restart **autogenerates a migration** by diffing `models.py` against the live database.
2. It is written **onto the node's filesystem**, because `versions/` is bind-mounted.
3. `upgrade(head)` applies it.

The evidence is in the directory. Of 29 revisions:

- **`886f54aa575c`** — 8354 bytes, January 2026. The only one that ever created anything.
- **28 others** — exactly 580 bytes each, `def upgrade(): pass`. One per restart since January.

This is why the repo and production diverged on migrations and nobody noticed: the artifacts were gitignored,
so the drift was invisible to git by construction.

> **The latent hazard, stated plainly.** Because `app/` is bind-mounted and `autogenerate` runs at boot, a
> `models.py` change merged to `latest` and pulled onto the node will **alter the production database schema at
> the next restart, with no migration review and no human in the loop.** That is independent of this
> integration and worth its own decision.

---

## 3. Why the P1 deploy is nevertheless safe

The obvious worry: the migration file is present but unapplied, and `autogenerate` runs *before* `upgrade` —
so does it generate a duplicate migration for the same columns, and then fail applying both?

No, and this is verified rather than assumed. Alembic refuses to autogenerate against a database that is not
at head (`alembic/autogenerate/api.py`):

```python
if set(self.script_directory.get_revisions(rev)) != set(
        self.script_directory.get_revisions("heads")):
    raise util.CommandError("Target database is not up to date.")
```

So on the first restart after this migration is deployed:

1. DB is at `3a65a83e0463`; file-head is `b7c2e9a41d38` → **`autogenerate` raises**, and `startup.sh`'s
   `try/except` swallows it and prints *"No new migration needed"*.
2. `upgrade(config, 'head')` then applies `b7c2e9a41d38` cleanly — **including the backfill**.

The sequence is self-correcting. It is still worth removing the `autogenerate` call, but that requires an image
rebuild (`startup.sh` is baked in, not mounted) and is a separate, scheduled change.

---

## 4. What P1 adds

Purely additive: new columns only, every one nullable or defaulted, against **623 live attempt rows**.

| Table | Columns | Why |
|---|---|---|
| `projects` | `airtable_project_id`, `airtable_mockup_id`, `airtable_mockup_name` | Contract §4.1 linkage |
| `static_tests`, `cyclic_tests` | `airtable_protocol_id`, `airtable_section_id`, `airtable_section_name` | The Protocol Section a result attaches to |
| `test_results` | identity, correction chain, lifecycle, measurements, artifacts, 2 JSON columns, sync visibility | The attempt record — contract §3, §4, §6 |

**Lightweight references, not mirrored tables** (pre-closed decision #2). Airtable owns the
Project → Mock-Up → Protocol → Section hierarchy and LabOS never writes it, so copying it into Postgres would
create a second version free to drift, with nothing permitted to reconcile the two. LabOS stores the `rec…` ID
it was given plus a display name.

**`trial_number` is reused, not replaced.** It already means exactly what the contract calls `Attempt Number`.
Adding a synonym beside it would have created two columns that must agree forever.

**Datetimes are `TIMESTAMP WITH TIME ZONE`.** This was a bug caught by the new tests: the envelope rejects a
naive datetime because §4.5 requires ISO 8601 UTC, and a naive column would have made the same guess one layer
lower, silently, where nothing would reject it.

**`required_value` / `required_unit` are stored per attempt** even though Airtable has no column for them yet.
They are the only available defence against §10.19 — when the Airtable team fix their extractor, these columns
are what allow the question *"which attempts ran against a wrong requirement?"* to be answered at all.

### 4.1 The load-bearing line of the backfill

```sql
UPDATE test_results SET airtable_sync_state = 'Excluded' WHERE airtable_sync_state IS NULL;
```

Every pre-integration attempt is explicitly excluded from sync. Without it, those 623 historical rows would
have a NULL sync state, and the first run of the W4 worker — if it treated NULL as *not yet synced* — would
upload **every test IFET has ever performed** into Airtable. The default has to be "never send this", and
eligibility has to be opt-in.

Lifecycle columns (`status`, `test_result`, …) are deliberately left NULL on those rows. They predate the
contract, and back-filling them would be asserting things about historical tests that cannot be known.

---

## 5. Rehearsal — standing in for the missing test node

The test node has been offline since ~2026-07-24, so there is no non-production database to try this on.
`tests/rehearse_p1_migration.py` substitutes for one: it builds the **production** pre-migration schema
(transcribed from `\d test_results` on the node, not from `models.py`), seeds representative rows, runs
`upgrade()`, asserts, then runs `downgrade()`.

Asserted, and passing:

- every attempt ends with a merge key, and they are unique
- two attempts at the **same** test share a `labos_test_id`; a static and a cyclic test do not collide
- an attempt with no subclass row still gets a merge key
- **every historical row comes out `Excluded`**
- `retest_required` defaults to `false`, never NULL
- the migration invents no lifecycle status for historical rows
- `labos_test_id` derivation is deterministic — re-running reproduces it
- `downgrade()` removes every column and loses no rows

---

## 6. Where this leaves W2

| | |
|---|---|
| **Done** | Models · the migration, **now tracked** and rehearsed both directions · ORM→envelope mapping · attempt identity + lifecycle · both `/trials` endpoints wired · **132 offline tests** |
| **Unblocked** | `alembic/versions/` was root-owned *and* gitignored, so a hand-written migration could not be committed at all. Both fixed — the directory was chowned, and `.gitignore` now excludes only `*_auto_generated_migration.py` |
| **Not deployed** | Nothing has been deployed. Merging to `latest` and restarting is what applies this, and that is a scheduled decision |
| **Recommended follow-up** | Remove `command.revision(autogenerate=True)` from `startup.sh` — needs an image rebuild, so fold it into the next deliberate deploy |
| **Next in W2** | The firmware `/trials` seam (gap H), and the open question in §7 |

## 7. One question P1 deliberately left open

`PUT /test-results/{id}` still lets an operator attach a note or photo **after** an attempt is terminal.

Contract §3 says a terminal attempt is final and LabOS never rewrites it, so such an edit cannot reach
Airtable — the local record and the synced record diverge silently. Three possible answers:

1. **Block the edit** once terminal. Correct by the contract, but it would change how operators use the UI
   today, and notes are often added after a test finishes.
2. **Allow it and re-sync.** Violates §3 — the whole point is that a written result is evidence.
3. **Record it as a correction** — a new attempt carrying `corrects_attempt_id`. Contract-correct, but heavy
   for "I forgot to attach a photo".

Most likely the honest answer splits the difference: *artifacts* (photos, report links) are not results and
can be appended, while *results* (values, pass/fail) require a correction. That needs confirming with Luis,
because it decides what the Airtable record means.

Not resolved unilaterally here: it is a behaviour change to a production endpoint, and picking wrong is worse
than leaving it visible.
