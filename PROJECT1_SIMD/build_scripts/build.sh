#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p evidence_generated
cc=${CC:-gcc}
for build in scalar default native; do
 flags=(-O3 -std=c11 -Wall -Wextra)
 case "$build" in
 scalar) flags+=(-march=native -fno-tree-vectorize);;
 native) flags+=(-march=native);;
 esac
 suffix=$build
 [[ "$build" == native ]] && suffix=simd
 "$cc" "${flags[@]}" main.c multiply.c -o "multiply_${suffix}" 2> "evidence_generated/multiply_${build}.txt"
 "$cc" "${flags[@]}" main_axpy.c axpy.c -o "axpy_${suffix}" 2> "evidence_generated/axpy_${build}.txt"
 "$cc" -O3 -march=native -std=c11 -Wall -Wextra -c main_dot.c -o main_dot.o
 "$cc" "${flags[@]}" -ffast-math -fopt-info-vec-all -c dot.c -o "dot_${build}.o" 2> "evidence_generated/dot_${build}.txt"
 "$cc" main_dot.o "dot_${build}.o" -o "dot_${suffix}"
done
cp multiply_scalar scalar
cp multiply_simd simd
for suffix in scalar simd; do
 flags=(-O3 -march=native)
 [[ "$suffix" == scalar ]] && flags+=(-fno-tree-vectorize)
 "$cc" "${flags[@]}" main_layout.c multiply.c -o "layout_${suffix}"
 stride_suffix=$suffix
 [[ "$suffix" == simd ]] && stride_suffix=auto
 "$cc" "${flags[@]}" main_stride.c multiply_stride.c -o "stride_${stride_suffix}"
done
"$cc" -O3 -march=native -fno-tree-loop-distribute-patterns -fopt-info-vec-optimized main_bandwidth.c copy_kernel.c -o bandwidth 2> evidence_generated/bandwidth.txt
