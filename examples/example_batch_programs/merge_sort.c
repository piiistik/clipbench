/*
 * Merge Sort Benchmark (Optimized Version)
 * ----------------------------------------
 *
 * This program sorts an array using mergesort.
 *
 * Inputs:
 *   --n    size of the array
 *   --pct  percentage of items that are disturbed before sorting
 *
 * This version is optimized:
 * it avoids unnecessary work when subarrays are already in order,
 * so runtime scales smoothly as the array size grows.
 *
 * The optional --delay parameter sleeps for a fixed number of
 * milliseconds after each merge operation, making runtime differences
 * easier to observe in an external benchmark.
 *
 * Usage:
 *     ./merge_sort --n <value> --pct <value> [--delay <ms>]
 */

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <getopt.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const size_t INSERTION_CUTOFF = 24;

static void sleep_ms(double delay_ms) {
    if (delay_ms <= 0.0) return;
    
    unsigned long delay_ns = (unsigned long)(delay_ms * 1000000.0 + 0.5);
    struct timespec req;
    req.tv_sec = delay_ns / 1000000000UL;
    req.tv_nsec = (long)(delay_ns % 1000000000UL);

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping */
    }
}

static uint64_t round_nonneg_to_u64(double v) {
    if (v < 0.0) v = -v;
    return (uint64_t)(v + 0.5);
}

static void die_oom(void) {
    fprintf(stderr, "Out of memory\n");
    exit(1);
}

static void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (p == NULL && n != 0) {
        die_oom();
    }
    return p;
}

static void swap_u64(uint64_t *a, uint64_t *b) {
    uint64_t t = *a;
    *a = *b;
    *b = t;
}

static uint64_t xorshift64star(uint64_t *state) {
    uint64_t x = *state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;
    return x * UINT64_C(2685821657736338717);
}

static size_t rand_below(uint64_t *state, size_t n) {
    return (size_t)(xorshift64star(state) % (uint64_t)n);
}

static void insertion_sort(uint64_t *a, size_t lo, size_t hi) {
    for (size_t i = lo + 1; i < hi; ++i) {
        uint64_t v = a[i];
        size_t j = i;
        while (j > lo && a[j - 1] > v) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = v;
    }
}

static void merge(uint64_t *a, uint64_t *tmp, size_t lo, size_t mid, size_t hi, double delay_ms) {
    size_t i = lo;
    size_t j = mid;
    size_t k = lo;

    while (i < mid && j < hi) {
        if (a[i] <= a[j]) {
            tmp[k++] = a[i++];
        } else {
            tmp[k++] = a[j++];
        }
    }
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi) tmp[k++] = a[j++];

    memcpy(a + lo, tmp + lo, (hi - lo) * sizeof(uint64_t));
    
    if (delay_ms > 0.0) {
        sleep_ms(delay_ms);
    }
}

static void merge_sort_impl(uint64_t *a, uint64_t *tmp, size_t lo, size_t hi, double delay_ms) {
    size_t n = hi - lo;
    if (n <= INSERTION_CUTOFF) {
        insertion_sort(a, lo, hi);
        return;
    }

    size_t mid = lo + n / 2;
    merge_sort_impl(a, tmp, lo, mid, delay_ms);
    merge_sort_impl(a, tmp, mid, hi, delay_ms);

    /* Skip the merge if the halves are already in order. */
    if (a[mid - 1] <= a[mid]) {
        return;
    }

    merge(a, tmp, lo, mid, hi, delay_ms);
}

static uint64_t checksum_array(const uint64_t *a, size_t n) {
    uint64_t h = UINT64_C(1469598103934665603);
    for (size_t i = 0; i < n; ++i) {
        h ^= a[i] + UINT64_C(0x9e3779b97f4a7c15) * (uint64_t)(i + 1);
        h *= UINT64_C(1099511628211);
    }
    return h;
}

static void make_dataset(uint64_t n, uint64_t pct, uint64_t *a) {
    for (uint64_t i = 0; i < n; ++i) {
        a[i] = i;
    }

    if (n <= 1 || pct == 0) {
        return;
    }

    if (pct > 100) {
        pct = 100;
    }

    uint64_t swaps = (n * pct + 99) / 100;
    if (swaps == 0) {
        swaps = 1;
    }

    uint64_t state = UINT64_C(0x243f6a8885a308d3) ^
                     (n * UINT64_C(0x9e3779b97f4a7c15)) ^
                     (pct * UINT64_C(0xbf58476d1ce4e5b9));

    for (uint64_t s = 0; s < swaps; ++s) {
        size_t i = rand_below(&state, (size_t)(n - 1));
        swap_u64(&a[i], &a[i + 1]);
    }
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --n <size> --pct <unsorted_percentage> [--delay <ms>]\n"
        "\n"
        "  --n     array size\n"
        "  --pct   percentage of items to disturb (0..100)\n"
        "  --delay sleep this many milliseconds (float) after each merge\n",
        prog);
}

int main(int argc, char **argv) {
    double n_in = 0.0;
    double pct_in = 0.0;
    double delay_ms = 0.0;
    int have_n = 0, have_pct = 0;

    static struct option long_opts[] = {
        {"n", required_argument, 0, 'n'},
        {"pct", required_argument, 0, 'p'},
        {"delay", required_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt, opt_idx = 0;
    while ((opt = getopt_long(argc, argv, "", long_opts, &opt_idx)) != -1) {
        switch (opt) {
            case 'n':
                n_in = strtod(optarg, NULL);
                have_n = 1;
                break;
            case 'p':
                pct_in = strtod(optarg, NULL);
                have_pct = 1;
                break;
            case 'd': {
                char *end = NULL;
                double v = strtod(optarg, &end);
                if (end == optarg || *end != '\0') {
                    fprintf(stderr, "Invalid --delay value: %s\n", optarg);
                    return 1;
                }
                delay_ms = v;
                break;
            }
            case 'h':
            default:
                usage(argv[0]);
                return 1;
        }
    }

    if (!have_n || !have_pct) {
        usage(argv[0]);
        return 1;
    }

    uint64_t n = round_nonneg_to_u64(n_in);
    uint64_t pct = round_nonneg_to_u64(pct_in);
    if (pct > 100) {
        pct = 100;
    }

    if (n == 0) {
        puts("0");
        return 0;
    }

    uint64_t *a = (uint64_t *)xmalloc((size_t)n * sizeof(uint64_t));
    uint64_t *tmp = (uint64_t *)xmalloc((size_t)n * sizeof(uint64_t));

    make_dataset(n, pct, a);
    merge_sort_impl(a, tmp, 0, (size_t)n, delay_ms);

    printf("%" PRIu64 "\n", checksum_array(a, (size_t)n));

    free(a);
    free(tmp);
    return 0;
}
