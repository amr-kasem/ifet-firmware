#!/usr/bin/env python3
"""Generate the production change specification CSV for the Airtable team.

    ###################################################################
    #  SUPERSEDED 2026-09-10 - DO NOT RUN THIS AND SEND THE RESULT.   #
    ###################################################################

    Running this today reproduces the hazard it is marked for. Lines 70-77
    below derive `ADD` purely from base membership - in Testing, not in
    production - so `Missile Type`, `Missile Weight` and `Impact Velocity`
    come out as `ADD` against production every single time. The product owner
    withdrew all three from the Airtable -> LabOS input contract on
    2026-09-10; the Impact requirement is now the LabOS-owned **Impact
    Classification**, published outbound.

    This script needs a **third action** before it is correct: a field the
    register marks deprecated must be omitted from the spec rather than
    proposed for production. That change is part of TA7 and lands together
    with the register flip and the code, because `check_register.py` binds
    the three to each other.

    Production is untouched and stays at 142 fields.
    See ../../correspondence/po-answers-and-impact-remap-2026-09-10.md.

    python3 production-change-spec.csv.py            # writes production-change-spec.csv

One row per field, covering **both** the 142 fields production already has and
the 14 it needs, so the Airtable team can work from a single sheet rather than
diffing two schema dumps.

Why this exists rather than sending `interface-schema.csv`: that file is the
internal join of both bases against the register and carries our own delivery
vocabulary (`BASELINE`, `CONDITIONAL`, `write_phase`, and so on). None of that
means anything to them. This says only what they need to act on:

    action        ADD -> create this field in production; KEEP -> already there
    labos_reads   does LabOS read it
    labos_writes  does LabOS write it
    why           the reason, in their terms

Generated, never hand-edited. Regenerate after any register change.
"""
import csv
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
INTERFACE = HERE.parent.parent / "contract" / "interface-schema.csv"
OUT = HERE / "production-change-spec.csv"

# Their table order, most relevant to this integration first.
TABLE_ORDER = [
    "Protocol Sections",
    "LabOS Raw Data Table",
    "IFET Projects",
    "Mock-Ups/Specimens",
    "Tests Protocols",
]

HEADER = [
    "action", "table", "field", "type", "choices",
    "labos_reads", "labos_writes", "field_id_production", "why",
]


def why(row):
    """The reason, written for the Airtable team rather than for us."""
    use, action = row["labos_use"], row["_action"]
    if action == "ADD":
        reason = row["rule"].strip() or "Required by the LabOS write contract."
        if use == "ignore":
            # Honest about the awkward case: we are asking them to create a field
            # we do not touch. Better stated than discovered in review.
            return ("PARITY ONLY - LabOS does not read or write this today. Requested so the "
                    "Testing and production schemas stay identical, and so a future release "
                    "that does consume requirement values needs no second schema change. "
                    + reason)
        return reason
    if use == "read":
        return "LabOS reads this to identify which job, specimen, protocol or section a result belongs to."
    if use == "write":
        return "LabOS writes this on the results row."
    if use == "read-only":
        return "Owned by your automation; LabOS never writes it."
    return ("Not used by LabOS. Listed so the sheet is complete and so nobody has to "
            "guess whether an omission was deliberate.")


def main():
    rows = list(csv.DictReader(open(INTERFACE)))
    out = []
    for r in rows:
        if r["labos_use"] == "not-a-field":
            continue                      # local queue metadata, never an Airtable field
        if r["in_production"] == "yes":
            r["_action"] = "KEEP"
        elif r["in_testing"] == "yes":
            r["_action"] = "ADD"          # applied to Testing, still needed in production
        else:
            continue                      # proposed and deliberately never created
        out.append({
            "action": r["_action"],
            "table": r["airtable_table"],
            "field": r["airtable_field"],
            "type": r["airtable_type"],
            "choices": r["choices"],
            "labos_reads": "yes" if r["labos_use"] in ("read", "read-only") else "no",
            "labos_writes": "yes" if r["labos_use"] == "write" else "no",
            "field_id_production": r["field_id_production"],
            "why": why(r),
        })

    def key(row):
        t = row["table"]
        return (0 if row["action"] == "ADD" else 1,
                TABLE_ORDER.index(t) if t in TABLE_ORDER else len(TABLE_ORDER),
                t, row["field"])

    out.sort(key=key)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(out)

    adds = sum(1 for r in out if r["action"] == "ADD")
    reads = sum(1 for r in out if r["labos_reads"] == "yes")
    writes = sum(1 for r in out if r["labos_writes"] == "yes")
    print(f"{OUT.name}: {len(out)} fields — {adds} ADD, {len(out) - adds} KEEP; "
          f"LabOS reads {reads}, writes {writes}")


if __name__ == "__main__":
    main()
