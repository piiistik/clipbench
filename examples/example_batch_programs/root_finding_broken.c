/*
 * Broken 2D Root Finding (Fixed-Step Version)
 * -------------------------------------------
 *
 * This program finds a root of the same two equations:
 *
 *     x^2 - 2 = 0
 *     y^2 - 3 = 0
 *
 * The solution is near:
 *
 *     (sqrt(2), sqrt(3))
 *
 * The program uses the same Newton-style iteration, but with a fixed
 * damping factor on every step.
 *
 * This version is "broken" on purpose:
 * it uses the same step size everywhere, even when the current point is
 * far from the solution and needs a different amount of damping.
 *
 * That creates a few hot spots in the input space where convergence is
 * noticeably slower than in the adaptive version.
 *
 * The optional --delay parameter adds a fixed sleep (in milliseconds)
 * after each iteration to amplify runtime differences.
 *
 * Usage:
 *     ./root_delay --a <value> --b <value> [--delay <ms>]
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <time.h>
#include <errno.h>
#include <math.h>

static void sleep_ms(unsigned int ms) {
    struct timespec req;
    req.tv_sec = ms / 1000U;
    req.tv_nsec = (long)(ms % 1000U) * 1000000L;

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static double root_u64(double x, double y, unsigned int delay_ms) {
    const int max_iter = 100000;
    const double tol = 1e-12;
    const double alpha = 0.5;

    for (int iter = 0; iter < max_iter; ++iter) {
        double fx = x * x - 2.0;
        double fy = y * y - 3.0;

        double err = sqrt(fx * fx + fy * fy);
        if (err < tol) {
            break;
        }

        if (fabs(x) < 1e-12) {
            x = (x < 0.0) ? -1e-12 : 1e-12;
        }
        if (fabs(y) < 1e-12) {
            y = (y < 0.0) ? -1e-12 : 1e-12;
        }

        x -= alpha * (fx / (2.0 * x));
        y -= alpha * (fy / (2.0 * y));

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
    }

    double fx = x * x - 2.0;
    double fy = y * y - 3.0;
    return sqrt(fx * fx + fy * fy);
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

    double err = root_u64(a_in, b_in, delay_ms);
    printf("%.17g\n", err);

    return 0;
}