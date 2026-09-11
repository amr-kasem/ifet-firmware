# TC5 operator interface contract — **superseded 2026-09-11**

**This document has been replaced by
[`tc5-ui-developer-handoff-2026-09-11.md`](tc5-ui-developer-handoff-2026-09-11.md).**

Go there. It is the canonical UI contract and the only one maintained.

**Why the replacement rather than a revision.** The original was written from the backend outwards — five
screens and their routes. The handoff is written from the developer's task inwards: per screen, its
purpose, routes, payloads, response fields that matter, state transitions, which fields the operator types
and which are read-only, the errors and how to display each one, completion and abort, photograph
behaviour, review, and the acceptance test. It also carries the results of a route-by-route verification
against the running application, which found one stale field name in our own documentation.

This stub exists only so links to the old filename keep working. **Two contracts is worse than one**, so
nothing is maintained here; the full previous text is in git history.
