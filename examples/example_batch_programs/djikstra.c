/*
 * Dijkstra Shortest Path
 * ----------------------
 *
 * This program computes the shortest path distance in a randomly generated
 * directed weighted graph using Dijkstra’s algorithm.
 *
 * Dijkstra’s algorithm works by repeatedly selecting the not-yet-finalized
 * vertex with the smallest tentative distance, then relaxing its outgoing
 * edges.
 *
 * Why this program is useful:
 * ---------------------------
 * The runtime depends strongly on the size of the graph:
 *
 *   - the number of vertices has a large effect,
 *   - the number of edges has a large effect.
 *
 * Other inputs have much weaker effect:
 *
 *   - the source vertex,
 *   - the target vertex,
 *   - the random seed used to generate the graph.
 *
 * This makes it a good benchmark example where two inputs dominate
 * execution time while three inputs have only minor influence.
 *
 * Usage example:
 *     ./dijkstra --vertices 1000 --edges 5000 --source 0 --target 999 --seed 123
 *
 * This will build a random graph with 1000 vertices and 5000 edges and
 * compute the shortest path from vertex 0 to vertex 999.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <getopt.h>
#include <limits.h>
#include <time.h>
#include <errno.h>

typedef struct {
    uint32_t to;
    uint32_t weight;
} Edge;

typedef struct {
    uint32_t *data;
    uint64_t size;
    uint64_t cap;
} MinHeap;

static uint64_t round_nonneg_to_u64(double v) {
    if (v < 0.0) v = -v;
    return (uint64_t)(v + 0.5);
}

static void sleep_ms_float(double ms) {
    if (ms <= 0.0) return;
    struct timespec req;
    req.tv_sec = (time_t)(ms / 1000.0);
    req.tv_nsec = (long)((ms - (req.tv_sec * 1000.0)) * 1000000.0);
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

static uint32_t rand_range_u32(uint64_t *state, uint32_t limit) {
    if (limit == 0) {
        return 0;
    }
    return (uint32_t)(xorshift64(state) % limit);
}

static void *xmalloc(size_t n) {
    void *p = malloc(n);
    if (p == NULL && n != 0) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    return p;
}

static void *xcalloc(size_t count, size_t size) {
    void *p = calloc(count, size);
    if (p == NULL && count != 0 && size != 0) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    return p;
}

static void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n);
    if (q == NULL && n != 0) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    return q;
}

static void heap_init(MinHeap *h, uint64_t cap) {
    h->size = 0;
    h->cap = (cap == 0) ? 1 : cap;
    h->data = (uint32_t *)xmalloc((size_t)h->cap * sizeof(uint32_t));
}

static void heap_free(MinHeap *h) {
    free(h->data);
    h->data = NULL;
    h->size = 0;
    h->cap = 0;
}

static void heap_swap(uint32_t *a, uint32_t *b) {
    uint32_t t = *a;
    *a = *b;
    *b = t;
}

static void heap_push(MinHeap *h, uint32_t v, const uint64_t *dist) {
    if (h->size == h->cap) {
        h->cap *= 2;
        h->data = (uint32_t *)xrealloc(h->data, (size_t)h->cap * sizeof(uint32_t));
    }

    uint64_t i = h->size++;
    h->data[i] = v;

    while (i > 0) {
        uint64_t parent = (i - 1) / 2;
        if (dist[h->data[parent]] <= dist[h->data[i]]) {
            break;
        }
        heap_swap(&h->data[parent], &h->data[i]);
        i = parent;
    }
}

static uint32_t heap_pop(MinHeap *h, const uint64_t *dist) {
    uint32_t out = h->data[0];
    h->data[0] = h->data[--h->size];

    uint64_t i = 0;
    while (1) {
        uint64_t left = 2 * i + 1;
        uint64_t right = 2 * i + 2;
        uint64_t smallest = i;

        if (left < h->size && dist[h->data[left]] < dist[h->data[smallest]]) {
            smallest = left;
        }
        if (right < h->size && dist[h->data[right]] < dist[h->data[smallest]]) {
            smallest = right;
        }
        if (smallest == i) {
            break;
        }

        heap_swap(&h->data[i], &h->data[smallest]);
        i = smallest;
    }

    return out;
}

static int heap_empty(const MinHeap *h) {
    return h->size == 0;
}

static uint64_t dijkstra(uint32_t vertices,
                         const Edge *edges,
                         const uint32_t *head,
                         uint32_t source,
                         uint32_t target,
                         double delay_ms) {
    uint64_t *dist = (uint64_t *)xmalloc((size_t)vertices * sizeof(uint64_t));
    uint8_t *done = (uint8_t *)xcalloc(vertices, sizeof(uint8_t));
    MinHeap heap;

    for (uint32_t i = 0; i < vertices; ++i) {
        dist[i] = UINT64_MAX / 4;
    }
    dist[source] = 0;

    heap_init(&heap, vertices > 0 ? vertices : 1);
    heap_push(&heap, source, dist);

    while (!heap_empty(&heap)) {
        uint32_t u = heap_pop(&heap, dist);
        if (done[u]) {
            continue;
        }

        done[u] = 1;

        uint32_t start = head[u];
        uint32_t end = head[u + 1];

        for (uint32_t i = start; i < end; ++i) {
            uint32_t v = edges[i].to;
            uint64_t w = edges[i].weight;

            if (done[v]) {
                continue;
            }

            if (delay_ms > 0.0) {
                sleep_ms_float(delay_ms);
            }

            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                heap_push(&heap, v, dist);
            }
        }
    }

    uint64_t result = dist[target];

    heap_free(&heap);
    free(dist);
    free(done);

    return result;
}

static void build_random_graph(uint32_t vertices,
                               uint32_t edges_count,
                               uint64_t seed,
                               Edge **edges_out,
                               uint32_t **head_out) {
    if (vertices == 0) {
        vertices = 1;
    }

    uint64_t max_edges = (uint64_t)vertices * (uint64_t)(vertices - 1);
    if (edges_count > max_edges) {
        edges_count = (uint32_t)max_edges;
    }

    Edge *edges = (Edge *)xmalloc((size_t)edges_count * sizeof(Edge));
    uint32_t *outdeg = (uint32_t *)xcalloc(vertices, sizeof(uint32_t));
    uint64_t rng = seed ? seed : 0xD1B54A32D192ED03ULL;

    for (uint32_t i = 0; i < edges_count; ++i) {
        uint32_t u = rand_range_u32(&rng, vertices);
        uint32_t v = rand_range_u32(&rng, vertices);

        if (u == v) {
            v = (v + 1U) % vertices;
        }

        uint32_t w = 1U + rand_range_u32(&rng, 1000U);

        edges[i].to = v;
        edges[i].weight = w;
        outdeg[u]++;
    }

    uint32_t *head = (uint32_t *)xmalloc((size_t)(vertices + 1U) * sizeof(uint32_t));
    head[0] = 0;
    for (uint32_t i = 0; i < vertices; ++i) {
        head[i + 1] = head[i] + outdeg[i];
    }

    Edge *adj = (Edge *)xmalloc((size_t)edges_count * sizeof(Edge));
    uint32_t *cursor = (uint32_t *)xmalloc((size_t)vertices * sizeof(uint32_t));
    for (uint32_t i = 0; i < vertices; ++i) {
        cursor[i] = head[i];
    }

    rng = seed ? seed : 0xD1B54A32D192ED03ULL;
    for (uint32_t i = 0; i < edges_count; ++i) {
        uint32_t u = rand_range_u32(&rng, vertices);
        uint32_t v = rand_range_u32(&rng, vertices);

        if (u == v) {
            v = (v + 1U) % vertices;
        }

        uint32_t w = 1U + rand_range_u32(&rng, 1000U);
        uint32_t pos = cursor[u]++;
        adj[pos].to = v;
        adj[pos].weight = w;
    }

    free(edges);
    free(outdeg);
    free(cursor);

    *edges_out = adj;
    *head_out = head;
}

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s --vertices <value> --edges <value> --source <value> --target <value> --seed <value> [--delay <ms>]\n"
        "\n"
        "  --vertices  number of graph vertices\n"
        "  --edges     number of graph edges\n"
        "  --source    source vertex\n"
        "  --target    target vertex\n"
        "  --seed      random seed for graph generation\n"
        "  --delay     sleep this many milliseconds (float allowed) after each finalized vertex\n",
        prog
    );
}

int main(int argc, char **argv) {
    double vertices_in = 0.0;
    double edges_in = 0.0;
    double source_in = 0.0;
    double target_in = 0.0;
    double seed_in = 0.0;
    double delay_ms = 0.0;
    int have_vertices = 0, have_edges = 0, have_source = 0, have_target = 0, have_seed = 0;

    static struct option long_opts[] = {
        {"vertices", required_argument, 0, 'v'},
        {"edges", required_argument, 0, 'e'},
        {"source", required_argument, 0, 's'},
        {"target", required_argument, 0, 't'},
        {"seed", required_argument, 0, 'r'},
        {"delay", required_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };

    int opt, opt_idx = 0;

    while ((opt = getopt_long(argc, argv, "", long_opts, &opt_idx)) != -1) {
        switch (opt) {
            case 'v':
                vertices_in = strtod(optarg, NULL);
                have_vertices = 1;
                break;
            case 'e':
                edges_in = strtod(optarg, NULL);
                have_edges = 1;
                break;
            case 's':
                source_in = strtod(optarg, NULL);
                have_source = 1;
                break;
            case 't':
                target_in = strtod(optarg, NULL);
                have_target = 1;
                break;
            case 'r':
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

    if (!have_vertices || !have_edges || !have_source || !have_target || !have_seed) {
        usage(argv[0]);
        return 1;
    }

    uint64_t vertices_u64 = round_nonneg_to_u64(vertices_in);
    uint64_t edges_u64 = round_nonneg_to_u64(edges_in);
    uint64_t source_u64 = round_nonneg_to_u64(source_in);
    uint64_t target_u64 = round_nonneg_to_u64(target_in);
    uint64_t seed_u64 = round_nonneg_to_u64(seed_in);

    if (vertices_u64 == 0) {
        vertices_u64 = 1;
    }

    if (source_u64 >= vertices_u64) {
        source_u64 %= vertices_u64;
    }
    if (target_u64 >= vertices_u64) {
        target_u64 %= vertices_u64;
    }

    Edge *edges = NULL;
    uint32_t *head = NULL;

    build_random_graph((uint32_t)vertices_u64, (uint32_t)edges_u64, seed_u64, &edges, &head);

    uint64_t dist = dijkstra((uint32_t)vertices_u64, edges, head,
                              (uint32_t)source_u64, (uint32_t)target_u64,
                              delay_ms);

    if (dist >= UINT64_MAX / 8) {
        printf("inf\n");
    } else {
        printf("%" PRIu64 "\n", dist);
    }

    free(edges);
    free(head);

    return 0;
}