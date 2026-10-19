#!/usr/bin/env bash
set -euo pipefail

mkdir -p evidence

# Build each data type in three configurations.
for dtype in float double; do
    if [[ "$dtype" == "float" ]]; then
        driver="main_layout.c"
        kernel="multiply.c"
    else
        driver="main_double.c"
        kernel="multiply_double.c"
    fi

    # Optimized scalar, targeting this CPU.
    gcc -O3 -march=native -fno-tree-vectorize \
        "$driver" "$kernel" -o "types_${dtype}_scalar"

    # Auto-vectorization using GCC's default CPU target.
    gcc -O3 -fopt-info-vec-all \
        "$driver" "$kernel" -o "types_${dtype}_default" \
        2> "evidence/types_${dtype}_default.txt"

    # Auto-vectorization targeting this CPU.
    gcc -O3 -march=native -fopt-info-vec-all \
        "$driver" "$kernel" -o "types_${dtype}_native" \
        2> "evidence/types_${dtype}_native.txt"
done

# Check every executable before beginning the sweep.
for dtype in float double; do
    for build in scalar default native; do
        "./types_${dtype}_${build}" 1024 1000 0 > /dev/null
    done
done

output="types_results.csv"

echo "dtype,build,run,n,repetitions,offset_bytes,total_seconds,us_per_pass,gflops,correctness" > "$output"

for n in 1024 16384 262144 8388608; do
    case "$n" in
        1024) repetitions=1000000 ;;
        16384) repetitions=100000 ;;
        262144) repetitions=2000 ;;
        8388608) repetitions=100 ;;
    esac

    for run in 1 2 3 4 5; do
        # Alternate order to reduce systematic ordering effects.
        dtypes=(float double)
        builds=(scalar default native)

        if (( run % 2 == 0 )); then
            dtypes=(double float)
            builds=(native default scalar)
        fi

        for dtype in "${dtypes[@]}"; do
            for build in "${builds[@]}"; do
                row=$("./types_${dtype}_${build}" \
                    "$n" "$repetitions" 0)

                printf '%s,%s,%s,%s\n' \
                    "$dtype" "$build" "$run" "$row" >> "$output"
            done
        done

        echo "Finished n=$n, run=$run"
    done
done

echo "Saved $output"