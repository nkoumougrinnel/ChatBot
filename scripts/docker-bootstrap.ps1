# Initialise FAQ + index ML dans les conteneurs Docker (à lancer une fois).
$ErrorActionPreference = "Stop"

Write-Host "=== Import FAQ JSON + indexation ==="
docker compose exec api python manage.py import_faq_json --allow-download

Write-Host "=== Diagnostic Gen3 ==="
docker compose exec api python manage.py check_gen3

Write-Host "=== Santé API ==="
docker compose exec api curl -fsS http://127.0.0.1:8000/api/health/

Write-Host "Bootstrap terminé."
