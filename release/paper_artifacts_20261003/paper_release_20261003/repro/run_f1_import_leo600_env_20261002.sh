#!/usr/bin/env bash
set -euo pipefail
export F1_CREATED_UTC="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
exec taskset -c 7 nice -n 19 ionice -c 3 matlab -batch "run('/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_import_leo600_env_20261002.m')"
