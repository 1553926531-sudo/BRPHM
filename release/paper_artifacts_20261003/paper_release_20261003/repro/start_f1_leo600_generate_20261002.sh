#!/usr/bin/env bash
set -euo pipefail
pid_file=/mnt/data/BRPHM/rul-space/work/f1_leo600_run1_20261002/generator.pid
run_file=/mnt/data/BRPHM/rul-space/work/paper/repro/run_f1_leo600_generate_20261002.sh
log_file=/mnt/data/BRPHM/rul-space/work/f1_leo600_run1_20261002/generator.log
if [ -s "$pid_file" ]; then
  old_pid=$(<"$pid_file")
  if kill -0 "$old_pid" 2>/dev/null; then
    printf 'F1 generator already active: %s\n' "$old_pid" >&2
    exit 2
  fi
fi
nohup bash "$run_file" >"$log_file" 2>&1 </dev/null &
printf '%s\n' "$!" >"$pid_file"
printf 'F1 generator launched: %s\n' "$(<"$pid_file")"
