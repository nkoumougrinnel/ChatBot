# Dockerfile
# Image de base python 3.12
FROM python:3.12-slim-bullseye
# Eviter les messages interactifs
ENV DEBIAN FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITTEBYCODE=1
# Variables d'environnement pour Ollama
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_ORIGINS=*
ENV OLLLAMA_MODELS=/root/.ollama/OLLLAMA_MODELS
# Definir e repertoire de travail
WORKDIR /app
# Installer les dependences systeme
RUN apt-get update && apt-get install -y \
 # Pour compiler les packages python
 gcc \
 g++ \
 make \
 # Pour FAISS
 libopenblas-dev \
 liblapack-dev \
 # Pour Ollama (binaires)
 curl \
 wget \
 git \
 # Utilitaires
 vim \
 htop \
 && rm -rf /var/lib/apt/lists/*
# installer Ollama
RUN curl -fsSLhttps://ollama.com/install.sh | sh
# Creer un utilisateur non-root pour la securite
RUN useradd -m -u 1000 -s /bin/bash appuser
# Copier les dependences Python
COPY requirements.txt .
# Installer les dependences Python
RUN pip install --no-cache-dir -r requirements.txt
# Copier tout le code source
COPY --chown=appuser:appuser . .
# Donner les permissions a l'utilisateur
RUN chown -R appuser:appuser /app
RUN chown -R appuser:appuser /root/.ollama
# Changer pour l'utilisateur non-root
USER appuser
# Exposer les ports
# 8000: Django
# 11434: Ollama API
EXPOSE 8000 11434
# Script d'entree
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]