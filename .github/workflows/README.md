# CI / workflows

## `publish.yml`

Renders the Quarto site and deploys `_site/` to GitHub Pages on every push to
`main`. Enable Pages with **Source: GitHub Actions** before the first run.

## `generate-reference.yml`

Populates **versioned** reference docs for the **whole ecosystem**, driven
entirely from this repo, no package repository needs its own workflow. Layout:

```
reference/<package>/<version>/<namespace>/<name>.qmd
```

On manual dispatch (or a weekly schedule) it:

1. **scans** `packages.viash-hub.com` for each package's latest release
   (`openpipeline`, `openpipeline_spatial`, `openpipeline_qc`,
   `openpipeline_composed`; `openpipeline_rapids` excluded for now),
2. **caches**: if `reference/<package>/<version>/` already exists, that version
   is skipped and never rebuilt, so a run does nothing unless a **new** release
   has appeared ("latest forward"),
3. for each new version, clones that tag from viash-hub (public, no credentials;
   the tag ships the built `target/` the generator reads) and runs
   `viash-io/viash-actions/pro/generate-documentation-qmd` in two passes
   (modules via `^(?!workflows|test_workflows)`, then workflows via
   `^workflows`) into `reference/<package>/<version>/`,
4. opens a PR against `main` with only the newly added version(s).

This is a **pull model**: the docs repo owns generation, so the reference stays
organized by package + version and can never drift from released code. The
generator must read a **built** package (`target/`), which is why we pull tagged
releases from viash-hub rather than `main` (where `target/` is not committed).

**Setup required:** add repo secret **`GTHB_PAT`**: used only as the
`viash_pro_token`, which the generator needs to clone the private
`viash-io/viash_tools` repo. Package fetching itself needs no credentials. This
is the same token the production website workflow uses; reuse that value. Then
run the workflow from the Actions tab (**Generate reference → Run workflow**) to
produce the first PR.

Never hand-edit anything under `reference/<package>/<version>/`, a version is
generated once and then frozen (later runs skip it).
