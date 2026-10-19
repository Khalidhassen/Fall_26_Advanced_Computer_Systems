#include <stddef.h>

void multiply_double(const double *restrict x,
              const double *restrict y,
              double *restrict z,
              size_t n)
{
    for (size_t i = 0; i < n; i++) {
        z[i] = x[i] * y[i];
    }
}