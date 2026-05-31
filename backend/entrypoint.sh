#!/bin/bash
set -e

echo "=== SUP'ONE Backend démarrage ==="

# Migrations automatiques
echo ">>> Lancement des migrations..."
python manage.py migrate --noinput

echo ">>> Démarrage de Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info