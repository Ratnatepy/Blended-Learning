#!/usr/bin/env sh
set -eu

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

python - <<PY
import socket
import time
import sys

host = "${POSTGRES_HOST}"
port = int("${POSTGRES_PORT}")
deadline = time.time() + 90

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"PostgreSQL is reachable at {host}:{port}")
            sys.exit(0)
    except OSError:
        print(f"Waiting for PostgreSQL at {host}:{port}...")
        time.sleep(2)

print(f"PostgreSQL was not reachable at {host}:{port} before timeout", file=sys.stderr)
sys.exit(1)
PY

exec "$@"
