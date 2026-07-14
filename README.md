# openpipeline_docs

Draft next-generation documentation site for the **OpenPipeline** ecosystem —
covering single-cell (`openpipeline`) and spatial (`openpipeline_spatial`), plus
the cross-cutting `openpipeline_qc`, `openpipeline_rapids`, and
`openpipeline_composed` packages.

This is a **from-scratch rebuild** and does not touch the current production site
in [`openpipelines-bio/website`](https://github.com/openpipelines-bio/website).

## Why a rebuild

The current docs mix a single guided path with dev-facing detail, the narrative
has drifted from the code (broken component links, renamed workflows), and the
reference is one flat 150-row table. This site reorganizes around the
[Diátaxis](https://diataxis.fr) model and unifies all five packages into one
information architecture, with the package surfaced as a **facet** rather than a
separate silo.

## Structure

```
_quarto.yml          site config: navbar, per-package reference sidebar
theme.scss           palette derived from the logo green (#70d287)
index.qmd            landing page (single-cell + spatial flows)
get-started/         tutorial: guided first run (Local / Seqera / Viash Hub)
guides/              task-oriented how-tos
concepts/            explanation: MuData, Viash, param_list, pipeline model
reference/           AUTO-GENERATED per package (see below) — do not hand-edit
  openpipeline/
  openpipeline_spatial/
  openpipeline_qc/
  openpipeline_rapids/
  openpipeline_composed/
contributing/        how to add components / pipelines / tests
design/mockup.html   the clickable design prototype this scaffold implements
```

## Building locally

Requires [Quarto](https://quarto.org).

```bash
quarto preview      # live preview on http://localhost:4200
quarto render       # build to _site/
```

## Reference generation (to be wired up)

The `reference/<package>/` folders are **populated by each package's release
workflow**, not by hand. Each of the five repositories runs
`viash-io/viash-actions/pro/generate-documentation-qmd` and opens a PR here that
writes `reference/<package>/<namespace>/<name>.qmd`. This keeps the reference
from ever drifting from the source configs.

See `.github/workflows/README.md` for the wiring plan.

## Status

Scaffold + design mockup. Narrative content is partially ported from the current
site and partially placeholder — see individual pages.
