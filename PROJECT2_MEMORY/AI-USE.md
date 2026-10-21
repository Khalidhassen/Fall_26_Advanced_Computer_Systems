# AI-use disclosure

## Contributions

| Contributor/tool | Work performed |
|---|---|
| Me — Khalid Hassen | I installed and ran Intel MLC, Coreinfo, WPR and the native compiler; compiled the C programs; executed the PowerShell experiments; changed and checked the power scheme; tested privilege setup and large-page allocation; supplied console output and original result folders; carried out additional counter controls and chose to retain unsuccessful measurements as negative results. |
| OpenAI Codex / ChatGPT | Generated most benchmark code, collection commands, WPR profile, allocation helper, parsing/validation and plotting code; inspected raw logs and decoded ETL counters; computed summaries; drafted the README, report and supporting documentation. |

The packaged collector and build wrapper consolidate commands used during the conversation. The individual commands and benchmarks ran on my laptop; the final consolidated wrappers were reviewed but not executed there in this packaged form. Python processing and counter-decoding scripts were executed against the uploaded raw data. No other AI tool is claimed to have worked on this project.

I used the supplied AI-generated validators rather than writing them independently. Codex performed the automated validation and report calculations described here. I remain responsible for reviewing, understanding, and explaining my submission; I do not claim an even division of work or independent hand checks that were not recorded.

## What was checked or rejected

- **Counter-order assumption rejected.** The WPR XML lists TotalCycles first, but the trace metadata lists InstructionRetired, LLCMisses, TotalCycles. The decoder uses metadata and checks the three names rather than assuming the XML order.
- **Whole-process normalization rejected.** Initialization, warmup and validation are outside the benchmark's QPC interval. Counter analysis uses the recorded thread and timed window. It retains lower and upper attribution bounds where a context-switch interval crosses a boundary.
- **False large-page comparison rejected.** MLC initially said it was using 4 KiB pages after `-L` failed. Its 86.1 ns result was not accepted as a large-page measurement. Later MLC assertions and direct VirtualAlloc error 1450 remain documented failures.
- **Power-state assumption corrected.** The user expected high performance, but `powercfg` reported Silent. Later sessions recorded Performance before and after; early sessions are not retroactively relabeled.
- **Direct TLB inference rejected.** A spread pointer chain was slower than a packed chain, but that alone does not measure a TLB miss rate or exclude cache effects.
- **Sharp-knee assumption rejected.** The observed throughput/latency curve bends gradually. A chosen near-peak operating point is distinguished from a proven physical saturation threshold.
- **Prefetch interpretation narrowed.** A 64-byte randomized MLC spacing gave much lower latency than 128 bytes. Spacing also changes the random block's byte span, so the difference is not presented as an isolated prefetcher experiment.

## Validation actually run

The analysis checks 360 main MLC observations with exact condition/run coverage, 20 native kernel trials, 50 page-locality trials, and 35 global-random cache-latency trials. Native timing, ns/element or ns/load and kernel GFLOP/s are recomputed from QPC ticks. Kernel checksums are compared with the analytically repeated 100-element initialization pattern. All recorded native trials passed. Source and compiled executable hashes in the supplied archive match the original collection hash logs.

The ETL decoder checked counter metadata, thread continuity, nonnegative counter deltas, QPC clock agreement, CPU-0 placement during the timed intervals, and zero reported lost events/buffers. Startup switches without PMCs occur before the measurement windows. Outliers are retained, including a 9.00 ns/load packed trial and the 140 ns spacing trial.

## Prediction provenance

[HYPOTHESES.md](HYPOTHESES.md) transcribes two original note files retained unchanged in the raw archive. Initial general predictions are undated. Later predictions are timestamped; some explicitly follow related pilot results. A cache-kernel prediction suggested in conversation is not present in the uploaded note files and is not claimed as a saved pre-experiment record.

## Global-random follow-up

Codex extended the existing pointer-chain benchmark to 2,097,152 packed nodes and generated the collection commands. I compiled and ran the pilot and five-repeat sweep, then supplied the source, binary and original logs. Codex checked source/executable hashes against the session log, both Performance snapshots, all 35 timings and exact size/run coverage, then added a separate plot and report section. The saved notes do not establish a new timestamped hypothesis before this follow-up; none is invented. The 16 MiB latency rise remains unresolved.

## TLB-counter attempts and final exclusion

I executed the proposed WPR profiles, collected the pilot/control traces and 50-trial study, supplied the original archives, and decided to stop troubleshooting and document the limitation. Codex generated the profiles, decoded the traces and drafted the interpretation. The first page-walk counters remained flat; a custom instruction control closely matched the built-in instruction counter. A later retired-STLB pilot produced a signal, but after Codex changed the counter combination to add cycles, the full study did not reproduce it. That combination should have been piloted first. No cause is established, and the earlier pilot is not promoted to a confirmed quantitative TLB conclusion.

The final analysis matches the program's command line and lifetime to the CSV timing window, then uses ETL initial-thread start records to identify the main benchmark thread. A process-exit record can belong to a helper thread, so its thread ID is not assumed to identify the timed loop. All 50 native timing checks passed; all 50 selected STLB counter deltas were zero and were marked unusable. The successful latency results and failed counter attempts are retained separately from the earlier page-locality session. This adds a counter-validation pitfall, not a successful direct-TLB measurement.
