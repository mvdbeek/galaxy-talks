# Galaxy Tools 2.0 — Bring your own!

*Source of truth for the deck. Edit this file, then run `python3 build.py` to regenerate `slides.html`. See `build.py` for the small set of Markdown conventions used below.*

---

## Slide 1: Galaxy Tools 2.0 {.title}

**Bring your own!**

From throwaway LLM code → reproducible, validatable workflows

::: meta
Marius van den Beek
PSU / SCI-SCALE
marius@galaxyproject.org
:::

---

## Slide 2: Why can’t users just install tools? {.section}

---

## Slide 3: The catch — a tool is arbitrary code

> [!WARN] **The catch:** A classic Galaxy tool’s command is a Cheetah template — evaluated as **arbitrary Python** while the job is built. A tool author can read the database, touch the filesystem, do anything. That’s exactly why users can’t be allowed to install tools.

```xml {hl=2-4}
<command><![CDATA[
    #from pathlib import Path
    #user_id = $__app__.model.session().query($__app__.model.User.id).one()
    #open(f"{Path.home()}/a_file", "w").write("Hello!")
]]></command>
```
*Nothing stops a classic tool template from running this*

---

## Slide 4: …so every tool is hand-curated

![Slide 6](images/slide-06.png)
*galaxyproject/tools-iuc — thousands of reviewed pull requests. Safe, but every tool goes through people. That doesn’t scale to “I need xyz, right now.”*

---

## Slide 5: The answer — User-Defined Tools

```yaml {hl=8}
class: GalaxyUserTool
name: Boxplot (ggplot2)
description: Boxplot from a tabular file
container: rocker/tidyverse
inputs:
  - {name: table, type: data, format: tabular}
  - {name: group_column, type: text}
  - {name: value_column, type: text}
shell_command: Rscript plot.R     # the R script lives in a configfile
outputs:
  - {name: plot, type: data, format: png, from_work_dir: boxplot.png}
```
*A User-Defined Tool: typed inputs, a container, sandboxed JS expressions — no XML, no Python, no review queue. This boxplot tool is our running example.*

---

## Slide 6: …and the editor makes it safe and pleasant

> **Typed, in the browser:** Monaco knows the inferred type of `inputs.*` from the tool’s schema — offering autocomplete, hover docs, and real TypeScript errors on the expressions, before anything runs.

![Slide 10](images/slide-10.png)
*The live Tool Editor: type-aware autocomplete driven by the generated schema*

---

## Slide 7: Your LLM code, made reproducible {.section}

---

## Slide 8: LLMs write great throwaway code

- Everyone is generating analysis code with an LLM
  - …a pandas snippet, an R plot, a one-off filter
- But the output is **ephemeral**: a chat message, a copied cell
  - hard to re-run, hard to share, impossible to reproduce six months later
- A User-Defined Tool is the natural package for it
  - structured inputs · typed parameters · a pinned container
  - → a throwaway snippet becomes a recomputable, workflow-embeddable component

---

## Slide 9: So let’s not write it by hand

> [!WARN] **Live demo:** “Write a tool that uses ggplot2 to create a boxplot from a tabular file. The user should select a grouping column and a numeric column. Put the R script in a configfile.”

![Slide 99](images/slide-99.png)
*GalaxyAI (shipped as a FastMCP server) — or Claude / Orbit over MCP + a skill — authors the User-Defined Tool, multi-step, from that one sentence*

---

## Slide 10: The agent writes it — typed, not trusted blindly

```yaml {hl=10-16}
class: GalaxyUserTool
name: Boxplot (ggplot2)
description: Boxplot from a tabular file
container: rocker/tidyverse
inputs:
  - {name: table, type: data, format: tabular}
  - {name: group_column, type: text}
  - {name: value_column, type: text}
shell_command: Rscript plot.R
configfiles:
  - name: plot.R
    content: |
      library(ggplot2)
      df <- read.delim("$(inputs.table.path)")
      ggplot(df, aes(`$(inputs.group_column)`, `$(inputs.value_column)`)) +
        geom_boxplot()
      ggsave("boxplot.png")
outputs:
  - {name: plot, type: data, format: png, from_work_dir: boxplot.png}
```
*The R script lands in a `configfile`; `inputs.*` are still type-checked by Monaco and the linter — generated code that doesn’t type-check never runs.*

---

## Slide 11: From my tool to our tool {.section}

---

## Slide 12: Sharing — what works today

User-defined tools are **private to their creator**. But they already travel:

- Embed one in a **workflow** — anyone who imports the workflow gets the tool created in their account
- **Export to disk** and load it like a regular tool — instance-wide availability when you want it

*Great for “me” and “my lab”. But there’s nothing between a private tool and a fully curated IUC toolshed tool.*

---

## Slide 13: Proposal — a graduated promotion path

A tool should earn trust **incrementally** — without the full IUC toolshed overhead at every step:

1. **Personal** — just you (create it)
2. **Shared** — rides along in a workflow; passes static validation
3. **Reviewed** — ≥1 peer review + at least one recorded test
4. **Annotated** — description, ontology terms, license, citation
5. **Community** — maintainer sign-off → a curated registry

> Each stage adds exactly one trust signal — scope, review, testing, annotation, curation. Full proposal in `promotion-path.md`.

---

## Slide 14: Check the workflow before you run it {.section}

---

## Slide 15: Validation in three layers — all run today, no runtime

- **Static schema** — generated JSON Schema
  - every input/output type-checks; outputs line up with the inputs they feed
- **Pydantic validators** — the params *are* Pydantic models
  - value & cross-field rules (a cutoff in range; `group_column` ≠ `value_column`); wiring across the workflow
- **Linter** — lives in `galaxy-tool-util`
  - the *same* engine that already powers the editor’s errors — annotations, deprecations, missing tests

---

## Slide 16: Proposal — expose it through planemo

Inputs and outputs are formally typed, so a workflow of UDTs is a **portable artifact** you can validate anywhere — in a repo, in CI, with no Galaxy server:

```console
$ planemo validate workflow.gxwf.yml
✗ filter step:  'value_column' references a column not produced upstream
✗ boxplot step: 'group_column' equals 'value_column'   (model validator)
⚠ boxplot step: tool has no test case                  (lint)

# …fix…

$ planemo validate workflow.gxwf.yml
✓ schema · ✓ validators · ✓ lint — valid, no Galaxy runtime required
```
*The same three layers, surfaced outside Galaxy. Full proposal in `workflow-validation.md`.*

---

## Slide 17: Coming to a server near you soon! {.closing}

```yaml
class: GalaxyUserTool
name: Thank You!
description: Bring your own gratitude
container: busybox
shell_command: |
  echo "An LLM writes it → the editor types it → the community
  promotes it → planemo verifies it. Bring your own tool!" > thanks.txt
outputs:
  - {name: output1, type: data, from_work_dir: thanks.txt}
```
*Enable it, build one, help build the path. Thanks to John Chilton, Dannon Baker, Michael Crusoe, Nicola Soranzo, Anton Nekrutenko, and the audience at GCC!*

::: meta
With gratitude 💜
:::
