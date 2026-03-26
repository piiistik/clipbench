#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>

#define MAX_CMD_LEN 4096
#define CHUNK_SIZE 4096
#define CAPTURE_MAX 65536

typedef enum {
    CMD_STATUS_OK = 0,
    CMD_STATUS_TIMEOUT = 1,
    CMD_STATUS_ERROR = 2,
} CommandStatus;

typedef struct {
    HANDLE stdin_write;
    HANDLE stdout_read;
    HANDLE stderr_read;
    PROCESS_INFORMATION pi;
} PersistentShell;

typedef struct {
    CommandStatus status;
    double elapsed_seconds;
    int exit_code;
    char reason[128];
    char stderr_text[CAPTURE_MAX];
    char stdout_tail[CAPTURE_MAX];
} CommandResult;

static void init_result(CommandResult *result) {
    result->status = CMD_STATUS_ERROR;
    result->elapsed_seconds = 0.0;
    result->exit_code = -1;
    result->reason[0] = '\0';
    result->stderr_text[0] = '\0';
    result->stdout_tail[0] = '\0';
}

static double now_seconds(void) {
    static LARGE_INTEGER freq;
    static int has_freq = 0;
    LARGE_INTEGER counter;

    if (!has_freq) {
        QueryPerformanceFrequency(&freq);
        has_freq = 1;
    }

    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart / (double)freq.QuadPart;
}

static void append_capped(char *dst, size_t dst_size, const char *src, size_t src_len) {
    size_t dst_len;
    size_t keep;

    if (dst_size == 0 || src_len == 0) {
        return;
    }

    dst_len = strlen(dst);
    if (src_len >= dst_size) {
        src += (src_len - (dst_size - 1));
        src_len = dst_size - 1;
        dst[0] = '\0';
        dst_len = 0;
    }

    if (dst_len + src_len >= dst_size) {
        keep = dst_size - 1 - src_len;
        memmove(dst, dst + (dst_len - keep), keep);
        dst[keep] = '\0';
        dst_len = keep;
    }

    memcpy(dst + dst_len, src, src_len);
    dst[dst_len + src_len] = '\0';
}

static int find_marker_exit_code(const char *text, const char *marker, int *exit_code) {
    const char *start;
    const char *colon;
    char *endptr;
    long code;

    start = strstr(text, marker);
    if (!start) {
        return 0;
    }

    colon = start + strlen(marker);
    if (*colon != ':') {
        return -1;
    }
    colon += 1;

    code = strtol(colon, &endptr, 10);
    if (endptr == colon) {
        return -1;
    }

    *exit_code = (int)code;
    return 1;
}

static int read_pipe_available(HANDLE pipe, char *buffer, DWORD buffer_size, DWORD *bytes_read) {
    DWORD available = 0;
    DWORD to_read;

    *bytes_read = 0;

    if (!PeekNamedPipe(pipe, NULL, 0, NULL, &available, NULL)) {
        return -1;
    }

    if (available == 0) {
        return 0;
    }

    to_read = available;
    if (to_read > buffer_size) {
        to_read = buffer_size;
    }

    if (!ReadFile(pipe, buffer, to_read, bytes_read, NULL)) {
        return -1;
    }

    return 1;
}

static int write_shell_line(HANDLE stdin_write, const char *line) {
    DWORD written = 0;
    size_t len = strlen(line);

    if (!WriteFile(stdin_write, line, (DWORD)len, &written, NULL) || written != (DWORD)len) {
        return -1;
    }

    if (!WriteFile(stdin_write, "\r\n", 2, &written, NULL) || written != 2) {
        return -1;
    }

    return 0;
}

static int start_persistent_shell(PersistentShell *shell) {
    SECURITY_ATTRIBUTES sa;
    STARTUPINFOA si;
    HANDLE stdin_read = NULL;
    HANDLE stdout_write = NULL;
    HANDLE stderr_write = NULL;
    char cmdline[] = "cmd.exe /Q /D";

    ZeroMemory(shell, sizeof(PersistentShell));
    ZeroMemory(&sa, sizeof(sa));
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    if (!CreatePipe(&stdin_read, &shell->stdin_write, &sa, 0)) {
        return -1;
    }
    if (!CreatePipe(&shell->stdout_read, &stdout_write, &sa, 0)) {
        CloseHandle(stdin_read);
        CloseHandle(shell->stdin_write);
        return -1;
    }
    if (!CreatePipe(&shell->stderr_read, &stderr_write, &sa, 0)) {
        CloseHandle(stdin_read);
        CloseHandle(shell->stdin_write);
        CloseHandle(shell->stdout_read);
        CloseHandle(stdout_write);
        return -1;
    }

    SetHandleInformation(shell->stdin_write, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(shell->stdout_read, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(shell->stderr_read, HANDLE_FLAG_INHERIT, 0);

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = stdin_read;
    si.hStdOutput = stdout_write;
    si.hStdError = stderr_write;

    if (!CreateProcessA(
            NULL,
            cmdline,
            NULL,
            NULL,
            TRUE,
            CREATE_NO_WINDOW,
            NULL,
            NULL,
            &si,
            &shell->pi)) {
        CloseHandle(stdin_read);
        CloseHandle(stdout_write);
        CloseHandle(stderr_write);
        CloseHandle(shell->stdin_write);
        CloseHandle(shell->stdout_read);
        CloseHandle(shell->stderr_read);
        ZeroMemory(shell, sizeof(PersistentShell));
        return -1;
    }

    CloseHandle(stdin_read);
    CloseHandle(stdout_write);
    CloseHandle(stderr_write);
    return 0;
}

static void stop_persistent_shell(PersistentShell *shell) {
    if (shell->pi.hProcess) {
        TerminateProcess(shell->pi.hProcess, 1);
        WaitForSingleObject(shell->pi.hProcess, 1000);
        CloseHandle(shell->pi.hProcess);
        shell->pi.hProcess = NULL;
    }

    if (shell->pi.hThread) {
        CloseHandle(shell->pi.hThread);
        shell->pi.hThread = NULL;
    }

    if (shell->stdin_write) {
        CloseHandle(shell->stdin_write);
        shell->stdin_write = NULL;
    }

    if (shell->stdout_read) {
        CloseHandle(shell->stdout_read);
        shell->stdout_read = NULL;
    }

    if (shell->stderr_read) {
        CloseHandle(shell->stderr_read);
        shell->stderr_read = NULL;
    }
}

static void log_diagnostics(const char *command, const CommandResult *result) {
    if (result->status == CMD_STATUS_TIMEOUT) {
        fprintf(stderr, "[cmd_runner] TIMEOUT command=\"%s\" elapsed=%.6f stderr=\"%s\"\n",
                command,
                result->elapsed_seconds,
                result->stderr_text);
    } else if (result->status == CMD_STATUS_ERROR) {
        fprintf(stderr,
                "[cmd_runner] ERROR reason=%s command=\"%s\" exit_code=%d stderr=\"%s\" stdout_tail=\"%s\"\n",
                result->reason,
                command,
                result->exit_code,
                result->stderr_text,
                result->stdout_tail);
    }
    fflush(stderr);
}

static CommandResult execute_command(
    PersistentShell *shell,
    const char *command,
    double timeout_seconds,
    unsigned long long command_id
) {
    CommandResult result;
    char wrapped[(MAX_CMD_LEN * 2) + 128];
    char marker[64];
    char chunk[CHUNK_SIZE];
    double start;
    DWORD bytes_read;

    init_result(&result);

    if (command[0] == '\0') {
        snprintf(result.reason, sizeof(result.reason), "empty_command");
        return result;
    }

    snprintf(marker, sizeof(marker), "__CLIPBENCH_DONE_%llu__", command_id);
    snprintf(
        wrapped,
        sizeof(wrapped),
        "%s & echo %s:%%ERRORLEVEL%%",
        command,
        marker
    );

    start = now_seconds();

    if (write_shell_line(shell->stdin_write, wrapped) != 0) {
        snprintf(result.reason, sizeof(result.reason), "shell_write_failed");
        return result;
    }

    while (1) {
        int marker_state;

        if (read_pipe_available(shell->stderr_read, chunk, CHUNK_SIZE, &bytes_read) < 0) {
            snprintf(result.reason, sizeof(result.reason), "stderr_read_failed");
            return result;
        }
        if (bytes_read > 0) {
            append_capped(result.stderr_text, sizeof(result.stderr_text), chunk, bytes_read);
        }

        if (read_pipe_available(shell->stdout_read, chunk, CHUNK_SIZE, &bytes_read) < 0) {
            snprintf(result.reason, sizeof(result.reason), "stdout_read_failed");
            return result;
        }
        if (bytes_read > 0) {
            append_capped(result.stdout_tail, sizeof(result.stdout_tail), chunk, bytes_read);
            marker_state = find_marker_exit_code(result.stdout_tail, marker, &result.exit_code);
            if (marker_state < 0) {
                snprintf(result.reason, sizeof(result.reason), "marker_parse_failed");
                return result;
            }
            if (marker_state > 0) {
                break;
            }
        }

        result.elapsed_seconds = now_seconds() - start;
        if (timeout_seconds > 0.0 && result.elapsed_seconds >= timeout_seconds) {
            result.status = CMD_STATUS_TIMEOUT;
            return result;
        }

        Sleep(2);
    }

    result.elapsed_seconds = now_seconds() - start;

    if (result.exit_code == 0) {
        result.status = CMD_STATUS_OK;
        return result;
    }

    result.status = CMD_STATUS_ERROR;
    snprintf(result.reason, sizeof(result.reason), "exit_code=%d", result.exit_code);
    return result;
}

int main(int argc, char **argv) {
    PersistentShell shell;
    double timeout_seconds = 0.0;
    char line[MAX_CMD_LEN];
    unsigned long long command_id = 1;
    int did_warmup = 0;

    if (argc > 1) {
        timeout_seconds = atof(argv[1]);
        if (timeout_seconds < 0.0) {
            fprintf(stderr, "[cmd_runner] invalid timeout: %s\n", argv[1]);
            return 2;
        }
    }

    if (start_persistent_shell(&shell) != 0) {
        fprintf(stderr, "[cmd_runner] failed to start persistent cmd.exe shell\n");
        return 1;
    }

    while (fgets(line, sizeof(line), stdin)) {
        size_t len;
        CommandResult result;

        len = strlen(line);
        while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r')) {
            line[len - 1] = '\0';
            len -= 1;
        }

        if (!did_warmup) {
            CommandResult warmup_result = execute_command(&shell, line, timeout_seconds, command_id++);
            did_warmup = 1;

            if (warmup_result.status == CMD_STATUS_TIMEOUT) {
                log_diagnostics(line, &warmup_result);

                stop_persistent_shell(&shell);
                if (start_persistent_shell(&shell) != 0) {
                    fprintf(stderr, "[cmd_runner] failed to recover shell after warm-up timeout\n");
                    return 1;
                }
            } else if (warmup_result.status == CMD_STATUS_ERROR) {
                log_diagnostics(line, &warmup_result);

                if (strcmp(warmup_result.reason, "shell_write_failed") == 0 ||
                    strcmp(warmup_result.reason, "stdout_read_failed") == 0 ||
                    strcmp(warmup_result.reason, "stderr_read_failed") == 0) {
                    stop_persistent_shell(&shell);
                    if (start_persistent_shell(&shell) != 0) {
                        fprintf(stderr, "[cmd_runner] failed to recover shell after warm-up runner I/O error\n");
                        return 1;
                    }
                }
            }
        }

        result = execute_command(&shell, line, timeout_seconds, command_id++);

        if (result.status == CMD_STATUS_OK) {
            printf("OK %.6f\n", result.elapsed_seconds);
            fflush(stdout);
            continue;
        }

        if (result.status == CMD_STATUS_TIMEOUT) {
            printf("TIMEOUT\n");
            fflush(stdout);
            log_diagnostics(line, &result);

            stop_persistent_shell(&shell);
            if (start_persistent_shell(&shell) != 0) {
                fprintf(stderr, "[cmd_runner] failed to recover shell after timeout\n");
                return 1;
            }
            continue;
        }

        printf("ERROR %s\n", result.reason[0] ? result.reason : "command_failed");
        fflush(stdout);
        log_diagnostics(line, &result);

        if (strcmp(result.reason, "shell_write_failed") == 0 ||
            strcmp(result.reason, "stdout_read_failed") == 0 ||
            strcmp(result.reason, "stderr_read_failed") == 0) {
            stop_persistent_shell(&shell);
            if (start_persistent_shell(&shell) != 0) {
                fprintf(stderr, "[cmd_runner] failed to recover shell after runner I/O error\n");
                return 1;
            }
        }
    }

    stop_persistent_shell(&shell);
    return 0;
}

#else

int main(void) {
    fprintf(stderr, "cmd_runner is currently implemented for Windows only.\n");
    return 1;
}

#endif
