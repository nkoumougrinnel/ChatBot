#!/bin/bash
# scripts/entrypoint.sh

set -e

echo "=========================================="
echo "🚀 Démarrage du conteneur ChatBot SUP'PTIC"
echo "=========================================="

# Attendre que Ollama soit prêt
echo "⏳ Attente du service Ollama..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 2
done
echo "✅ Ollama est prêt"

# Télécharger le modèle Phi-3 si non présent
echo "📥 Vérification du modèle phi3:mini..."
if ! curl -s http://localhost:11434/api/tags | grep -q "phi3:mini"; then
    echo "   Téléchargement du modèle (peut prendre plusieurs minutes)..."
    ollama pull phi3:mini
    echo "✅ Modèle téléchargé"
else
    echo "✅ Modèle déjà présent"
fi

# Appliquer les migrations Django
echo "🔄 Application des migrations..."
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur automatiquement (optionnel)
echo "👤 Création du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superutilisateur créé: admin/admin123')
else:
    print('✅ Superutilisateur existe déjà')
"

# Construire l'index FAISS initial
echo "🔨 Construction de l'index FAISS..."
python -c "
from backend.chatbot.scripts.build_index import build_faiss_index
import glob
import os

json_files = glob.glob('data/*.json')
if json_files:
    build_faiss_index(json_files)
    print('✅ Index FAISS construit')
else:
    print('⚠️ Aucun fichier JSON trouvé, index non construit')
"

# Démarrer le serveur Django
echo "=========================================="
echo "✨ Environnement prêt !"
echo "   Django: http://localhost:8000"
echo "   Admin: http://localhost:8000/admin"
echo "   Ollama API: http://localhost:11434"
echo "=========================================="

exec python manage.py runserver 0.0.0.0:8000
