# 🚀 SUP'ONE AI — Assistant Intelligent SUP'PTIC

SUP'ONE AI est une solution complète d'assistance pour les étudiants et l'administration de SUP'PTIC, utilisant le **RAG (Retrieval-Augmented Generation)** pour fournir des réponses instantanées et fiables.

## ✨ Fonctionnalités Clés

- **Réponses en temps réel** : Streaming de tokens via SSE (Server-Sent Events).
- **IA Hybride** : Bascule automatique entre le pipeline IA (Gemini) et la base de connaissances locale (TF-IDF).
- **Multi-plateforme** : Web, PWA installable et Application Android native.
- **Historique Intelligent** : Synchronisation transparente entre le stockage local et le compte utilisateur.
- **Système de Feedback** : Apprentissage continu basé sur les notes des utilisateurs.

## 🛠 Stack Technique

**Backend:**
- Python 3.13 / Django 4.2
- FAISS / Sentence-Transformers (Recherche Vectorielle)
- Google Gemini 1.5 Flash API

**Frontend:**
- React 19 / Vite / Capacitor
- Interface "Glassmorphism" optimisée pour mobile

## 📦 Installation Rapide

```bash
# Installer les dépendances backend
pip install -r requirements.txt

# Préparer le frontend
cd frontend/app
npm install
npm run dev
```

## 📱 Application Mobile

Le projet est prêt pour le déploiement mobile. Consultez le fichier `DOCUMENTATION.md` pour les instructions détaillées sur la génération de l'APK de production.

---
*Propulsé par le Club Informatique de SUP'PTIC*