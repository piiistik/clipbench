/*
 * Dynamic Array Append with Geometric Growth and Artificial Delay
 * ---------------------------------------------------------------
 *
 * This program appends a sequence of values into a dynamically growing
 * array, similar to the behavior of a vector or resizable buffer.
 *
 * The first input controls how many values are appended.
 * The second input controls the initial reserved capacity of the buffer.
 *
 * This version is "good" on purpose:
 * it grows the buffer geometrically, usually by doubling its capacity
 * whenever more space is needed.
 *
 * That makes appends mostly constant time, with only occasional resize
 * events, so the runtime rises smoothly as the number of appends grows.
 *
 * Why this program is useful:
 * ---------------------------
 * The overall runtime increases roughly linearly with the number of
 * appended elements, but the resize cost is spread out over time.
 *
 * This gives a clean baseline for benchmarking buffer growth behavior.
 *
 * Artificial Delay:
 * -----------------
 * The --delay parameter adds a fixed sleep (in milliseconds) after each
 * append operation.
 *
 * This does NOT change the algorithm’s result, but it amplifies timing
 * differences between inputs, making them easier to observe in external
 * benchmarking tools.
 *
 * Usage example:
 *     ./append_delay --a 100000 --b 16 --delay 1
 *
 * This will append 100000 values starting from capacity 16 and wait
 * 1 ms after each append.
 */

 #define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <time.h>
#include <errno.h>

static void sleep_ms(double delay_ms) {
    if (delay_ms <= 0.0) return;
    struct timespec req;
    unsigned long delay_ns = (unsigned long)(delay_ms * 1000000.0 + 0.5);
    req.tv_sec = delay_ns / 1000000000UL;
    req.tv_nsec = (long)(delay_ns % 1000000000UL);
    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static uint64_t round_nonneg_to_u64(double v) {
    if (v < 0.0) v = -v;
    return (uint64_t)(v + 0.5);
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
            uint64_t new_cap = cap * 2;
            if (new_cap < cap + 1) {
                new_cap = cap + 1;
            }
            buf = (uint64_t *)xrealloc(buf, (size_t)new_cap * sizeof(uint64_t));
            cap = new_cap;
        }

        buf[size++] = i;
        checksum += i;

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
    }

    free(buf);
    return checksum;
}
    double delay_ms = 0.0;
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