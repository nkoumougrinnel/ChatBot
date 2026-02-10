# 📖 Guide Complet: Advanced Chat Chatbot

## Vue d'ensemble

Ce guide explique comment configurer et utiliser le chatbot **SUP'PTIC Assistant** développé avec:

- **Backend**: Django REST Framework (DRF) + spaCy + TF-IDF
- **Frontend**: HTML/CSS/JavaScript vanilla + Bootstrap Icons
- **Base de données**: SQLite (FAQ, Categories, Vectors)

---

## 📁 Structure du Projet

```
ChatBot/
├── backend/
│   ├── manage.py
│   ├── start_server.py        # Script pour démarrer Django
│   ├── config/
│   │   ├── settings.py        # Configuration Django
│   │   └── urls.py
│   ├── faq/                   # App: modèles FAQ
│   ├── chatbot/               # App: API chatbot
│   └── users/                 # App: utilisateurs
├── frontend/
│   └── advanced_chat/
│       ├── index.html         # Page HTML principale
│       ├── main.js            # Logique chatbot
│       ├── styles.css         # Design responsive
│       ├── start_server.py    # Script serveur frontend
│       ├── icone.png          # Logo
│       └── README.md
├── scripts/
│   └── load_test_data.py      # Script d'import CSV
├── data/
│   ├── faq.csv                # Données FAQ
│   └── categories.csv         # Catégories
└── requirements.txt           # Dépendances Python
```

---

## 🚀 Démarrage Rapide (Local)

### Prérequis

- Python 3.8+
- pip ou conda
- Git (optionnel)

### Étape 1: Installer les dépendances

```bash
cd c:\Users\DELL\Desktop\ChatBot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Vérifier l'installation:**

```bash
python -c "import django, rest_framework, spacy; print('✓ All dependencies OK')"
```

---

## 📊 Importer les données

### Option A: Charger les données de test CSV

**Script:** `scripts/load_test_data.py`

```bash
cd c:\Users\DELL\Desktop\ChatBot
python scripts/load_test_data.py
```

**Qu'il fait:**

- 🗑️ Vide les tables FAQ et Category
- 📥 Importe les données de `data/faq.csv` et `data/categories.csv`
- 🔧 **NE PAS** vectoriser pendant l'import (flag `SKIP_FAQ_VECTORIZER`)

**Résultat attendu:**

```
✓ Cleaned FAQ and Category tables
✓ Imported X FAQs
✓ Imported X Categories
```

### Option B: Charger les données manuellement (Django shell)

```bash
cd c:\Users\DELL\Desktop\ChatBot\backend
python manage.py shell
```

Puis dans le shell Django:

```python
from faq.models import Category, FAQ

# Créer une catégorie
cat = Category.objects.create(name="Admissions", slug="admissions")

# Créer une FAQ
faq = FAQ.objects.create(
    question="Quand ouvre les admissions?",
    answer="Les admissions ouvrent le 1er janvier.",
    category=cat
)

print(f"✓ Created FAQ: {faq.id}")
exit()
```

---

## 🔧 Initialiser les Vecteurs TF-IDF

**Après** importer les données, vous devez générer les vecteurs TF-IDF pour chaque FAQ.

**Management Command:** `python manage.py init_vectors`

```bash
cd c:\Users\DELL\Desktop\ChatBot\backend
python manage.py init_vectors
```

**Qu'il fait:**

- 📊 Construit un vectoriseur TF-IDF sur tous les FAQs
- 💾 Calcule un vecteur pour chaque question FAQ
- 🗄️ Stocke les vecteurs dans la table `FAQVector` (JSONField + norm)

**Résultat attendu:**

```
✓ Initialized TF-IDF vectorizer
✓ Vectorized X FAQs
✓ Vectors saved to database
```

---

## 🌐 Démarrer les Serveurs

### Terminal 1: Backend Django (Port 8000)

```bash
cd c:\Users\DELL\Desktop\ChatBot\backend
python start_server.py
```

Ou manuellement:

```bash
cd c:\Users\DELL\Desktop\ChatBot\backend
python manage.py runserver 0.0.0.0:8000
```

**Attendu:**

```
Starting development server at http://0.0.0.0:8000/
Press Ctrl+C to stop.
```

**Vérifier:**

- Backend: `http://localhost:8000/api/chatbot/ask/` (POST request)
- Admin: `http://localhost:8000/admin/`

---

### Terminal 2: Frontend Simple HTTP Server (Port 9090)

```bash
cd c:\Users\DELL\Desktop\ChatBot\frontend\advanced_chat
python start_server.py
```

**Attendu:**

```
✓ Server running and listening on 0.0.0.0:9090
  - Access locally via http://localhost:9090
  - Access on this machine's LAN IP (if configured): http://<your-ip>:9090
✓ Press Ctrl+C to stop
```

**Vérifier:**

- Frontend: `http://localhost:9090`

---

## 🧪 Tester le Chatbot

### 1. Via Interface Web

Ouvrir dans votre navigateur:

```
http://localhost:9090
```

**Tester:**

1. Saisir une question (ex: "Quand ouvre les admissions?")
2. Cliquer "Envoyer" ou appuyer Entrée
3. Vérifier que le chatbot répond avec les FAQs correspondantes
4. Vérifier la Console DevTools (F12) pour les logs:
   ```
   ✅ SUP'PTIC Assistant initialisé
   🔗 API: http://localhost:8000/api/chatbot/ask/
   ```

### 2. Via cURL (Terminal)

Tester l'API backend directement:

```bash
curl -X POST "http://localhost:8000/api/chatbot/ask/" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"Quand ouvre les admissions?\"}"
```

**Réponse attendue:**

```json
{
  "question": "Quand ouvre les admissions?",
  "results": [
    {
      "id": 1,
      "question": "...",
      "answer": "...",
      "similarity": 0.95
    }
  ]
}
```

### 3. Via Postman/REST Client

- **Method:** POST
- **URL:** `http://localhost:8000/api/chatbot/ask/`
- **Body (JSON):**
  ```json
  {
    "question": "Quand ouvre les admissions?",
    "topk": 3
  }
  ```

---

## 📡 Adresses des Serveurs (Local)

| Component        | Address    | Port | URL                                    |
| ---------------- | ---------- | ---- | -------------------------------------- |
| **Frontend**     | localhost  | 9090 | http://localhost:9090                  |
| **Backend API**  | localhost  | 8000 | http://localhost:8000/api/chatbot/ask/ |
| **Django Admin** | localhost  | 8000 | http://localhost:8000/admin/           |
| **SQLite DB**    | local file | -    | `backend/db.sqlite3`                   |

---

## 🌍 Configuration pour NGrok (✅ URLs Configurées)

✅ **Vos tunnels NGrok sont maintenant actifs!**

### 🔗 URLs NGrok

| Component    | URL                                                       |
| ------------ | --------------------------------------------------------- |
| **Backend**  | `https://patternable-felicitously-shaunta.ngrok-free.dev` |
| **Frontend** | `https://sharron-prehazard-gully.ngrok-free.dev`          |

---

### ⚡ Étapes de Configuration Finale

#### Étape 1: Mettre à jour `backend/config/settings.py`

Ajouter les URLs ngrok à `ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS`:

```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.10.82',
    '0.0.0.0',
    'patternable-felicitously-shaunta.ngrok-free.dev',  # ← Backend ngrok
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:9090',
    'http://127.0.0.1:9090',
    'http://192.168.10.82:9090',
    'https://sharron-prehazard-gully.ngrok-free.dev',  # ← Frontend ngrok
]
```

#### Étape 2: Mettre à jour `frontend/advanced_chat/main.js`

Modifier la détection de l'API pour utiliser le backend ngrok:

```javascript
const API_BASE = (() => {
  const host = window.location.hostname;

  // Si accès via ngrok frontend
  if (host.includes("sharron-prehazard-gully.ngrok-free.dev")) {
    return "https://patternable-felicitously-shaunta.ngrok-free.dev";
  }

  // Si accès via IP local
  if (host.includes("192.168") || host.includes("10.")) {
    return `http://${host}:8000`;
  }

  // Local development
  return "http://localhost:8000";
})();

const API_URL = `${API_BASE}/api/chatbot/ask/`;
```

#### Étape 3: Redémarrer les Serveurs

**Terminal 1 - Backend Django (sur port 8000):**

```bash
cd c:\Users\DELL\Desktop\ChatBot\backend
python start_server.py
```

**Terminal 2 - Frontend Server (sur port 9090):**

```bash
cd c:\Users\DELL\Desktop\ChatBot\frontend\advanced_chat
python start_server.py
```

#### Étape 4: Vérifier les Tunnels NGrok

Assurez-vous que vos tunnels ngrok sont **actifs** et **correctement routés**:

```bash
# Vous devriez voir dans vos terminaux ngrok:
# Forwarding https://patternable-felicitously-shaunta.ngrok-free.dev -> http://localhost:8000
# Forwarding https://sharron-prehazard-gully.ngrok-free.dev -> http://localhost:9090
```

#### Étape 5: Tester

1. **Ouvrir le frontend ngrok dans le navigateur:**

   ```
   https://sharron-prehazard-gully.ngrok-free.dev
   ```

2. **Vérifier les logs console (F12):**

   ```
   ✅ SUP'PTIC Assistant initialisé
   🔗 API: https://patternable-felicitously-shaunta.ngrok-free.dev/api/chatbot/ask/
   ```

3. **Envoyer une question** et vérifier que le chatbot répond

4. **Vérifier DevTools Network:**
   - Chercher la requête POST vers `/api/chatbot/ask/`
   - Vérifier le code HTTP: `200 OK` (pas d'erreurs CORS)
   - Headers de réponse doivent inclure:
     ```
     Access-Control-Allow-Origin: https://sharron-prehazard-gully.ngrok-free.dev
     Access-Control-Allow-Credentials: true
     ```

---

## 📡 Adresses des Serveurs (Résumé Complet)

### 🏠 Local (Développement)

| Component    | Address        | URL                                      |
| ------------ | -------------- | ---------------------------------------- |
| Frontend     | localhost:9090 | `http://localhost:9090`                  |
| Backend API  | localhost:8000 | `http://localhost:8000/api/chatbot/ask/` |
| Django Admin | localhost:8000 | `http://localhost:8000/admin/`           |

### 🌍 NGrok (Production-like)

| Component   | Address     | URL                                                                        |
| ----------- | ----------- | -------------------------------------------------------------------------- |
| Frontend    | ngrok HTTPS | `https://sharron-prehazard-gully.ngrok-free.dev`                           |
| Backend API | ngrok HTTPS | `https://patternable-felicitously-shaunta.ngrok-free.dev/api/chatbot/ask/` |

---

## 🔍 Dépannage

### ❌ "API request failed" dans le frontend

**Cause:** Backend n'est pas accessible
**Solution:**

```bash
# Vérifier que Django tourne
curl http://localhost:8000/api/chatbot/ask/
# Doit retourner une erreur 405 (Method Not Allowed) pour GET, c'est normal
```

### ❌ CORS error dans DevTools

**Cause:** `CORS_ALLOWED_ORIGINS` ne contient pas l'adresse frontend
**Solution:** Vérifier `backend/config/settings.py` et ajouter l'adresse frontend

### ❌ "Vectors not found" ou pas de réponses

**Cause:** TF-IDF vectorizer pas initialisé
**Solution:**

```bash
cd backend
python manage.py init_vectors
```

### ❌ Port 8000/9090 déjà utilisé

**Solution:**

```bash
# Tuer le processus sur le port
lsof -i :8000        # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

Puis redémarrer le serveur sur un autre port:

```bash
python manage.py runserver 0.0.0.0:8001
```

Et mettre à jour `main.js`:

```javascript
return "http://localhost:8001"; // ← Nouveau port
```

---

## 📝 Logs et Débogage

### Activer les logs Django

Dans `backend/config/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Console Frontend (DevTools F12)

Logs disponibles:

- `✅ SUP'PTIC Assistant initialisé` — Démarrage OK
- `🔗 API: ...` — URL de l'API utilisée
- `Erreur lors de la requête: ...` — Erreur réseau/CORS

---

## 📚 Ressources Utiles

- Django: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- spaCy: https://spacy.io/
- scikit-learn (TF-IDF): https://scikit-learn.org/
- NGrok: https://ngrok.com/docs

---

## ✅ Checklist de Démarrage

- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Données importées (`python scripts/load_test_data.py`)
- [ ] Vecteurs initialisés (`python manage.py init_vectors`)
- [ ] Backend lancé (`Terminal 1: python start_server.py`)
- [ ] Frontend lancé (`Terminal 2: python start_server.py`)
- [ ] Frontend accessible (`http://localhost:9090`)
- [ ] API accessible (`http://localhost:8000/api/chatbot/ask/`)
- [ ] Chatbot répond correctement
- [ ] Console DevTools sans erreurs CORS

---

## 🎯 Prochaines Étapes

1. ✅ **Setup Local**: Confirmer que tout fonctionne en local
2. 🌍 **NGrok Setup**: Exposer les serveurs via NGrok (2 tunnels: 1 backend, 1 frontend)
3. 🔐 **Production**: Déployer sur un serveur (Heroku, AWS, etc.)
4. 📱 **PWA**: Ajouter PWA support si nécessaire

---

Bonne utilisation! 🚀
