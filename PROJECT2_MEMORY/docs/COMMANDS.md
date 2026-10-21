# Commands and collection provenance

The authoritative original MLC arguments are printed in each raw log; delay files are preserved with the loaded sweeps. Raw files keep their original bytes and names inside session archives. The final collector consolidates those workloads, adding common power logging. It is not a claim that the early sessions had the later power controls.

## Native builds actually used

From an x64 Developer Command Prompt at the project root:

```cmd
cl /nologo /O2 /W4 /arch:AVX2 /fp:precise src\cache_kernel.c /Febin\cache_kernel.exe /Fobin\cache_kernel.obj
cl /nologo /O2 /W4 src\page_chase.c advapi32.lib /Febin\page_chase.exe /Fobin\page_chase.obj
cl /nologo /W4 src\large_page_right.c advapi32.lib /Febin\large_page_right.exe /Fobin\large_page_right.obj
```

## Main kernel study

One WPR recording enclosed all 20 processes. For each of five trials, run the following configurations; reverse their size order on even trials:

| Elements | Repetitions | Three-array working set |
|---:|---:|---:|
| 1024 | 50000000 | 12 KiB |
| 16384 | 1000000 | 192 KiB |
| 262144 | 30000 | 3 MiB |
| 8388608 | 500 | 96 MiB |

```powershell
wpr -start "$project\scripts\pmu_test.wprp!PMUTest" -filemode
# Invoke bin\cache_kernel.exe elements repetitions and save each CSV.
# Stop in finally so the trace is saved even when the benchmark fails.
wpr -stop "$outDir\kernel_study.etl"
```

Each CSV contains PID/TID, CPU, QPC start/end/frequency, time, work counts and correctness. The trace must be matched to these absolute time windows. No whole-process PMC count is treated as the timed-loop count.

## Page-locality study

For five trials, use nodes 32,128,512,2048,8192, both spacing values 64 and 4096, normal allocation and 100000000 dependent loads. Reverse size and spacing order on even trials. Example:

```cmd
bin\page_chase.exe 512 4096 100000000 normal
```

Large-page setup used the helper's `--grant` and a new Windows sign-in. MLC `-L` failed/fell back or asserted. The native allocation attempt was:

```cmd
bin\page_chase.exe 512 4096 10000000 large
```

It returned VirtualAlloc error 1450; no latency measurement was produced.

## Main loaded sweep

```powershell
.\mlc.exe --loaded_latency -R -c0 -i0 "-k2,4,6,8,10" -e -r -D4096 -l128 -b131072 -Y -t2 "-g$delayFile"
```

Delay values are 30000,10000,3200,1600,800,400,200,100,50,0; reverse their order on even sweeps. The comma-containing CPU argument must remain quoted in PowerShell. A malformed earlier `-g` attempt is preserved under the earlier RW session but excluded from measurements.

The mixed comparison uses the same probe/worker settings with `-d0` instead of the delay file and selects `-R`, `-W3`, `-W5`, or `-W6`. The traffic workers are sequential; `-r` applies to the latency probe, while `-U` is the bandwidth randomization option.

## Access patterns

```powershell
# Sequential latency; use spacing 64,256,1024.
.\mlc.exe --idle_latency -e -c0 -i0 -l64 -b131072 -t2
# Randomized latency adds -r -D4096.
.\mlc.exe --idle_latency -e -c0 -i0 -l64 -b131072 -t2 -r -D4096
# Sequential bandwidth; throughput-only mode has no latency measurement.
.\mlc.exe --loaded_latency -T -R -k0 -e -b131072 -l64 -Y -d0 -t2
# Randomized bandwidth adds -U -n4096, not -r.
.\mlc.exe --loaded_latency -T -R -k0 -e -b131072 -l64 -Y -d0 -t2 -U -n4096
```

Patterns/strides have five trials. Early bandwidth config order was shuffled; the later latency sweep alternated ascending/reversed orders. The reconstructed collector uses explicit alternation and saves any new session separately.

The `-e` warning is meaningful for sequential probe latency: a prefetched hit is not an intrinsic DRAM service time. In throughput-only mode its latency warning does not create a latency measurement.

## Global-random latency follow-up

Source: `src/cache_latency.c`; session: `cache-latency-20261020-195943`. Build with:

```cmd
cl /nologo /O2 /W4 src\cache_latency.c advapi32.lib /Febin\cache_latency.exe /Fobin\cache_latency.obj
bin\cache_latency.exe 2097152 64 20000000 normal
```

The sweep uses nodes 512,4096,16384,65536,262144,524288,2097152 at 64-byte spacing, five runs per size. Use 100 million loads through 65536 nodes and 20 million for larger sizes. Odd runs ascend; even runs descend. The source creates one seeded Fisher–Yates random cycle, warms up with eight full traversals, pins CPU 0 and checks the final node. Allocation rounding is distinct from the active footprint; all successful trials use 4 KiB pages. `scripts/collect_cache_latency.ps1` reproduces these commands into a separate `runs/` session and records the Performance plan and hashes. The wrapper was reviewed, not executed here on Windows.
