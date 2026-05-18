/*
 * Double-Well Gradient Descent
 * ----------------------------
 *
 * This program performs gradient descent on the function:
 *
 *     f(x, y) = (x^2 - 1)^2 + y^2
 *
 * This surface has two distinct global minima with the same value:
 *     (-1, 0) and (1, 0)
 *
 * Both minima have f(x, y) = 0.
 *
 * The rest of the surface rises smoothly away from those two wells,
 * so the objective trends toward one of the two minima depending on
 * the starting point.
 *
 * The optional --delay parameter sleeps for a fixed number of
 * milliseconds after each iteration, making runtime differences
 * easier to observe in an external benchmark.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <math.h>
#include <time.h>
#include <errno.h>

#define MAX_ITERS 1000
#define STEP_SIZE  0.02

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

static double objective(double x, double y) {
    return (x * x - 1.0) * (x * x - 1.0) + y * y;
}

static void descent(double *x, double *y, unsigned int delay_ms, int *iters) {
    int i;
    for (i = 0; i < MAX_ITERS; i++) {
        double gx = 4.0 * (*x) * ((*x) * (*x) - 1.0);
        double gy = 2.0 * (*y);

        double new_x = *x - STEP_SIZE * gx;
        double new_y = *y - STEP_SIZE * gy;

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }

        *x = new_x;
        *y = new_y;

        if (fabs(gx) + fabs(gy) < 1e-8) {
            i++;
            break;
        }
    }

    *iters = i;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --a <value> --b <value> [--delay <ms>]\n"
        "\n"
        "  --a      initial x value\n"
        "  --b      initial y value\n"
        "  --delay  sleep this many milliseconds (float) after each iteration\n",
        prog);
}

int main(int argc, char **argv) {
    double x = 0.0, y = 0.0;
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
                x = strtod(optarg, NULL);
                have_a = 1;
                break;
            case 'b':
                y = strtod(optarg, NULL);
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

    int iters = 0;
    descent(&x, &y, delay_ms, &iters);

    printf("final_x=%.8f\n", x);
    printf("final_y=%.8f\n", y);
    printf("value=%.12f\n", objective(x, y));
    printf("iterations=%d\n", iters);

    return 0;
}