#!/usr/bin/env python3
"""Generate the before/after field CSV for the Testing Base.

    python3 make-before-after-csv.py

The before/after evidence already exists as full schema dumps, one pair per
change. JSON is the right thing to *keep* — it carries field IDs, select options
and everything else, and it is what the change register diffs against.

It is the wrong thing to *send*. The Airtable team works in spreadsheets, and
asking someone to diff two 60KB JSON files by eye to see what changed is asking
them to take our word for it.

So this flattens the chain into one sheet: **one row per field**, saying whether
it was already there or added, and when. Three changes have been made, and the
chain is verifiable — each change's `after` is byte-identical to the next
change's `before`, which is checked below rather than assumed. A field is
attributed to the first change whose `before` did not contain it.

Generated, never hand-edited.
"""
import csv
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# **The chain, in order, one entry per change.** Generalised 2026-09-08 when a
# third change was applied: the two-link version hard-coded `FIRST`/`SECOND` and
# `MIDDLE`, so adding a link meant renaming variables and re-deriving which
# snapshot was which. Adding a change is now one row here.
CHAIN = (
    ("testing-base-changes-2026-09-06",
     "before-20260905T230411Z.json", "after-20260905T230411Z.json", "2026-09-06"),
    ("testing-base-changes-2026-09-08",
     "before-20260907T233423Z.json", "after-20260907T233423Z.json", "2026-09-08"),
    ("testing-base-changes-2026-09-08-impact-number",
     "before-20260908T194711Z.json", "after-20260908T194711Z.json", "2026-09-08"),
)
OUT = HERE / "testing-base-before-after-2026-09-08.csv"

COLUMNS = ["table", "field", "change", "before_type", "after_type",
           "field_id", "added_on", "select_options"]


def fields(path):
    doc = json.load(open(path))
    tables = doc["tables"] if isinstance(doc, dict) else doc
    out = {}
    for t in tables:
        for f in t["fields"]:
            opts = f.get("options", {}).get("choices")
            out[(t["name"], f["name"])] = {
                "type": f["type"],
                "id": f["id"],
                "options": " | ".join(c["name"] for c in opts) if opts else "",
            }
    return out


def main():
    links = [(HERE / d / b, HERE / d / a, when) for d, b, a, when in CHAIN]

    # Each link has to join the next, or "142 -> 156 -> 159 -> 160" is four
    # unrelated snapshots rather than a history.
    for (_, prev_after, _), (next_before, _, _) in zip(links, links[1:]):
        if hashlib.sha256(prev_after.read_bytes()).hexdigest() != \
           hashlib.sha256(next_before.read_bytes()).hexdigest():
            print(f"ERROR: the chain breaks at {next_before.parent.name} — the "
                  f"previous change's `after` is not this change's `before`, so "
                  "this CSV would describe a history that did not happen.")
            return 1

    before = fields(links[0][0])
    after = fields(links[-1][1])
    # Attribution is by each change's **after**, not its before. A field added
    # by change 2 is absent from change 1's `before` as well, so scanning the
    # befores attributes every new field to the first change — which is exactly
    # what it did on the first run of the three-link version.
    afters = [(fields(a), when) for _, a, when in links]

    rows = []
    for key in sorted(after, key=lambda k: (k[0], k[1])):
        table, name = key
        a = after[key]
        if key in before:
            change, added, b_type = "UNCHANGED", "", before[key]["type"]
        else:
            # The first change whose `after` contains it is the one that
            # added it.
            added = next((when for present, when in afters if key in present),
                         links[-1][2])
            change, b_type = "ADDED", ""
        rows.append({
            "table": table, "field": name, "change": change,
            "before_type": b_type, "after_type": a["type"],
            "field_id": a["id"], "added_on": added,
            "select_options": a["options"],
        })

    # Nothing may vanish. A removal would not show up in a pass over `after`.
    removed = sorted(set(before) - set(after))
    if removed:
        print(f"ERROR: {len(removed)} field(s) present before and absent after: "
              f"{removed}. Every change was supposed to be additive.")
        return 1

    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    added = [r for r in rows if r["change"] == "ADDED"]
    retyped = [r for r in rows
               if r["change"] == "UNCHANGED" and r["before_type"] != r["after_type"]]
    by_date = {}
    for r in added:
        by_date[r["added_on"]] = by_date.get(r["added_on"], 0) + 1
    breakdown = ", ".join(f"{n} on {d}" for d, n in sorted(by_date.items()))
    print(f"{OUT.name}: {len(rows)} fields — {len(rows) - len(added)} unchanged, "
          f"{len(added)} added ({breakdown})")
    counts = " -> ".join(str(len(fields(b))) for b, _, _ in links)
    print(f"  chain verified: {counts} -> after {len(after)}")
    print(f"  fields removed: 0 · fields retyped: {len(retyped)}")
    if retyped:
        print("  WARNING — retyped fields:", [r["field"] for r in retyped])
    return 0


if __name__ == "__main__":
    sys.exit(main())
