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

## Phase 2 — Visual fidelity (close the mockup gap)

The scaffold ported content and IA but not the mockup's bespoke layout. Only
palette tokens made it into the theme, so existing markup renders as plain
Cosmo.

- [ ] Port the mockup's layout CSS into [`theme.scss`](theme.scss): `.hero`,
      `.flow-card` / `.stage`, `.rcard`, `.way`, `.btn.primary`, kicker +
      modality pills.
- [ ] Rebuild [`index.qmd`](index.qmd) to match: styled hero, "three ways in"
      cards, "run it your way" cards.
- [ ] Decide the interactive widgets that don't survive the SPA → multipage
      split:
  - Home flow toggle (single-cell / spatial) — keep the two static mermaids, or
    reimplement as a small embedded JS toggle.
  - Reference facet filter — Quarto's native `filter-ui` already covers most of
    it ([`reference/index.qmd`](reference/index.qmd)).
  - Guides facet filter — needs a Quarto listing with categories, or custom JS.

## Phase 3 — Fill the placeholder pages

- [ ] **Guides** — turn each of the 11 rows in [`guides/index.qmd`](guides/index.qmd)
      into its own `guides/<slug>.qmd` how-to, and convert the table to a Quarto
      listing.
- [ ] **Contributing** — port the 6 topics in
      [`contributing/index.qmd`](contributing/index.qmd) from the current
      `website` repo's `contributing/`.

## Phase 4 — Narrative port + drift fixes (highest content risk)

Port prose from `openpipelines-bio/website` (`fundamentals/`, `user_guide/`,
`more_information/`, `team/`), fixing the code drift flagged in `CLAUDE.md`.
Verify each against `openpipeline/src`:

- [ ] `multiomics/multisample` → `process_samples` / `process_batches`
- [ ] `initialize_integration` → `dimensionality_reduction` /
      `neighbors_leiden_umap`
- [ ] `multimodal_integration` → gone (stale example command references it)
- [ ] `filter_with_hvg` → `feature_annotation/highly_variable_features_scanpy`
- [ ] integration workflows `workflows/multiomics/integration/*` →
      `workflows/integration/*`
- [ ] `prot_multisample` / `rna_multisample` → under `prot/` and `rna/`
      namespaces
- [ ] reconcile inconsistent/stale version pins to one source of truth

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
