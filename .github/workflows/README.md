# CI / workflows

## `publish.yml`

Renders the Quarto site and deploys `_site/` to GitHub Pages on every push to
`main`. Enable Pages with **Source: GitHub Actions** before the first run.

## `generate-reference.yml`

Populates `reference/<package>/` for the **whole ecosystem**, driven entirely
from this repo — no package repository needs its own workflow. On manual
dispatch (or a weekly schedule) it:

1. checks out this repo plus all five packages
   (`openpipeline`, `openpipeline_spatial`, `openpipeline_qc`,
   `openpipeline_rapids`, `openpipeline_composed`),
2. runs `viash-io/viash-actions/pro/generate-documentation-qmd` once per
   package with `output_dir: reference/<package>/` and
   `dest_path: "{namespace}/{name}.qmd"` — one unified pass per package
   (modules + workflows by namespace; `test_workflows` skipped),
3. opens a PR against `main` with the regenerated reference.

This is a **pull model**: the docs repo owns generation, so the reference stays
organized by package and can never drift from the source configs. It uses the
same Viash pro tooling as the production `website` flow.

**Setup required:** add repo secret **`VIASH_PRO_TOKEN`** (viash-hub pro access —
the same token the website workflow uses). Then run the workflow from the
Actions tab (**Generate reference → Run workflow**) to produce the first PR.

Never hand-edit anything under `reference/<package>/<namespace>/` — it is
overwritten on every run (`clean: true`).
