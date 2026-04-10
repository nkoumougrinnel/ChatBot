# dev.ps1 - Version corrigée avec nouvelle syntaxe
param(
    [switch]$Build,
    [switch]$Down,
    [switch]$Shell,
    [switch]$Logs
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CHATBOT SUP'PTIC - Docker Dev" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($Down) {
    Write-Host "🛑 Arrêt des conteneurs..." -ForegroundColor Yellow
    docker compose down
    exit
}

if ($Build) {
    Write-Host "🔨 Construction des images..." -ForegroundColor Yellow
    docker compose build --no-cache
}

if ($Shell) {
    Write-Host "🐚 Accès au shell du conteneur django..." -ForegroundColor Yellow
    docker exec -it chatbot_django bash
    exit
}

if ($Logs) {
    Write-Host "📋 Affichage des logs..." -ForegroundColor Yellow
    docker compose logs -f
    exit
}

# Démarrer les services
Write-Host "🚀 Démarrage des conteneurs..." -ForegroundColor Green
docker compose up -d

Write-Host ""
Write-Host "✅ Services démarrés :" -ForegroundColor Green
Write-Host "   📦 Django: http://localhost:8000"
Write-Host "   🤖 Ollama: http://localhost:11434"
Write-Host "   🔧 Admin: http://localhost:8000/admin"
Write-Host ""

# Afficher les logs
docker compose logs -f
