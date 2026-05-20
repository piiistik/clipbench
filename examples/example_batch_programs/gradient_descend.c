/*
 * Gradient Descent with Backtracking Line Search and Artificial Delay
 * -------------------------------------------------------------------
 *
 * This program minimizes a simple convex quadratic function in two
 * variables using gradient descent with backtracking line search.
 *
 * The objective function is:
 *
 *     f(x, y) = x^2 + 4y^2
 *
 * This is a smooth bowl-shaped function with a single minimum at:
 *
 *     (0, 0)
 *
 * Gradient descent works by repeatedly moving in the direction of the
 * negative gradient. Backtracking line search adjusts the step size so
 * that each iteration makes sufficient progress.
 *
 * Why this program is useful:
 * ---------------------------
 * The runtime is fairly smooth over the whole 2D input space because the
 * same optimization logic is used everywhere.
 *
 * This makes it a good baseline for benchmarking iterative optimization.
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
 *     ./gd_delay --a 0 --b 0 --delay 10
 *
 * This will start from (0, 0) and wait 10 ms after each iteration.
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

static double objective(double x, double y) {
    return x * x + 4.0 * y * y;
}

static void gradient(double x, double y, double *gx, double *gy) {
    *gx = 2.0 * x;
    *gy = 8.0 * y;
}

static double optimize(double x, double y, unsigned int delay_ms) {
    const int max_iter = 100000;
    const double grad_tol = 1e-12;
    const double armijo = 1e-4;
    const double shrink = 0.5;

    for (int iter = 0; iter < max_iter; ++iter) {
        double gx, gy;
        gradient(x, y, &gx, &gy);

        double gnorm2 = gx * gx + gy * gy;
        if (gnorm2 < grad_tol * grad_tol) {
            break;
        }

        double fx = objective(x, y);
        double step = 1.0;

        while (step >= 1e-16) {
            double tx = x - step * gx;
            double ty = y - step * gy;
            double tf = objective(tx, ty);

            if (tf <= fx - armijo * step * gnorm2) {
                x = tx;
                y = ty;
                break;
            }

            step *= shrink;
        }

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
    }

    return objective(x, y);
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

    double result = optimize(a_in, b_in, delay_ms);
    printf("%.17g\n", result);

    return 0;
}
