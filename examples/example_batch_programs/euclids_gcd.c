/*
 * Euclid's GCD Algorithm with Artificial Delay
 * --------------------------------------------
 *
 * This program computes the Greatest Common Divisor (GCD) of two numbers
 * using Euclid’s algorithm.
 *
 * Euclid’s algorithm works by repeatedly replacing the pair (a, b) with
 * (b, a % b) until b becomes 0. At that point, a contains the GCD.
 *
 * Key property:
 *     gcd(a, b) = gcd(b, a mod b)
 *
 * Example:
 *     gcd(48, 18)
 *       -> gcd(18, 12)
 *       -> gcd(12, 6)
 *       -> gcd(6, 0) = 6
 *
 * Why this program is useful:
 * ---------------------------
 * The number of iterations Euclid’s algorithm takes depends on the input
 * values in a non-uniform way. Some inputs converge very quickly, while
 * others (notably Fibonacci-like pairs) take significantly longer.
 *
 * This creates an interesting "runtime landscape" over the input space,
 * with local minima and maxima in execution time.
 *
 * Artificial Delay:
 * -----------------
 * The --delay parameter adds a fixed sleep (in milliseconds) after each
 * iteration of the algorithm.
 *
 * This does NOT change the algorithm’s result, but it amplifies timing
 * differences between inputs, making them easier to observe in external
 * benchmarking tools.
 *
 * Usage example:
 *     ./gcd_delay --a 48 --b 18 --delay 10
 *
 * This will compute gcd(48, 18) and wait 10 ms after each iteration.
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
    while (b != 0) {
        uint64_t r = a % b;
        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
        a = b;
        b = r;
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