/* AI-assisted Project 2 page-locality benchmark for native Windows x64.
 * Usage: page_chase.exe nodes spacing_bytes loads normal|large
 * spacing=64 packs cache-line nodes; spacing=4096 places one per 4KiB region.
 * The latter rotates the line offset to avoid putting every node in one L1 set.
 * All modes use the same seeded random cycle for the same node count.
 * Large-page failure is fatal: this benchmark NEVER falls back silently.
 * Compare allocation modes at the same nodes/spacing. Layout differences can
 * also affect caches and prefetching; this is not a direct TLB miss counter.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>

static int error(const char *where, DWORD code)
{
    fprintf(stderr, "%s failed: Windows error %lu\n", where, code);
    return 1;
}
static int enable_lock_pages(void)
{
    HANDLE token;
    TOKEN_PRIVILEGES p = {0};
    DWORD code;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &token))
        return error("OpenProcessToken", GetLastError());
    if (!LookupPrivilegeValueA(NULL, "SeLockMemoryPrivilege", &p.Privileges[0].Luid)) {
        code = GetLastError(); CloseHandle(token);
        return error("LookupPrivilegeValue", code);
    }
    p.PrivilegeCount = 1;
    p.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    SetLastError(ERROR_SUCCESS);
    if (!AdjustTokenPrivileges(token, FALSE, &p, 0, NULL, NULL)) {
        code = GetLastError(); CloseHandle(token);
        return error("AdjustTokenPrivileges", code);
    }
    code = GetLastError();
    CloseHandle(token);
    return code == ERROR_SUCCESS ? 0 : error("Enable SeLockMemoryPrivilege", code);
}
static uint32_t random32(uint32_t *s)
{
    *s ^= *s << 13; *s ^= *s >> 17; *s ^= *s << 5;
    return *s;
}
static void *node(unsigned char *base, size_t i, size_t spacing)
{
    return base + i * spacing + (spacing == 4096 ? (i % 64) * 64 : 0);
}
__declspec(noinline) static void *chase(void *p, unsigned long long loads)
{
    unsigned long long i;
    for (i = 0; i < loads; ++i) p = *(void * volatile *)p;
    return p;
}
static int positive(const char *s, unsigned long long *n)
{
    char *end;
    if (*s < '0' || *s > '9') return 0;
    errno = 0; *n = strtoull(s, &end, 10);
    return errno == 0 && *end == '\0' && *n != 0;
}
int main(int argc, char **argv)
{
    unsigned long long nn, ss, loads;
    size_t n, spacing, span, allocated, unit, large_min, i, j, tmp;
    size_t *order;
    unsigned char *base;
    void *first, *last;
    int large, pass;
    DWORD flags = MEM_RESERVE | MEM_COMMIT;
    SYSTEM_INFO info;
    LARGE_INTEGER freq, begin, end;
    uint32_t seed = 0x93a48b17u;
    double seconds;
    if (argc != 5 || !positive(argv[1], &nn) || nn > 65536 ||
        !positive(argv[2], &ss) || (ss != 64 && ss != 4096) ||
        !positive(argv[3], &loads) ||
        (strcmp(argv[4], "normal") && strcmp(argv[4], "large"))) {
        fprintf(stderr, "Usage: %s nodes(1..65536) spacing(64|4096) loads normal|large\n", argv[0]);
        return 1;
    }
    large = !strcmp(argv[4], "large");
    if (!SetThreadAffinityMask(GetCurrentThread(), (DWORD_PTR)1))
        return error("CPU 0 affinity", GetLastError());
    GetSystemInfo(&info);
    large_min = GetLargePageMinimum();
    if (large && !large_min) return error("GetLargePageMinimum", ERROR_NOT_SUPPORTED);
    if (large && enable_lock_pages()) return 1;
    n = (size_t)nn; spacing = (size_t)ss; span = n * spacing;
    unit = large_min ? large_min : info.dwPageSize;
    allocated = ((span + unit - 1) / unit) * unit;
    if (large) flags |= MEM_LARGE_PAGES;
    base = (unsigned char *)VirtualAlloc(NULL, allocated, flags, PAGE_READWRITE);
    if (!base) return error(large ? "VirtualAlloc MEM_LARGE_PAGES" : "VirtualAlloc normal", GetLastError());
    order = (size_t *)malloc(n * sizeof(*order));
    if (!order) { VirtualFree(base, 0, MEM_RELEASE); return error("malloc", ERROR_NOT_ENOUGH_MEMORY); }
    for (i = 0; i < n; ++i) order[i] = i;
    for (i = n - 1; i > 0; --i) {
        j = (size_t)random32(&seed) % (i + 1);
        tmp = order[i]; order[i] = order[j]; order[j] = tmp;
    }
    for (i = 0; i < n; ++i)
        *(void **)node(base, order[i], spacing) = node(base, order[(i + 1) % n], spacing);
    first = node(base, order[0], spacing);
    if (chase(first, (unsigned long long)n * 8) != first) {
        free(order); VirtualFree(base, 0, MEM_RELEASE); return error("Warmup cycle validation", ERROR_INVALID_DATA);
    }
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&begin);
    last = chase(first, loads);
    QueryPerformanceCounter(&end);
    pass = last == node(base, order[(size_t)(loads % n)], spacing);
    seconds = (double)(end.QuadPart - begin.QuadPart) / (double)freq.QuadPart;
    printf("mode,cpu,nodes,spacing_bytes,unique_cacheline_bytes,span_bytes,allocated_bytes,page_bytes,loads,seed,qpc_frequency,qpc_start,qpc_end,total_seconds,ns_per_load,correctness\n");
    printf("%s,0,%zu,%zu,%zu,%zu,%zu,%zu,%llu,2477034263,%lld,%lld,%lld,%.9f,%.6f,%s\n",
        argv[4], n, spacing, n * 64, span, allocated,
        large ? large_min : (size_t)info.dwPageSize, loads,
        freq.QuadPart, begin.QuadPart, end.QuadPart, seconds,
        seconds * 1e9 / (double)loads, pass ? "PASS" : "FAIL");
    free(order); VirtualFree(base, 0, MEM_RELEASE);
    return pass ? 0 : 1;
}
