// build (Linux/macOS): gcc -Wall -Wextra -O2 sleep_ms.c -o sleep_ms
// build (Windows, MinGW): gcc -Wall -Wextra -O2 sleep_ms.c -o sleep.exe
// build (Windows, MSVC): cl /W4 /O2 sleep_ms.c user32.lib

#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
static void sleep_ms(int ms) {
    Sleep(ms);
}
#else
#include <unistd.h>
static void sleep_ms(int ms) {
    usleep((useconds_t)ms * 1000);
}
#endif

int main(int argc, char **argv) {
    int ms;

    if (argc == 2) {
        int a = atoi(argv[1]);
        if (a < 0) return 1;
        ms = a;
    } else if (argc == 3) {
        int a = atoi(argv[1]);
        int b = atoi(argv[2]);
        ms = a + 2 * b;
        if (ms < 0) return 1;
    } else if (argc == 4) {
        int a = atoi(argv[1]);
        int b = atoi(argv[2]);
        int c = atoi(argv[3]);
        ms = a + 2 * b - c;
        if (ms < 0) ms = 0;
    } else {
        return 1;
    }

    sleep_ms(ms);
    return 0;
}
