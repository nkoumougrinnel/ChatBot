# Configuration CORS dans Django

## Problème

Quand le frontend (HTML) est servi depuis un serveur HTTP différent du backend Django, le navigateur bloque les requêtes cross-origin pour des raisons de sécurité (CORS = Cross-Origin Resource Sharing).

**Symptôme :** Erreur dans la console du navigateur :

```
Failed to fetch
TypeError: Failed to fetch
```

## Solution Implémentée

### 1. Installation de `django-cors-headers`

Package Django qui gère automatiquement les en-têtes CORS.

```bash
pip install django-cors-headers
```

### 2. Modifications dans `backend/config/settings.py`

#### Ajout à INSTALLED_APPS

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',  # ← Nouveau
    'faq',
    'chatbot',
    'users',
]
```

#### Ajout du Middleware CORS

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← Doit être après SecurityMiddleware et avant SessionMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Important :** L'ordre des middlewares est critique. `CorsMiddleware` doit être proche du haut pour traiter les requêtes préflightées.

#### Configuration CORS

```python
# CORS Configuration - Allow frontend to access API
CORS_ALLOWED_ORIGINS = [
    # Localhost
    'http://localhost:8000',      # Django dev server
    'http://127.0.0.1:8000',      # Localhost alias
    'http://localhost:3000',      # React dev server
    'http://127.0.0.1:3000',      # Localhost alias
    'http://localhost:5500',      # Live Server ou Python HTTP server
    'http://127.0.0.1:5500',      # Localhost alias
    'http://localhost',           # Generic localhost
    'http://127.0.0.1',           # Generic localhost

    # Network IPs (pour accès via IP interne)
    'http://192.168.1.0:3000',    # Frontend sur IP réseau, port 3000
    'http://192.168.1.0:5500',    # Frontend sur IP réseau, port 5500
    'http://10.0.0.0:3000',       # Autres plages de réseau
    'http://10.0.0.0:5500',

    # ngrok & DevTunnels (pour partage public)
    'https://sharron-prehazard-gully.ngrok-free.dev',  # ngrok frontend
    'https://jlhld2dz-8000.use.devtunnels.ms',         # DevTunnels backend
]

# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = True

# Allowed HTTP methods
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']

# Allowed request headers
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
```

**Note :** Pour les IPs réseau dynamiques, vous pouvez utiliser une pattern plus flexible :

```python
import re

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http:\/\/192\.168\.\d+\.\d+:\d+$",  # Toute IP 192.168.x.x
    r"^http:\/\/10\.\d+\.\d+\.\d+:\d+$",   # Toute IP 10.x.x.x
    r"^https:\/\/.*\.ngrok[-a-z]*\.dev$",  # Tous les domaines ngrok
    r"^https:\/\/.*\.devtunnels\.ms$",     # Tous les domaines devtunnels
]
```

### 3. Côté Frontend (Détection Automatique)

Le frontend dans `advanced_chat/main.js` détecte automatiquement l'environnement et configure l'URL API :

```javascript
// Detect API endpoint based on current location
const API_BASE = (() => {
  const host = window.location.hostname;

  // If on ngrok frontend, call backend via devtunnels HTTPS
  if (host.includes("sharron-prehazard-gully.ngrok-free.dev")) {
    return "https://jlhld2dz-8000.use.devtunnels.ms";
  }

  // Network IP detected, use same IP for API
  if (host.includes("192.168") || host.includes("10.")) {
    return `http://${host}:8000`;
  }

  // Local development
  return "http://localhost:8000";
})();
const API_URL = `${API_BASE}/api/chatbot/ask/`;
```

**Cas d'usage :**

- **Localhost** : `http://localhost:8000/api/chatbot/ask/`
- **IP réseau** (ex: `192.168.10.82`) : `http://192.168.10.82:8000/api/chatbot/ask/`
- **ngrok frontend** : Appelle le backend via DevTunnels HTTPS

Cela permet au frontend d'être servi depuis n'importe quel contexte (localhost, réseau local, ou ngrok) tout en communiquant avec le backend approprié.

## Comment ça fonctionne

1. **Requête préflight (OPTIONS)** :
   - Le navigateur envoie une requête OPTIONS à l'API
   - Django (via `CorsMiddleware`) répond avec les en-têtes CORS appropriés

2. **Requête réelle (POST/GET)** :
   - Si les en-têtes CORS sont valides, le navigateur autorise la requête
   - La requête est envoyée normalement

## Configuration pour la Production

Pour la production, soyez plus restrictif :

```python
CORS_ALLOWED_ORIGINS = [
    'https://www.example.com',  # Votre domaine de production
]

# Optionnel : pour autoriser tous les domaines (NON RECOMMANDÉ)
# CORS_ALLOW_ALL_ORIGINS = True
```

## Dépannage

### "Failed to fetch" persiste

- Vérifiez que Django tourne sur `http://localhost:8000`
- Assurez-vous que `corsheaders` est installé : `pip list | grep django-cors`
- Vérifiez que `CorsMiddleware` est dans `MIDDLEWARE` (dans l'ordre correct)
- Redémarrez le serveur Django après les modifications

### Erreur CORS dans la console

- Ouvrez F12 → onglet Console
- Vérifiez le message d'erreur exact
- Comparez l'origine de la requête avec `CORS_ALLOWED_ORIGINS`

## Références

- [Django CORS Headers Documentation](https://github.com/adamchainz/django-cors-headers)
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Django REST Framework: CORS](https://www.django-rest-framework.org/topics/rest-frameworks/)
