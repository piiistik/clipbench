import sys
import time


def sleep_linear(a: int, b: int):
    """Sleep for a + 10*b"""
    sleep_time_ms = a + 10 * b
    sleep_time_seconds = sleep_time_ms / 10000.0
    time.sleep(sleep_time_seconds)


def main():
    if len(sys.argv) != 3:
        print("Usage: test_sleep_linear.py <a> <b>")
        sys.exit(1)

    a = int(sys.argv[1])
    b = int(sys.argv[2])

    sleep_linear(a, b)


if __name__ == "__main__":
    main()
