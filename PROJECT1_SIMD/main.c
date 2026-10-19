#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void multiply(const float *restrict x,
              const float *restrict y,
              float *restrict z,
              size_t n);

double seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "Usage: %s elements repetitions\n", argv[0]);
        return 1;
    }

    size_t n = (size_t)strtoull(argv[1], NULL, 10);
    int repetitions = atoi(argv[2]);

    if (n == 0 || n > (size_t)-1 / sizeof(float)
        || repetitions <= 0) {
        fprintf(stderr, "Invalid size or repetition count.\n");
        return 1;
    }

    float *x = malloc(n * sizeof(float));
    float *y = malloc(n * sizeof(float));
    float *z = malloc(n * sizeof(float));

    if (x == NULL || y == NULL || z == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        free(x);
        free(y);
        free(z);
        return 1;
    }

    for (size_t i = 0; i < n; i++) {
        x[i] = (float)(i % 100) * 0.25f;
        y[i] = (float)(i % 50) * 0.5f;
    }

    // Warm up before measuring.
    for (int r = 0; r < 10; r++) {
        multiply(x, y, z, n);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        multiply(x, y, z, n);
    }

    double elapsed = seconds() - start;

    // Check correctness outside the timed section.
    for (size_t i = 0; i < n; i++) {
        if (z[i] != x[i] * y[i]) {
            fprintf(stderr, "Incorrect result at index %zu\n", i);
            free(x);
            free(y);
            free(z);
            return 1;
        }
    }

    printf("Correctness: PASS\n");
    printf("Elements: %zu\n", n);
    printf("Repetitions: %d\n", repetitions);
    printf("Total time: %.6f seconds\n", elapsed);
    printf("Time per pass: %.3f microseconds\n",
           elapsed / repetitions * 1e6);
    printf("Throughput: %.3f GFLOP/s\n",
           (double)n * repetitions / elapsed / 1e9);

    free(x);
    free(y);
    free(z);
    return 0;
}