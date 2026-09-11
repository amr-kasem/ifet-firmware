#!/usr/bin/env python3
"""Generate the production change specification CSV for the Airtable team.

    **Three actions, not two, since 2026-09-10.** This used to derive `ADD`
    purely from base membership - in Testing, not in production - which meant
    a field withdrawn from the read contract but deliberately left sitting in
    the Testing Base came out as an `ADD` against production every single
    time. `Missile Type`, `Missile Weight` and `Impact Velocity` are exactly
    that: applied on 2026-09-08, withdrawn on 2026-09-10, and never to be
    created in production. Emitting them would have asked the Airtable team to
    create two permanently unread fields in their live base.

    So a field the register marks `DEPRECATED` is **omitted**, and one marked
    `PENDING_SCHEMA` is omitted until it actually exists in Testing - there is
    nothing to propose for a field that has not been created anywhere yet.

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
# The same sheet, under the name the Airtable team is actually sent. One
# generator, two paths: the evidence folder keeps the artefact next to the
# change it documents, and `correspondence/` is what goes out.
CANONICAL = (HERE.parent.parent / "correspondence"
             / "LabOS-Airtable-Production-Schema-Changes-2026-09-11.csv")

# Their table order, most relevant to this integration first.
TABLE_ORDER = [
    "Protocol Sections",
    "LabOS Raw Data Table",
    "IFET Projects",
    "Mock-Ups/Specimens",
    "Tests Protocols",
]

HEADER = [
    "action", "table", "table_id", "field",
    "current_production_state", "required_production_state",
    "airtable_type", "options_or_precision", "direction",
    "labos_reads", "labos_writes",
    "why_labos_needs_it", "field_id_testing", "field_id_production",
    "automation_impact",
]

# **Automation impact, per field, written for whoever owns their views.** Only
# the fields that actually change what an existing view, roll-up or automation
# sees carry one; the rest say so explicitly rather than leaving a blank that
# reads as "not considered".
AUTOMATION_IMPACT = {
    "Impact Number": (
        "CHANGES WHAT EXISTING ROLL-UPS SEE. One physical impact is now one row, so a "
        "five-impact test publishes five rows where it published one. Count tests by "
        "grouping on LabOS Test ID; count impacts with this field. A roll-up that counts "
        "rows to mean tests will over-count impact tests."),
    "Forced Entry Result": (
        "New reporting axis. A view or report about Forced Entry alone no longer has to "
        "filter Test Result by Test Type first. Blank on the other four types."),
    "ANSI Result": (
        "New reporting axis, as Forced Entry Result. Blank on the other four types."),
    "Impact Classification": (
        "New reporting axis for Impact. Populated by LabOS on the results row; blank on "
        "the other four types."),
    "LabOS Photos": (
        "Attachment field. An automation that fires on record update will see it populated "
        "separately from the result, because attachments are delivered on their own channel "
        "and may land after the verdict."),
    "Corrects Attempt ID": (
        "Distinguishes a correction from a retest. A roll-up that picks the current result "
        "should prefer a row that is not superseded by a later correction."),
    "LabOS Verdict At": (
        "Set once, at first review. Useful as the trigger for anything that should fire on "
        "a reviewed result rather than on a recorded one."),
    "LabOS Verdict By": "Set once, at first review, alongside LabOS Verdict At.",
    "Testing Start Date": (
        "UTC instant, ISO, 24-hour. Distinct from your existing Test Date, which is "
        "unchanged and stays local/client."),
    "Testing End Date": "As Testing Start Date.",
    "Target Impact Velocity": (
        "Populated by LabOS for Impact only. **Precision 2 matters**: precision 0 truncates "
        "50.25 ft/s to 50 and would pass a type check while doing it."),
}

NO_IMPACT = "No automation impact: LabOS reads this and never writes it."
NO_IMPACT_IGNORED = "No automation impact: LabOS neither reads nor writes this."


def why(row):
    """The reason, written for the Airtable team rather than for us."""
    use, action = row["labos_use"], row["_action"]
    if action == "DO NOT PROMOTE / DEPRECATED":
        return ("WITHDRAWN from the LabOS contract - do NOT create this in production. "
                "It exists in the Testing base and LabOS does not read it. "
                + (row["rule"].strip() or ""))
    if action in ("CHANGE OPTIONS", "CHANGE TYPE"):
        return ("The production field differs from what LabOS validated against in Testing. "
                + (row["rule"].strip() or ""))
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


def divergence(row):
    """KEEP, or the specific change production needs. Compared, not assumed.

    Only meaningful where the field exists in Testing too — that is the shape
    LabOS validated against. A production-only field has nothing to diverge
    from and is KEEP by definition.
    """
    if row["in_testing"] != "yes":
        return "KEEP"
    if row["airtable_type_production"] != row["airtable_type"]:
        row["_current"] = (row["airtable_type_production"]
                           + _shape_of(row["choices_production"],
                                       row["precision_production"]))
        return "CHANGE TYPE"
    if (row["choices_production"] != row["choices"]
            or row["precision_production"] != row["precision"]):
        row["_current"] = (row["airtable_type_production"]
                           + _shape_of(row["choices_production"],
                                       row["precision_production"]))
        return "CHANGE OPTIONS"
    return "KEEP"


def _shape_of(choices, precision):
    if choices:
        return f" ({choices})"
    if precision != "":
        return f" (precision {precision})"
    return ""


def shape(row):
    """Options for a select, precision for a number, blank otherwise.

    One column rather than two, because an Airtable engineer creating a field
    needs exactly one extra fact and which one it is follows from the type.
    """
    if row["choices"]:
        return row["choices"]
    if row["precision"] != "":
        return f"precision {row['precision']}"
    return ""


def states(row, action):
    """What production holds today, and what it must hold. Said plainly."""
    shp = shape(row)
    typed = row["airtable_type"] + (f" ({shp})" if shp else "")
    if action == "ADD":
        return "absent", typed
    if action == "DO NOT PROMOTE / DEPRECATED":
        return "absent", "absent - do NOT create"
    if action in ("CHANGE OPTIONS", "CHANGE TYPE"):
        return row["_current"], typed
    return typed, typed + " - unchanged"


def main():
    rows = list(csv.DictReader(open(INTERFACE)))
    out = []
    for r in rows:
        if r["labos_use"] == "not-a-field":
            continue                      # local queue metadata, never an Airtable field
        if r["delivery_state"] == "DEPRECATED":
            # **Listed now, rather than omitted.** Until 2026-09-11 these were
            # dropped silently, which meant the sheet could not distinguish
            # "we did not think about it" from "we decided against it". They
            # are in Testing, they are withdrawn from the contract, and the
            # instruction to the Airtable team is to NOT create them.
            r["_action"] = "DO NOT PROMOTE / DEPRECATED"
        elif r["delivery_state"] == "PENDING_SCHEMA" and r["in_testing"] != "yes":
            # Decided, not yet created anywhere. Nothing to propose.
            continue
        elif r["in_production"] == "yes":
            # **A field present in both bases is not automatically KEEP.** The
            # type and the option set are part of the contract: a select whose
            # production options differ accepts nothing LabOS sends, and a
            # number at precision 0 truncates. Both would pass a presence
            # check, so both are compared against what production actually
            # holds.
            r["_action"] = divergence(r)
        elif r["in_testing"] == "yes":
            r["_action"] = "ADD"          # applied to Testing, still needed in production
        else:
            continue                      # proposed and deliberately never created

        use = r["labos_use"]
        out.append({
            "action": r["_action"],
            "table": r["airtable_table"],
            "table_id": r["airtable_table_id"],
            "field": r["airtable_field"],
            "current_production_state": states(r, r["_action"])[0],
            "required_production_state": states(r, r["_action"])[1],
            "airtable_type": r["airtable_type"],
            "options_or_precision": shape(r),
            "direction": r["direction"] or ("IGNORED" if use == "ignore" else ""),
            "labos_reads": "yes" if use in ("read", "read-only") else "no",
            "labos_writes": "yes" if use == "write" else "no",
            "why_labos_needs_it": why(r),
            "field_id_testing": r["field_id_testing"],
            "field_id_production": r["field_id_production"],
            "automation_impact": AUTOMATION_IMPACT.get(
                r["airtable_field"],
                NO_IMPACT_IGNORED if use == "ignore" else NO_IMPACT),
        })

    ORDER = {"ADD": 0, "CHANGE TYPE": 1, "CHANGE OPTIONS": 2,
             "DO NOT PROMOTE / DEPRECATED": 3, "KEEP": 4}

    def key(row):
        t = row["table"]
        return (ORDER.get(row["action"], 9),
                TABLE_ORDER.index(t) if t in TABLE_ORDER else len(TABLE_ORDER),
                t, row["field"])

    out.sort(key=key)
    for path in (OUT, CANONICAL):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=HEADER)
            w.writeheader()
            w.writerows(out)

    tally = {}
    for r in out:
        tally[r["action"]] = tally.get(r["action"], 0) + 1
    reads = sum(1 for r in out if r["labos_reads"] == "yes")
    writes = sum(1 for r in out if r["labos_writes"] == "yes")
    print(f"{len(out)} rows -> {OUT.name} and {CANONICAL.name}")
    for action in ("ADD", "CHANGE TYPE", "CHANGE OPTIONS",
                   "DO NOT PROMOTE / DEPRECATED", "KEEP"):
        print(f"  {action:<28} {tally.get(action, 0)}")
    print(f"  LabOS reads {reads}, writes {writes}")
    keeps = tally.get("KEEP", 0)
    print(f"  production {keeps} today + {tally.get('ADD', 0)} ADD "
          f"= {keeps + tally.get('ADD', 0)} after promotion")


if __name__ == "__main__":
    main()
