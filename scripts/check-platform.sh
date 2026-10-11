#!/usr/bin/env bash
# Shared runtime requirements for setup and scenario preflight.
if [[ $(uname -s) != Linux ]]; then
  printf '%s\n' 'The lab requires a Linux host or VM.' \
    'On macOS, run the repository, Docker and Containerlab inside a Linux VM.' \
    'See README.md, Setup. Docker Desktop alone does not provide this shell environment.' >&2
  exit 1
fi
if (( BASH_VERSINFO[0] < 4 )); then
  printf '%s\n' 'The lab scripts require Bash 4 or newer.' >&2
  exit 1
fi
