#!/usr/bin/env bash
set -euo pipefail
exec matlab -batch "cd('/mnt/data/BRPHM/rul-space/work/paper/repro'); run('run_f1_single_S918_20261002.m')"
