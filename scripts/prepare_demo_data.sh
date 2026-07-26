#!/usr/bin/env bash
# Generate the two pre-computed .h5mu samples the Quickstart uses.
#
# Downloads two small public 10x PBMC filtered count matrices (different
# chemistries -> a technical batch effect for integration to correct) and
# converts each to MuData (.h5mu) with openpipeline's from_10xh5_to_h5mu. Upload
# the two resulting .h5mu to your demo host and point get-started/index.qmd
# (step 2) at them.
#
# The Quickstart deliberately starts from these pre-computed counts, so the demo
# needs no Cell Ranger run and no genome reference. (Cell Ranger from raw FASTQ is
# covered separately in the ingestion guide.)
#
# Requires: nextflow, docker, curl.
#
# Usage:
#   scripts/prepare_demo_data.sh [OUTPUT_DIR]     (default: ./demo_data)

set -euo pipefail

OUT="${1:-./demo_data}"
export NXF_VER="${NXF_VER:-25.10.2}"   # openpipeline needs a compatible Nextflow

# sample id  ->  10x filtered_feature_bc_matrix.h5 URL. Uses the S3 origin; the
# cf.10xgenomics.com CDN blocks scripted downloads. Edit to pick your two
# datasets (the ids become the .h5mu filenames the Quickstart curls).
SAMPLES=(
  "pbmc_1k_v2|https://s3-us-west-2.amazonaws.com/10x.files/samples/cell-exp/3.0.0/pbmc_1k_v2/pbmc_1k_v2_filtered_feature_bc_matrix.h5"
  "pbmc_1k_v3|https://s3-us-west-2.amazonaws.com/10x.files/samples/cell-exp/3.0.0/pbmc_1k_v3/pbmc_1k_v3_filtered_feature_bc_matrix.h5"
)

command -v nextflow >/dev/null 2>&1 || { echo "ERROR: nextflow not found on PATH." >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl not found on PATH." >&2; exit 1; }

# One-time: tell Nextflow where to pull openpipeline from.
scm="$HOME/.nextflow/scm"
if ! grep -q "packages.viash-hub.com" "$scm" 2>/dev/null; then
  mkdir -p "$HOME/.nextflow"
  cat >> "$scm" <<'EOM'
providers.vsh.platform = "gitea"
providers.vsh.server = "packages.viash-hub.com"
EOM
fi

mkdir -p "$OUT"
for entry in "${SAMPLES[@]}"; do
  id="${entry%%|*}"
  url="${entry#*|}"
  echo "=== $id ==="
  h5="$OUT/${id}_filtered_feature_bc_matrix.h5"

  echo "Downloading counts..."
  curl -fL --retry 3 -o "$h5" "$url"

  echo "Converting to MuData (.h5mu)..."
  nextflow run https://packages.viash-hub.com/vsh/openpipeline.git \
    -r v4.2.0 -latest -profile docker \
    -main-script target/nextflow/convert/from_10xh5_to_h5mu/main.nf \
    --id "$id" \
    --input "$h5" \
    --output "${id}.h5mu" \
    --publish_dir "$OUT"

  rm -f "$h5"
done

echo
echo "Done. Quickstart demo objects in: $OUT"
find "$OUT" -name '*.h5mu' | sort | sed 's/^/  /'
echo
echo "Next: upload the two .h5mu to your demo host, then set <demo-data-host> in"
echo "get-started/index.qmd (step 2) to match, keeping the pbmc_1k_v2 / pbmc_1k_v3 filenames."
