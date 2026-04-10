# Documentation API

Ce dossier contient la documentation des APIs REST du backend Django.

## Structure

### Fichiers principaux

- `API_REST_IMPLEMENTATION.md` - Implémentation détaillée des APIs
- `API_TEST_GUIDE.md` - Guide de test des endpoints

### Organisation par endpoint

- `api-faq-endpoints.md` - Endpoints FAQ (/api/faq/)
- `api-chatbot-endpoints.md` - Endpoints ChatBot (/api/chatbot/)
- `api-feedback-endpoints.md` - Endpoints Feedback (/api/feedback/)
- `api-stats-endpoints.md` - Endpoints Statistiques (/api/stats/)

## Format de documentation

Pour chaque endpoint documenté :

### Endpoint: `GET /api/faq/list/`

**Description** : Liste toutes les FAQs disponibles

**Paramètres** :

- `categorie` (optionnel) : Filtrer par catégorie
- `limit` (optionnel) : Nombre maximum de résultats (défaut: 50)

**Réponse** :

```json
{
  "count": 25,
  "results": [
    {
      "id": "faq_001",
      "question": "Comment s'inscrire ?",
      "categorie": "Admissions"
    }
  ]
}
```

**Codes d'erreur** :

- `400` : Paramètres invalides
- `500` : Erreur serveur

## Tests

Voir `API_TEST_GUIDE.md` pour les procédures de test complètes.
