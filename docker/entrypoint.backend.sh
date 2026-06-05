#!/bin/sh
set -e

cd /app/backend

if [ -n "${DATABASE_URL}" ]; then
  echo "[entrypoint] Attente PostgreSQL…"
  python - <<'PY'
import os
import sys
import time

url = os.environ.get("DATABASE_URL", "")
if not url:
    sys.exit(0)

try:
    import psycopg2
except ImportError:
    sys.exit(0)

for attempt in range(60):
    try:
        psycopg2.connect(url).close()
        print("[entrypoint] PostgreSQL prêt.")
        sys.exit(0)
    except Exception as exc:
        print(f"[entrypoint] Postgres ({attempt + 1}/60): {exc}")
        time.sleep(2)

print("[entrypoint] Timeout PostgreSQL.")
sys.exit(1)
PY
fi

exec "$@"
