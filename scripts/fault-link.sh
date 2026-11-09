#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ui_info 'Applying SR Linux candidate configuration on edge01.bob1.reefnet.test'
srl_apply edge01 <<'CFG'
enter candidate
set / interface ethernet-1/4 admin-state disable
commit now
CFG
ui_warn 'FAULT ACTIVE · ReefNet core-b (edge01 ethernet-1/4) administratively down'
