# Experiment predictions

I expect access latency to increase as the working set becomes too large to fit in each cache. I also expect sequential access to have higher bandwidth than random access.

As competing memory traffic increases, I expect bandwidth to eventually level off while latency continues to rise.

I expect larger pages to reduce address-translation overhead for some access patterns.

## Loaded-latency prediction

Recorded before this collection:

I expect shorter delays between memory requests to increase bandwidth until it gets close to saturation. After that point, I expect latency to keep increasing while bandwidth improves only slightly.

## Performance-plan loaded latency

Recorded before this collection:

I expect latency to rise as memory traffic increases, with smaller bandwidth improvements at higher loads. Switching to the Performance power plan may affect the results, but I do not have a specific prediction about whether it will improve them or by how much.

## Page-size prediction

Recorded before this collection:

I expect large pages to reduce address-translation overhead in this random-access test. However, a difference in latency alone would not tell me the TLB miss rate.

## Page-locality sweep

Recorded after the pilot, before the full sweep:

I expect dependent loads to take longer when the same number of cache-line nodes is spread across more 4 KiB pages. Cache behavior could also affect the results, so I cannot attribute the entire difference to TLB misses, especially since this test does not directly count them.

## Access-pattern latency sweep

Recorded after earlier experiments, before this collection:

I expect sequential access to show lower latency because prefetchers are still enabled. Increasing the spacing between accesses may reduce that benefit. MLC randomizes accesses within bounded blocks, so I would not treat it as a fully random pointer chain across the entire working set.

## Mixed-traffic latency

Recorded before this collection:

I expect changing the background mix of reads and writes to affect both bandwidth and read-probe latency. Non-temporal writes also change the store policy, so any difference in those results would not be caused by the read/write ratio alone.
