# From *my* tool to *our* tool — a graduated promotion path for User-Defined Tools

**Status:** proposal / discussion starter (GCC 2026)
**Author:** Marius van den Beek
**Related:** [workflow-validation.md](workflow-validation.md), the deck (`slides.md`, Act 3)

## Problem

User-Defined Tools (UDTs) made it trivial to *create* a tool: write some YAML + a JavaScript
expression, get typed inputs and containerized execution, run it. But the moment a tool is useful
to more than one person, today's options are coarse:

- **Private by default.** A UDT belongs to the user who created it.
- **Rides along in workflows.** If a UDT is embedded in a shared workflow, importers get a private
  copy created in their own account.
- **Export to disk.** A UDT can be exported and loaded like a regular tool for instance-wide
  availability.

What's missing is everything *between* "my private tool" and "a fully curated IUC toolshed tool":
no peer review, no shared test record, no provenance/annotation, no signal of quality. The full IUC
process (PR, review, CI, conda/container packaging, maintenance) is the right bar for the global
toolshed, but it is far too heavy for "this little plotting tool my lab uses every week."

## Goal

A **graduated path** that lets a tool earn trust incrementally, lowering the barrier to contribution
while preserving quality — without requiring the full IUC toolshed overhead at every step.

## Proposed stages

| Stage | Who can run it | Gate to reach this stage |
|------|----------------|--------------------------|
| **1. Personal** | creator only | — (create it) |
| **2. Shared** | anyone given the workflow / link | creator shares; passes static validation (schema + linter) |
| **3. Reviewed** | a group / instance | ≥1 peer review + at least one recorded test case |
| **4. Annotated** | a group / instance | metadata complete: description, EDAM/ontology terms, license, author, citation |
| **5. Community** | global / cross-instance | maintainer sign-off; promotion to a curated registry |

Each stage adds exactly one kind of trust signal — execution scope, review, testing, annotation,
curation — so a tool can stop at whatever level fits its audience.

## Mechanisms to design

- **Promotion request UI.** A "propose for promotion" action on a UDT that opens the next gate's
  checklist (what's missing: a test? an annotation? a reviewer?).
- **Review surface.** Lightweight in-Galaxy review (comment + approve) rather than a GitHub PR, for
  stages 3–4. Reviews are attached to a specific tool version.
- **Test record.** Reuse the existing test machinery: a promoted tool carries at least one
  input→expected-output example that re-runs on promotion and on the target instance.
- **Provenance & versioning.** Promotion is per-version; a tool's lineage (who reviewed, what tests
  passed, when) travels with it.
- **Demotion / expiry.** A reviewed tool whose tests break, or whose author disappears, falls back a
  stage rather than silently rotting.

## Open questions

- Where does the curated "Community" registry live — an existing toolshed surface, or a new
  UDT-native registry?
- How much review is "enough" per stage, and who is eligible to review (instance admins? trusted
  users? domain WGs)?
- How does promotion interact with **workflow validation** (a workflow should be able to require a
  minimum stage for the tools it uses)?
- Trust & safety: a promoted tool is run by *other* people — what re-audit happens at the
  Shared→Reviewed boundary, given UDTs are already sandboxed (JS expressions, no Cheetah/Python)?

## Non-goals

- Replacing the IUC toolshed. This path *feeds* it: a tool that reaches "Community" and outgrows the
  UDT format is a strong, pre-vetted candidate for full toolshed packaging.
