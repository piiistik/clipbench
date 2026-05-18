/*
 * Conway's Game of Life with Artificial Delay
 * -------------------------------------------
 *
 * This program simulates Conway’s Game of Life on a rectangular grid.
 *
 * Each cell is either alive or dead. On every generation, the next state
 * is computed from the number of live neighbors around each cell.
 *
 * The basic rules are:
 *   - A live cell survives with 2 or 3 live neighbors.
 *   - A dead cell becomes alive with exactly 3 live neighbors.
 *   - Otherwise, the cell becomes or stays dead.
 *
 * This program is useful for benchmarking because the runtime depends
 * mostly on the grid width, grid height, and number of generations.
 *
 * The other inputs have much weaker effect:
 *   - the initial live-cell density changes the starting pattern,
 *   - the wraparound flag changes boundary handling,
 *   - but neither changes the overall amount of grid work very much.
 *
 * Artificial Delay:
 * -----------------
 * The --delay parameter adds a fixed sleep (in milliseconds) after each
 * generation.
 *
 * This does NOT change the algorithm’s result, but it amplifies timing
 * differences between inputs, making them easier to observe in external
 * benchmarking tools.
 *
 * Usage example:
 *     ./life_delay --width 256 --height 256 --generations 100 --density 30 --wraparound 1 --delay 10
 *
 * This will simulate a 256x256 grid for 100 generations, with 30%
 * initial live cells, wraparound enabled, and 10 ms of delay after each
 * generation.
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

static uint64_t xorshift64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    return x;
}

static size_t idx2d(uint64_t x, uint64_t y, uint64_t width) {
    return (size_t)(y * width + x);
}

static uint64_t count_neighbors(const uint8_t *grid,
                                uint64_t width,
                                uint64_t height,
                                uint64_t x,
                                uint64_t y,
                                int wraparound) {
    uint64_t count = 0;

    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            if (dx == 0 && dy == 0) {
                continue;
            }

            int64_t nx = (int64_t)x + dx;
            int64_t ny = (int64_t)y + dy;

            if (wraparound) {
                if (nx < 0) nx += (int64_t)width;
                if (ny < 0) ny += (int64_t)height;
                if (nx >= (int64_t)width) nx -= (int64_t)width;
                if (ny >= (int64_t)height) ny -= (int64_t)height;

                count += grid[idx2d((uint64_t)nx, (uint64_t)ny, width)] ? 1U : 0U;
            } else {
                if (nx >= 0 && ny >= 0 &&
                    nx < (int64_t)width && ny < (int64_t)height) {
                    count += grid[idx2d((uint64_t)nx, (uint64_t)ny, width)] ? 1U : 0U;
                }
            }
        }
    }

    return count;
}

static uint64_t simulate_life(uint64_t width,
                              uint64_t height,
                              uint64_t generations,
                              uint64_t density_percent,
                              int wraparound,
                              unsigned int delay_ms) {
    size_t cells = (size_t)width * (size_t)height;
    uint8_t *cur = NULL;
    uint8_t *next = NULL;
    uint64_t live_count = 0;
    uint64_t seed = 0x9E3779B97F4A7C15ULL
                  ^ (width * 0xBF58476D1CE4E5B9ULL)
                  ^ (height * 0x94D049BB133111EBULL)
                  ^ (generations + 0xD1B54A32D192ED03ULL)
                  ^ (density_percent << 1)
                  ^ (wraparound ? 0xA5A5A5A5A5A5A5A5ULL : 0x5A5A5A5A5A5A5A5AULL);

    cur = (uint8_t *)calloc(cells, sizeof(uint8_t));
    next = (uint8_t *)calloc(cells, sizeof(uint8_t));
    if (cur == NULL || next == NULL) {
        fprintf(stderr, "Out of memory\n");
        free(cur);
        free(next);
        exit(1);
    }

    {
        uint64_t threshold = (density_percent > 100U) ? 100U : density_percent;
        threshold = (threshold * UINT64_C(0xFFFFFFFFFFFFFFFF)) / 100U;

        for (size_t i = 0; i < cells; ++i) {
            uint64_t r = xorshift64(&seed);
            if (r <= threshold) {
                cur[i] = 1;
                live_count++;
            }
        }
    }

    for (uint64_t gen = 0; gen < generations; ++gen) {
        uint64_t next_live_count = 0;

        for (uint64_t y = 0; y < height; ++y) {
            for (uint64_t x = 0; x < width; ++x) {
                uint64_t n = count_neighbors(cur, width, height, x, y, wraparound);
                uint8_t alive = cur[idx2d(x, y, width)];

                uint8_t new_alive = 0;
                if (alive) {
                    if (n == 2 || n == 3) {
                        new_alive = 1;
                    }
                } else {
                    if (n == 3) {
                        new_alive = 1;
                    }
                }

                next[idx2d(x, y, width)] = new_alive;
                next_live_count += new_alive ? 1U : 0U;
            }
        }

        {
            uint8_t *tmp = cur;
            cur = next;
            next = tmp;
        }

        live_count = next_live_count;

        if (delay_ms > 0) {
            sleep_ms(delay_ms);
        }
    }

    free(cur);
    free(next);

    return live_count;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --width <value> --height <value> --generations <value> --density <value> --wraparound <value> [--delay <ms>]\n"
        "\n"
        "  --width        grid width\n"
        "  --height       grid height\n"
        "  --generations  number of generations\n"
        "  --density      initial live-cell density in percent\n"
        "  --wraparound   wraparound flag (0 or 1)\n"
        "  --delay  sleep this many milliseconds after each generation\n",
        prog
    );
}

int main(int argc, char **argv) {
    double width_in = 0.0;
    double height_in = 0.0;
    double generations_in = 0.0;
    double density_in = 0.0;
    double wraparound_in = 0.0;
    unsigned int delay_ms = 0;
    int have_width = 0, have_height = 0, have_generations = 0, have_density = 0, have_wraparound = 0;

    static struct option long_opts[] = {
        {"width", required_argument, 0, 'a'},
        {"height", required_argument, 0, 'b'},
        {"generations", required_argument, 0, 'c'},
        {"density", required_argument, 0, 'd'},
        {"wraparound", required_argument, 0, 'e'},
        {"delay", required_argument, 0, 'l'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt, opt_idx = 0;

    while ((opt = getopt_long(argc, argv, "", long_opts, &opt_idx)) != -1) {
        switch (opt) {
            case 'a':
                width_in = strtod(optarg, NULL);
                have_width = 1;
                break;
            case 'b':
                height_in = strtod(optarg, NULL);
                have_height = 1;
                break;
            case 'c':
                generations_in = strtod(optarg, NULL);
                have_generations = 1;
                break;
            case 'd':
                density_in = strtod(optarg, NULL);
                have_density = 1;
                break;
            case 'e':
                wraparound_in = strtod(optarg, NULL);
                have_wraparound = 1;
                break;
            case 'l': {
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

    if (!have_width || !have_height || !have_generations || !have_density || !have_wraparound) {
        usage(argv[0]);
        return 1;
    }

    uint64_t width = round_nonneg_to_u64(width_in);
    uint64_t height = round_nonneg_to_u64(height_in);
    uint64_t generations = round_nonneg_to_u64(generations_in);
    uint64_t density = round_nonneg_to_u64(density_in);
    uint64_t wrap_u64 = round_nonneg_to_u64(wraparound_in);
    int wraparound = (wrap_u64 != 0);

    if (width == 0) {
        width = 1;
    }
    if (height == 0) {
        height = 1;
    }

    if (density > 100U) {
        density = 100U;
    }

    uint64_t live = simulate_life(width, height, generations, density, wraparound, delay_ms);
    printf("%" PRIu64 "\n", live);

    return 0;
}