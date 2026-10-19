#include <stddef.h>

void axpy(float a,
          const float *restrict x,
          float *restrict y,
          size_t n)
{
    for (size_t i = 0; i < n; i++) {
        y[i] = a * x[i] + y[i];
    }
}