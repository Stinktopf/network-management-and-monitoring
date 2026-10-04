#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/slides/nmm.md"
OUT="$ROOT/slides/exports"

mkdir -p "$OUT"

format="${1:-html}"

export_one() {
  local fmt="$1"
  local target="$OUT/nmm.$fmt"

  case "$fmt" in
    html)
      npx --yes @marp-team/marp-cli "$SRC" \
        --html \
        --allow-local-files \
        -o "$target"
      ;;
    pdf)
      npx --yes @marp-team/marp-cli "$SRC" \
        --pdf \
        --allow-local-files \
        -o "$target"
      ;;
    pptx)
      npx --yes @marp-team/marp-cli "$SRC" \
        --pptx \
        --allow-local-files \
        -o "$target"
      ;;
    *)
      echo "Unknown format: $fmt" >&2
      echo "Usage: $0 [html|pdf|pptx|all]" >&2
      exit 2
      ;;
  esac

  echo "Generated: ${target#$ROOT/}"
}

case "$format" in
  all)
    export_one html
    export_one pdf
    export_one pptx
    ;;
  html|pdf|pptx)
    export_one "$format"
    ;;
  *)
    echo "Usage: $0 [html|pdf|pptx|all]" >&2
    exit 2
    ;;
esac
