# Documentation SUP'ONE AI — Plateforme Éducative

## 1. Vision du Produit
SUP'ONE AI est une plateforme d'intelligence artificielle conçue pour accompagner les étudiants dans leur parcours académique. L'interface suit les standards de l'industrie (ChatGPT/Gemini) : minimalisme, rapidité et fiabilité.

## 2. Architecture Technique
### Frontend (Vanilla JS + Capacitor)
- **Architecture State-Driven** : L'interface réagit à un objet `state` centralisé.
- **Sécurité Session** : Utilisation de cookies `HttpOnly`. Le client ne manipule plus de jetons JWT en clair dans le code JS.
- **Modularité API** : `api.js` centralise toutes les communications vers le backend Django.

### Expérience Utilisateur (UX)
1. **Splash Screen** : Branding institutionnel immédiat et masquage du temps de latence réseau.
2. **Offline Mode** : Redirection vers une vue dédiée pour éviter toute corruption d'UI ou perte de données utilisateur.
3. **Navigation** : Sidebar escamotable pour l'historique et profil utilisateur via modal.

## 3. Configuration et Build (Mobile)

### Prérequis
- Node.js (v20+)
- Java JDK 21
- Android Studio

### Procédure de compilation APK
1. **Build Web** : 
   ```bash
   cd frontend/app
   npm run build
   ```
2. **Sync Capacitor** :
   ```bash
   npx cap sync android
   ```
3. **Génération APK** :
   ```bash
   cd android
   ./gradlew assembleDebug
   ```
Localisation de l'APK : `android/app/build/outputs/apk/debug/app-debug.apk`

## 4. Sécurité et Bonnes Pratiques
- **CORS** : Le backend doit autoriser `capacitor://localhost` et votre domaine de production.
- **Sanitization** : Toutes les entrées utilisateur sont échappées via `escapeHtml()`.
- **Performance** : Utilisation de `requestAnimationFrame` pour les auto-scrolls et le rendu des tokens en streaming.

---
*© 2026 SUP'PTIC - Club Informatique*