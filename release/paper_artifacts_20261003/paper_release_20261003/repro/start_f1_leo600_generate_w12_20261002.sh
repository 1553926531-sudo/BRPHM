#!/usr/bin/env bash
set -euo pipefail
status_dir=/mnt/data/BRPHM/rul-space/work/f1_leo600_run1_20261002
run_file=/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_generate_w12_20261002.sh
pid_file="$status_dir/generator_w12.pid"
log_file="$status_dir/generator_w12.log"
exit_file="$status_dir/generator_w12.exitcode"
if [ -s "$pid_file" ]; then
  old_pid=$(<"$pid_file")
  if kill -0 "$old_pid" 2>/dev/null; then
    printf 'F1 generator already active: %s\n' "$old_pid" >&2
    exit 2
  fi
fi
if [ -e "$exit_file" ]; then
  printf 'F1 generator exit code already exists: %s\n' "$exit_file" >&2
  exit 3
fi
nohup bash "$run_file" >"$log_file" 2>&1 </dev/null &
printf '%s\n' "$!" >"$pid_file"
printf 'F1 generator launched: %s\n' "$(<"$pid_file")"
