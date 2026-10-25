# Experiment predictions and provenance

This file is a retrospective reconstruction of AI-assisted predictions that were supplied with collection commands in the project conversation. It is not the original timestamped HYPOTHESES.md from my laptop; that file was not uploaded. The original scripts requested that predictions be appended before collection, but I cannot verify the bytes or timestamps of that local file from the supplied archives. These notes must not be presented as independent student-authored preregistration.

- Block size: larger blocks may increase bytes per operation and byte throughput; sequential access may benefit more than random access; wider transfers can increase operation latency.
- Queue depth: throughput may improve with concurrency until gains diminish, while latency rises. Actual depth should be checked rather than assumed.
- Mix: changing the read/write ratio may change throughput and directional latency. Earlier write variation means a monotonic trend should not be assumed.
- File range: smaller ranges may change locality or device-cache behavior, but a performance difference alone does not identify a mechanism.
- Cache pitfall: warmed buffered reads may look faster than direct reads and should not be labeled uncached SSD performance.
- Write time series: throughput and latency may change with time, without assuming a slowdown or a particular cause. Bounded overwrites of a small file do not establish whole-drive steady state.

The actual outcomes, including the lack of a consistent smaller-range improvement and the recovery after the first slow write-series run, are discussed in REPORT.md.
