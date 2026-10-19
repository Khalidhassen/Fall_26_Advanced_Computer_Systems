#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for kernel in multiply axpy dot; do
 output="${kernel}_results_new.txt"
 : > "$output"
 for config in "1024 200000" "16384 20000" "262144 2000" "8388608 100"; do
  read -r n reps <<< "$config"
  for run in 1 2 3; do
   for build in scalar simd; do
    label=scalar
    [[ "$build" == simd ]] && label=SIMD
    echo "Configuration: $config | Run: $run | $label" >> "$output"
    "./${kernel}_${build}" "$n" "$reps" >> "$output"
   done
  done
 done
 # Additional default-build measurements are NEW, not part of the saved original dataset.
 output="${kernel}_default_results_new.txt"
 : > "$output"
 for config in "1024 200000" "16384 20000" "262144 2000" "8388608 100"; do
  read -r n reps <<< "$config"
  for run in 1 2 3; do
   echo "Configuration: $config | Run: $run | default" >> "$output"
   "./${kernel}_default" "$n" "$reps" >> "$output"
  done
 done
done
