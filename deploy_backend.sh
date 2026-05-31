#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# deploy_backend.sh — Déploiement Railway du backend SUP'ONE
# Branche cible : backend
# Usage : bash deploy_backend.sh [--setup | --deploy | --logs]
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Couleurs ────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[OK]${RESET}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo -e "${RED}[ERR]${RESET}  $*"; exit 1; }

BRANCH="backend"

# ════════════════════════════════════════════════════════════════
# Vérifications préalables
# ════════════════════════════════════════════════════════════════
check_deps() {
    info "Vérification des dépendances..."
    command -v git     >/dev/null 2>&1 || error "git non installé"
    command -v railway >/dev/null 2>&1 || error "Railway CLI non installé. Exécutez : npm install -g @railway/cli"
    success "Dépendances OK"
}

check_branch() {
    local current
    current=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current" != "$BRANCH" ]; then
        warn "Vous êtes sur la branche '$current', pas sur '$BRANCH'."
        read -r -p "Basculer sur la branche '$BRANCH' ? [o/N] " rep
        if [[ "$rep" =~ ^[oO]$ ]]; then
            git checkout "$BRANCH"
            success "Basculé sur '$BRANCH'"
        else
            error "Abandon. Placez-vous sur la branche '$BRANCH' avant de déployer."
        fi
    else
        success "Branche '$BRANCH' active"
    fi
}

# ════════════════════════════════════════════════════════════════
# --setup : première configuration Railway
# ════════════════════════════════════════════════════════════════
setup() {
    echo -e "\n${BOLD}═══ SETUP RAILWAY — Backend SUP'ONE ═══${RESET}\n"
    check_deps
    check_branch

    # Connexion
    info "Connexion Railway..."
    railway login

    # Initialisation du projet
    info "Initialisation du projet Railway..."
    railway init

    # Ajout PostgreSQL
    echo -e "\n${YELLOW}→ Ajoutez un service PostgreSQL dans le dashboard Railway${RESET}"
    echo "  Dashboard → New Service → Database → PostgreSQL"
    echo "  Railway injectera DATABASE_URL automatiquement."
    read -r -p "Appuyez sur Entrée une fois PostgreSQL ajouté..."

    # Variables d'environnement
    info "Configuration des variables d'environnement..."

    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || \
                 python -c "import secrets; print(secrets.token_urlsafe(50))")

    railway variables set \
        SECRET_KEY="$SECRET_KEY" \
        DEBUG="False" \
        DJANGO_SETTINGS_MODULE="config.settings" \
        TRANSFORMERS_OFFLINE="1" \
        HF_DATASETS_OFFLINE="1" \
        SCORE_DIRECT="0.55" \
        SCORE_LLM="0.30"

    success "Variables de base définies"

    # Gemini API Key
    echo ""
    read -r -p "Entrez votre GEMINI_API_KEY (ou Entrée pour ignorer) : " GEMINI_KEY
    if [ -n "$GEMINI_KEY" ]; then
        railway variables set GEMINI_API_KEY="$GEMINI_KEY"
        railway variables set GEMINI_MODEL="gemini-1.5-flash"
        success "Clé Gemini configurée"
    fi

    # ALLOWED_HOSTS sera mis à jour après le premier déploiement
    railway variables set ALLOWED_HOSTS="localhost,127.0.0.1"

    success "Setup terminé. Lancez maintenant : bash deploy_backend.sh --deploy"
}

# ════════════════════════════════════════════════════════════════
# --deploy : déploiement
# ════════════════════════════════════════════════════════════════
deploy() {
    echo -e "\n${BOLD}═══ DÉPLOIEMENT RAILWAY — Branche: $BRANCH ═══${RESET}\n"
    check_deps
    check_branch

    # Vérifier les fichiers requis
    info "Vérification des fichiers requis..."
    [ -f "backend/Dockerfile" ]          || error "backend/Dockerfile introuvable"
    [ -f "railway.toml" ]                || error "railway.toml introuvable"
    [ -f "backend/rag_data/index.bin" ]  || error "backend/rag_data/index.bin introuvable — commitez les fichiers rag_data/"
    [ -f "backend/rag_data/metadata.json" ] || error "backend/rag_data/metadata.json introuvable"
    success "Fichiers requis présents"

    # Vérifier que rag_data/ est suivi par Git
    if git check-ignore -q backend/rag_data/ 2>/dev/null; then
        warn "backend/rag_data/ est dans .gitignore — Railway ne l'aura pas !"
        warn "Supprimez la ligne rag_data/ de backend/.gitignore et recommittez."
        exit 1
    fi

    # Commit des modifications locales si nécessaire
    if ! git diff --quiet || ! git diff --cached --quiet; then
        warn "Modifications non commitées détectées."
        read -r -p "Commit automatique ? [o/N] " rep
        if [[ "$rep" =~ ^[oO]$ ]]; then
            git add -A
            git commit -m "chore: prepare deployment $(date +%Y-%m-%d)"
            success "Commit effectué"
        fi
    fi

    # Push sur la branche backend
    info "Push sur origin/$BRANCH..."
    git push origin "$BRANCH"
    success "Push effectué"

    # Déploiement Railway
    info "Démarrage du déploiement Railway..."
    railway up --detach

    echo ""
    success "Déploiement lancé ! Suivez les logs avec :"
    echo -e "  ${BOLD}bash deploy_backend.sh --logs${RESET}"
    echo -e "  ${BOLD}railway open${RESET}  ← ouvrir le dashboard"

    # Récupérer et afficher l'URL
    echo ""
    info "Récupération de l'URL publique..."
    sleep 5
    railway domain 2>/dev/null || warn "URL non encore disponible — vérifiez le dashboard Railway."
}

# ════════════════════════════════════════════════════════════════
# --update-hosts : mettre à jour ALLOWED_HOSTS après déploiement
# ════════════════════════════════════════════════════════════════
update_hosts() {
    echo -e "\n${BOLD}═══ MISE À JOUR ALLOWED_HOSTS ═══${RESET}\n"
    read -r -p "Entrez l'URL Railway (ex: mon-projet.up.railway.app) : " RAILWAY_URL
    read -r -p "Entrez l'URL Netlify (ex: supone.netlify.app) : " NETLIFY_URL

    railway variables set \
        ALLOWED_HOSTS="localhost,127.0.0.1,$RAILWAY_URL,$NETLIFY_URL" \
        CORS_ALLOWED_ORIGINS_EXTRA="https://$NETLIFY_URL"

    success "ALLOWED_HOSTS mis à jour"
    info "Redéploiement nécessaire pour appliquer les changements :"
    echo "  railway up --detach"
}

# ════════════════════════════════════════════════════════════════
# --logs : suivre les logs en temps réel
# ════════════════════════════════════════════════════════════════
show_logs() {
    info "Logs Railway en temps réel (Ctrl+C pour quitter)..."
    railway logs --tail
}

# ════════════════════════════════════════════════════════════════
# --check : vérifier le déploiement
# ════════════════════════════════════════════════════════════════
check_deployment() {
    echo -e "\n${BOLD}═══ VÉRIFICATION DU DÉPLOIEMENT ═══${RESET}\n"
    read -r -p "URL Railway (ex: https://mon-projet.up.railway.app) : " BASE_URL

    info "Test health check..."
    if curl -sf "$BASE_URL/api/chatbot/status/" | python3 -m json.tool 2>/dev/null; then
        success "Pipeline UP"
    else
        error "Health check échoué — vérifiez les logs : bash deploy_backend.sh --logs"
    fi

    info "Test pipeline DIRECT..."
    curl -sf -X POST "$BASE_URL/api/chatbot/ask/" \
        -H "Content-Type: application/json" \
        -d '{"question": "Quels sont les frais de scolarité ?", "stream": false}' \
        | python3 -m json.tool 2>/dev/null && success "Pipeline DIRECT OK" || warn "Pipeline DIRECT KO"
}

# ════════════════════════════════════════════════════════════════
# Point d'entrée
# ════════════════════════════════════════════════════════════════
case "${1:-}" in
    --setup)        setup ;;
    --deploy)       deploy ;;
    --update-hosts) update_hosts ;;
    --logs)         show_logs ;;
    --check)        check_deployment ;;
    *)
        echo -e "${BOLD}Usage :${RESET}"
        echo "  bash deploy_backend.sh --setup          # Première configuration Railway"
        echo "  bash deploy_backend.sh --deploy         # Déployer sur Railway (branche backend)"
        echo "  bash deploy_backend.sh --update-hosts   # Mettre à jour ALLOWED_HOSTS"
        echo "  bash deploy_backend.sh --logs           # Suivre les logs"
        echo "  bash deploy_backend.sh --check          # Vérifier le déploiement"
        ;;
esac
