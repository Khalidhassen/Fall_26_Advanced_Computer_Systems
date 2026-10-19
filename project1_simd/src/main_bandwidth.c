#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void copy_kernel(const float *restrict source,
                 float *restrict destination,
                 size_t n);

double seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(void)
{
    const size_t n = 33554432;
    const int repetitions = 100;
    size_t bytes = n * sizeof(float);

    void *source_base = NULL;
    void *destination_base = NULL;

    if (posix_memalign(&source_base, 64, bytes) != 0
        || posix_memalign(&destination_base, 64, bytes) != 0) {
        fprintf(stderr, "Memory allocation failed.\n");
        free(source_base);
        free(destination_base);
        return 1;
    }

    float *source = source_base;
    float *destination = destination_base;

    // Initialize outside the timed section.
    for (size_t i = 0; i < n; i++) {
        source[i] = (float)(i % 100);
        destination[i] = -1.0f;
    }

    for (int r = 0; r < 5; r++) {
        copy_kernel(source, destination, n);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        copy_kernel(source, destination, n);
    }

    double elapsed = seconds() - start;

    for (size_t i = 0; i < n; i++) {
        if (destination[i] != source[i]) {
            fprintf(stderr, "Correctness failed at %zu\n", i);
            free(source_base);
            free(destination_base);
            return 1;
        }
    }

    // Useful traffic: read source + write destination.
    double useful_bytes = 2.0 * bytes * repetitions;

    // Estimated traffic for ordinary write-allocate stores:
    // source read + destination allocation read + writeback.
    double modeled_bytes = 3.0 * bytes * repetitions;

    double useful_gib_s =
        useful_bytes / elapsed / 1073741824.0;

    double modeled_gib_s =
        modeled_bytes / elapsed / 1073741824.0;

    printf("%zu,%d,%.9f,%.6f,%.6f,PASS\n",
           n, repetitions, elapsed,
           useful_gib_s, modeled_gib_s);

    free(source_base);
    free(destination_base);
    return 0;
}