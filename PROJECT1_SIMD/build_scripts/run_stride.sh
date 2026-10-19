#!/usr/bin/env bash
set -euo pipefail

output="stride_results.csv"

echo "build,run,length,stride,processed,repetitions,total_seconds,ns_per_element,gflops,useful_gib_s,correctness" > "$output"

for length in 1024 8388608; do
    repetitions=1000000
    if (( length == 8388608 )); then
        repetitions=100
    fi

    for stride in 1 2 4 8; do
        for run in 1 2 3 4 5; do
            builds=(scalar auto)
            if (( run % 2 == 0 )); then
                builds=(auto scalar)
            fi

            for build in "${builds[@]}"; do
                row=$("./stride_${build}" \
                    "$length" "$repetitions" "$stride")
                printf '%s,%s,%s\n' \
                    "$build" "$run" "$row" >> "$output"
            done
        done
        echo "Finished length=$length, stride=$stride"
    done
done

echo "Saved $output"