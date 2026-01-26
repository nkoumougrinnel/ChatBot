# INDEX RAPIDE - Phase 1 V2

## Accès Rapide aux Catégories

### 🎓 Inscriptions et Admissions

```
path: phase-1/data/categories/1_inscriptions_admissions/
sous-thèmes: 9
cible: 1000+ Q/R
```

- Conditions d'admission
- Procédures en ligne
- Documents requis
- Frais et paiements
- Réinscription
- Étudiants étrangers
- Orientation et filière
- Cas particuliers (handicap)
- Plateformes numériques

---

### 📝 Examens et Évaluations

```
path: phase-1/data/categories/2_examens_evaluations/
sous-thèmes: 9
cible: 1000+ Q/R
```

- Calendrier des examens
- Modalités
- Notes et barème
- Rattrapages et dispenses
- Fraude et sanctions
- Publication résultats
- Préparation et méthodologie
- Examens en ligne
- Accessibilité

---

### 🎉 Vie Étudiante

```
path: phase-1/data/categories/3_vie_etudiante/
sous-thèmes: 9
cible: 1000+ Q/R
```

- Clubs et associations
- Logement étudiant
- Restauration
- Activités culturelles et sportives
- Santé et accompagnement
- Événements académiques
- Vie quotidienne
- Engagement citoyen
- Numérique étudiant

---

### 🏢 Services Administratifs

```
path: phase-1/data/categories/4_services_administratifs/
sous-thèmes: 9
cible: 1000+ Q/R
```

- Bibliothèque et ressources
- Scolarité
- Finances
- Stages et partenariats
- Diplômes et certifications
- Relations internationales
- Support informatique
- Archives et mémoire
- Communication officielle

---

### 📚 Programmes Académiques

```
path: phase-1/data/categories/5_programmes_academiques/
sous-thèmes: 4
cible: 500+ Q/R
```

- Présentation filières (Télécoms, Réseaux, Informatique)
- Organisation cours (semestres, crédits, UE)
- Encadrement pédagogique
- Projets académiques et TP

---

### 🔧 Infrastructures et Ressources

```
path: phase-1/data/categories/6_infrastructures_ressources/
sous-thèmes: 4
cible: 500+ Q/R
```

- Laboratoires et salles spécialisées
- Accès internet et plateformes (Moodle, intranet)
- Logiciels et licences
- Sécurité et maintenance

---

### 💼 Carrières et Insertion Professionnelle

```
path: phase-1/data/categories/7_carrieres_insertion/
sous-thèmes: 4
cible: 400+ Q/R
```

- Stages et conventions
- Partenariats avec entreprises
- Forums emploi et journées carrières
- Réseau des anciens (alumni)

---

### 📢 Communication et Vie Institutionnelle

```
path: phase-1/data/categories/8_communication_vie_institutionnelle/
sous-thèmes: 4
cible: 400+ Q/R
```

- Canaux officiels
- Procédures de réclamation et médiation
- Actualités et annonces
- Participation aux instances

---

### 🚌 Vie Pratique

```
path: phase-1/data/categories/9_vie_pratique/
sous-thèmes: 4
cible: 400+ Q/R
```

- Transport et accessibilité du campus
- Sécurité et règlement intérieur
- Coût de la vie à Yaoundé
- Services annexes (photocopies, fournitures)

---

## 📊 Statistiques Cibles

| Catégorie       | Sous-thèmes | Cible Q/R     |
| --------------- | ----------- | ------------- |
| Inscriptions    | 9           | 1000+         |
| Examens         | 9           | 1000+         |
| Vie Étudiante   | 9           | 1000+         |
| Services        | 9           | 1000+         |
| Programmes      | 4           | 500+          |
| Infrastructures | 4           | 500+          |
| Carrières       | 4           | 400+          |
| Communication   | 4           | 400+          |
| Vie Pratique    | 4           | 400+          |
| **TOTAL**       | **52**      | **5000-9000** |

---

## 🔄 Workflow Standard

```
Création CSV → Placement pending/ → Pré-validation IA
    ↓
Validation humaine (processing/) → Révisions
    ↓
Acceptation → validated/ → Intégration BD vectorielle
```

---

## ✅ Checklist Avant Soumission

Pour chaque fichier CSV :

- [ ] Nomenclature respectée : `categorie_soustheme_equipeX_sessionY.csv`
- [ ] En-têtes présents : Question, Reponse, Categorie, SousTheme, Source
- [ ] Minimum 20 Q/R (objectif 30-40)
- [ ] Pas de lignes vides ou incomplètes
- [ ] Guillemets correctement fermés
- [ ] Encodage UTF-8
- [ ] Au moins 3 sources différentes citées
- [ ] Relecture collective effectuée

---

## 🚀 Commandes Utiles

### Lister tous les fichiers pending :

```bash
find . -path "*pending*" -name "*.csv" | sort
```

### Compter les Q/R par catégorie :

```bash
for dir in */; do
  count=$(find "$dir" -name "*.csv" -exec wc -l {} + | tail -1 | awk '{print $1}')
  echo "$dir: $count lignes"
done
```

### Fusionner tous les CSV validés :

```bash
cat */*/validated/*.csv > master_validated.csv
```

---

## 📞 Support et Questions

**Responsable V2** : NKOUMOU Germain  
**Email** : germain.nkoumou@supptic.cm  
**Slack** : #chatbot-faq-v2

---

**Version** : 2.0 (Janvier 2026)  
**Dernière mise à jour** : 2026-01-26
