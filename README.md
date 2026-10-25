# Advanced Computer Systems: Performance Across Compute, Memory, and Storage

**Khalid Hassen · ECSE 4320/6320 · Fall 2026**

I completed three related performance studies on my ASUS-TUF laptop: SIMD numerical kernels, cache and memory access, and NVMe SSD I/O. Together, they examine how locality, data movement, concurrency, and measurement choices affect performance. This README summarizes the findings, environments, AI assistance, lecture connections, and rubric evidence. The project folders contain the detailed reports and available supporting files.

**Scope of this overview:** This document reviews the uploaded repository snapshot on October 25, 2026. It distinguishes reported experimental results from evidence actually present in that snapshot. It does not claim that every rubric requirement is fully satisfied or predict an instructor-assigned score.

## Project guide

| Project | Main question | Detailed report | Collected observations reported by the project |
|---|---|---|---|
| [Project 1: SIMD](PROJECT1_SIMD/) | When does vectorization improve numerical-loop performance? | [SIMD report and README](PROJECT1_SIMD/README.md) | 437 successful benchmark trials across baseline, layout, stride, type, and copy studies |
| [Project 2: Cache and memory](PROJECT2_MEMORY/) | How do footprint, access pattern, page locality, and competing traffic change memory performance? | [Memory report](PROJECT2_MEMORY/REPORT.md) | 360 main MLC observations, 20 instrumented kernel trials, 50 page-locality trials, 35 global-random trials, and 50 separate follow-up timing trials |
| [Project 3: SSD](PROJECT3_SSD/) | How do block size, queue depth, mix, caching, and device state affect storage performance? | [SSD report](PROJECT3_SSD/REPORT.md) | 141 main measurements; 150 fio jobs including preparation, pilots, and warm-ups |

The counts describe different units of observation and should not be added into one statistical sample. Results from different sessions and operating systems are kept separate. Repeated-trial summaries generally use medians and observed minimum–maximum ranges; those ranges are not confidence intervals. A median of per-run percentiles is not a pooled percentile.

## Measurement environments

All three projects used the same laptop, but Project 1 ran in WSL2 and Projects 2–3 ran natively on Windows. Their scheduling, compiler, timing, and counter behavior are therefore not interchangeable.

| Item | Project 1: SIMD | Project 2: Cache/memory | Project 3: SSD |
|---|---|---|---|
| CPU | Intel Core i7-12700H, AVX2 available | Same processor; native Coreinfo shows 6 P-cores + 8 E-cores, 20 logical processors | Same processor |
| OS | Ubuntu 22.04.3 LTS under WSL2; kernel 5.15.133.1-microsoft-standard-WSL2 | Windows 11 Home, 10.0.26300, build 26300 | Windows 11 Home, 10.0.26300, build 26300 |
| Main tools | GCC 11.4.0; compiler vectorization reports; disassembly; attempted perf | Intel MLC 3.13; MSVC x64 19.51.36260; Coreinfo; WPR/ETW; custom C kernels | Native fio 3.43 with windowsaio; Windows storage inventory/reliability queries |
| Build policy | `-O3 -march=native`; scalar adds `-fno-tree-vectorize`; default-target multiply uses `-O3`; dot uses documented fast-math policy | Multiplication uses `/O2 /arch:AVX2 /fp:precise`; dependent-chain programs use `/O2` | No custom compiled SSD kernel; workload controlled by fio configs |
| Timer | CLOCK_MONOTONIC | QueryPerformanceCounter, reported 10 MHz timer frequency; MLC output | fio runtime and total latency statistics from `lat_ns` |
| Placement | Single-threaded kernels; no physical-core affinity | Native benchmarks/probe on logical CPU 0; loaded workers requested on 2,4,6,8,10; SMT enabled | One fio job; no documented CPU affinity |
| Power | Plugged in; Windows High performance mode reported by me; actual clock not recorded | Early power policy unverified; later sessions bracketed by Performance snapshots; an OEM Silent-plan reset was documented | Performance plan recorded before/after archived studies; laptop reported plugged in |
| Frequency/isolation limits | No measured clock, temperature, or host-wide isolation | No fixed clock or OS-wide core isolation; Windows could use the same cores | Active system volume and background work were not isolated; actual PCIe link negotiation was not measured |

Native Windows inventory reported **16 GiB RAM**, comprising two 8 GiB SK Hynix modules with configured-speed value 3200, and one NUMA node. Coreinfo reported a shared 24 MB LLC and 64-byte cache lines. WSL's guest topology display differed from the physical hybrid-core layout; I do not treat the guest's “10 cores × 2 threads” display as the physical processor configuration.

Project 3 used the **NVMe Micron_2400_MTFDKBA1T0QFM**, firmware **V3MA003**, physical capacity **1,024,203,640,320 bytes** (about 953.9 GiB), on the **C: NTFS** system volume. Most main tests accessed a 2 GiB disposable file on a nearly full drive; the range study accessed its first 64 MiB, 256 MiB, or 2 GiB. All archived temperature snapshots returned 60°C, but no in-run temperature trace or confirmed throttling event was obtained. Blank or unusable reliability fields are treated as unavailable rather than zero.

Environment details: [SIMD evidence](PROJECT1_SIMD/evidence/environment.txt), [memory environment](PROJECT2_MEMORY/ENVIRONMENT.md), and [SSD environment](PROJECT3_SSD/ENVIRONMENT.md). Some native inventory information is transcribed from my terminal output rather than included as an original raw inventory file in this snapshot.

## Project 1 — SIMD Advantage Profiling

### Experiments and main findings

I compared single-threaded scalar and auto-vectorized elementwise multiplication, AXPY, and dot product across four array sizes. I then studied alignment, vector-width remainders, strides 1/2/4/8, float versus double, default versus native compiler targets, and a copy-derived roofline reference. The 437 successful trials comprise 72 baseline, 160 layout, 80 stride, 120 type/build, and 5 bandwidth trials.

| Elements per array | Multiply speedup | AXPY speedup | Dot-product speedup |
|---:|---:|---:|---:|
| 1,024 | 5.96× | 3.87× | 11.00× |
| 16,384 | 4.30× | 2.40× | 8.27× |
| 262,144 | 1.45× | 1.67× | 7.16× |
| 8,388,608 | 1.06× | 1.35× | 3.43× |

Speedup is median scalar time divided by median vector-build time. Multiplication's shrinking benefit is consistent with data movement becoming more limiting as its three-array footprint grows from 12 KiB to 96 MiB. Dot product retained more benefit, but its 11× small-array result is not proof that eight lanes alone provide an 11× gain; reduction dependencies, overhead, frequency, and placement were not isolated.

Other findings were:

- **Vectorization was verified.** Compiler reports and assembly show packed 256-bit multiplication over eight floats, with smaller vector/scalar remainder paths. AXPY and dot use packed FMA; FLOP accounting treats multiply-add as two operations.
- **Alignment mattered.** In the small-array layout study, shifting all three float-array addresses by four bytes increased vector-build median time by about 44–52%. A separate stable remainder penalty was not resolved.
- **Non-unit stride was a verified negative case.** The runtime stride-one path used packed arithmetic, while strides 2/4/8 took a scalar path. Large-array useful bandwidth fell from about 22.79 GiB/s at stride one to 2.82 GiB/s at stride eight. These are useful bytes, not measured DRAM traffic, and this was not a gather-instruction benchmark.
- **Precision and target width changed both execution and footprint.** Default/native multiplication used 128-/256-bit vectors. At 1,024 elements native was about 1.72× faster than default for either type. Native float took about half the time of native double, but equal element counts give double twice the footprint, so this does not isolate arithmetic precision alone.
- **Wider code did not always help.** In the later largest-size type session, native float speedup was approximately 1.02×, and native double was approximately 0.91×, with overlapping ranges and drift. I retain this result without claiming that vectorization inherently harms double precision.
- **The roofline interpretation was bandwidth-oriented.** The copy study measured 17.23 GiB/s median useful bandwidth. With explicitly modeled write-allocation traffic, the bandwidth reference predicted about 1.735 GFLOP/s for float multiply, near the observed 1.829 GFLOP/s in that session. The assumed compute peak and modeled traffic are not measured hardware limits.

Hardware cycles per element remain unavailable: WSL perf reported `<not supported>` for the requested cycle/instruction events. Nanoseconds per element were not relabeled as core cycles. The mislabeled earlier multiplication sweep is excluded and retained under `data/excluded/`; timing anomalies in valid runs were not removed. Separate assistant-environment code checks were not used as laptop benchmark results.

Evidence: [processed speedups](PROJECT1_SIMD/processed/baseline_speedup.csv), [validation counts](PROJECT1_SIMD/processed/validation.json), [compiler/disassembly evidence](PROJECT1_SIMD/evidence/), and [five figures](PROJECT1_SIMD/plots/).

## Project 2 — Cache and Memory Performance Profiling

### Experiments and main findings

I used MLC sweeps, a globally randomized dependent pointer chain, a vectorized multiplication kernel with WPR counters, and packed-versus-page-spread pointer layouts. The reported studies investigate locality, access granularity, loaded latency, read/write traffic, LLC misses, translation-related effects, and measurement pitfalls.

**Evidence qualification:** The numerical results below are reported in the included Project 2 report. The current repository snapshot lacks Project 2's source and raw/processed data folders, so these results cannot be independently regenerated from this snapshot alone.

| Global-random active footprint | Median dependent-load time |
|---|---:|
| 32 KiB | 1.607 ns/load |
| 256 KiB | 4.865 ns/load |
| 1 MiB | 6.514 ns/load |
| 4 MiB | 23.227 ns/load |
| 16 MiB | 85.991 ns/load |
| 32 MiB | 118.511 ns/load |
| 128 MiB | 130.303 ns/load |

The increasing times are consistent with moving beyond small fast-cache regions. However, the rise at 16 MiB occurred below the reported 24 MB LLC capacity. A clean LLC plateau and isolated intrinsic per-level latencies were not established; translation, conflicts, frequency, and other effects were not separated.

Other reported findings were:

- **Predictable accesses can look much faster.** At 128 MiB and 64-byte spacing, sequential MLC latency was 4.4 ns versus 35.1 ns for bounded-random access. Hardware prefetching and block locality make these different from an isolated global-random DRAM access.
- **Greater offered load increased probe latency.** In the Performance-plan loaded sweep, median estimated traffic bandwidth rose from 1.12 to 26.24 GB/s while probe latency rose from 89.36 to 151.99 ns. A practical near-peak point at delay 50 reached 24.85 GB/s and 142.38 ns, but a sharp physical saturation knee was not demonstrated.
- **Write-heavy traffic increased the reader's wait.** Under five-worker background traffic, median probe latency was 144.41 ns for read-only, 201.69 ns for the available MLC 75/25 preset, 297.86 ns for 50/50, and 498.58 ns for non-temporal writes. The 75/25 preset is not relabeled 70/30, and NT stores change store policy as well as mix.
- **LLC events correlated with multiplication runtime.** From 12 KiB to 96 MiB, median time increased from about 0.0443 to 0.5634 ns/element. The large case had roughly 0.140–0.142 LLCMisses events per element. Counter timing windows produced attribution bounds; misses per element are not a conditional LLC miss probability.
- **Page spreading was slower at larger node counts.** At 8,192 nodes, packed/spread median times were 4.029/13.341 ns per dependent load, about 3.31× apart. Translation overhead is plausible, but cache effects were not isolated and no valid TLB miss rate was obtained.
- **Large-page and TLB-counter failures were retained.** MLC first fell back to 4 KiB pages, and later large-page allocations failed, including Windows error 1450. An earlier STLB pilot signal did not reproduce in the repeated counter study. Flat counters were excluded rather than reported as zero TLB misses. The 50 follow-up timing trials remain separate from the earlier page study.

Little's Law and AMAT were used with explicit limits. Combining worker bandwidth with a different probe's latency does not measure worker concurrency. Likewise, multiplying LLC events per element by serial pointer-chase latency would ignore request overlap and the missing reference denominator. The report therefore treats those models as explanatory, not fitted hardware measurements.

The ten figures and [counter-attempt discussion](PROJECT2_MEMORY/docs/COUNTER_ATTEMPTS.md) are present, but the underlying missing evidence must be restored for reproducibility credit.

## Project 3 — SSD Performance Profiling

### Experiments and main findings

I used fio for QD1 baselines, a six-block-size/four-pattern sweep, random-read queue depths 1–256, four read/write mixes, a file-range comparison, a buffered-I/O pitfall, and three bounded sequential-write time series. The main count is 12 baseline + 72 block + 27 QD + 12 mix + 9 range + 6 cache + 3 write-series measurements = **141**.

| Requested QD, 4 KiB random reads | Median throughput | Mean total latency | p99.9 total latency |
|---:|---:|---:|---:|
| 1 | 26.62 MB/s | 152.96 µs | 757.76 µs |
| 8 | 238.60 MB/s | 128.39 µs | 643.07 µs |
| 16 | 342.96 MB/s | 160.71 µs | 913.41 µs |
| 32 | 428.82 MB/s | 218.71 µs | 1,482.75 µs |
| 64 | 380.85 MB/s | 423.62 µs | 3,129.34 µs |
| 128 | 425.17 MB/s | 695.85 µs | 4,685.82 µs |
| 256 | 426.12 MB/s | 1,319.93 µs | 8,978.43 µs |

Requested **QD32 was a practical knee** in this workload: further increases did not consistently improve throughput, while mean and tail latency increased markedly. At QD32, the median per-run Little's Law estimate, IOPS × mean total latency, was **22.85 outstanding requests**. It describes a fio-level estimate, not directly measured controller occupancy; requested depth is not constant achieved depth.

Additional findings were:

- **The original QD1 baseline had large write tails.** Median mean latency was 114 µs for 4 KiB random reads, 244 µs for random writes, 236 µs for 128 KiB sequential reads, and 5,321 µs for sequential writes. Sequential-write p99.9 was about 255 ms. That slower session remains separate from the later block sweep.
- **Larger blocks generally raised byte throughput.** From 4 to 256 KiB, random-read median throughput rose from 39 to 1,109 MB/s; sequential reads rose from 58 to 1,353 MB/s. Sequential writes reached 2,119 MB/s at 256 KiB in that QD1 session. These are observed workload results, not established maximum device throughput.
- **Mixed I/O worsened read latency.** At 4 KiB and requested QD32, total median throughput was 418/302/284/278 MB/s for read/write mixes 100/0, 70/30, 50/50, and 0/100. Read mean latency increased from 196 µs for read-only to about 364–378 µs for mixed conditions.
- **Smaller ranges did not consistently help.** Median throughput was about 405, 419, and 407 MB/s for 64 MiB, 256 MiB, and 2 GiB; the smallest range had worse p99 latency. This did not identify a device-cache boundary.
- **Buffered reads created a misleading performance gain.** At QD1 over a warmed 256 MiB range, buffered/direct median throughput was 248.02/24.52 MB/s, about 10.1× apart. Mean latency was 16.03/166.00 µs. No cache-hit rate was measured, so the result shows a cache-policy pitfall rather than uncached SSD capability.
- **Write performance varied strongly over time and between repeats.** Run 1 wrote 11.67 GiB in 120 seconds at 104 MB/s average; its first/last five logged intervals had median throughput near 1,877/30 MB/s. Runs 2 and 3 each completed 40 GiB in roughly 32–33 seconds at 1,352/1,303 MB/s. The recovery prevents a simple claim of a reproducible SLC-cache cliff. Neither GC nor thermal throttling was established as the cause.

The tests repeatedly overwrote a small disposable file rather than a raw device. They did not establish whole-drive steady state, maximum sequential throughput, maximum random-write IOPS, or negotiated PCIe-link saturation. End-of-job flushing was not equivalent to forcing every write durable. One-second latency logs contain averages; whole-run JSON percentiles were used for tails.

Evidence: [SSD report](PROJECT3_SSD/REPORT.md), [trial tables](PROJECT3_SSD/data/processed/), [raw results](PROJECT3_SSD/data/raw/), [configs](PROJECT3_SSD/configs/), and [nine figures](PROJECT3_SSD/plots/). The original pre-GitHub files passed the combined checks, but the current snapshot has the line-ending/hash issue described below.

## Connections to the lectures

The lecture references below use **PDF page numbers, including the title page**. Duplicate uploaded copies were identical; each deck is referenced once. The lecture PDFs were supplied for this review and are not included in this repository snapshot, so these are source references rather than links to nonexistent repository files.

| Lecture source | Concepts and pages | Connection to the projects |
|---|---|---|
| `Introduction.pdf` | Engineering loop, p.7; systems-thinking toolkit, p.8 | Across all projects I move from workload and hypothesis to measurement and interpretation. Locality, queueing, roofline, overhead, and bottleneck migration organize the findings. Negative results and failed counters show why polished output alone is not validation. |
| `Thread 1-1-1.pdf` | Dependencies and independent work, pp.3–5; superscalar width/ILP, pp.17–21 | Project 1's reduction recurrence differs from independent elementwise work. Project 2's dependent pointer chase deliberately limits overlap, unlike its streaming multiplication kernel. None of these tests directly measures reorder-buffer or issue-width behavior. |
| `Thread 1-1-2.pdf` | SIMD and imperfect lane scaling, pp.3–5; SMT/shared resources, pp.8–11; Amdahl's Law, pp.14–15 | Project 1 verifies packed instructions but shows that eight lanes do not guarantee eightfold speedup. Its shrinking large-array gains illustrate an unchanged data-movement bottleneck. Project 2's placement avoids the probe's SMT sibling for requested workers, without claiming OS-wide isolation. |
| `Thread 1-1-3.pdf` | CPU latency vs GPU throughput, p.2; SIMT, p.3; latency hiding/occupancy, pp.8–9 | The distinction between response time and total throughput helps interpret Projects 2–3. No GPU/CUDA experiment was performed; GPU occupancy and SIMT behavior are conceptual connections, not measured findings. The assignment's GPU extension is optional. |
| `Thread 1-2-1.pdf` | Cache locality, p.3; writes/miss classes, pp.7–8; hit latency, miss rate and penalty, p.9; translation, p.10; access layout/prefetching, pp.11–12 | Project 1's footprint/stride results and Project 2's latency, LLC, and page-locality studies test consequences of these mechanisms. AMAT-style reasoning requires the correct denominator and cannot be inferred from misses per element alone. |
| `Thread 1-2-2.pdf` | Rows/mapping/banks, pp.3–8; Little's Law, p.9; queueing knee, p.10; scheduling, p.11; roofline, p.13 | Project 1 applies a measured-bandwidth roofline reference. Project 2 examines rising probe latency under offered traffic, while acknowledging its different request populations. Project 3 provides the clearer throughput plateau and same-workload Little's Law calculation. Row-hit rates and DRAM scheduling were not directly measured. |
| `Thread 1-2-3.pdf` | NAND operation asymmetry, p.5; updates/FTL, pp.7–8; GC/free space, p.9; overprovisioning, p.10; internal parallelism and I/O path, pp.11–12 | Project 3's read/write mixes, QD sweep, near-full volume, and write time series connect to SSD controller and media tradeoffs. They motivate hypotheses about internal work, but do not identify GC, SLC occupancy, or throttling from latency alone. |
| `Thread 1-3-1.pdf` | Data movement and DDR/PCIe, pp.2–3; software path/queueing, p.7; DMA/direct movement, pp.8–11 | Project 1 shows that more arithmetic capacity can leave data movement limiting. Project 3's buffered/direct comparison shows that the path through the system changes apparent performance. Direct file I/O is not proof of kernel bypass or absence of all CPU overhead. |
| `Thread 1-3-2.pdf` | NUMA/placement, pp.2–4; page-size tradeoffs, p.5; allocation/fragmentation, p.6 | Project 2's packed/spread accesses and failed large-page allocation relate to translation and allocation tradeoffs. This one-NUMA-node laptop did not test remote NUMA placement or demonstrate a successful huge-page benefit; error 1450 does not by itself prove fragmentation. |
| `Thread 1-3-3.pdf` | B-tree access/node-size tradeoffs, pp.4–10; LSM write organization, pp.14–17; workload-dependent choice, pp.22–23 | The locality, block-size, and mixed-I/O findings explain why index design depends on access granularity and read/write behavior. I did not benchmark a B-tree, LSM tree, Bloom filter, or hash table; this is an application-level interpretation of the lower-level studies. |

Across the three projects, more parallelism initially helps keep resources busy, but eventually moves the bottleneck or increases waiting. Locality determines how much useful work each transfer provides. The experiments also show why a plausible architectural explanation must remain a hypothesis when its distinguishing counters or controls are unavailable.

## AI use and my contribution

I used **OpenAI ChatGPT/Codex** for experiment planning, most benchmark/collection code, debugging, parsing and validation code, plotting, architectural interpretation, and documentation drafts. No Claude, Grok, or other tool is claimed to have contributed to these projects.

I installed and configured the tools, compiled and ran the native programs, executed the experiments on my laptop, checked and changed power settings, collected the original logs, and supplied console output, compiler reports, assembly, and traces. I worked through the failures and chose to retain unsuccessful measurements as limitations. I do not claim that I independently wrote the automated validators or that work was divided evenly. First-person reporting does not imply independent authorship of every script or paragraph.

| Project | AI assistance | Checks, corrections, and rejected interpretations |
|---|---|---|
| SIMD | Benchmark drivers, build/run commands, data analysis, plots, interpretation, report draft | Excluded the mislabeled multiplication sweep; reran with printed sizes/repetitions; checked packed versus scalar assembly paths; retained unavailable hardware cycles and timing outliers. |
| Memory | C benchmarks, WPR profiles, allocation helper, collection commands, ETL decoder, validation, figures and prose | Corrected the assumed power plan; decoded counters using trace metadata rather than XML order; distinguished timed-loop counts from whole-process counts; rejected fallback pages as large pages and flat STLB events as valid zero misses. |
| SSD | fio collection commands, mix-script correction, validation/plot pipeline, replay configs/scripts, report draft | Corrected `randrw` plus `--readonly` by selecting pure read/write modes at the mix endpoints; separated requested/achieved QD; retained slow write sessions; labeled buffered I/O and unsupported causal claims correctly. |

Prediction provenance differs by project. SIMD has no verified separately saved pre-experiment hypothesis document. Memory preserves a transcription whose initial predictions are undated and whose later timestamped notes sometimes follow related pilots. SSD's original local hypotheses file was not uploaded; its supplied overview is explicitly retrospective. None should be backdated or presented as stronger preregistration evidence than it provides.

Detailed disclosures: [SIMD report disclosure](PROJECT1_SIMD/README.md), [memory AI-use note](PROJECT2_MEMORY/AI-USE.md), and [SSD AI-use note](PROJECT3_SSD/AI-USE.md). I remain responsible for reviewing and explaining the submitted methods, code, numbers, and limitations.

## Rubric evidence by project

### Project 1 rubric — 110 possible points

| Category | Weight | Evidence and coverage limits in the uploaded snapshot |
|---|---:|---|
| Baseline, correctness, reproducibility | 15 | Three kernels, raw measurements, 437 reported successful checks, processed tables, C source, analysis and shell scripts are present. Seven raw files match the recorded hashes. The README's root-level run-script path and missing requirements file need correction. Actual hardware cycles/element remain unavailable. |
| Vectorization verification | 15 | Compiler reports, packed instructions, vector width/FMA interpretation, and scalar remainder/non-unit-stride paths are documented. |
| Locality and memory-bound analysis | 20 | Four-size sweeps show compressed SIMD gains; footprint and bandwidth interpretation are present. Exact cache thresholds and direct memory-controller traffic were not measured. |
| Alignment, tail, stride/gather studies | 20 | Offset/remainder and stride 1/2/4/8 studies are present. A stable separate tail penalty was unresolved; scalar stride paths are verified. No gather-instruction experiment is claimed. |
| Roofline and quantitative insight | 20 | Arithmetic intensity, measured copy bandwidth, modeled traffic, and assumed single-core compute peak are explained. Clock and physical traffic assumptions limit the ceiling interpretation. |
| AI-use transparency and failure case | 10 | AI disclosure is in the project README; scalar non-unit-stride and minimal large-array speedup are documented negative cases. |
| Report quality | 10 | Detailed report/README, five figures, tables, and limitations are present. |

### Project 2 rubric — 185 possible points

| Category | Weight | Evidence and coverage limits in the uploaded snapshot |
|---|---:|---|
| Zero-queue baselines | 25 | Report gives candidate cache/DRAM regions and a global-random follow-up, with units and caveats. Clean intrinsic per-level latency and a universal LLC plateau are not established. Raw/source evidence is missing from this snapshot. |
| Pattern/granularity/RW sweeps | 35 | Report and figures cover sequential/random patterns, 64/256/1024-byte granularity, and supported mixes. MLC 75/25 is documented instead of exact 70/30; some latency/bandwidth comparisons are different sessions. Missing raw data prevents regeneration here. |
| Throughput-latency knee | 35 | Loaded curve, diminishing-return discussion, operational near-peak rule, and Little's Law caveat are present. A sharp physical knee and measured worker concurrency were not established. |
| Working-set/cache/TLB analysis | 35 | Report gives footprint/runtime/LLC-counter correlation and page-locality timings. Direct TLB readings failed repeated validation; no successful large-page comparison exists. The kernel sources and underlying traces/data are absent here. |
| Experimental rigor | 25 | Placement, SMT, repetitions, later power brackets, counter-attribution bounds, and provenance are documented. Early power state was not bracketed; missing src/data folders block reproducibility. |
| AI-use transparency and pitfall analysis | 15 | Dedicated disclosure and counter/prefetch/fallback pitfalls are present. Failed measurements are not promoted to valid TLB or huge-page results. |
| Report quality | 15 | Detailed report, environment notes, and ten figure pairs are present. |

### Project 3 rubric — 185 possible points

| Category | Weight | Evidence and coverage limits in the uploaded snapshot |
|---|---:|---|
| Safety and zero-queue baselines | 30 | Disposable-file setup and preparation/verification record; four QD1 conditions with tails; recorded direct-I/O settings. The Windows system volume was not isolated. |
| Block-size and pattern sweeps | 35 | Complete 6 × 4 × 3 matrix, same-run throughput/latency and IOPS tables. Sequential tests used QD1, so maximum sequential throughput is not established. |
| Read/write and queue-depth analysis | 40 | Four mixes × 3, nine read QDs × 3, throughput-latency curve, practical QD32 knee, Little's Law estimate, and depth distributions. No random-write QD sweep or exact controller-occupancy measurement. |
| Tail latency and device state | 25 | p50/p95/p99/p99.9, mid-QD/near-knee discussion, three bounded write time series, and state snapshots. No verified full-drive steady state, in-run temperature trace, or isolated GC/SLC/throttling cause. |
| Reproducibility and data hygiene | 25 | Configs, replay/analysis scripts, raw results, CSV, and nine figure pairs are present. Git line-ending conversion currently breaks the raw SHA-256 checks; reconstructed scripts and inventory/prediction provenance are disclosed. |
| AI-use transparency and pitfall analysis | 15 | Dedicated AI-use note and a warmed buffered/direct comparison. The rejected mix command is disclosed; its failed-run log was not uploaded. |
| Report quality | 15 | Detailed report, labeled figures, units, repeat ranges, and limitations. |

### Common requirements across all projects

| Requirement | Current coverage |
|---|---|
| AI-use disclosure | Present in all projects; generated validation code is not claimed as independently authored. |
| Reproducible source, scripts, raw/processed data | Substantial in SIMD and SSD, with issues below; Project 2 is incomplete in the uploaded repository snapshot. |
| Pre-experiment hypotheses | Qualified/incomplete evidence, with different provenance by project; retrospective summaries are not substitute timestamped originals. |
| Correctness/sanity checks | SIMD output checks, memory benchmark and counter controls reported, SSD preparation verification plus fio-status/arithmetic checks. These are different levels of validation, not interchangeable proof. |
| Measurement discipline | Units, repetitions, and variation documented; clock/isolation/early-power limits remain. |
| Negative or misleading case | SIMD stride/no-speedup cases; memory prefetch/fallback/nonresponsive counters; SSD buffered caching and variable writes. |
| Honest anomalies | Outliers, unsuccessful counters/pages, baseline drift, and write slowdowns retained with qualified explanations. |

## Overall findings

The three studies connect one recurring pattern across different layers. SIMD raises arithmetic capacity, but memory traffic can limit the benefit. More memory traffic can raise aggregate bandwidth while making a dependent reader wait longer. More SSD concurrency can raise throughput up to an operating knee, then worsen response times with little additional gain. Cache reuse can also make an apparent hardware improvement come from a different access path entirely.

My conclusions therefore depend on the measured workload, environment, units, and controls. I distinguish measured outcomes from modeled quantities and plausible causes, and retain failures where the evidence does not justify a stronger claim.
