# Runtime-independent validation of User-Defined Tool workflows

**Status:** layers 1–3 exist today (inside Galaxy); the **planemo exposure is the proposal** (GCC 2026)
**Author:** Marius van den Beek
**Related:** [promotion-path.md](promotion-path.md), the deck (`slides.md`, Act 4)

## The idea

Because a User-Defined Tool describes its inputs and outputs *formally* — as typed, schema-backed
artifacts — a workflow composed of UDTs can be checked **before it runs, without a Galaxy runtime**.
Type correctness, parameter compatibility, and structural soundness become properties of a static
artifact you can verify in CI, on a laptop, or on another platform.

Validation is **layered** — three composing checks, each catching a different class of error. All
three run *today* inside Galaxy; the new work is exposing them as a standalone tool.

## Layer 1 — Static schema (structural / type correctness)

Each UDT's parameter model is emitted as **JSON Schema** (the same generation that drives the Monaco
editor's typing). At the workflow level this answers structural questions with no code execution:

- Does every required input have a producer or a value?
- Do the declared types line up where one tool's output feeds another's input?
- Is the shape of each input object (File: `class`, `path`, `basename`, …) what the consumer expects?

**Status:** built — JSON Schema is generated from the tool definition today.

## Layer 2 — Pydantic models with validators (semantic / value correctness)

The tool parameters *are* Pydantic models, so they carry validators beyond raw structure:

- Field validators — e.g. a column selector must be non-empty; a numeric cutoff in range.
- Model validators — cross-field rules, e.g. `group_column` ≠ `value_column`.
- Wiring checks — format compatibility between a producing output and a consuming input across a
  whole workflow, evaluated as plain Python.

**Status:** built — params are Pydantic models; richer cross-tool wiring validators are where this
layer keeps growing.

## Layer 3 — Linter (best-practice correctness)

A linter layer flags the things a schema can't: missing descriptions/annotations, deprecated
constructs, suspicious-but-legal expressions, untested tools. This linter **lives in
`galaxy-tool-util` today and already powers the editor's checks** when authoring or editing a UDT —
the inline errors a user sees in the Tool Editor are this same engine.

**Status:** built and live *inside* Galaxy (editor/authoring path).

## The proposal — expose the linter through planemo

The three layers run inside Galaxy, but a workflow author wants to validate **outside** it: in a
repo, in CI, on a machine with no Galaxy server. The proposal is to surface the `galaxy-tool-util`
validation/linting through **planemo**, so a workflow of UDTs validates as a portable artifact:

```console
$ planemo validate workflow.gxwf.yml
✗ filter step: input 'value_column' references column not produced upstream
✗ boxplot step: 'group_column' equals 'value_column' (model validator)
⚠ boxplot step: tool has no test case (lint)
... fix ...
$ planemo validate workflow.gxwf.yml
✓ schema      — all inputs/outputs type-check
✓ validators  — semantic + wiring checks pass
✓ lint        — annotations & tests present
Workflow is valid (no Galaxy runtime required).
```

### Why this matters

- **Portable & verifiable** across platforms — validation travels with the workflow.
- **CI-friendly** — a workflow PR can gate on `planemo validate`.
- **Composes with promotion** ([promotion-path.md](promotion-path.md)) — a promotion gate can require
  a clean validation run, and a workflow can require a minimum tool stage.

## Open questions

- Command surface: extend `planemo lint` / `planemo workflow_lint`, or a new `planemo validate`?
- How much of `galaxy-tool-util` can run truly standalone vs. needs a Galaxy context shim?
- Reporting format for machine consumption (JSON) in addition to the human view above.
