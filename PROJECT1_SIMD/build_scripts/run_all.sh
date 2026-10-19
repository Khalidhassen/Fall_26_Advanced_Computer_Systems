#!/usr/bin/env bash
# Run on the original laptop. New results never overwrite data/raw.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p runs
run_dir=$(mktemp -d "$PWD/runs/run-XXXXXXXX")
cp ./*.c ./build.sh ./run_baseline.sh ./run_layout.sh ./run_stride.sh ./run_types.sh ./run_bandwidth.sh "$run_dir/"
cd "$run_dir"
mkdir -p evidence
{ uname -a; cat /etc/os-release; lscpu; gcc --version; } > evidence/environment.txt
bash build.sh
bash run_baseline.sh
bash run_layout.sh
bash run_stride.sh
bash run_types.sh
bash run_bandwidth.sh
for item in 'layout_simd multiply' 'stride_auto multiply_stride' 'dot_simd dot' 'axpy_simd axpy' 'bandwidth copy_kernel'; do
 read -r exe symbol <<< "$item"
 objdump -d -Mintel --disassemble="$symbol" "$exe" > "evidence/${symbol}_assembly.txt"
done
echo "New results saved separately in $run_dir"
