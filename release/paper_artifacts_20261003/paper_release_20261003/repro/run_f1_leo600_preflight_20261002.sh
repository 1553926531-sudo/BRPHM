#!/usr/bin/env bash
set -euo pipefail
exec taskset -c 0,1 nice -n 15 ionice -c 3 matlab -batch "run('/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_preflight_20261002.m')"
