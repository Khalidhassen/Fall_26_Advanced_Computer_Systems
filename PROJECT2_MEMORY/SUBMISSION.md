# Submission and coverage

## What to upload

Extract the delivered repository ZIP. Upload the **contents of `memory-project`** to the GitHub repository, retaining the folder structure. The root should show `README.md`, `REPORT.md`, `ENVIRONMENT.md`, `HYPOTHESES.md`, `AI-USE.md`, `SUBMISSION.md`, `requirements.txt`, and the folders `src`, `scripts`, `data`, `plots`, and `docs`.

In GitHub's browser interface, use **Add file → Upload files**, then drag the extracted files/folders into the upload area and commit. Check that the report's figures render and paths such as `src/cache_kernel.c` and `data/raw/` are still nested. Uploading only the outer repository ZIP will not make the report and source directly reviewable. The session ZIPs inside `data/raw/` should remain zipped.

Every included file is below 25 MiB. The main compressed trace is split into three pieces, with checksums and a restore script, so it can be uploaded through the browser. Keep every part and the JSON manifest. Do not upload an expanded ETL or the generated `build/`, `bin/`, virtual environment or new `runs/` folders.

GitHub documents a browser limit of [25 MiB per file and up to 100 files per upload](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository). If the interface rejects a large selection, upload the root documents and then one folder at a time. Submit the repository URL using the course's required submission channel. A separate PDF is not specified in the supplied project handout.

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

## Before committing

Read the report and AI disclosure, confirm that you can explain the benchmark loops and limitations, and update any prose you revise. The documentation intentionally reports unresolved items rather than representing them as completed measurements. Course staff decide whether these substitutions and limitations satisfy the rubric.

For a local integrity check, run `python scripts/analyze.py` followed by `python scripts/validate.py` after installing requirements. For independent PMC reproduction, also restore and decode the trace using the commands in the README.
