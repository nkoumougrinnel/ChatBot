# 📋 Guide pour les Équipes Contributeurs - Phase 1

**Architecture V2** : Collecte par catégories étudiantes

## Pour les Équipes Contributeurs Étudiants

### Étape 1 : Identifier votre Assignation

Votre équipe a été assignée à une **catégorie** et un **sous-thème** spécifique.

**Exemple :**

```
Équipe 3 → Catégorie: Vie Étudiante
           Sous-thème: Logement Étudiant
           Session: 1
```

### Étape 2 : Localiser le Dossier

Naviguer jusqu'à :

```
phase-1/data/categories/3_vie_etudiante/3b_logement_etudiant/pending/
```

### Étape 3 : Créer Votre Fichier CSV

Créer un fichier nommé exactement comme ceci :

```
vieetudiante_logement_equipe3_session1.csv
```

#### Règles de Nomenclature :

- ✅ Tout en **minuscules**
- ✅ Sans **accents**
- ✅ Sans **espaces**
- ✅ Séparation par **underscore (\_)**
- ✅ Format: `categorie_soustheme_equipeX_sessionY.csv`

### Étape 4 : Remplir le CSV

#### Format Requis :

```csv
Question,Reponse,Categorie,SousTheme,Source
```

#### Exemple Complet :

```csv
"Où se trouve la cité universitaire la plus proche de SUP'PTIC ?","La Cité Verte est à 10 minutes à pied du campus principal. Vous pouvez aussi consulter la liste complète sur le portail étudiant.","vieetudiante","Logement étudiant","Site SUP'PTIC"
"Comment s'inscrire dans une cité universitaire ?","L'inscription se fait en juillet-août auprès du MINESUP en ligne ou sur place. Les places sont limitées, inscrivez-vous tôt.","vieetudiante","Logement étudiant","Communiqué officiel"
```

### Étape 5 : Respect des Standards

#### 📝 Questions :

- Commencer par un **mot interrogatif** : Quoi, Quand, Où, Comment, Pourquoi, Quels, Combien
- **Max 200 caractères**
- Une seule question par ligne
- **Formulation naturelle** (comme si vous parliez à un ami)

#### ✅ Réponses :

- **2-3 phrases maximum**
- Langage **accessible** (pas de jargon)
- **Informations concrètes** (chiffres, noms, délais)
- **Pas de listes à puces** (utiliser du texte continu)

#### 🏷️ Catégorie :

Doit correspondre à votre assignation (en minuscules) :

- `inscriptions`
- `examens`
- `vieetudiante`
- `services`
- `programmes`
- `infrastructures`
- `carrieres`
- `communication`
- `viepratique`

#### 🎯 SousTheme :

Utiliser exactement le nom du dossier (minuscules) :

- `logement_etudiant`
- `conditions_admission`
- etc.

#### 📚 Source :

L'une de ces valeurs :

- `Site SUP'PTIC`
- `Communiqué officiel`
- `IA`
- `Atelier`
- `Guide étudiant 2025-2026`
- `Règlement intérieur SUP'PTIC`

### Étape 6 : Outils Recommandés

#### Pour créer/éditer le CSV :

- ✅ **Excel** (meilleur pour CSV)
- ✅ **LibreOffice Calc**
- ✅ **VS Code** (avec Live Share pour collaboration)
- ✅ **Google Sheets** → exporter en CSV

#### Pour générer des Q/R avec IA :

**Prompt ChatGPT/Claude :**

```
Génère 30 questions-réponses sur le thème "Logement étudiant à SUP'PTIC"
en format CSV avec colonnes : Question, Reponse, Categorie, SousTheme, Source

Contraintes :
- Réponses en 2-3 phrases max
- Questions variées et pratiques
- Spécifiques au contexte camerounais/Yaoundé
- Vérifiables auprès du service vie étudiante

Format de sortie :
"Question ?","Réponse courte et claire.","vieetudiante","logement_etudiant","IA"
```

### Étape 7 : Qualité Avant Quantité

#### ✅ Excellent :

```csv
"Combien coûte une chambre en cité universitaire ?","Une chambre en cité universitaire coûte entre 50 000 et 80 000 FCFA par mois selon la cité. Les tarifs incluent électricité et eau. Des bourses sont disponibles pour étudiants en difficulté financière.","vieetudiante","logement_etudiant","Service vie étudiante SUP'PTIC"
```

#### ❌ Mauvais :

```csv
"Logement ?","Tu peux trouver un logement à Yaoundé.","vieetudiante","logement_etudiant","IA"
```

(Question vague, réponse inutile)

### Étape 8 : Vérification Finale

#### Avant de soumettre, vérifier :

**Format :**

- [ ] Guillemets correctement fermés
- [ ] Pas de guillemets manquants dans les données
- [ ] Séparateur de colonnes correct (virgule)
- [ ] Encodage UTF-8

**Contenu :**

- [ ] Minimum 20 Q/R (mieux : 30-40)
- [ ] Pas de lignes vides
- [ ] Toutes les colonnes remplies
- [ ] Au moins 3 sources différentes citées

**Qualité :**

- [ ] Relecture pour fautes d'orthographe
- [ ] Réponses concises (pas de pavés)
- [ ] Cohérence catégorie/sous-thème
- [ ] Questions vraiment utiles

**Validité Excel :**

- Ouvrir le fichier dans Excel/LibreOffice
- Vérifier qu'il s'ouvre sans erreur
- Vérifier que les données s'affichent correctement

### Étape 9 : Soumission

1. **Placer le fichier** dans :

   ```
   phase-1/data/categories/[VOTRE_CATEGORIE]/[VOTRE_SOUS_THEME]/pending/
   ```

2. **Notifier l'équipe** via :
   - Slack #chatbot-faq-v2
   - Email à : germain.nkoumou@supptic.cm
   - Message : "Équipe [X] a soumis [fichier.csv]"

3. **Attendre la validation** :
   - Pré-validation IA : 24h
   - Révision humaine : 2-3 jours
   - Retours ou approbation

### Étape 10 : Cycle de Révision

Si vous recevez des retours :

1. ✏️ **Corriger** les Q/R signalées
2. 📤 **Renommer** le fichier : `...session2.csv`
3. 📁 **Replacer** dans pending/
4. 🔄 **Redémarrer** le processus

---

## 🏆 Conseils pour Excellentes Q/R

### 1. Source Primaire

Toujours vérifier avec **documents officiels** :

- Site SUP'PTIC
- Règlement intérieur
- Guides administratifs
- Communiqués officiels

### 2. Perspective Étudiante

Poser les questions qu'un **étudiant réel** posera :

```
"Comment ?" → Pratique
"Où ?" → Localisation
"Combien ?" → Tarifs
"Quand ?" → Délais
```

### 3. Détail Contextuel

Ajouter des **infos utiles** :

```
❌ Mauvais : "Où loger ?"
✅ Bon : "Combien coûte une chambre en cité à côté de SUP'PTIC ?"
```

### 4. Cohérence Ton

Maintenir un **ton formel mais accessible** :

```
❌ "Yo mec, tu peux loger à la cité"
✅ "Vous pouvez vous loger à la Cité Verte, 10 min du campus"
```

### 5. Éviter les Pièges

- ❌ Copier-coller sans vérifier → L'IA invente !
- ❌ Réponses trop longues → Garder 2-3 phrases
- ❌ Jargon administratif → Langage clair
- ❌ Doublons → Vérifier avant soumettre
- ❌ Infos obsolètes → Indiquer l'année académique

---

## 📊 Cible de Votre Équipe

| Métrique                | Cible        |
| ----------------------- | ------------ |
| Q/R minimum par fichier | 20           |
| Cible optimale          | 30-40        |
| Sessions planifiées     | 3            |
| Cible totale équipe     | 100-120 Q/R  |
| Délai par session       | 2-3 semaines |

---

## 🎓 Formation IA Recommandée

Avant votre première contribution :

1. **Atelier Prompting** (2h)
   - 15 prompts essentiels
   - Exercices pratiques
   - Débriefing collectif

2. **Tutoriel VS Code Live Share** (1h)
   - Collaboration temps réel
   - Partage de fichiers
   - Bonnes pratiques

3. **Review d'Exemples** (30 min)
   - Q/R excellentes
   - Erreurs courantes
   - Corrections

---

## 💬 Support et Questions

**Responsable V2 :** NKOUMOU Germain  
**Email :** germain.nkoumou@supptic.cm  
**Slack :** #chatbot-faq-v2  
**Heures disponibles :** 9h-17h (LMT)

**Problème fréquent ?**

**Problème :** Erreur guillemets CSV

```
Solution: Utiliser l'option "Enregistrer sous" → Format CSV UTF-8
```

**Problème :** Doublons détectés

```
Solution: Vérifier avec autres fichiers validés
Utiliser: difflib pour détection automatique
```

**Problème :** Réponse trop longue

```
Solution: Garder l'info essentielle, condenser à 2-3 phrases
```

---

## ✅ Checklist Finale

Avant d'envoyer votre fichier :

```
[ ] Nomenclature exacte : categorie_soustheme_equipeX_sessionY.csv
[ ] Fichier dans le bon dossier pending/
[ ] Format CSV : Question,Reponse,Categorie,SousTheme,Source
[ ] Min 20 Q/R (idéal 30-40)
[ ] Toutes les colonnes remplies
[ ] Pas de guillemets manquants
[ ] Réponses max 3 phrases
[ ] Questions commencent par mot interrogatif
[ ] Minimum 3 sources différentes
[ ] Encodage UTF-8
[ ] Relecture et vérification
[ ] Notif Slack équipe
```

---

**Version:** 2.0 (Janvier 2026)  
**Ressource:** phase-1/data/categories/README.md

Bonne contribution ! 🚀
