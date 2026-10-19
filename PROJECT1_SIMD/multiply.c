#include <stddef.h>

void multiply(const float *restrict x,
              const float *restrict y,
              float *restrict z,
              size_t n)
{
    for (size_t i = 0; i < n; i++) {
        z[i] = x[i] * y[i];
    }
}