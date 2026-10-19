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
    if (argc != 4) {
        fprintf(stderr, "Usage: %s elements repetitions offset\n",
                argv[0]);
        return 1;
    }

    size_t n = (size_t)strtoull(argv[1], NULL, 10);
    int repetitions = atoi(argv[2]);
    int offset = atoi(argv[3]);

    if (n == 0 || n > 8388608 || repetitions <= 0
        || repetitions > 1000000
        || (offset != 0 && offset != 1)) {
        fprintf(stderr, "Invalid arguments.\n");
        return 1;
    }

    // Reserve extra space so shifting the pointers is safe.
    size_t bytes = (n + 16) * sizeof(float);

    void *base_x = NULL;
    void *base_y = NULL;
    void *base_z = NULL;

    if (posix_memalign(&base_x, 64, bytes) != 0
        || posix_memalign(&base_y, 64, bytes) != 0
        || posix_memalign(&base_z, 64, bytes) != 0) {
        fprintf(stderr, "Memory allocation failed.\n");
        free(base_x);
        free(base_y);
        free(base_z);
        return 1;
    }

    float *x = (float *)base_x + offset;
    float *y = (float *)base_y + offset;
    float *z = (float *)base_z + offset;

    for (size_t i = 0; i < n; i++) {
        x[i] = (float)(i % 100) * 0.25f;
        y[i] = (float)(i % 50) * 0.5f;
    }

    for (int r = 0; r < 10; r++) {
        multiply(x, y, z, n);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        multiply(x, y, z, n);
    }

    double elapsed = seconds() - start;

    for (size_t i = 0; i < n; i++) {
        if (z[i] != x[i] * y[i]) {
            fprintf(stderr, "Correctness failed at %zu\n", i);
            free(base_x);
            free(base_y);
            free(base_z);
            return 1;
        }
    }

    // Output one CSV row. Timing excludes initialization/checking.
    printf("%zu,%d,%d,%.9f,%.9f,%.6f,PASS\n",
           n, repetitions, offset * (int)sizeof(float),
           elapsed,
           elapsed / repetitions * 1e6,
           (double)n * repetitions / elapsed / 1e9);

    // Free the original allocation addresses, not shifted pointers.
    free(base_x);
    free(base_y);
    free(base_z);
    return 0;
}