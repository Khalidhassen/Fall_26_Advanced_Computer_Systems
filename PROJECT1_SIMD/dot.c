#include <stddef.h>

float dot(const float *restrict x,
          const float *restrict y,
          size_t n)
{
    float sum = 0.0f;

    for (size_t i = 0; i < n; i++) {
        sum += x[i] * y[i];
    }

    return sum;
}