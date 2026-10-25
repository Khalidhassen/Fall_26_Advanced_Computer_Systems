/* AI-assisted Project 2 runtime/cache-counter benchmark.
 * Build on Windows: cl /nologo /O2 /W4 /arch:AVX2 /fp:precise cache_kernel.c
 * Usage: cache_kernel.exe elements repetitions
 * Three float arrays: working-set bytes = 12 * elements.
 * QPC timestamps delimit the timed loop; initialization, warmup and validation
 * are outside that interval. Whole-process PMCs also include that other work.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>

__declspec(noinline) void multiply(const float *__restrict x,
    const float *__restrict y, float *__restrict z, size_t n)
{
    size_t i;
    for (i = 0; i < n; ++i) z[i] = x[i] * y[i];
}

static int parse_positive(const char *s, unsigned long long *out)
{
    char *end;
    if (*s < '0' || *s > '9') return 0;
    errno = 0;
    *out = strtoull(s, &end, 10);
    return errno == 0 && *end == '\0' && *out != 0;
}

int main(int argc, char **argv)
{
    unsigned long long count, reps, r;
    size_t n, i, bytes;
    float *x, *y, *z;
    LARGE_INTEGER freq, begin, end;
    double elapsed, checksum = 0.0;
    if (argc != 3 || !parse_positive(argv[1], &count) ||
        !parse_positive(argv[2], &reps) || count > SIZE_MAX / 12) {
        fprintf(stderr, "Usage: %s positive_elements positive_repetitions\n", argv[0]);
        return 1;
    }
    if (!SetThreadAffinityMask(GetCurrentThread(), (DWORD_PTR)1)) {
        fprintf(stderr, "CPU 0 affinity failed: %lu\n", GetLastError());
        return 1;
    }
    if (!QueryPerformanceFrequency(&freq)) return 1;
    n = (size_t)count;
    bytes = n * sizeof(float);
    x = (float *)_aligned_malloc(bytes, 64);
    y = (float *)_aligned_malloc(bytes, 64);
    z = (float *)_aligned_malloc(bytes, 64);
    if (!x || !y || !z) {
        fprintf(stderr, "Allocation failed.\n");
        _aligned_free(x); _aligned_free(y); _aligned_free(z);
        return 1;
    }
    for (i = 0; i < n; ++i) {
        x[i] = (float)(i % 100) * 0.25f;
        y[i] = (float)(i % 50) * 0.5f;
        z[i] = -1.0f;
    }
    for (r = 0; r < 10; ++r) multiply(x, y, z, n);
    QueryPerformanceCounter(&begin);
    for (r = 0; r < reps; ++r) multiply(x, y, z, n);
    QueryPerformanceCounter(&end);
    for (i = 0; i < n; ++i) {
        if (z[i] != x[i] * y[i]) {
            fprintf(stderr, "Correctness failed at %zu\n", i);
            _aligned_free(x); _aligned_free(y); _aligned_free(z);
            return 1;
        }
        checksum += z[i];
    }
    elapsed = (double)(end.QuadPart - begin.QuadPart) / (double)freq.QuadPart;
    printf("pid,tid,cpu,n,working_set_bytes,repetitions,qpc_frequency,qpc_start,qpc_end,total_seconds,ns_per_element,gflops,checksum,correctness\n");
    printf("%lu,%lu,0,%zu,%zu,%llu,%lld,%lld,%lld,%.9f,%.6f,%.6f,%.9g,PASS\n",
        GetCurrentProcessId(), GetCurrentThreadId(), n, n * 12, reps,
        freq.QuadPart, begin.QuadPart, end.QuadPart, elapsed,
        elapsed * 1e9 / ((double)n * (double)reps),
        (double)n * (double)reps / elapsed / 1e9, checksum);
    _aligned_free(x); _aligned_free(y); _aligned_free(z);
    return 0;
}
