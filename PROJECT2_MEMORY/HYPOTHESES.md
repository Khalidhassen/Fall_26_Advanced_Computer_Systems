# Experiment predictions

This UTF-8 transcription combines the two original note files. Their unchanged bytes remain in [original-hypotheses.zip](data/raw/original-hypotheses.zip). The initial general predictions have no recorded timestamp. Later entries contain local timestamps. Some predictions were written after related pilot results; they are not represented as predictions made before all project measurements.

## Original HYPOTHESIS.md

The Access latency should increase as the working set exceeds each cache's capacity and Sequential access should receive higher bandwidth than random access.



Increasing competing memory traffic should eventually stop improving bandwidth while latency continues rising.



Larger pages may reduce address-translation overhead for some access patterns.


## Loaded-latency prediction — 2026-10-20T12:32:13.1527311-04:00
AI-assisted prediction recorded before this collection:
Reducing the delay between memory requests should increase bandwidth
until it approaches saturation. Beyond that region, latency should
continue increasing while bandwidth gains become smaller.

## Performance-plan loaded latency — 2026-10-20T12:37:43.4735150-04:00
AI-assisted prediction recorded before collection:
Latency should rise as memory traffic increases, with smaller bandwidth
gains at higher loads. The Performance plan may change the results;
the direction and size of that change are not assumed.


## Original HYPOTHESES.md


## Page-size prediction — 2026-10-20T13:09:07.3848212-04:00
AI-assisted prediction before collection:
Large pages may reduce address-translation overhead for this random-access
test. A latency difference alone would not prove a particular TLB miss rate.

## Page-locality sweep — 2026-10-20T13:21:04.4510724-04:00
AI-assisted prediction after the pilot, before this full sweep:
Spreading the same number of cache-line nodes across more 4 KiB pages
may increase dependent-load time. Cache behavior can also contribute;
this experiment does not directly count TLB misses.

## Access-pattern latency sweep — 2026-10-20T13:27:17.4178378-04:00
AI-assisted prediction after earlier experiments, before this collection:
Sequential access may report lower latency because prefetchers remain
enabled. Increasing spacing may reduce that benefit. MLC randomization
uses bounded blocks, so it is not a globally random pointer chain.

## Mixed-traffic latency — 2026-10-20T13:30:43.9937830-04:00
AI-assisted prediction before this collection:
Changing background read/write traffic may change both bandwidth and
read-probe latency. Non-temporal writes use a different store policy,
so their results cannot isolate read/write ratio alone.

