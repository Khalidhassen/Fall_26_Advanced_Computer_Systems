# Submission and coverage
## Assignment coverage

This maps the supplied ECSE 4320/6320 Project 2 handout to evidence, without estimating a grade.

| Required area | Evidence | Status and limits |
|---|---|---|
| Zero-queue/per-level baseline | Two 14-size MLC sweeps plus 35 native global-random trials, baseline tables, `cache_latency` and `global_random_latency` figures | Strengthened: native global-random sweep has Performance snapshots and five trials at seven sizes. Cache-resident and DRAM-sized access paths are measured, but intrinsic per-level times remain unisolated; the 16 MiB rise is unresolved. |
| Sequential/random, 64/256/1024 B | Five trials per pattern/spacing for latency and bandwidth; `pattern_sweep` | Collected. Latency and bandwidth are distinct sessions/workloads; bandwidth session lacks bracketed power records. |
| Read/write mixes | Single-thread throughput and later five-worker loaded-latency/throughput; `mixed_traffic`, `single_thread_mixes` | Collected with MLC presets. 75/25 substitutes for an unavailable exact 70/30 preset. NT-write store policy is a confound. |
| Intensity and knee | Five 10-point Performance sweeps; `loaded_latency`, model table | Tradeoff measured. No sharp physical knee/plateau established; delay 50 is an explicitly chosen near-peak operating point. |
| Little's Law | Equation, request-population discussion, clearly labeled scale-model table | Interpretation supplied. The probe latency is not worker request latency, so actual worker concurrency is not measured. |
| Working set and cache impact | Twenty instrumented multiplication trials, cycle/instruction/LLC counters, `cache_miss_impact` | Collected with boundary bounds and documented counter semantics. |
| TLB/page locality | Fifty original pointer-chain trials, a separate 50-trial follow-up, counter controls and large-page attempts; `page_locality`, `page_locality_followup` | Partial: page-locality effects measured. Direct counters were attempted but failed repeated validation, and large-page allocation failed. Both are documented negatives; neither substitutes for a successful measurement. |
| AMAT-style analysis | Report's cache/runtime section | Qualitative: no fabricated conditional miss probability or fitted AMAT. |
| Pitfall/negative case | Sequential prefetch warning, spacing diagnostic, false large-page fallback, failed allocation and nonreproducible TLB counter signal | Supplied; adverse and anomalous outcomes retained. |
| Correctness and rigor | Native checks, analytical checksums, exact coverage, QPC arithmetic, source/executable hashes, ETL audit, ranges | Checks passed on the supplied data. CPU isolation and fixed frequency were not established. |
| Reproducibility | Source/build/run/analysis code, raw archives, processed tables and ten PNG/SVG figures | Supplied. Packaged collection wrapper reconstructed from executed commands, reviewed but not itself executed on Windows. |
| AI-use and hypotheses | `AI-USE.md`, readable note transcription and original byte-preserved notes | Supplied. Initial predictions undated; later predictions may follow related pilots; I do not claim independent validation that was not performed. |

