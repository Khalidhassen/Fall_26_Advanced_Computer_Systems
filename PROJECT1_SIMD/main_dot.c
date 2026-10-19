#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

float dot(const float *restrict x,
          const float *restrict y,
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

    if (n == 0 || n > 8388608
        || repetitions <= 0 || repetitions > 1000000) {
        fprintf(stderr, "Invalid size or repetition count.\n");
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

    // Compute a double-precision reference outside the timing.
    double expected = 0.0;

    for (size_t i = 0; i < n; i++) {
        x[i] = (float)(i % 4) * 0.25f;
        y[i] = 0.5f;
        expected += (double)x[i] * (double)y[i];
    }

    float result = dot(x, y, n);

    if ((double)result != expected) {
        fprintf(stderr, "FAIL: got %.9g, expected %.9g\n",
                (double)result, expected);
        free(x);
        free(y);
        return 1;
    }

    // Accumulate returned values so their results are used.
    double checksum = 0.0;

    for (int r = 0; r < 10; r++) {
        checksum += dot(x, y, n);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        checksum += dot(x, y, n);
    }

    double elapsed = seconds() - start;
    double expected_checksum = expected * (repetitions + 10.0);

    if (checksum != expected_checksum) {
        fprintf(stderr, "Repeated-result check failed.\n");
        free(x);
        free(y);
        return 1;
    }

    printf("Correctness: PASS\n");
    printf("Elements: %zu\n", n);
    printf("Repetitions: %d\n", repetitions);
    printf("Dot product: %.9g\n", (double)result);
    printf("Checksum: %.9g\n", checksum);
    printf("Total time: %.6f seconds\n", elapsed);
    printf("Time per pass: %.3f microseconds\n",
           elapsed / repetitions * 1e6);
    printf("Throughput: %.3f GFLOP/s\n",
           2.0 * n * repetitions / elapsed / 1e9);

    free(x);
    free(y);
    return 0;
}