# Guide de Démarrage — SUP'ONE AI

Démarrage local du chatbot en mode développement.

---

## Prérequis

| Outil | Version min. | Vérification |
|-------|-------------|--------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | 2.x+ | `git --version` |

> **Pas besoin de PostgreSQL ni Docker** pour le développement local — SQLite est utilisé par défaut.

---

## 1. Cloner et configurer

```bash
git clone <url-du-depot> ChatBot
cd ChatBot
```

### Configurer l'environnement

```bash
copy .env.example .env
```

Éditer `.env` et renseigner au minimum :

```ini
SECRET_KEY=<generer-avec-la-cmd-ci-dessous>
DEBUG=True
GEMINI_API_KEY=<votre-cle-api-gemini>
```

Générer une clé secrète :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> Obtenir une clé Gemini : https://aistudio.google.com/app/apikey

---

## 2. Backend (Django)

### Créer l'environnement virtuel

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
```

### Installer les dépendances

```bash
pip install -r ..\requirements.txt
```

### Initialiser la base de données

```bash
python manage.py migrate
```

### Charger les données FAQ + entraîner le moteur RAG

```bash
python manage.py setup_gen3 --allow-download
```

> Cette commande :
> - Importe les FAQ depuis les fichiers JSON dans `data/`
> - Entraîne le vectorizer TF-IDF
> - Génère les embeddings MiniLM
> - Construit l'index FAISS
> - Durée : ~2-5 min la première fois

### Lancer le serveur

```bash
python manage.py runserver 0.0.0.0:8001 --noreload
```

Le backend est accessible sur **http://127.0.0.1:8001**

#### Vérification

```bash
curl http://127.0.0.1:8001/api/health/
```

Réponse attendue :
```json
{
  "status": "healthy",
  "faiss_loaded": true,
  "tfidf_loaded": true,
  "faq_count": 11686
}
```

---

## 3. Frontend (React)

### Depuis un second terminal

```bash
cd frontend\app
npm install
npm run dev
```

Le frontend est accessible sur **http://localhost:5174**

> Le proxy Vite redirige automatiquement les appels `/api/*` vers le backend sur le port 8001.

---

## 4. Tester le chatbot

Ouvrir **http://localhost:5174** dans un navigateur.

### Exemples de questions

| Question | Niveau attendu |
|----------|---------------|
| `Bonjour` | CONV (regex) |
| `C'est combien les frais d'inscription ?` | DIRECT ou TF-IDF |
| `Quelles sont les filières proposées ?` | TF-IDF ou LLM |
| `Comment faire pour candidater ?` | LLM (Gemini) |

---

## 5. Structure des ports

| Service | Port | URL |
|---------|------|-----|
| Backend Django | 8001 | http://127.0.0.1:8001 |
| Frontend Vite | 5174 | http://localhost:5174 |
| SQLite | — | `backend/db.sqlite3` |

---

## 6. Arrêter les serveurs

- **Backend** : `Ctrl+C` dans le terminal du backend
- **Frontend** : `Ctrl+C` dans le terminal du frontend

---

## 7. Démarrage alternatif (Docker)

```bash
cp .env.example .env
# Éditer .env (SECRET_KEY, GEMINI_API_KEY, POSTGRES_PASSWORD)

docker compose up -d --build
```

| Service | Port |
|---------|------|
| Frontend (Nginx) | 80 |
| Backend (Gunicorn) | 8001 (interne) |
| PostgreSQL | 5432 (interne) |

---

## 8. Dépannage

### "Lock files" vectorizer bloqués

Si le serveur reste bloqué sur "Attente de l'initialisation du vectorizer" :

```bash
del %TEMP%\faq_vectorizer.lock
del %TEMP%\faq_vectorizer_done.flag
```

### Port 8001 déjà utilisé

```bash
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### Erreur "ModuleNotFoundError" au démarrage

Réinstaller les dépendances :
```bash
pip install -r ..\requirements.txt
```

### Base de données corrompue

Réinitialiser :
```bash
del backend\db.sqlite3
python manage.py migrate
python manage.py setup_gen3 --allow-download
```

### Erreur FAISS "Could not load library with AVX2"

C'est un avertissement normal — FAISS fonctionne en mode fallback. Pas d'action requise.

---

## 9. Endpoints API principaux

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/api/health/` | État du serveur |
| GET | `/api/faq/` | Liste des FAQ |
| POST | `/api/chatbot/ask/` | Poser une question (JSON ou SSE) |
| GET | `/api/v2/chatbot/status/` | Statut du pipeline Gen3 |
| GET | `/api/v2/chatbot/reload-index/` | Recharger l'index FAISS |

### Exemple de requête

```bash
curl -X POST http://127.0.0.1:8001/api/chatbot/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "C\'est combien les frais ?", "stream": false}'
```
