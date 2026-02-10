README — frontend/

Ce dossier contient un mini-frontend de test (HTML + JS) pour se connecter
à l'API chatbot. Il sert d'exemple rapide pour l'équipe Frontend.

Fichiers principaux:

- `simple_chat.html` : mini-app qui envoie une requête POST à `/api/chatbot/ask/` et affiche les résultats.
- `README.md` (ce fichier) : instructions pour lancer et tester.

Comment utiliser :

1. Démarrer le serveur Django :

```powershell
cd C:\Users\DELL\Desktop\ChatBot
.venv\Scripts\Activate.ps1
python backend/manage.py runserver
```

2. Servir le frontend temporairement (optionnel, utile pour éviter les issues CORS) :

```powershell
# depuis la racine du repo
python -m http.server 8001
# ouvrir http://localhost:8001/frontend/simple_chat.html
```

3. Ouvrir `frontend/simple_chat.html` dans le navigateur (ou via le serveur HTTP ci-dessus).

Notes :

- Le fichier est prévu pour un usage développement local uniquement.
- Si vous servez la page depuis un hôte différent du backend, configurez CORS côté backend.

Erreurs courantes :

- `TypeError: Failed to fetch` : serveur backend non démarré ou CORS refusé.
- `400/500` : montreront le message d'erreur renvoyé par l'API dans la zone "status".

Sécurité : Ne pas déployer ce fichier en production sans contrôles (CORS, auth, rate limit).
