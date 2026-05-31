#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# deploy_frontend.sh — Déploiement Netlify du frontend SUP'ONE
# App Expo React Native Web → Netlify
# Usage : bash deploy_frontend.sh [--setup | --deploy | --preview]
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[OK]${RESET}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo -e "${RED}[ERR]${RESET}  $*"; exit 1; }

REACT_DIR="frontend/react-app"

# ════════════════════════════════════════════════════════════════
# Vérifications
# ════════════════════════════════════════════════════════════════
check_deps() {
    info "Vérification des dépendances..."
    command -v node    >/dev/null 2>&1 || error "Node.js non installé (requis >= 18)"
    command -v npm     >/dev/null 2>&1 || error "npm non installé"
    command -v git     >/dev/null 2>&1 || error "git non installé"

    # Netlify CLI (optionnel pour le deploy manuel)
    if ! command -v netlify >/dev/null 2>&1; then
        warn "Netlify CLI non installé. Installation : npm install -g netlify-cli"
        warn "Vous pouvez déployer via le dashboard Netlify sans le CLI."
    fi
    success "Dépendances OK"
}

check_react_dir() {
    [ -d "$REACT_DIR" ] || error "Répertoire '$REACT_DIR' introuvable. Lancez ce script depuis la racine du projet."
    [ -f "$REACT_DIR/package.json" ] || error "package.json introuvable dans $REACT_DIR"
    success "Répertoire React trouvé"
}

# ════════════════════════════════════════════════════════════════
# --setup : installation des dépendances + config env
# ════════════════════════════════════════════════════════════════
setup() {
    echo -e "\n${BOLD}═══ SETUP FRONTEND SUP'ONE ═══${RESET}\n"
    check_deps
    check_react_dir

    # Installation des dépendances npm
    info "Installation des dépendances npm..."
    cd "$REACT_DIR"
    npm install
    cd - > /dev/null
    success "npm install terminé"

    # Création du fichier .env.local
    echo ""
    read -r -p "URL Railway du backend (ex: https://mon-projet.up.railway.app) : " BACKEND_URL

    cat > "$REACT_DIR/.env.local" << EOF
# Variables d'environnement locales — NE PAS COMMITER
# Expo: toute variable publique doit commencer par EXPO_PUBLIC_

EXPO_PUBLIC_BACKEND_URL=$BACKEND_URL
EOF
    success "Fichier $REACT_DIR/.env.local créé"

    # Vérifier que .env.local est dans .gitignore
    if ! grep -q ".env.local" "$REACT_DIR/.gitignore" 2>/dev/null; then
        echo ".env.local" >> "$REACT_DIR/.gitignore"
        warn ".env.local ajouté à .gitignore"
    fi

    # Mise à jour de api.ts si l'URL hardcodée est encore présente
    if grep -q "10.227.132.171" "$REACT_DIR/Service/api.ts" 2>/dev/null; then
        warn "api.ts contient encore une IP locale hardcodée."
        warn "Remplacez le contenu de Service/api.ts par le fichier api.ts fourni."
    fi

    success "Setup terminé. Testez avec : bash deploy_frontend.sh --preview"
}

# ════════════════════════════════════════════════════════════════
# --build : build local Expo web
# ════════════════════════════════════════════════════════════════
build() {
    echo -e "\n${BOLD}═══ BUILD EXPO WEB ═══${RESET}\n"
    check_react_dir

    info "Build Expo pour le web..."
    cd "$REACT_DIR"

    # S'assurer que expo-cli est disponible
    if ! npx expo --version >/dev/null 2>&1; then
        error "Expo CLI non disponible. Vérifiez npm install."
    fi

    # Export web
    npx expo export --platform web
    cd - > /dev/null

    if [ -d "$REACT_DIR/dist" ]; then
        success "Build terminé → $REACT_DIR/dist/"
        echo "  $(find "$REACT_DIR/dist" -type f | wc -l) fichiers générés"
    else
        error "Le dossier dist/ n'a pas été créé. Vérifiez les erreurs ci-dessus."
    fi
}

# ════════════════════════════════════════════════════════════════
# --preview : déploiement preview Netlify (sans production)
# ════════════════════════════════════════════════════════════════
preview() {
    echo -e "\n${BOLD}═══ PREVIEW NETLIFY ═══${RESET}\n"
    command -v netlify >/dev/null 2>&1 || error "Netlify CLI requis : npm install -g netlify-cli"

    build

    info "Déploiement preview Netlify..."
    cd "$REACT_DIR"
    netlify deploy --dir=dist
    cd - > /dev/null
}

# ════════════════════════════════════════════════════════════════
# --deploy : déploiement en production Netlify
# ════════════════════════════════════════════════════════════════
deploy() {
    echo -e "\n${BOLD}═══ DÉPLOIEMENT PRODUCTION NETLIFY ═══${RESET}\n"

    # Option A — via Netlify CLI
    if command -v netlify >/dev/null 2>&1; then
        build

        echo ""
        warn "Vous êtes sur le point de déployer en PRODUCTION."
        read -r -p "Confirmer ? [o/N] " rep
        [[ "$rep" =~ ^[oO]$ ]] || { info "Abandon."; exit 0; }

        info "Déploiement production Netlify..."
        cd "$REACT_DIR"
        netlify deploy --dir=dist --prod
        cd - > /dev/null
        success "Déployé en production !"

    else
        # Option B — via Git (Netlify lit le netlify.toml)
        warn "Netlify CLI non disponible — déploiement via Git."
        info "Netlify détecte automatiquement les pushs sur la branche connectée."

        if ! git diff --quiet || ! git diff --cached --quiet; then
            read -r -p "Commit et push des modifications ? [o/N] " rep
            if [[ "$rep" =~ ^[oO]$ ]]; then
                git add -A
                git commit -m "chore: frontend deploy $(date +%Y-%m-%d)"
                git push
                success "Push effectué — Netlify va déclencher le build automatiquement."
            fi
        else
            git push
            success "Push effectué"
        fi

        echo ""
        info "Suivez le build sur : https://app.netlify.com"
    fi
}

# ════════════════════════════════════════════════════════════════
# --set-backend-url : mettre à jour l'URL backend dans Netlify
# ════════════════════════════════════════════════════════════════
set_backend_url() {
    echo -e "\n${BOLD}═══ MISE À JOUR URL BACKEND ═══${RESET}\n"
    command -v netlify >/dev/null 2>&1 || error "Netlify CLI requis"

    read -r -p "Nouvelle URL Railway (ex: https://mon-projet.up.railway.app) : " NEW_URL
    netlify env:set EXPO_PUBLIC_BACKEND_URL "$NEW_URL"
    success "Variable EXPO_PUBLIC_BACKEND_URL mise à jour dans Netlify"
    warn "Un redéploiement est nécessaire pour appliquer le changement."
    read -r -p "Redéployer maintenant ? [o/N] " rep
    if [[ "$rep" =~ ^[oO]$ ]]; then
        netlify deploy --dir="$REACT_DIR/dist" --prod
    fi
}

# ════════════════════════════════════════════════════════════════
# Point d'entrée
# ════════════════════════════════════════════════════════════════
case "${1:-}" in
    --setup)           setup ;;
    --build)           build ;;
    --preview)         preview ;;
    --deploy)          deploy ;;
    --set-backend-url) set_backend_url ;;
    *)
        echo -e "${BOLD}Usage :${RESET}"
        echo "  bash deploy_frontend.sh --setup           # Installer deps + configurer .env.local"
        echo "  bash deploy_frontend.sh --build           # Builder Expo web localement"
        echo "  bash deploy_frontend.sh --preview         # Déploiement preview Netlify"
        echo "  bash deploy_frontend.sh --deploy          # Déploiement production Netlify"
        echo "  bash deploy_frontend.sh --set-backend-url # Mettre à jour l'URL backend"
        ;;
esac
