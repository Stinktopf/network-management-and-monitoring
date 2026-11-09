#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/ui.sh"

TOPO="${TOPO:-lab.clab.yml}"

clab_container() {
  printf 'clab-ai5049-%s\n' "${1:?node required}"
}

srl_apply() {
  local node=${1:?node required}
  docker exec -i "clab-ai5049-${node}" bash -lc \
    "su -s /bin/bash admin -c '/opt/srlinux/bin/sr_cli -ed'"
}

srl_show() {
  local node=${1:?node required}
  shift
  local cmd="$*"
  docker exec "clab-ai5049-${node}" bash -lc \
    "su -s /bin/bash admin -c '/opt/srlinux/bin/sr_cli -d \"${cmd}\"'"
}

ping4() {
  local node=$1 target=$2
  docker exec "$(clab_container "$node")" ping -4 -c 1 -W 1 "$target" >/dev/null 2>&1
}

ping6() {
  local node=$1 target=$2
  docker exec "$(clab_container "$node")" ping -6 -c 1 -W 1 "$target" >/dev/null 2>&1
}
