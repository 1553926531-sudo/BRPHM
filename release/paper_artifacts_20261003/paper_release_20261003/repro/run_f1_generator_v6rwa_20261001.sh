#!/usr/bin/env bash
set -u
cd /mnt/data/BRPHM/rul-space/work/paper/repro
exec matlab -batch "cd('/mnt/data/BRPHM/rul-space/work/paper/repro'); run('run_f1_generator_v6rwa_20261001.m')"
