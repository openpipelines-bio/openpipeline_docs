# CI / workflows

## `publish.yml`

Renders the Quarto site and deploys `_site/` to GitHub Pages on every push to
`main`. Enable Pages with **Source: GitHub Actions** before the first run.

## `generate-reference.yml`

Populates `reference/<package>/` for the **whole ecosystem**, driven entirely
from this repo — no package repository needs its own workflow. On manual
dispatch (or a weekly schedule) it:

1. clones each package (`openpipeline`, `openpipeline_spatial`,
   `openpipeline_qc`, `openpipeline_composed`) from **packages.viash-hub.com**
   (`vsh/<package>`) at its **highest semver tag** — viash-hub is public (no
   credentials) and ships the built `target/`, which the generator reads.
   `openpipeline_rapids` is excluded for now (not ready),
2. runs `viash-io/viash-actions/pro/generate-documentation-qmd` per package
   with `output_dir: reference/<package>/` and
   `dest_path: "{namespace}/{name}.qmd"` — two passes each (modules via
   `^(?!workflows|test_workflows)`, then workflows via `^workflows`), the same
   split the production website workflow uses,
3. opens a PR against `main` with the regenerated reference.

This is a **pull model**: the docs repo owns generation, so the reference stays
organized by package and can never drift from released code. The generator must
read a **built** package (`target/`), which is why we pull tagged releases from
viash-hub rather than `main` (where `target/` is not committed).

**Setup required:** add repo secret **`GTHB_PAT`** — used only as the
`viash_pro_token`, which the generator needs to clone the private
`viash-io/viash_tools` repo. Package fetching itself needs no credentials. This
is the same token the production website workflow uses; reuse that value. Then
run the workflow from the Actions tab (**Generate reference → Run workflow**) to
produce the first PR.

Never hand-edit anything under `reference/<package>/<namespace>/` — it is
overwritten on every run (`clean: true`).
