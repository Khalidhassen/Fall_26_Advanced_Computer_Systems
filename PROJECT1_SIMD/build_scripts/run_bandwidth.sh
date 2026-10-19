#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo 'run,n,repetitions,total_seconds,useful_gib_s,modeled_traffic_gib_s,correctness' > bandwidth_results.csv
for run in 1 2 3 4 5; do
 row=$(./bandwidth)
 printf '%s,%s\n' "$run" "$row" >> bandwidth_results.csv
done
