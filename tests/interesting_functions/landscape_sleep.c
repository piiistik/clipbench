#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#endif

/*
  Fast deterministic timing landscape over 3D space.

  Usage:
    landscape_sleep X Y Z SEED N MODE BOTTOM_BORDER TOP_BORDER

  MODE:
    0 = local minima (faster near hotspots)
    1 = local maxima (slower near hotspots)

  Notes:
    - No dynamic allocation.
    - No actual 3D grid is created.
    - Hotspots are generated on the fly from SEED.
    - The same inputs always produce the same sleep time.
    - Hotspot centers are generated inside [BOTTOM_BORDER, TOP_BORDER].
*/

#define BASE_SLEEP_MS 50.0
#define AMP_MIN_MS   1.0
#define AMP_MAX_MS   40.0
#define MIN_SLEEP_MS  1.0
#define MAX_SLEEP_MS 500.0
#define INV_RADIUS2   0.0004  /* Larger => tighter hotspots */

static inline uint64_t splitmix64_next(uint64_t *state) {
    uint64_t z = (*state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static inline double u64_to_unit_double(uint64_t x) {
    /* Convert top 53 bits to [0, 1). */
    return (double)(x >> 11) * (1.0 / 9007199254740992.0);
}

static void fast_sleep_ms(double ms) {
    if (ms < 0.0) ms = 0.0;

#ifdef _WIN32
    DWORD whole = (DWORD)(ms + 0.5);
    Sleep(whole);
#else
    struct timespec ts;
    long long nsec = (long long)(ms * 1000000.0) * 1000LL;
    ts.tv_sec = (time_t)(nsec / 1000000000LL);
    ts.tv_nsec = (long)(nsec % 1000000000LL);
    nanosleep(&ts, NULL);
#endif
}

static int parse_mode(const char *s) {
    if (s == NULL || *s == '\0') return 1;
    if (s[0] == '0') return 0;
    if (s[0] == '1') return 1;
    if (s[0] == 'm' || s[0] == 'M') {
        if (s[1] == 'i' || s[1] == 'I') return 0;
        return 1;
    }
    return 1;
}

int main(int argc, char **argv) {
    if (argc < 9) {
        fprintf(stderr, "Usage: %s X Y Z SEED N MODE BOTTOM_BORDER TOP_BORDER\n", argv[0]);
        return 1;
    }

    const double x = strtod(argv[1], NULL);
    const double y = strtod(argv[2], NULL);
    const double z = strtod(argv[3], NULL);
    uint64_t seed = (uint64_t)strtoull(argv[4], NULL, 10);
    unsigned long n_in = strtoul(argv[5], NULL, 10);
    int mode = parse_mode(argv[6]);
    double bottom = strtod(argv[7], NULL);
    double top = strtod(argv[8], NULL);

    if (n_in == 0) n_in = 1;
    if (top < bottom) {
        double tmp = bottom;
        bottom = top;
        top = tmp;
    }

    const double span = top - bottom;

    /* Small, deterministic, stack-free landscape generation. */
    double sleep_ms = BASE_SLEEP_MS;
    uint64_t rng = seed;

    for (unsigned long i = 0; i < n_in; ++i) {
        /* Generate one hotspot center inside the requested box. */
        double cx = bottom + u64_to_unit_double(splitmix64_next(&rng)) * span;
        double cy = bottom + u64_to_unit_double(splitmix64_next(&rng)) * span;
        double cz = bottom + u64_to_unit_double(splitmix64_next(&rng)) * span;

        /* Per-hotspot strength, randomized but deterministic. */
        double amp = AMP_MIN_MS + u64_to_unit_double(splitmix64_next(&rng)) * (AMP_MAX_MS - AMP_MIN_MS);

        double dx = x - cx;
        double dy = y - cy;
        double dz = z - cz;
        double d2 = dx * dx + dy * dy + dz * dz;
        double w = 1.0 / (1.0 + d2 * INV_RADIUS2);

        if (mode == 0) {
            sleep_ms -= amp * w;
        } else {
            sleep_ms += amp * w;
        }
    }

    if (sleep_ms < MIN_SLEEP_MS) sleep_ms = MIN_SLEEP_MS;
    if (sleep_ms > MAX_SLEEP_MS) sleep_ms = MAX_SLEEP_MS;

    fast_sleep_ms(sleep_ms);
    return 0;
}
