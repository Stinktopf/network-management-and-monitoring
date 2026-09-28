#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
ui_section 'Restore healthy network baseline'
bash scripts/clear-routing.sh || true
bash scripts/clear-link.sh || true
bash scripts/traffic.sh stop || true
bash scripts/apply-capacity-profile.sh
ui_hint 'Allow a few seconds for routing convergence.'
bash scripts/wait-healthy.sh
