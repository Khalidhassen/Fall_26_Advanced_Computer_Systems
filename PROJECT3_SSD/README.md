# SSD Performance Profiling

**Khalid Hassen — Project 3, ECSE 4320/6320**

I measured my laptop’s Micron 2400 NVMe SSD using native Windows fio 3.43. The repository contains 141 main measurements, their raw results, reconstructed replay configs, analysis code, nine figures, and my report.

Read **[REPORT.md](REPORT.md)** for the findings and **[RUBRIC-COVERAGE.md](RUBRIC-COVERAGE.md)** for evidence and limitations. The key results are a practical random-read knee near requested QD32, rising tail latency beyond that region, a roughly 10× buffered-read pitfall, and large write-performance variation that I retained in the analysis.

## Files

```text
ssd-project/
  README.md
  REPORT.md
  ENVIRONMENT.md
  AI-USE.md
  HYPOTHESES.md
  requirements.txt
  configs/               # Portable configs reconstructed from recorded settings
  scripts/
    analyze.py           # Validate originals; regenerate CSV tables and figures
    prepare.ps1          # Create and verify a NEW disposable 2 GiB file
    run-study.ps1        # Replay a selected study into a separate output directory
  data/
    raw/                 # Original uploaded contents, manifests, state records
    processed/           # Trials, summaries, depth data, state data, validation
  plots/                 # Nine figures, each supplied as PNG and SVG
```

## Rebuild the analysis

Python 3.10 or later is sufficient. No fio installation or benchmark rerun is needed to reproduce the figures from the included data.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\analyze.py
```

Expected result: `PASS: 141 main measurements, 150 total fio jobs` followed by table/figure generation. The figures use medians and minimum–maximum bars across three repeats, not confidence intervals. Individual trials remain available in the CSV files.

## Replay a study on Windows

Replay is optional and writes new results separately. Use native Windows fio, choose the Performance power plan, plug in the laptop, and avoid other disk-heavy activity. Review the script and available space first. Do not substitute a raw device or partition for the disposable filename.

```powershell
# From this repository root, in PowerShell:
& .\scripts\prepare.ps1
& .\scripts\run-study.ps1 -Study qd-read
```

Supported studies: `baseline`, `blocks`, `qd-read`, `mix`, `range`, `cache-pitfall`, `write-series`. The preparation script refuses to overwrite an existing file. Write-bearing replays overwrite ONLY `testfiles/benchmark.bin`. The write-series study is capped at 40 GiB or 120 seconds per run. Other time-based write studies can rewrite the 2 GiB file many times. `testfiles/` is excluded from Git.

The replay configs and runner were generated after the measurements. Original uploaded configs remain under `data/raw/`. New replay folders are intentionally excluded from the fixed original-study analysis; integrating a new session requires updating the manifest and study definition explicitly.

## My work and AI assistance

I set up fio on my Windows laptop, ran the experiments, collected and uploaded the raw output, and worked through configuration errors and platform checks. AI helped design the experiment scripts and generated the combined analysis, figures, and report draft. I use first person for the report, while keeping authorship details explicit in [AI-USE.md](AI-USE.md).

## Interpretation limits

These are measurements of a small file on a nearly full Windows system drive. They do not establish maximum device performance, full-drive steady state, cache-hit rates, or a proven cause of the write slowdowns. Unsupported health fields are not treated as zeros, and all recorded repeats are retained.
