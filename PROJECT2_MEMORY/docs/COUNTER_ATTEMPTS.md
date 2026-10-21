# Counter attempts retained as negative evidence

The submitted project does not claim a validated direct TLB miss rate or a successful large-page comparison. The latency study, original kernel counters and other successful results remain included.

| Attempt | Observation | Treatment |
|---|---|---|
| Initial TLB pilot | Both selected custom TLB events stayed zero across the trace; cycles advanced | Failed event validation |
| Instruction control | Custom retired-instruction event closely matched built-in instruction event; page-walk event stayed flat | Control for that custom event, not proof every PMU event works |
| Retired-STLB pilot | Retired-STLB signal changed with layout; all-retired-load control was zero on the timed P-core thread | Unconfirmed pilot; not used as a quantitative TLB conclusion |
| Repeated study | All 50 benchmarks passed; STLB event flat in all timed CPU-0 windows, with instruction/cycle activity | TLB readings excluded; timing retained in a separate session |
| Large pages | MLC fallback/assertions and native VirtualAlloc error 1450 | No successful comparison; no invented speedup or slowdown |

The exact raw counter-attempt archives are under `data/raw/counter-attempts/`. Their original Windows paths and encodings are preserved. `docs/RAW_ARCHIVES.csv` records checksums. No hardware cause is established for the changing PMU response. The counter set changed between the retired pilot and the repeated study; this makes a fresh pilot necessary before any further full collection. No further collection is required for this submission's documented negative case.

The 50-trial trace decoder uses counter names from ETL metadata, checks zero reported event/buffer loss, monotonic counter deltas and thread continuity, and matches each command/lifetime to the CSV timing window. It obtains the benchmark main-thread identity from the thread created by the parent process, rather than assuming a process-exit event belongs to the main thread. This distinction matters because loader/helper threads occur in some processes. Counter intervals crossing a timing boundary provide lower/upper attribution bounds; they are not confidence intervals.

The profile's retired-STLB event is Event 0xD0, Unit 0x11. Its observations are normalized only by the known dependent-load count. They are not divided by the unusable all-retired-load control. In this final study all such observations are marked `tlb_counter_usable=False` and are excluded from TLB performance claims.

Rebuild the diagnostic export from the original archive:

```powershell
python scripts/decode_tlb.py data/raw/counter-attempts/tlb-study.zip --allow-zero-response --output data/processed
python scripts/analyze.py
python scripts/validate.py
```

Without `--allow-zero-response`, the decoder rejects the failed event instead of accepting its zeros. The explicit export writes `tlb_attempt_trials.csv` and `tlb_attempt_audit.json`. `page_locality_followup_summary.csv` and the corresponding plot use latency only. The overall integrity check can pass while the TLB measurement is explicitly marked failed: file/timing integrity and event validity are different checks.

Large-page error 1450 is retained without assigning a particular cause. The earlier 4 KiB fallback is not compared with normal pages as if it were a large-page result. Failed attempts support the benchmark-pitfall requirement, but do not replace the rubric's missing successful measurements.

## Collection provenance for the final attempt

The user ran the original `page_chase.exe` with the submitted source/executable hashes. The WPR profile saved in the raw study and copied to `scripts/pmu_tlb_study.wprp` selects InstructionRetired, TotalCycles and KH_ADL_RETIRED_STLB_MISS. One trace encloses 50 separate processes: nodes 32,128,512,2048,8192 crossed with spacing 64,4096; each condition uses 100 million loads and normal pages, repeated five times. Odd repetitions use ascending nodes then spacing; even repetitions reverse the entire condition list. The Performance plan and hashes are saved before collection; the plan is saved again afterward.

The corresponding commands are:

```powershell
$project = "$env:USERPROFILE\memory-project"
wpr -start "$project\scripts\pmu_tlb_study.wprp!PMUTest" -filemode
# For each condition: bin\page_chase.exe nodes spacing 100000000 normal
# Save each result as n{nodes}_s{spacing}_run{run}.csv.
# Stop in finally to retain the trace even if collection fails.
wpr -stop "$outDir\tlb_study.etl"
```

These describe the executed negative attempt, not a recommendation to repeat it or a claim that another collection will fix the event.
