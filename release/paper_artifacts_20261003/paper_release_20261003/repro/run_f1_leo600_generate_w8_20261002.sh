#!/usr/bin/env bash
set -uo pipefail
status_dir=/mnt/data/BRPHM/rul-space/work/f1_leo600_run1_20261002
exit_file="$status_dir/generator_w8.exitcode"
tmp_file="$exit_file.tmp.$$"
taskset -c 0-7 nice -n 15 ionice -c 3 matlab -batch "run('/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_generate_w8_20261002.m')"
rc=$?
printf '%s\n' "$rc" > "$tmp_file"
mv "$tmp_file" "$exit_file"
exit "$rc"
