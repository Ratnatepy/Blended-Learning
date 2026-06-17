#!/usr/bin/env sh
set -eu

BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

python - <<PY
import socket
import time
import sys

host = "${BACKEND_HOST}"
port = int("${BACKEND_PORT}")
deadline = time.time() + int("${BACKEND_WAIT_TIMEOUT:-90}")

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"FastAPI backend is reachable at {host}:{port}")
            sys.exit(0)
    except OSError:
        print(f"Waiting for FastAPI backend at {host}:{port}...")
        time.sleep(2)

print(f"FastAPI backend was not reachable at {host}:{port} before timeout", file=sys.stderr)
sys.exit(1)
PY

exec "$@"
