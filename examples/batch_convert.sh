#!/usr/bin/env bash
# Batch convert all .epub files in a directory to PDF with JSON sidecars.
# Usage: ./batch_convert.sh /path/to/epubs /path/to/output [workers]

set -euo pipefail

INPUT_DIR="${1:-.}"
OUTPUT_DIR="${2:-./pdf-output}"
WORKERS="${3:-2}"

mkdir -p "$OUTPUT_DIR"

# Collect all epub files and run epub2pdf batch.
mapfile -t EPUBS < <(find "$INPUT_DIR" -maxdepth 1 -name '*.epub' | sort)

if [ ${#EPUBS[@]} -eq 0 ]; then
  echo "No .epub files found in $INPUT_DIR"
  exit 1
fi

epub2pdf batch \
  --output-dir "$OUTPUT_DIR" \
  --workers "$WORKERS" \
  --sidecar-json \
  --engine weasyprint \
  "${EPUBS[@]}"
