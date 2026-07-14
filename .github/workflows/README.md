# CI / workflows

## `publish.yml`

Renders the Quarto site and deploys `_site/` to GitHub Pages on every push to
`main`. Enable Pages with **Source: GitHub Actions** before the first run.

## Reference generation (to wire up)

The `reference/<package>/` folders are populated by **each package repository**,
not from this repo. Every package
(`openpipeline`, `openpipeline_spatial`, `openpipeline_qc`,
`openpipeline_rapids`, `openpipeline_composed`) gains a
`create-documentation-pr.yml` that:

1. checks out the package repo **and** this repo,
2. runs `viash-io/viash-actions/pro/generate-documentation-qmd` with
   `output_dir: <this-repo>/reference/<package>/` and
   `dest_path: "{namespace}/{name}.qmd"`,
3. opens a PR against `openpipeline_docs`.

This mirrors the current `openpipeline` → `website` flow (see
`openpipeline/.github/workflows/create-documentation-pr.yml`), but each package
writes into its own package-scoped subfolder so the reference stays organized by
package and can never drift from the source configs.

**Open question for the team:** whether each package PRs here on its own release
cadence (independent, simplest) or a scheduled job aggregates all five (single
consistent snapshot). Independent PRs are recommended to start.
