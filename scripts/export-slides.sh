#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/slides"
case "${1:-html}" in
  all) npm run build ;;
  html) npm run build:html ;;
  pdf|pptx)
    format=$1
    mkdir -p exports
    node tools/sync-theme.mjs
    export CHROME_NO_SANDBOX=1
    node node_modules/@marp-team/marp-cli/marp-cli.js nmm.md \
      --html "--$format" --allow-local-files \
      --browser-path "${CHROME_PATH:-/usr/bin/chromium}" --browser-timeout 120 \
      -o "exports/nmm.$format"
    if [[ "$format" == pdf ]]; then
      node node_modules/@marp-team/marp-cli/marp-cli.js resources/CHEATSHEET.md \
        --html --pdf --allow-local-files \
        --browser-path "${CHROME_PATH:-/usr/bin/chromium}" --browser-timeout 120 \
        -o exports/cheatsheet.pdf
    fi
    ;;
  *) echo 'Usage: scripts/export-slides.sh [html|pdf|pptx|all]' >&2; exit 2 ;;
esac
