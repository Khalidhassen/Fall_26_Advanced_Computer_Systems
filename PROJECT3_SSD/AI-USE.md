# AI-use disclosure

## Approach

I used OpenAI ChatGPT/Codex to help plan and implement the SSD experiments and prepare this repository. AI generated most of the PowerShell collection commands, the portable replay scripts, Python parsing/validation/plotting code, and report/documentation draft.

## My contribution

I used my own Windows laptop, installed and ran fio, checked the hardware and power-plan information, executed the experiments, and collected and uploaded the raw results. I supplied the output needed to identify failures and move to corrected runs. These were actual measurements, not fabricated or simulated benchmark numbers. I did not independently author the automated validator; it was AI-generated.

## What was checked or corrected

- The first mix script incorrectly combined `rw=randrw` with `--readonly` for a 100% read condition. fio rejected it before I/O. I supplied the error, and the corrected script selected `randread`, `randwrite`, or `randrw` according to the condition. The successful mix archive contains the corrected results. The failed run was not included as performance data, and its original failure log was not uploaded.
- Requested queue depth was not equated with constant achieved depth. The analysis retains fio's depth distributions and computes a separate Little's Law estimate.
- The report retains slow repeats, the much slower original baseline, and the first write-series slowdown. It does not claim SLC exhaustion, garbage collection, or thermal throttling as measured causes.
- Buffered reads are labeled as a deliberate setup pitfall. Their throughput is not reported as uncached SSD capability.
- The combined validator checks coverage, hashes, settings, status, and arithmetic. Small bounded byte-count discrepancies are disclosed rather than silently changed. Passing these checks is not independent proof of hardware correctness.

## Provenance limits

The original collection scripts were supplied through the conversation rather than uploaded as standalone files. The portable replay scripts/configs in this repository were reconstructed after collection; raw uploaded configs and JSON remain unchanged. HYPOTHESES.md identifies its reconstructed status. Hardware inventory is transcribed from the terminal output I supplied. I should review the final interpretation before submitting the repository.
