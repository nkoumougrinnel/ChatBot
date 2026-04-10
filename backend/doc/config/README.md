# Configuration et Environnement

Ce dossier contient la documentation de configuration du backend.

## Types de configuration

### Configuration Django

- `settings.py` - Configuration principale
- Variables d'environnement
- Configuration par environnement (dev/prod)

### Configuration base de données

- Connexion PostgreSQL
- Migrations Django
- Backup et restauration

### Configuration services externes

- Ollama (Phase 2)
- Ngrok (développement)
- Services de cache

## Variables d'environnement

### Obligatoires

```bash
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/db
OLLAMA_BASE_URL=http://localhost:11434
```

### Optionnelles

```bash
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourfrontend.com
LOG_LEVEL=INFO
```

## Environnements

### Développement

- `DEBUG=True`
- Base SQLite locale
- Logs détaillés
- Ngrok pour les tests externes

### Production

- `DEBUG=False`
- Base PostgreSQL
- Logs structurés
- Variables sécurisées

## Scripts de configuration

### Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### Configuration Ngrok

```bash
ngrok config add-authtoken YOUR_TOKEN
ngrok http 8000
```

## Sécurité

- **Clés secrètes** : Jamais en dur dans le code
- **Variables sensibles** : Utiliser des secrets managers
- **CORS** : Configurer correctement pour la production
- **HTTPS** : Toujours en production

## Dépannage

### Erreurs communes

- **Database connection failed** : Vérifier DATABASE_URL
- **Ollama connection error** : Vérifier OLLAMA_BASE_URL
- **CORS errors** : Vérifier CORS_ALLOWED_ORIGINS

