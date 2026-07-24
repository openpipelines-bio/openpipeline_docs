#!/usr/bin/env bash
# Prepare lightweight two-sample demo data for the "first pipeline" tutorial.
#
# Downloads two public 10x Genomics 3' PBMC datasets (~1k cells each, different
# chemistry -> a real batch effect worth integrating), subsamples the reads so a
# full Cell Ranger -> process_samples -> integration run finishes in minutes,
# and lays the result out ready to upload to a demo bucket.
#
# Why these two: both are plain single-sample Gene Expression runs, so each maps
# with ingestion/cellranger_mapping and converts cleanly to one .h5mu. This is
# deliberately NOT barcode-multiplexed data (e.g. Flex 4-plex): the
# convert/from_cellranger_multi_to_h5mu step "does not allow parsing the output
# from cell barcode demultiplexing", so multiplexed data cannot flow through to
# integration.
#
# The subsampled reads only need to be hosted once; the tutorial then downloads
# a few hundred MB instead of ~10 GB.
#
# Requires: curl, tar, gzip, and seqkit (https://bioinf.shenwei.me/seqkit/).
#
# Usage:
#   scripts/prepare_demo_data.sh [OUTPUT_DIR] [N_READS]
#     OUTPUT_DIR   where to write the subsampled data   (default: ./demo_data)
#     N_READS      reads to keep per FASTQ file          (default: 3000000)
#
# Tuning N_READS: too few reads and Cell Ranger calls almost no cells (an empty
# object breaks process_samples/integration); more reads means a bigger upload
# and a slower run. It interacts with the reference the tutorial uses: against
# the chr1-only reference (below) only chr1 reads map, so keep N_READS on the
# higher side there. Start at the default, bump it if too few cells survive.
#
# After running, upload OUTPUT_DIR/* to your demo bucket and point the tutorial
# at it. The matching chr1-only Cell Ranger reference is already public:
#   https://openpipelines-data.s3.amazonaws.com/reference_gencodev41_chr1/reference_cellranger.tar.gz

set -euo pipefail

OUT="${1:-./demo_data}"
N_READS="${2:-3000000}"

# Origin that serves 10x public sample files to non-browser clients (the cf.
# 10xgenomics.com CDN blocks scripted downloads; this S3 origin does not).
BASE="https://s3-us-west-2.amazonaws.com/10x.files/samples/cell-exp/3.0.0"

# Datasets to include. Same tissue (human PBMC), different 10x chemistry, which
# is the batch effect the integration step corrects. Edit this list to swap in
# other single-sample Gene Expression datasets.
SAMPLES=(
  "pbmc_1k_v2"
  "pbmc_1k_v3"
)

command -v seqkit >/dev/null 2>&1 || {
  echo "ERROR: seqkit not found on PATH. Install it: https://bioinf.shenwei.me/seqkit/" >&2
  exit 1
}

mkdir -p "$OUT"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

for s in "${SAMPLES[@]}"; do
  echo "=== $s ==="
  tar_path="$tmp/${s}_fastqs.tar"
  echo "Downloading ${s} FASTQs..."
  curl -fL --retry 3 -o "$tar_path" "${BASE}/${s}/${s}_fastqs.tar"

  echo "Extracting..."
  ext="$tmp/${s}_extracted"
  mkdir -p "$ext"
  tar -xf "$tar_path" -C "$ext"

  # Subsample every R1/R2 pair, keeping the original filenames so the output
  # still reads as standard bcl2fastq/mkfastq naming to Cell Ranger. seqkit head
  # takes the first N records deterministically, so R1 and R2 stay paired.
  dest="$OUT/$s"
  mkdir -p "$dest"
  while IFS= read -r r1; do
    r2="${r1/_R1_/_R2_}"
    for read_file in "$r1" "$r2"; do
      if [ ! -f "$read_file" ]; then
        echo "  WARN: missing mate for $(basename "$r1"), skipping" >&2
        continue
      fi
      base="$(basename "$read_file")"
      echo "  subsampling $base -> first $N_READS reads"
      seqkit head -n "$N_READS" "$read_file" | gzip > "$dest/$base"
    done
  done < <(find "$ext" -name '*_R1_*.fastq.gz' | sort)

  echo "  wrote: $dest"
done

echo
echo "Done. Subsampled demo data in: $OUT"
echo "Upload the following to your demo bucket, then point the tutorial at it:"
find "$OUT" -type f | sort | sed 's/^/  /'
