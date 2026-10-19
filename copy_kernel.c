#include <stddef.h>

void copy_kernel(const float *restrict source,
                 float *restrict destination,
                 size_t n)
{
    for (size_t i = 0; i < n; i++) {
        destination[i] = source[i];
    }
}