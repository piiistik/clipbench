/*
 * Broken Euclid GCD (Subtraction Version)
 * --------------------------------------
 *
 * This program computes the Greatest Common Divisor (GCD) of two numbers
 * using a subtraction-based variant of Euclid’s algorithm.
 *
 * Instead of using modulo, it repeatedly subtracts the smaller number
 * from the larger one until they become equal.
 *
 * This version is "broken" on purpose:
 * it replaces the efficient modulo step with repeated subtraction,
 * making it significantly slower, especially for imbalanced inputs.
 *
 * The optional --delay parameter adds a fixed sleep (in milliseconds)
 * after each iteration to amplify runtime differences.
 *
 * Usage:
 *     ./gcd_delay --a <value> --b <value> [--delay <ms>]
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <time.h>
#include <errno.h>

static uint64_t round_nonneg_to_u64(double v) {
    if (v < 0.0) v = -v;
    return (uint64_t)(v + 0.5);
}

static void sleep_ms(unsigned int ms) {
    struct timespec req;
    req.tv_sec = ms / 1000U;
    req.tv_nsec = (long)(ms % 1000U) * 1000000L;

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static uint64_t gcd_u64(uint64_t a, uint64_t b, unsigned int delay_ms) {
    if (a == 0) {
        return b;
    }
    if (b == 0) {
        return a;
    }

    while (a != b) {
        if (a > b) {
            a -= b;
        } else {
            b -= a;
        }

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
    }

    return a;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --a <value> --b <value> [--delay <ms>]\n"
        "\n"
        "  --a      first input number\n"
        "  --b      second input number\n"
        "  --delay  sleep this many milliseconds after each iteration\n",
        prog
    );
}

int main(int argc, char **argv) {
    double a_in = 0.0;
    double b_in = 0.0;
    unsigned int delay_ms = 0;
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
                unsigned long v = strtoul(optarg, &end, 10);
                if (end == optarg || *end != '\0') {
                    fprintf(stderr, "Invalid --delay value: %s\n", optarg);
                    return 1;
                }
                delay_ms = (unsigned int)v;
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

    uint64_t a = round_nonneg_to_u64(a_in);
    uint64_t b = round_nonneg_to_u64(b_in);

    if (a == 0 && b == 0) {
        a = 1;
    }

    uint64_t g = gcd_u64(a, b, delay_ms);
    printf("%" PRIu64 "\n", g);

    return 0;
}