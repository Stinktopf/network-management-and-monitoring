#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
mode=${1:-missing}
mkdir -p .state/pulls
images=(
  ghcr.io/nokia/srlinux:25.10
  ghcr.io/srl-labs/network-multitool:v0.9.0
  ghcr.io/openconfig/gnmic:0.45.0
  quay.io/prometheus/prometheus:v3.11.3
  grafana/grafana:13.0.1
  grafana/alloy:v1.16.0
  grafana/loki:3.7.1
  netboxcommunity/netbox:v4.7-5.1.1
  postgres:18-alpine
  valkey/valkey:9.1-alpine
)
missing=()
for image in "${images[@]}"; do
  if [[ "$mode" == "--all" ]] || ! docker image inspect "$image" >/dev/null 2>&1; then missing+=("$image"); fi
done

if ((${#missing[@]})); then
  ui_info "Preparing ${#missing[@]} pinned classroom images"
  for image in "${missing[@]}"; do
    safe=${image//\//_}; safe=${safe//:/_}
    ui_section "Image · $image"
    ui_cmd docker pull "$image"
    docker pull "$image" 2>&1 | tee ".state/pulls/${safe}.log"
    ui_ok "$image"
  done
else
  ui_ok 'All pinned classroom images are already present'
fi

if [[ "$mode" == "--all" ]] || ! docker image inspect ai5049-tools:bob1-v20 >/dev/null 2>&1; then
  ui_section 'Local classroom tools image'
  ui_cmd docker build -t ai5049-tools:bob1-v20 tools
  docker build -t ai5049-tools:bob1-v20 tools 2>&1 | tee .state/tools-build.log
  ui_ok 'ai5049-tools:bob1-v20 built'
else
  ui_ok 'Local tools image · ai5049-tools:bob1-v20'
fi
