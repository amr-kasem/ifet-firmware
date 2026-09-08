#!/usr/bin/env python3
"""Generate the before/after field CSV for the Testing Base.

    python3 make-before-after-csv.py

The before/after evidence already exists as full schema dumps, one pair per
change. JSON is the right thing to *keep* — it carries field IDs, select options
and everything else, and it is what the change register diffs against.

It is the wrong thing to *send*. The Airtable team works in spreadsheets, and
asking someone to diff two 60KB JSON files by eye to see what changed is asking
them to take our word for it.

So this flattens the chain into one sheet: **one row per field, all 159**, saying
whether it was already there or added, and when. Two changes were made, and the
chain is verifiable — the `after` of the first is byte-identical to the `before`
of the second, which is checked below rather than assumed.

Generated, never hand-edited.
"""
import csv
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
FIRST = HERE / "testing-base-changes-2026-09-06"
SECOND = HERE / "testing-base-changes-2026-09-08"
OUT = HERE / "testing-base-before-after-2026-09-08.csv"

BEFORE = FIRST / "before-20260905T230411Z.json"
MIDDLE_AFTER = FIRST / "after-20260905T230411Z.json"
MIDDLE_BEFORE = SECOND / "before-20260907T233423Z.json"
AFTER = SECOND / "after-20260907T233423Z.json"

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
    # The chain has to actually join, or "142 -> 156 -> 159" is three unrelated
    # snapshots rather than a history.
    if hashlib.sha256(MIDDLE_AFTER.read_bytes()).hexdigest() != \
       hashlib.sha256(MIDDLE_BEFORE.read_bytes()).hexdigest():
        print("ERROR: the two changes do not chain — the first change's `after` is "
              "not the second change's `before`, so this CSV would describe a "
              "history that did not happen.")
        return 1

    before, middle, after = fields(BEFORE), fields(MIDDLE_AFTER), fields(AFTER)

    rows = []
    for key in sorted(after, key=lambda k: (k[0], k[1])):
        table, name = key
        a = after[key]
        if key in before:
            change, added, b_type = "UNCHANGED", "", before[key]["type"]
        elif key in middle:
            change, added, b_type = "ADDED", "2026-09-06", ""
        else:
            change, added, b_type = "ADDED", "2026-09-08", ""
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
    print(f"{OUT.name}: {len(rows)} fields — {len(rows) - len(added)} unchanged, "
          f"{len(added)} added "
          f"({sum(1 for r in added if r['added_on'] == '2026-09-06')} on 2026-09-06, "
          f"{sum(1 for r in added if r['added_on'] == '2026-09-08')} on 2026-09-08)")
    print(f"  chain verified: before {len(before)} -> {len(middle)} -> after {len(after)}")
    print(f"  fields removed: 0 · fields retyped: {len(retyped)}")
    if retyped:
        print("  WARNING — retyped fields:", [r["field"] for r in retyped])
    return 0


if __name__ == "__main__":
    sys.exit(main())
