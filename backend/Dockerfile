# ─────────────────────────────────────────────────────────────────
# Dockerfile — Backend SUP'ONE (Django + FAISS + MiniLM)
# Image cible : python:3.11-slim  (plus stable que 3.13 sur Railway)
# ─────────────────────────────────────────────────────────────────

# ── Étape 1 : builder ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Dépendances système pour FAISS, numpy, psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ── Étape 2 : image finale ──────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Runtime libs pour psycopg2 et FAISS
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copier les wheels compilés et installer
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --find-links /wheels -r /wheels/../requirements.txt 2>/dev/null || \
    pip install --no-cache-dir /wheels/*.whl

# Copier le code source
COPY . .

# Variables d'environnement par défaut (surchargées par Railway)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    PORT=8000

# Collecter les fichiers statiques (sans base de données requise)
RUN python backend/manage.py collectstatic --noinput

# Port exposé
EXPOSE 8000

# Démarrage — utilise $PORT injecté par Railwa
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info
