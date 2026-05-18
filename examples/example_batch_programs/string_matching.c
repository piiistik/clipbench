/*
 * Naive String Matching
 * ---------------------
 *
 * This program computes the number of exact occurrences of a pattern in a
 * randomly generated text using the classic naive string matching algorithm.
 *
 * The runtime depends strongly on the text length:
 *
 *   - the number of text characters has a large effect,
 *   - the pattern length has a moderate effect.
 *
 * Other inputs have weaker effect:
 *
 *   - the alphabet size,
 *   - the mutation rate used when generating the pattern,
 *   - the random seed used to generate the instance,
 *   - the optional delay per character comparison.
 *
 * The text and pattern are generated from the same seed. The pattern is
 * created by copying a substring of the text and then mutating some of its
 * characters. This makes the alphabet size and mutation rate influence the
 * average mismatch depth during search, without dominating total runtime.
 *
 * If --delay is set, the algorithm sleeps after each character comparison.
 * This is useful for benchmarking and for making the number of comparisons
 * more visible in wall-clock time.
 *
 * Usage example:
 *     ./string_match --text-len 10000000 --pattern-len 12 --alphabet 26 --mutation-rate 0.05 --seed 123 --delay 0.01
 *
 * This will build a random text of length 10,000,000 and a pattern of length
 * 12, then count the number of exact matches.
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

static uint64_t xorshift64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    return x;
}

static uint64_t rand_range_u64(uint64_t *state, uint64_t limit) {
    if (limit == 0) {
        return 0;
    }
    return xorshift64(state) % limit;
}

static double rand_unit_double(uint64_t *state) {
    return (double)xorshift64(state) / ((double)UINT64_MAX + 1.0);
}

static void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (p == NULL && n != 0) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    return p;
}

static void sleep_ms_float(double ms) {
    if (ms <= 0.0) {
        return;
    }

    struct timespec req;
    req.tv_sec = (time_t)(ms / 1000.0);
    req.tv_nsec = (long)((ms - (req.tv_sec * 1000.0)) * 1000000.0);

    while (nanosleep(&req, &req) == -1 && errno == EINTR) {
        /* continue sleeping if interrupted */
    }
}

static uint8_t random_symbol(uint64_t *rng, uint32_t alphabet) {
    if (alphabet <= 1U) {
        return 0U;
    }
    return (uint8_t)rand_range_u64(rng, (uint64_t)alphabet);
}

static uint8_t mutate_symbol(uint64_t *rng, uint8_t old_sym, uint32_t alphabet) {
    if (alphabet <= 1U) {
        return old_sym;
    }

    uint32_t choice = (uint32_t)rand_range_u64(rng, (uint64_t)(alphabet - 1U));
    if (choice >= old_sym) {
        choice++;
    }
    return (uint8_t)choice;
}

static void build_random_instance(uint64_t text_len,
                                  uint64_t pattern_len,
                                  uint32_t alphabet,
                                  double mutation_rate,
                                  uint64_t seed,
                                  uint8_t **text_out,
                                  uint8_t **pattern_out) {
    if (text_len == 0) {
        text_len = 1;
    }
    if (pattern_len == 0) {
        pattern_len = 1;
    }
    if (pattern_len > text_len) {
        pattern_len = text_len;
    }
    if (alphabet == 0) {
        alphabet = 1;
    }
    if (alphabet > 256U) {
        alphabet = 256U;
    }

    uint8_t *text = (uint8_t *)xmalloc((size_t)text_len * sizeof(uint8_t));
    uint8_t *pattern = (uint8_t *)xmalloc((size_t)pattern_len * sizeof(uint8_t));

    uint64_t rng = seed ? seed : 0xD1B54A32D192ED03ULL;

    for (uint64_t i = 0; i < text_len; ++i) {
        text[i] = random_symbol(&rng, alphabet);
    }

    uint64_t start = 0;
    if (pattern_len < text_len) {
        start = rand_range_u64(&rng, text_len - pattern_len + 1U);
    }

    for (uint64_t i = 0; i < pattern_len; ++i) {
        pattern[i] = text[start + i];
    }

    for (uint64_t i = 0; i < pattern_len; ++i) {
        if (mutation_rate > 0.0 && rand_unit_double(&rng) < mutation_rate) {
            pattern[i] = mutate_symbol(&rng, pattern[i], alphabet);
        }
    }

    *text_out = text;
    *pattern_out = pattern;
}

static uint64_t naive_string_match_count(const uint8_t *text,
                                         uint64_t text_len,
                                         const uint8_t *pattern,
                                         uint64_t pattern_len,
                                         double delay_ms) {
    if (pattern_len == 0 || text_len < pattern_len) {
        return 0;
    }

    uint64_t matches = 0;
    uint64_t last_start = text_len - pattern_len;

    for (uint64_t i = 0; i <= last_start; ++i) {
        uint64_t j = 0;
        while (j < pattern_len) {
            if (delay_ms > 0.0) {
                sleep_ms_float(delay_ms);
            }

            if (text[i + j] != pattern[j]) {
                break;
            }

            ++j;
        }

        if (j == pattern_len) {
            ++matches;
        }
    }

    return matches;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --text-len <value> --pattern-len <value> --alphabet <value> "
        "--mutation-rate <value> --seed <value> [--delay <ms>]\n"
        "\n"
        "  --text-len       length of generated text\n"
        "  --pattern-len    length of generated pattern\n"
        "  --alphabet       number of symbols used in generation\n"
        "  --mutation-rate  probability in [0, 1] of mutating each pattern character\n"
        "  --seed           random seed for instance generation\n"
        "  --delay          sleep this many milliseconds after each character comparison\n",
        prog
    );
}

int main(int argc, char **argv) {
    double text_len_in = 0.0;
    double pattern_len_in = 0.0;
    double alphabet_in = 0.0;
    double mutation_rate = 0.0;
    double seed_in = 0.0;
    double delay_ms = 0.0;

    int have_text_len = 0;
    int have_pattern_len = 0;
    int have_alphabet = 0;
    int have_mutation_rate = 0;
    int have_seed = 0;

    static struct option long_opts[] = {
        {"text-len", required_argument, 0, 'n'},
        {"pattern-len", required_argument, 0, 'p'},
        {"alphabet", required_argument, 0, 'a'},
        {"mutation-rate", required_argument, 0, 'm'},
        {"seed", required_argument, 0, 's'},
        {"delay", required_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt, opt_idx = 0;
    while ((opt = getopt_long(argc, argv, "", long_opts, &opt_idx)) != -1) {
        switch (opt) {
            case 'n':
                text_len_in = strtod(optarg, NULL);
                have_text_len = 1;
                break;
            case 'p':
                pattern_len_in = strtod(optarg, NULL);
                have_pattern_len = 1;
                break;
            case 'a':
                alphabet_in = strtod(optarg, NULL);
                have_alphabet = 1;
                break;
            case 'm': {
                char *end = NULL;
                mutation_rate = strtod(optarg, &end);
                if (end == optarg || *end != '\0') {
                    fprintf(stderr, "Invalid --mutation-rate value: %s\n", optarg);
                    return 1;
                }
                have_mutation_rate = 1;
                break;
            }
            case 's':
                seed_in = strtod(optarg, NULL);
                have_seed = 1;
                break;
            case 'd': {
                char *end = NULL;
                delay_ms = strtod(optarg, &end);
                if (end == optarg || *end != '\0') {
                    fprintf(stderr, "Invalid --delay value: %s\n", optarg);
                    return 1;
                }
                break;
            }
            case 'h':
            default:
                usage(argv[0]);
                return 1;
        }
    }

    if (!have_text_len || !have_pattern_len || !have_alphabet || !have_mutation_rate || !have_seed) {
        usage(argv[0]);
        return 1;
    }

    if (mutation_rate < 0.0 || mutation_rate > 1.0) {
        fprintf(stderr, "--mutation-rate must be between 0 and 1\n");
        return 1;
    }

    if (delay_ms < 0.0) {
        fprintf(stderr, "--delay must be non-negative\n");
        return 1;
    }

    uint64_t text_len = round_nonneg_to_u64(text_len_in);
    uint64_t pattern_len = round_nonneg_to_u64(pattern_len_in);
    uint64_t alphabet_u64 = round_nonneg_to_u64(alphabet_in);
    uint64_t seed = round_nonneg_to_u64(seed_in);

    if (text_len == 0) {
        text_len = 1;
    }
    if (pattern_len == 0) {
        pattern_len = 1;
    }
    if (alphabet_u64 == 0) {
        alphabet_u64 = 1;
    }
    if (alphabet_u64 > 256U) {
        alphabet_u64 = 256U;
    }

    uint8_t *text = NULL;
    uint8_t *pattern = NULL;

    build_random_instance(text_len,
                          pattern_len,
                          (uint32_t)alphabet_u64,
                          mutation_rate,
                          seed,
                          &text,
                          &pattern);

    uint64_t matches = naive_string_match_count(text,
                                                text_len,
                                                pattern,
                                                pattern_len,
                                                delay_ms);

    printf("%" PRIu64 "\n", matches);

    free(text);
    free(pattern);

    return 0;
}