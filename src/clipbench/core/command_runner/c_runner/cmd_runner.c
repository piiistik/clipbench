#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>

static HANDLE shell_stdin_w = NULL;
static HANDLE shell_stdout_r = NULL;
static HANDLE shell_stderr_r = NULL;
static PROCESS_INFORMATION shell_pi = {0};

int send_command_to_shell(const char *cmd) {
    if (!shell_stdin_w) return -1;
    DWORD written = 0;
    DWORD len = (DWORD)strlen(cmd);
    fprintf(stderr, "[debug] send_command_to_shell: writing %u bytes cmd=\"%s\"\n", (unsigned)len, cmd);
    fflush(stderr);
    if (!WriteFile(shell_stdin_w, cmd, len, &written, NULL) || written != len) {
        fprintf(stderr, "[debug] send_command_to_shell: WriteFile failed or short write (%u/%u)\n", (unsigned)written, (unsigned)len);
        fflush(stderr);
        return -1;
    }
    if (!WriteFile(shell_stdin_w, "\r\n", 2, &written, NULL) || written != 2) {
        fprintf(stderr, "[debug] send_command_to_shell: WriteFile CRLF failed\n");
        fflush(stderr);
        return -1;
    }
    fprintf(stderr, "[debug] send_command_to_shell: written and flushed\n");
    fflush(stderr);
    return 0;
}

int read_shell_output_line(char *buf, size_t buflen) {
    if (!shell_stdout_r) return -1;
    DWORD read = 0;
    size_t pos = 0;
    while (pos + 1 < buflen) {
        char ch;
        BOOL ok = ReadFile(shell_stdout_r, &ch, 1, &read, NULL);
        if (!ok || read == 0) {
            if (pos == 0) return -1;
            break;
        }
        buf[pos++] = ch;
        if (ch == '\n') break;
    }
    buf[pos] = '\0';
    return (int)pos;
}

int drain_one_pipe_named(HANDLE h) {
    if (!h) return 0;
    DWORD avail = 0;
    char tmp[8192];
    DWORD total = 0;
    for (;;) {
        if (!PeekNamedPipe(h, NULL, 0, NULL, &avail, NULL)) return -1;
        if (avail == 0) break;
        DWORD toread = avail > sizeof(tmp) ? (DWORD)sizeof(tmp) : avail;
        DWORD read = 0;
        if (!ReadFile(h, tmp, toread, &read, NULL)) return -1;
        if (read == 0) break;
        total += read;
    }
    return (int)total;
}

int drain_shell_output(void) {
    int a = drain_one_pipe_named(shell_stdout_r);
    int b = drain_one_pipe_named(shell_stderr_r);
    if (a < 0 || b < 0) return -1;
    fprintf(stderr, "[debug] drain_shell_output: drained stdout=%d stderr=%d bytes\n", a, b);
    fflush(stderr);
    return a + b;
}

int init_persistent_shell(void) {
    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    HANDLE stdin_r = NULL;
    HANDLE stdout_w = NULL;
    HANDLE stderr_w = NULL;
    if (!CreatePipe(&stdin_r, &shell_stdin_w, &sa, 0)) return -1;
    if (!CreatePipe(&shell_stdout_r, &stdout_w, &sa, 0)) {
        CloseHandle(stdin_r); CloseHandle(shell_stdin_w);
        return -1;
    }
    if (!CreatePipe(&shell_stderr_r, &stderr_w, &sa, 0)) {
        CloseHandle(stdin_r); CloseHandle(shell_stdin_w);
        CloseHandle(shell_stdout_r); CloseHandle(stdout_w);
        return -1;
    }
    SetHandleInformation(shell_stdin_w, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(shell_stdout_r, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(shell_stderr_r, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.hStdInput = stdin_r;
    si.hStdOutput = stdout_w;
    si.hStdError = stderr_w;
    si.dwFlags |= STARTF_USESTDHANDLES;

    char cmdline[] = "cmd.exe /Q"; // /Q for no echo
    BOOL ok = CreateProcessA(NULL, cmdline, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &shell_pi);
    CloseHandle(stdin_r);
    CloseHandle(stdout_w);
    CloseHandle(stderr_w);
    if (!ok) {
        if (shell_stdin_w) CloseHandle(shell_stdin_w);
        if (shell_stdout_r) CloseHandle(shell_stdout_r);
        if (shell_stderr_r) CloseHandle(shell_stderr_r);
        shell_stdin_w = NULL;
        shell_stdout_r = NULL;
        shell_stderr_r = NULL;
        return -1;
    }
    fprintf(stderr, "[debug] init_persistent_shell: started cmd.exe pid=%lu\n", (unsigned long)shell_pi.dwProcessId);
    fflush(stderr);

    return 0;
}

void close_persistent_shell(void) {
    if (shell_pi.hProcess) {
        TerminateProcess(shell_pi.hProcess, 1);
        WaitForSingleObject(shell_pi.hProcess, 1000);
        CloseHandle(shell_pi.hProcess);
        CloseHandle(shell_pi.hThread);
        shell_pi.hProcess = NULL;
        shell_pi.hThread = NULL;
    }
    if (shell_stdin_w) { CloseHandle(shell_stdin_w); shell_stdin_w = NULL; }
    if (shell_stdout_r) { CloseHandle(shell_stdout_r); shell_stdout_r = NULL; }
    if (shell_stderr_r) { CloseHandle(shell_stderr_r); shell_stderr_r = NULL; }
    fprintf(stderr, "[debug] close_persistent_shell: closed\n");
    fflush(stderr);
}

#else

#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <signal.h>

static FILE *shell_stdin_fp = NULL;
static FILE *shell_stdout_fp = NULL;
static FILE *shell_stderr_fp = NULL;
static pid_t shell_pid = 0;

int init_persistent_shell(void) {
    int inpipe[2];
    int outpipe[2];
    int errpipe[2];
    if (pipe(inpipe) != 0) return -1;
    if (pipe(outpipe) != 0) { close(inpipe[0]); close(inpipe[1]); return -1; }
    if (pipe(errpipe) != 0) { close(inpipe[0]); close(inpipe[1]); close(outpipe[0]); close(outpipe[1]); return -1; }

    pid_t pid = fork();
    if (pid < 0) {
        close(inpipe[0]); close(inpipe[1]); close(outpipe[0]); close(outpipe[1]); close(errpipe[0]); close(errpipe[1]);
        return -1;
    }
    if (pid == 0) {
        dup2(inpipe[0], STDIN_FILENO);
        dup2(outpipe[1], STDOUT_FILENO);
        dup2(errpipe[1], STDERR_FILENO);
        close(inpipe[0]); close(inpipe[1]); close(outpipe[0]); close(outpipe[1]); close(errpipe[0]); close(errpipe[1]);
        execlp("sh", "sh", "-s", (char *)NULL);
        _exit(127);
    } else {
        close(inpipe[0]);
        close(outpipe[1]);
        close(errpipe[1]);
        shell_pid = pid;
        shell_stdin_fp = fdopen(inpipe[1], "w");
        shell_stdout_fp = fdopen(outpipe[0], "r");
        shell_stderr_fp = fdopen(errpipe[0], "r");
        if (!shell_stdin_fp || !shell_stdout_fp || !shell_stderr_fp) {
            if (shell_stdin_fp) fclose(shell_stdin_fp);
            if (shell_stdout_fp) fclose(shell_stdout_fp);
            if (shell_stderr_fp) fclose(shell_stderr_fp);
            shell_stdin_fp = NULL;
            shell_stdout_fp = NULL;
            shell_stderr_fp = NULL;
            return -1;
        }
        setvbuf(shell_stdin_fp, NULL, _IONBF, 0);
        setvbuf(shell_stdout_fp, NULL, _IONBF, 0);
        setvbuf(shell_stderr_fp, NULL, _IONBF, 0);
        fprintf(stderr, "[debug] init_persistent_shell: started sh pid=%d\n", (int)shell_pid);
        fflush(stderr);
        return 0;
    }
}

int send_command_to_shell(const char *cmd) {
    if (!shell_stdin_fp) return -1;
    fprintf(stderr, "[debug] send_command_to_shell: cmd=\"%s\"\n", cmd);
    fflush(stderr);
    if (fputs(cmd, shell_stdin_fp) == EOF) {
        fprintf(stderr, "[debug] send_command_to_shell: fputs failed\n"); fflush(stderr);
        return -1;
    }
    if (fputc('\n', shell_stdin_fp) == EOF) {
        fprintf(stderr, "[debug] send_command_to_shell: fputc NL failed\n"); fflush(stderr);
        return -1;
    }
    fflush(shell_stdin_fp);
    fprintf(stderr, "[debug] send_command_to_shell: flushed\n"); fflush(stderr);
    return 0;
}

int read_shell_output_line(char *buf, size_t buflen) {
    if (!shell_stdout_fp) return -1;
    if (!fgets(buf, (int)buflen, shell_stdout_fp)) return -1;
    return (int)strlen(buf);
}

int drain_one_pipe_fd(FILE *f) {
    if (!f) return 0;
    int fd = fileno(f);
    if (fd < 0) return -1;
    int total = 0;
    char tmp[8192];
    for (;;) {
        int avail = 0;
        if (ioctl(fd, FIONREAD, &avail) < 0) return -1;
        if (avail <= 0) break;
        ssize_t r = read(fd, tmp, (avail > (int)sizeof(tmp)) ? sizeof(tmp) : avail);
        if (r < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        if (r == 0) break;
        total += (int)r;
    }
    return total;
}

int drain_shell_output(void) {
    int a = drain_one_pipe_fd(shell_stdout_fp);
    int b = drain_one_pipe_fd(shell_stderr_fp);
    if (a < 0 || b < 0) return -1;
    fprintf(stderr, "[debug] drain_shell_output: drained stdout=%d stderr=%d bytes\n", a, b);
    fflush(stderr);
    return a + b;
}

void close_persistent_shell(void) {
    if (shell_stdin_fp) { fclose(shell_stdin_fp); shell_stdin_fp = NULL; }
    if (shell_stdout_fp) { fclose(shell_stdout_fp); shell_stdout_fp = NULL; }
    if (shell_stderr_fp) { fclose(shell_stderr_fp); shell_stderr_fp = NULL; }
    if (shell_pid > 0) {
        kill(shell_pid, SIGTERM);
        waitpid(shell_pid, NULL, 0);
        shell_pid = 0;
    }
    fprintf(stderr, "[debug] close_persistent_shell: closed\n");
    fflush(stderr);
}

#endif

#ifdef _WIN32
double get_current_time(void) {
    static LARGE_INTEGER freq;
    static int init = 0;
    LARGE_INTEGER now;
    if (!init) { QueryPerformanceFrequency(&freq); init = 1; }
    QueryPerformanceCounter(&now);
    return (double)now.QuadPart / (double)freq.QuadPart;
}
#else
#include <time.h>
double get_current_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}
#endif

#define MAX_CMD_LEN 4096

static int parse_end_marker(const char *line) {
    const char *p = strstr(line, "__MEASURE_END__:");
    if (!p) return -1;
    p += strlen("__MEASURE_END__:");
    while (*p == ' ' || *p == '\t') p++;
    int code = atoi(p);
    return code;
}

float measure_cmd_time(const char *cmd) {
    char wrapped[MAX_CMD_LEN * 2];
#ifdef _WIN32
    snprintf(wrapped, sizeof(wrapped),
    "%s > NUL 2>&1 & (if errorlevel 1 (echo __MEASURE_END__:1) else (echo __MEASURE_END__:0))",
    cmd);
#else
    snprintf(wrapped, sizeof(wrapped), "%s > /dev/null 2>&1; printf \"__MEASURE_END__:%d\\n\" $?", cmd);
#endif

    fprintf(stderr, "[debug] measure_cmd_time: wrapped=\"%s\"\n", wrapped);
    fflush(stderr);

    char buf[8192];

    double start = get_current_time();
    if (send_command_to_shell(wrapped) != 0) {
        fprintf(stderr, "[debug] measure_cmd_time: send_command_to_shell failed\n"); fflush(stderr);
        return -1.0f;
    }

    int exit_code = -1;
    
    while (1) {
        int r = read_shell_output_line(buf, sizeof(buf));
        if (r <= 0) {
            fprintf(stderr, "[debug] measure_cmd_time: read_shell_output_line returned %d\n", r);
            fflush(stderr);
            break;
        }
        fprintf(stderr, "[debug] measure_cmd_time: read line: %s", buf);
        fflush(stderr);
        int code = parse_end_marker(buf);
        if (code != -1) {
            exit_code = code;
            fprintf(stderr, "[debug] measure_cmd_time: parsed end marker code=%d\n", code);
            fflush(stderr);
            break;
        }
    }

    double end = get_current_time();

    if (drain_shell_output() < 0) {
        fprintf(stderr, "[debug] measure_cmd_time: drain_shell_output failed\n"); fflush(stderr);
        return -1.0f;
    }
    
    fprintf(stderr, "[debug] measure_cmd_time: start=%.6f end=%.6f elapsed=%.6f exit_code=%d\n",
            start, end, end - start, exit_code);
    fflush(stderr);

    if (exit_code != 0) return -1.0f;
    return (float)(end - start);
}

int main(void) {
    if (init_persistent_shell() != 0) {
        fprintf(stderr, "[debug] main: init_persistent_shell failed\n"); fflush(stderr);
        return 1;
    }

    boolean is_first = TRUE;

    char line[MAX_CMD_LEN];
    while (fgets(line, sizeof(line), stdin)) {
        fprintf(stderr, "----------------------------------------------------------------------\n"); fflush(stderr);
        size_t len = strlen(line);
        if (len > 0 && line[len - 1] == '\n') line[len - 1] = '\0';
        if (strlen(line) == 0) continue;
        fprintf(stderr, "[debug] main: got command: \"%s\"\n", line); fflush(stderr);
        float result = measure_cmd_time(line);
        if (is_first) {
            float result = measure_cmd_time(line);
            is_first = FALSE;
        }
        printf("%f\n", result);
        fflush(stdout);
    }

    close_persistent_shell();
    return 0;
}
