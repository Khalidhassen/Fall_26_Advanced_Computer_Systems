# Measurement environment

| Item | Recorded configuration |
|---|---|
| Machine | My ASUS-TUF laptop; I kept it plugged into AC power |
| CPU | Intel Core i7-12700H; native Windows reports 14 cores / 20 logical processors |
| Core topology | Six P-cores, each with two logical processors; eight single-thread E-cores |
| Logical P-core pairs | (0,1), (2,3), (4,5), (6,7), (8,9), (10,11) |
| Logical E-cores | 12–19 |
| NUMA | One node, containing all 20 logical processors |
| P-core caches | Coreinfo reports 48 KB L1 data, 32 KB L1 instruction, and a rounded 1 MB L2 display per P-core |
| E-core caches | 32 KB L1 data, 64 KB L1 instruction; logical CPUs 12–15 and 16–19 each share a reported 2 MB L2 |
| LLC / cache line | Reported shared 24 MB L3; 64-byte cache lines |
| Memory | Two 8 GiB SK Hynix HMAG68EXNSA051N modules, 16 GiB total; Windows reports Speed=3200 and ConfiguredClockSpeed=3200. Timings and channel operating mode were not independently measured. |
| OS | Windows 11 Home; version 10.0.26300, build 26300 |
| Native compiler | MSVC x64 19.51.36260; Visual Studio 2026 Developer Command Prompt 18.11.0, as recorded in the supplied console output |
| MLC | Intel Memory Latency Checker 3.13, Windows build |
| Counters | Windows WPR/ETW CSwitch profile; InstructionRetired, LLCMisses, TotalCycles identified from trace metadata |
| Timing | Native benchmarks use QueryPerformanceCounter; reported frequency 10,000,000 ticks/s. This is the timer frequency, not CPU frequency. |
| Analysis runtime | Python 3.12, NumPy 2.3.5, Matplotlib 3.10.8, dissect.etl 3.14 |

## Power, frequency, and isolation

The initial environment snapshot reported the OEM **Silent** power scheme. It does not prove that scheme was active during every earlier run. Early cache, bandwidth, and spacing sessions do not have bracketed power logs; their power state is therefore recorded as unverified.

The Performance scheme was selected at 12:37 local time on October 20, 2026. Its GUID on this laptop is `27fa6203-3987-4dcc-918d-748559d549ec`. The Performance loaded sweep, kernel study, page-locality study, later pattern-latency sweep and mixed-latency study have power evidence before and after their collection. A sign-out/sign-in restored Silent, which was observed before the large-page retry; Performance was then selected again.

Power schemes are evidence of requested policy, not a fixed clock or fan speed. Frequency was not locked, actual per-trial core frequency was not captured, and boost, temperature and background work could vary. No claim of a fixed 4.7 GHz clock is made.

Native benchmarks pin their main thread to logical CPU 0. MLC probes use `-c0 -i0`. Five-worker loaded/mixed tests request logical CPUs 2,4,6,8,10, one thread from each other P-core, excluding CPU 1, the probe's SMT sibling. SMT remained enabled. The sibling and worker cores were not reserved against Windows or other applications. No real-time priority or OS-wide CPU isolation was configured.

MLC's `-e` leaves hardware prefetcher settings unchanged. Default-page results report or use 4 KiB pages. The benchmark enables `SeLockMemoryPrivilege` when explicitly requesting large pages, but allocation still returned Windows error 1450. Large-page latency is unavailable.

## Evidence

The byte-preserved [environment archive](data/raw/environment-and-setup.zip) contains `windows_environment.txt`, `core_topology.txt`, `windows_pmc_sources.txt`, the power-policy timestamp and setup logs. Per-session ZIPs contain power snapshots and source/executable hash logs where collected. The raw ETL headers record zero lost events and buffers for the main kernel study. The exact WPR application version was not separately captured.

Windows is the measurement host for this project. The earlier SIMD project used WSL; its topology, times and counter limitations are not pooled into these results.
