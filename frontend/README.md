# Frontend SUP'ONE AI

> Documentation complète : **[../docs/GUIDE_COMPLET.md](../docs/GUIDE_COMPLET.md)**

## Application principale (React + PWA)

Le frontend recommandé est dans **`app/`** :

- React 19 + Vite
- PWA installable (mobile & desktop)
- Design moderne, responsive
- Connexion API Phase 1 + Gen3 (streaming)

```bash
cd app
npm install
npm run dev      # http://localhost:5174
npm run build    # production → dist/
```

## Anciennes versions (conservées)

- `index.html` + `app.js` — version HTML simple (redirige vers `app/`)
- `advanced_chat/` — version PWA vanilla JS historique
