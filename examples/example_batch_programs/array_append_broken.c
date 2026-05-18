/*
 * Dynamic Array Append (Broken Fixed-Chunk Growth Version)
 * -------------------------------------------------------
 *
 * This program appends a sequence of values into a dynamically growing
 * array, similar to the behavior of a vector or resizable buffer.
 *
 * The first input controls how many values are appended.
 * The second input controls the initial reserved capacity of the buffer.
 *
 * This version is "broken" on purpose:
 * it grows the buffer by a fixed constant amount whenever it runs out
 * of space.
 *
 * That means the program repeatedly reallocates and copies the whole
 * buffer, which creates a very visible jump in execution time once the
 * initial capacity is exhausted.
 *
 * During each resize, copying each existing item also sleeps for a small
 * fraction of the user-provided delay, which makes the resize ridge even
 * more pronounced in benchmarking results.
 *
 * The optional --delay parameter adds a fixed sleep (in milliseconds)
 * after each append operation to amplify runtime differences.
 *
 * Usage:
 *     ./append_delay --a <value> --b <value> [--delay <ms>]
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <time.h>
#include <errno.h>

static const uint64_t GROWTH_CHUNK = 16;

static uint64_t round_nonneg_to_u64(double v) {
    if (v < 0.0) v = -v;
    return (uint64_t)(v + 0.5);
}

static void sleep_ms(double delay_ms) {
    struct timespec req;
    if (delay_ms <= 0.0) return;
    unsigned long delay_ns = (unsigned long)(delay_ms * 1000000.0 + 0.5);
    req.tv_sec = delay_ns / 1000000000UL;
    req.tv_nsec = (long)(delay_ns % 1000000000UL);

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static void sleep_us(unsigned long us) {
    struct timespec req;
    req.tv_sec = us / 1000000UL;
    req.tv_nsec = (long)(us % 1000000UL) * 1000L;

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n);
    if (q == NULL && n != 0) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    return q;
}
static uint64_t append_values(uint64_t n, uint64_t initial_cap, double delay_ms) {
    uint64_t cap = initial_cap;
    uint64_t size = 0;
    uint64_t *buf = NULL;
    uint64_t checksum = 0;

    if (cap == 0) {
        cap = 1;
    }

    buf = (uint64_t *)malloc((size_t)cap * sizeof(uint64_t));
    if (buf == NULL) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }

    for (uint64_t i = 0; i < n; ++i) {
        if (size == cap) {
            uint64_t new_cap = cap + GROWTH_CHUNK;
            if (new_cap < cap) {
                new_cap = UINT64_MAX;
            }

            uint64_t *new_buf = (uint64_t *)malloc((size_t)new_cap * sizeof(uint64_t));
            if (new_buf == NULL) {
                fprintf(stderr, "Out of memory\n");
                free(buf);
                exit(1);
            }

            for (uint64_t j = 0; j < size; ++j) {
                new_buf[j] = buf[j];
                if (delay_ms > 0.0) {
                    sleep_us((unsigned long)(delay_ms * 10.0));
                }
            }

            free(buf);
            buf = new_buf;
            cap = new_cap;
        }

        buf[size++] = i;
        checksum += i;
        if (delay_ms > 0.0) {
            sleep_ms(delay_ms);
        }
    }

    free(buf);
    return checksum;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --a <value> --b <value> [--delay <ms>]\n"
        "\n"
        "  --a      number of elements to append\n"
        "  --b      initial reserved capacity\n"
        "  --delay  sleep this many milliseconds after each append\n",
        prog
    );
}

int main(int argc, char **argv) {
    double a_in = 0.0;
    double b_in = 0.0;
    double delay_ms = 0.0;
    int have_a = 0, have_b = 0;

    static struct option long_opts[] = {
        {"a", required_argument, 0, 'a'},
        {"b", required_argument, 0, 'b'},
        {"delay", required_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt, opt_idx = 0;

    while ((opt = getopt_long(argc, argv, "", long_opts, &opt_idx)) != -1) {
        switch (opt) {
            case 'a':
                a_in = strtod(optarg, NULL);
                have_a = 1;
                break;
            case 'b':
                b_in = strtod(optarg, NULL);
                have_b = 1;
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

    if (!have_a || !have_b) {
        usage(argv[0]);
        return 1;
    }

    uint64_t n = round_nonneg_to_u64(a_in);
    uint64_t cap = round_nonneg_to_u64(b_in);

    if (n == 0 && cap == 0) {
        n = 1;
    }

    uint64_t checksum = append_values(n, cap, delay_ms);
    printf("%" PRIu64 "\n", checksum);

    return 0;
}