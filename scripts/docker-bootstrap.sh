#!/bin/sh
# Initialise FAQ + index ML dans les conteneurs Docker (à lancer une fois).
set -e

echo "=== Import FAQ JSON + indexation ==="
docker compose exec api python manage.py import_faq_json --allow-download

echo "=== Diagnostic Gen3 ==="
docker compose exec api python manage.py check_gen3

echo "=== Santé API ==="
docker compose exec api curl -fsS http://127.0.0.1:8000/api/health/

echo "Bootstrap terminé."
