#!/usr/bin/env bash
set -euo pipefail

output="layout_results.csv"

echo "build,run,n,repetitions,offset_bytes,total_seconds,us_per_pass,gflops,correctness" > "$output"

for n in 1024 1025 1026 1027 1028 1029 1030 1031; do
    for offset in 0 1; do
        for run in 1 2 3 4 5; do
            # Alternate build order between trials.
            builds=(scalar simd)
            if (( run % 2 == 0 )); then
                builds=(simd scalar)
            fi

            for build in "${builds[@]}"; do
                row=$("./layout_${build}" "$n" 1000000 "$offset")
                printf '%s,%s,%s\n' "$build" "$run" "$row" >> "$output"
            done
        done
        echo "Finished n=$n, offset=$offset"
    done
done

echo "Saved $output"