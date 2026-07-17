# Plan — what's left to do

Status of the OpenPipeline docs rebuild. See [`CLAUDE.md`](CLAUDE.md) for the
decisions already locked in and [`design/mockup.html`](design/mockup.html) for
the visual source of truth.

## Done

- Information architecture, navbar, and per-package reference sidebar
  ([`_quarto.yml`](_quarto.yml)).
- Real ported content for the landing page, get-started, and the four concepts
  pages.
- Palette, mono headings, and `.pkg-tag` chips in [`theme.scss`](theme.scss).
- Draft site kept out of search (`noindex` meta + `robots.txt`) and pointed at
  its own GitHub Pages project URL, so it never overwrites `openpipelines.bio`.

## Phase 1 — Ship something live ✅

- [x] **Enable GitHub Pages** — done (`build_type: workflow`). Live at
      `https://openpipelines-bio.github.io/openpipeline_docs/`.
      [`publish.yml`](.github/workflows/publish.yml) redeploys on every push to
      `main`.
- [x] Confirm `quarto render` is clean on CI (empty-listing warnings for
      `reference/<package>/` are expected until pages are generated).

## Phase 2 — Visual fidelity (close the mockup gap) ✅

- [x] Mockup layout CSS in [`theme.scss`](theme.scss): `.hero`, `.flow-card` /
      `.stage`, `.rcard`, `.way`, `.btn.primary`, kicker + modality pills (scoped
      under `.op-home`).
- [x] [`index.qmd`](index.qmd) rebuilt to match: styled hero, "three ways in"
      cards, "run it your way" cards, plus an interactive single-cell/spatial
      flow toggle (richer than the mockup's static one).
- [x] **Global chrome ported** (this pass) so inner pages match the mockup, not
      just the landing: navbar → terminal bar (mono, lowercase, active pill,
      blur); left sidebar → mono; page title/description → headline + lede; code
      blocks → dark near-black (`#0a1310`) with `highlight-style: monokai`;
      content tables → mono-header mockup style (reference listing excluded);
      callouts → rounded mono-header cards; footer styled.
- [x] Interactive widgets resolved: home flow toggle reimplemented as embedded
      JS; reference + guides facet filters use Quarto-native mechanisms.

- [x] **Dark mode** — `theme: {light, dark}` pair in
      [`_quarto.yml`](_quarto.yml); Quarto renders a navbar toggle. The dark
      variant layers [`theme-dark.scss`](theme-dark.scss) (palette only) over the
      shared rules in [`theme.scss`](theme.scss). All component rules read
      `var(--…)` tokens, so the dark file just re-points the tokens + Bootstrap
      compile-time vars. Base palette vars are `!default` so the dark overrides
      win (Quarto concatenates `scss:defaults` in reverse theme order).

**Also noticed (unrelated):** the `scripts/generate_team.py` pre-render step
occasionally races Quarto's input walk (`WalkError` on a `team/<member>` dir),
because it rewrites `team/` mid-render. Re-running succeeds. Worth making the
script write atomically at some point.

## Phase 3 — Fill the placeholder pages ✅

Ported from the reconstructed-docs branch (`mdgrv/website`, PR
[#121](https://github.com/openpipelines-bio/website/pull/121)), drift-fixed and
adapted to this repo's IA, version pin (`4.2.0`), and link structure.

- [x] **Guides** — 11 task pages, one per row of the old index, plus a Quarto
      listing with per-package category filters ([`guides/index.qmd`](guides/index.qmd)).
      Core tasks (ingest-10x, process-filter, process-many-samples, integrate,
      annotate, tune-resources) carry full branch prose; satellite tasks
      (ingest-spatial, qc-report, gpu, spatial-niches, turnkey) are concise and
      link to the reference.
- [x] **Contributing** — 5 pages ported (getting-started, project-structure,
      creating-components, creating-pipelines, running-tests) + listing index.
      The 6th topic (pull requests) is folded into project-structure's
      versioning/branching/release section. Configs already on Viash 0.9.x
      syntax (`argument_groups` / `engines` / `runners`).

## Phase 4 — Narrative port + drift fixes (highest content risk) ✅

Ported the `fundamentals/` narrative into the **Concepts** section (this repo has
no `fundamentals/`), sourced from the same reconstructed-docs branch and verified
against the local v4.2.0 reference (generated from `openpipeline/src`).

- [x] **New** [`contributing/faq.qmd`](contributing/faq.qmd) — dev FAQ (Viash
      resources, `__merge__`, dockerfile, bug reports).

**Concepts restructured into a 6-card grid** (per Flo's direction — the section
had drifted into a placeholder mess). [`concepts/index.qmd`](concepts/index.qmd)
is now a clickable `.rcard.link` card grid (mockup pattern). The six cards:

- [`ecosystem.qmd`](concepts/ecosystem.qmd) — **new**; the 5-package ecosystem.
- [`modularity.qmd`](concepts/modularity.qmd) — **new**; execution-level (not
  just code-level) modularity.
- [`mudata.qmd`](concepts/mudata.qmd) — reworked; full slot anatomy + a converter
  table (H5AD / Seurat / TileDB / velocyto / spatial).
- [`viash.qmd`](concepts/viash.qmd) — reworked as "The engine: Viash and Viash
  Hub" (Viash builds CLI + Docker + Nextflow module; Viash Hub is the CI that
  builds containers, runs unit/workflow tests, publishes the catalog).
- [`param-list.qmd`](concepts/param-list.qmd) — kept.
- [`architecture.qmd`](concepts/architecture.qmd) — **merged** pipeline-model +
  the deep-dive into one un-numbered page; added a QC-reporting-after-ingestion
  paragraph and a spatial branch. Every workflow/tool name verified against the
  v4.2.0 reference.

Dropped: `philosophy.qmd` (OpenProblems link dead, "living best practices" not a
claim we make) and `pipeline-model.qmd` (folded into architecture).

Drift items — all handled by porting from the already-fixed branch + name
verification (none of the stale names survive):

- [x] `multiomics/multisample` → `process_samples` / `process_batches`
- [x] `initialize_integration` / `multimodal_integration` — not referenced anywhere
- [x] `filter_with_hvg` — HVF described conceptually, no stale component name
- [x] integration workflows use `workflows/integration/*`
- [x] `prot_multisample` / `rna_multisample` under `prot/` and `rna/`
- [x] version pins reconciled to `4.2.0` (guides); concepts pin no version

**Deferred (flagged, not ported):** `fundamentals/roadmap.qmd` — two large
component-level status mermaids that go stale fast; better regenerated from code
than hand-ported. `more_information/cheat_sheets.qmd` and the `*/index.qmd` stubs
add little. `team/` is already handled by `scripts/generate_team.py`.

## Phase 5 — Reference auto-generation (biggest structural task)

`reference/<package>/` is populated by each package repo, not here. Plan in
[`.github/workflows/README.md`](.github/workflows/README.md).

- [ ] Add a `create-documentation-pr.yml` to **`openpipeline`** first (proves
      the flow), with `output_dir: <docs>/reference/openpipeline/` and
      `dest_path: "{namespace}/{name}.qmd"`.
- [ ] Replicate for `openpipeline_spatial`, `openpipeline_qc`,
      `openpipeline_rapids`, `openpipeline_composed`.
- [ ] Confirm the reference listing renders correctly once real pages land.

## Phase 6 — Cutover decision *(team, not code)*

- [ ] Decide: point `openpipelines.bio` here, or PR the rework back into
      `website`.
</content>
</invoke>
