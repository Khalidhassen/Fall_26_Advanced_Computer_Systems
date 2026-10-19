#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void axpy(float a,
          const float *restrict x,
          float *restrict y,
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
    const int warmups = 10;
    const float a = 0.5f;

    if (n == 0 || n > (size_t)-1 / sizeof(float)
        || repetitions <= 0 || repetitions > 1000000) {
        fprintf(stderr,
                "Invalid size or repetitions (allowed: 1–1000000).\n");
        return 1;
    }

    float *x = malloc(n * sizeof(float));
    float *y = malloc(n * sizeof(float));

    if (x == NULL || y == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        free(x);
        free(y);
        return 1;
    }

    for (size_t i = 0; i < n; i++) {
        x[i] = (float)(i % 8) * 0.5f;
        y[i] = (float)(i % 16);
    }

    for (int r = 0; r < warmups; r++) {
        axpy(a, x, y, n);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        axpy(a, x, y, n);
    }

    double elapsed = seconds() - start;

    // Every call adds a*x[i], including the warm-up calls.
    for (size_t i = 0; i < n; i++) {
        double initial_y = (double)(i % 16);
        double expected = initial_y
            + (double)(repetitions + warmups) * a * x[i];

        if ((double)y[i] != expected) {
            fprintf(stderr,
                    "FAIL at %zu: got %.9g, expected %.9g\n",
                    i, (double)y[i], expected);
            free(x);
            free(y);
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
           2.0 * n * repetitions / elapsed / 1e9);

    free(x);
    free(y);
    return 0;
}