# Raw session index

All session archives preserve the original file bytes. The two original hypothesis files are in their own archive. Early power policy is not inferred from the later Silent snapshot.

| Archive | Parsed MLC observations | Native CSVs | Power evidence / role |
|---|---:|---:|---|
| `20261020-080651.zip` | 5 | 0 | Not bracketed / setup evidence |
| `cache-128B-20261020-083314.zip` | 70 | 0 | Not bracketed / setup evidence |
| `cache-latency-20261020-195943.zip` | 0 | 35 | Performance before/after; global random native chain |
| `cache-sweep-20261020-080757.zip` | 70 | 0 | Not bracketed / setup evidence |
| `environment-and-setup.zip` | 1 | 0 | Original notes / environment and setup logs |
| `kernel-pilot-20261020-125747.zip` | 0 | 1 | Not bracketed / setup evidence |
| `kernel-study-20261020-130137.zip` | 0 | 20 | Performance before/after |
| `large-page-retry-20261020-131534.zip` | 0 | 0 | Not bracketed / setup evidence |
| `loaded-latency-20261020-123213.zip` | 50 | 0 | Not bracketed / setup evidence |
| `loaded-performance-20261020-123743.zip` | 50 | 0 | Performance before/after |
| `mixed-latency-20261020-133043.zip` | 20 | 0 | Performance before/after |
| `original-hypotheses.zip` | 0 | 0 | Original notes / environment and setup logs |
| `page-locality-20261020-132104.zip` | 0 | 50 | Performance before/after |
| `page-pilot-20261020-130907.zip` | 2 | 0 | Not bracketed / setup evidence |
| `pattern-bandwidth-20261020-121518.zip` | 30 | 0 | Not bracketed / setup evidence |
| `pattern-latency-20261020-132717.zip` | 30 | 0 | Performance before/after |
| `read-bandwidth-20261020-121233.zip` | 5 | 0 | Not bracketed / setup evidence |
| `rw-mixes-20261020-122050.zip` | 20 | 0 | Not bracketed / setup evidence |
| `spacing-check-20261020-083150.zip` | 10 | 0 | Not bracketed / setup evidence |

## Trace evidence

- `traces/kernel_study.etl.zip.part001` through `.part003`: main trace, restored with `scripts/restore_trace.py`.
- `traces/kernel_pilot.etl.zip`: allocation/runtime pilot; not used for the final counter table.
- `traces/pmu_test.etl.zip`: original MLC counter setup test; not used for final per-element normalization.

The failed `loaded_run5.txt` under the earlier RW archive is a malformed `-g` command, not a sixth traffic condition. Allocation/fallback runs are listed separately in `data/processed/failed_or_fallback_runs.csv`. The direct native error-1450 output and compiler version are transcribed from the supplied conversation in this docs folder; those are labeled transcripts, not original instrument logs.

## Additional counter attempts

Original ZIPs are retained byte-for-byte in `data/raw/counter-attempts/`:

| Archive | Native trials | Role |
|---|---:|---|
| `tlb-pilot.zip` | 2 | Initial STLB-hit/page-walk events stayed flat |
| `tlb-control.zip` | 1 | Custom instruction count checked against built-in; page-walk event stayed flat |
| `tlb-retired.zip` | 2 | Retired-STLB event produced a pilot signal; all-load control unusable on benchmark thread |
| `tlb-study.zip` | 50 | Five trials per node-count/layout pair; selected STLB event flat in all timed windows; latency retained |

The 50 follow-up latency trials are not pooled with the earlier 50 page-locality trials. All four archives contain their original profiles, logs and traces. See [COUNTER_ATTEMPTS.md](COUNTER_ATTEMPTS.md) for exclusions.
