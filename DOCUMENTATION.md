# 📘 Documentation Technique SUP'ONE AI v2.0

## 1. Architecture Système
SUP'ONE AI utilise une architecture **RAG (Retrieval-Augmented Generation)** hybride pour garantir des réponses précises et contextuelles.

### Composants Backend (Django)
- **Moteur de Recherche (Phase 1)** : Basé sur TF-IDF et la similarité cosinus pour la recherche exacte dans la base FAQ.
- **Pipeline IA (Gen3)** : 
    - **Embeddings** : `all-MiniLM-L6-v2` via Sentence-Transformers.
    - **Indexation** : FAISS (Facebook AI Similarity Search) pour la recherche sémantique vectorielle.
    - **Génération** : Google Gemini 1.5 Flash via API pour la synthèse des réponses en français.
- **Gestion des Sessions** : Authentification par Token DRF avec persistance locale.

### Composants Frontend (React & Mobile)
- **Core** : React 19 + Vite (performance optimale).
- **Logic** : Custom Hook `useChat` gérant le streaming SSE, l'historique fusionné (Local/Backend) et la santé du serveur.
- **Mobile** : Capacitor 7 pour l'encapsulation native Android.
- **PWA** : Service Worker pour le support hors ligne et l'installation sur bureau.

## 2. Guide d'Installation (Développement)

### Backend
1. Créer un environnement virtuel : `python -m venv venv`
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer le `.env` (Clé Gemini requise).
4. Initialiser la base de données :
   ```bash
   python manage.py migrate
   python manage.py import_faq  # Si script dispo
   python manage.py rebuild_vectors # Génère l'index FAISS
   ```
5. Lancer : `python manage.py runserver 8001`

### Frontend
1. `cd frontend/app`
2. `npm install`
3. `npm run dev` (Port 5173 par défaut)

## 3. Pipeline de Production & Build APK

Pour générer l'APK final destiné aux utilisateurs :

### Étape 1 : Préparation du Bundle Web
   ```bash
   cd frontend/app
   npm run build  # Génère le dossier dist/
   ```

### Étape 2 : Synchronisation Native
   ```bash
   npx cap copy android
   npx cap sync android # Met à jour les plugins et les assets
   ```

### Étape 3 : Compilation via Gradle
   ```bash
   cd android
   ./gradlew assembleRelease # Génère l'APK de production optimisé
   ```
L'APK se trouvera dans : `android/app/build/outputs/apk/release/app-release.apk`. 

### Étape 4 : Signature de l'APK (Production)

Pour générer un APK signé prêt pour la distribution :

1. **Générer le Keystore** (si vous n'en avez pas) :
   ```bash
   keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias supone-alias
   ```
   *Note : Gardez ce fichier en sécurité dans le dossier `android/app/` et ne le commitez jamais.*

2. **Configurer les variables** (`android/gradle.properties`) :
   ```properties
   SUPONE_RELEASE_STORE_FILE=my-release-key.jks
   SUPONE_RELEASE_KEY_ALIAS=supone-alias
   SUPONE_RELEASE_STORE_PASSWORD=********
   SUPONE_RELEASE_KEY_PASSWORD=********
   ```

3. **Modifier le build.gradle** (`android/app/build.gradle`) :
   ```gradle
   signingConfigs {
       release {
           storeFile file(SUPONE_RELEASE_STORE_FILE)
           storePassword SUPONE_RELEASE_STORE_PASSWORD
           keyAlias SUPONE_RELEASE_KEY_ALIAS
           keyPassword SUPONE_RELEASE_KEY_PASSWORD
       }
   }
   buildTypes {
       release {
           signingConfig signingConfigs.release
       }
   }
   ```

### Étape 5 : Optimisation et réduction de taille (R8/ProGuard)

Pour réduire la taille de l'APK (gain de ~40%) et sécuriser le code, activez la minification dans `android/app/build.gradle` :

1. **Activer R8** :
   ```gradle
   buildTypes {
       release {
           minifyEnabled true
           shrinkResources true
           signingConfig signingConfigs.release
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
       }
   }
   ```

2. **Règles de conservation** (`android/app/proguard-rules.pro`) :
   Ajoutez ces lignes pour garantir que Capacitor fonctionne correctement :
   ```proguard
   -keep class com.getcapacitor.** { *; }
   -keep class * extends com.getcapacitor.Plugin
   ```

3. **Build final** : Relancez `./gradlew assembleRelease`.

*Note : Pour le Play Store, utilisez `./gradlew bundleRelease`.*

## 4. Sécurité et Maintenance
- **CORS** : Le serveur Django doit être configuré pour accepter `capacitor://localhost` (Android) et les domaines Netlify/Railway.
- **Confidentialité** : Les clés API ne doivent jamais être présentes dans le code frontend. Le passage par le backend Django est obligatoire.
- **Mise à jour FAQ** : Toute modification des fichiers JSON nécessite de relancer `rebuild_vectors` pour mettre à jour l'IA.

---
*© 2026 SUP'PTIC - Club Informatique*