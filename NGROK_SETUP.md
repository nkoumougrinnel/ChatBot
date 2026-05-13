# Configuration ngrok pour deux tunnels séparés

## Setup

1. Remplace `<TOKEN_FRONTEND>` et `<TOKEN_BACKEND>` par tes tokens ngrok dans les fichiers de configuration

2. Lance les deux tunnels dans des terminaux séparés :

### Terminal 1 - Frontend (port 3000)

```bash
ngrok start --config ngrok_front.yml frontend
```

### Terminal 2 - Backend (port 8000)

```bash
ngrok start --config ngrok_back.yml backend
```

## Notes

- Chaque tunnel utilise un compte ngrok différent
- Les URLs seront affichées dans chaque terminal ngrok
- Update settings.py et main.js avec les nouvelles URLs
