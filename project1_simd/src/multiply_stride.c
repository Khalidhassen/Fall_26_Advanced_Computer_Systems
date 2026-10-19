#include <stddef.h>

void multiply_stride(const float *restrict x,
                     const float *restrict y,
                     float *restrict z,
                     size_t length,
                     size_t stride)
{
    for (size_t i = 0; i < length; i += stride) {
        z[i] = x[i] * y[i];
    }
}
