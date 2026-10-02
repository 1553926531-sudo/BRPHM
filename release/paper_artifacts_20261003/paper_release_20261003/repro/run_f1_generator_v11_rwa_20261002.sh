#!/usr/bin/env bash
set -euo pipefail
exec matlab -batch "cd('/mnt/data/BRPHM/rul-space/work/paper/repro'); run('run_f1_generator_v11_rwa_20261002.m')"
