#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void multiply_stride(const float *restrict x,
                     const float *restrict y,
                     float *restrict z,
                     size_t length,
                     size_t stride);

double seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "Usage: %s length repetitions stride\n",
                argv[0]);
        return 1;
    }

    size_t length = (size_t)strtoull(argv[1], NULL, 10);
    int repetitions = atoi(argv[2]);
    size_t stride = (size_t)strtoull(argv[3], NULL, 10);

    if (length == 0 || length > 8388608
        || repetitions <= 0 || repetitions > 1000000
        || (stride != 1 && stride != 2
            && stride != 4 && stride != 8)) {
        fprintf(stderr, "Invalid arguments.\n");
        return 1;
    }

    size_t bytes = length * sizeof(float);

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

    float *x = base_x;
    float *y = base_y;
    float *z = base_z;

    for (size_t i = 0; i < length; i++) {
        x[i] = (float)(i % 100) * 0.25f;
        y[i] = (float)(i % 50) * 0.5f;
        z[i] = -1.0f;
    }

    for (int r = 0; r < 10; r++) {
        multiply_stride(x, y, z, length, stride);
    }

    double start = seconds();

    for (int r = 0; r < repetitions; r++) {
        multiply_stride(x, y, z, length, stride);
    }

    double elapsed = seconds() - start;

    // Check calculated elements and unchanged skipped elements.
    for (size_t i = 0; i < length; i++) {
        float expected = (i % stride == 0)
                       ? x[i] * y[i] : -1.0f;

        if (z[i] != expected) {
            fprintf(stderr, "Correctness failed at %zu\n", i);
            free(base_x);
            free(base_y);
            free(base_z);
            return 1;
        }
    }

    size_t processed = (length + stride - 1) / stride;
    double total_elements = (double)processed * repetitions;

    double ns_per_element = elapsed * 1e9 / total_elements;
    double gflops = total_elements / elapsed / 1e9;

    // Useful bytes: two float reads and one float write.
    // This is NOT a measurement of actual DRAM traffic.
    double useful_gib_s =
        total_elements * 3.0 * sizeof(float)
        / elapsed / 1073741824.0;

    printf("%zu,%zu,%zu,%d,%.9f,%.6f,%.6f,%.6f,PASS\n",
           length, stride, processed, repetitions,
           elapsed, ns_per_element, gflops, useful_gib_s);

    free(base_x);
    free(base_y);
    free(base_z);
    return 0;
}