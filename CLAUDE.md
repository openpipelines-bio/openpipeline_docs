# CLAUDE.md

Guidance for Claude Code working in **openpipeline_docs**. Read this first.

## What this repo is

A **from-scratch rebuild** of the OpenPipeline documentation site, as a
[Quarto](https://quarto.org) website. It is a private draft and intentionally
does **not** touch the current production site in
[`openpipelines-bio/website`](https://github.com/openpipelines-bio/website),
which stays live until the team decides to cut over.

The goal: one unified site covering the whole OpenPipeline **ecosystem** — not
just the core package — reorganized so entry-level bioinformaticians, wet-lab
scientists, and expert bioinformaticians can all find their way.

## The ecosystem (why this is multi-package)

`openpipeline` is the core; four satellite packages pin it as a Viash dependency:

| Package | Role | Pins |
|---|---|---|
| `openpipeline` | Core single-cell multi-omics (RNA, protein/ADT, ATAC, VDJ, GDO) | — (base) |
| `openpipeline_spatial` | Spatial transcriptomics (Space Ranger, NicheCompass) | openpipeline v4.1.0 |
| `openpipeline_qc` | QC components & reporting (`generate_qc_report`, `ingestion_qc`) | openpipeline v4.1.0 + craftbox |
| `openpipeline_rapids` | GPU components via rapids-singlecell | openpipeline v4.1.0 |
| `openpipeline_composed` | Turnkey composed pipelines (`single_cell`) | openpipeline v4.2.0 + openpipeline_qc + biobox |

All five are Viash 0.9.7 packages, so the same doc-generation tooling works for
each. `biobox`/`craftbox` are external component libs (dependencies, not
openpipelines-bio pipelines) — mention, don't fully document.

## Decisions already made (do not relitigate without reason)

- **IA = Diátaxis**: Get started (tutorial) · Guides (how-to) · Concepts
  (explanation) · Reference (auto-generated) · Contributing.
- **Unified IA, package as a facet** — NOT a separate doc silo per package.
  Packages surface as colored tags/filters within shared sections.
- **Landing overview shows only Single-cell vs Spatial.** Rapids/QC/composed are
  cross-cutting power-user knowledge — keep them OUT of the landing page.
- **Facet tags use real package names** (`openpipeline`, `openpipeline_spatial`,
  `openpipeline_qc`, `openpipeline_rapids`, `openpipeline_composed`), not
  friendly labels.
- **Execution routes**: Local (Nextflow) · Seqera · Viash Hub. Only install
  Nextflow for the Local route. Point at Viash/Viash Hub as the explainer.
- **`param_list` is a first-class concept** — explained in get-started and
  concepts (per-sample args inside the list, shared args outside).
- **Reference is auto-generated and never hand-edited** (see below).
- **Brand**: keep the OpenPipeline logo (`images/logo.svg`); palette derived from
  its green `#70d287`. It is "OpenPipeline" (singular).
- **Identity**: monospace headings ("scientific terminal" feel); see
  `design/mockup.html` for the approved visual prototype this scaffold implements.

## Repo structure

```
_quarto.yml          navbar + per-package reference sidebar
theme.scss           palette (logo green), mono headings, .pkg-tag styles
index.qmd            landing (single-cell + spatial mermaid flows)
get-started/         guided first run (Local/Seqera/Viash Hub tabs) + param_list + read-output
guides/              task index (placeholder rows → become pages)
concepts/            mudata · viash · param-list · pipeline-model (+ index)
reference/<package>/ AUTO-GENERATED targets — index.qmd placeholder per package
contributing/        build-path index (placeholder)
design/mockup.html   the clickable design prototype
.github/workflows/   publish.yml (Quarto→Pages) + README.md (reference-gen plan)
```

Content status: get-started, concepts, index carry **real ported content**.
guides + contributing indexes and the deep architecture page are **placeholders**
flagged in-page.

## Build / preview

```bash
quarto preview     # live, http://localhost:4200
quarto render      # build to _site/ (gitignored)
```

Empty-listing warnings for `reference/<package>/` are expected until generated
pages exist — not errors.

## Reference auto-generation (biggest remaining task)

`reference/<package>/` folders are populated by **each package repo**, not here.
Reference implementation to copy from:
`openpipeline/.github/workflows/create-documentation-pr.yml` (runs
`viash-io/viash-actions/pro/generate-documentation-qmd`, opens a PR to the docs
repo). For each of the five packages, add such a workflow with
`output_dir: <docs>/reference/<package>/` and `dest_path: "{namespace}/{name}.qmd"`.
Full plan in `.github/workflows/README.md`. Recommendation: independent per-package
PRs on each package's release cadence.

## Porting the current site — and the drift to FIX

Current production narrative lives in `openpipelines-bio/website`:
`fundamentals/` (philosophy, concepts, architecture, roadmap), `user_guide/*`,
`contributing/*`, `more_information/*`, `team/*`, `index.qmd`. Pull the good
prose, but the architecture/user-guide pages have **drifted from the code** —
fix these when porting (verified against `openpipeline/src`):

- `multiomics/multisample` → gone; now `process_samples` / `process_batches`
- `initialize_integration` → gone; now `dimensionality_reduction` / `neighbors_leiden_umap`
- `multimodal_integration` → gone (a stale example command references it)
- `filter_with_hvg` → gone; now `feature_annotation/highly_variable_features_scanpy`
- integration workflows moved `workflows/multiomics/integration/*` → `workflows/integration/*`
- `prot_multisample` / `rna_multisample` now under `prot/` and `rna/` namespaces
- version pins inconsistent/stale across pages — use one source of truth

## Conventions

- Package facet colors (keep consistent everywhere — mockup + theme.scss):
  openpipeline `#2b8f52` · openpipeline_spatial `#6f56e8` ·
  openpipeline_qc `#c9821f` · openpipeline_rapids `#cf3c92` ·
  openpipeline_composed `#2b78c2`.
- Never hand-edit anything under `reference/<package>/<namespace>/` — generated.
- Match Quarto/markdown style of existing pages; real content over lorem.
- The `design/mockup.html` is the visual source of truth; keep the built site
  faithful to it (or update the mockup deliberately if the direction changes).

## Roadmap (priority order)

1. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions) → `publish.yml` deploys.
2. Wire reference generation across all five package repos (start with a PR to `openpipeline`).
3. Port + fix narrative (architecture drift above), write full guide pages.
4. Decide cutover: point `openpipelines.bio` here vs. PR the rework into `website`.

## Related

- Design prototype: `design/mockup.html`
- Current site: https://openpipelines.bio · repo `openpipelines-bio/website`
- Core code: `openpipelines-bio/openpipeline` (the `src/` configs drive the reference)
