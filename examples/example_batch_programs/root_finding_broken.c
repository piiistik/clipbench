/*
 * Broken 2D Root Finding (Near-Zero Denominator Bug)
 * ---------------------------------------------------
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
 * The program uses the same Newton-style iteration as the adaptive
 * baseline, but keeps one intentional flaw.
 *
 * This version is "broken" on purpose:
 * when x or y is near zero, it clamps to an extremely tiny denominator
 * (1e-12), which can cause very large updates and slow convergence near
 * the coordinate axes.
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

static void sleep_ms(double delay_ms) {
    if (delay_ms <= 0.0) return;
    
    unsigned long delay_ns = (unsigned long)(delay_ms * 1000000.0 + 0.5);
    struct timespec req;
    req.tv_sec = delay_ns / 1000000000UL;
    req.tv_nsec = (long)(delay_ns % 1000000000UL);

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static double step_scale(double fx, double fy) {
    double r = sqrt(fx * fx + fy * fy);

    if (r > 1000.0) {
        return 0.25;
    }
    if (r > 10.0) {
        return 0.5;
    }
    return 1.0;
}

static double root_u64(double x, double y, unsigned int delay_ms) {
    const int max_iter = 100000;
    const double tol = 1e-12;

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

        double alpha = step_scale(fx, fy);

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
        "  --delay  sleep this many milliseconds (float) after each iteration\n",
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

    double err = root_u64(a_in, b_in, delay_ms);
    printf("%.17g\n", err);

    return 0;
}