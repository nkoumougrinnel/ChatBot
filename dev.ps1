# start_local.ps1 - Démarrage natif sans Docker
param(
    [switch]$OllamaOnly,
    [switch]$DjangoOnly,
    [switch]$BuildIndex
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHATBOT SUP'PTIC - Mode Natif" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Activer l'environnement virtuel
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "✅ Environnement virtuel activé" -ForegroundColor Green
}

# Vérifier Ollama
function Test-Ollama {
    try {
        $response = curl -s http://localhost:11434/api/tags
        return $true
    } catch {
        return $false
    }
}

# Démarrer Ollama si nécessaire
if (-not (Test-Ollama)) {
    Write-Host "🚀 Démarrage d'Ollama..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

if ($OllamaOnly) {
    Write-Host "✅ Ollama tourne sur http://localhost:11434" -ForegroundColor Green
    Write-Host "Appuyez sur Ctrl+C pour arrêter" -ForegroundColor Yellow
    # Maintenir Ollama actif
    while ($true) { Start-Sleep -Seconds 10 }
    exit
}

# Construire l'index FAISS
if ($BuildIndex) {
    Write-Host "🔨 Construction de l'index FAISS..." -ForegroundColor Yellow
    python -c "
from backend.chatbot.scripts.build_index import build_faiss_index
import glob
import os
json_files = glob.glob('data/*.json')
if json_files:
    build_faiss_index(json_files)
    print('✅ Index FAISS construit')
else:
    print('⚠️ Aucun fichier JSON trouvé')
"
}

# Appliquer les migrations Django
Write-Host "🔄 Migrations Django..." -ForegroundColor Yellow
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
Write-Host "👤 Création du superutilisateur..." -ForegroundColor Yellow
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superutilisateur créé: admin/admin123')
"

if (-not $DjangoOnly) {
    Write-Host ""
    Write-Host "✅ Environnement prêt !" -ForegroundColor Green
    Write-Host "   📦 Django: http://localhost:8000"
    Write-Host "   🤖 Ollama: http://localhost:11434"
    Write-Host "   🔧 Admin: http://localhost:8000/admin"
    Write-Host ""
}

# Démarrer Django
if (-not $OllamaOnly) {
    Write-Host "🚀 Démarrage du serveur Django..." -ForegroundColor Green
    python manage.py runserver
}
