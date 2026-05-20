import os
import re
import sys
from pathlib import Path

exclude_list = {
    'clipbench', 'input_file_editor', 'result_viewer', 'os', 'sys', 'pathlib', 'typing', 'unittest',
    're', 'json', 'abc', 'collections', 'datetime', 'enum', 'functools', 'inspect', 'itertools',
    'logging', 'math', 'operator', 'shutil', 'subprocess', 'tempfile', 'threading', 'time',
    'traceback', 'warnings', 'argparse', 'glob', 'importlib', 'io', 'pickle', 'random', 'signal',
    'struct', 'types', 'uuid', 'copy', 'array', 'base64', 'binascii', 'bisect', 'calendar',
    'contextlib', 'csv', 'decimal', 'difflib', 'errno', 'fnmatch', 'fractions', 'gc', 'getopt',
    'getpass', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'ipaddress', 'linecache',
    'locale', 'mailbox', 'mimetypes', 'multiprocessing', 'netrc', 'nntplib', 'numbers', 'pdb',
    'platform', 'plistlib', 'poplib', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile',
    'pyclbr', 'pydoc', 'queue', 'quopri', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets',
    'select', 'selectors', 'shelve', 'shlex', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket',
    'socketserver', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'sunau',
    'symbol', 'symtable', 'sysconfig', 'tabnanny', 'tarfile', 'telnetlib', 'textwrap', 'timeit',
    'token', 'tokenize', 'tracemalloc', 'tty', 'turtle', 'unicodedata', 'urllib', 'uu', 'venv',
    'wave', 'weakref', 'webbrowser', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
    'zipimport', 'zlib', 'pytest', 'sklearn', 'numpy', 'matplotlib', 'pexpect', 'jinja2', 'black', 'build', 'packaging'
}

results = {}
root = Path(".")
for path in root.rglob("*.py"):
    if "build" in path.parts or "src/clipbench.egg-info" in str(path) or "__pycache__" in path.parts:
        continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = re.search(r"^(?:import|from)\s+(\w+)", line)
            if match:
                mod = match.group(1)
                if mod not in exclude_list:
                    if mod not in results:
                        results[mod] = set()
                    results[mod].add(str(path))

for mod, paths in sorted(results.items()):
    print(f"{mod}: {', '.join(sorted(paths))}")
