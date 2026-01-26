# 🏗️ STRUCTURE COMPLÈTE V2 - Vue d'ensemble

## Arborescence Complète du Projet

```
ChatBot/
├── README.md
├── requirements.txt
├── db/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHASES.md
│   ├── PROJECT_OVERVIEW.md
│   ├── GUIDE_CONTRIBUTEURS_V2.md          ← NOUVEAU (Guide équipes)
│   └── phase-1/
│       ├── Gestion FAQ.tex
│       ├── README.md
│       ├── SETUP.md
│       └── USAGE.md
├── logs/
└── phase-1/
    ├── config/
    │   ├── faq-service-key.json
    │   └── PROGRESSION_V2.json              ← NOUVEAU (Tracking)
    ├── data/
    │   ├── last_row.txt
    │   ├── categories/                      ← NOUVEAU (Structure V2)
    │   │   ├── README.md                    ← NOUVEAU
    │   │   ├── INDEX.md                     ← NOUVEAU
    │   │   ├── TEMPLATE.csv                 ← NOUVEAU (Modèle)
    │   │   │
    │   │   ├── 1_inscriptions_admissions/
    │   │   │   ├── 1a_conditions_admission/
    │   │   │   │   ├── pending/
    │   │   │   │   ├── processing/
    │   │   │   │   ├── validated/
    │   │   │   │   └── archived/
    │   │   │   ├── 1b_procedure_enligne/
    │   │   │   │   └── [4 dossiers de workflow]
    │   │   │   ├── 1c_documents_requis/
    │   │   │   ├── 1d_frais_paiements/
    │   │   │   ├── 1e_reinscription_cas_particuliers/
    │   │   │   ├── 1f_etudiants_etrangers/
    │   │   │   ├── 1g_orientation_choix_filiere/
    │   │   │   ├── 1h_cas_particuliers_handicap/
    │   │   │   └── 1i_plateformes_numeriques/
    │   │   │
    │   │   ├── 2_examens_evaluations/       [9 sous-thèmes]
    │   │   │   ├── 2a_calendrier_examens/
    │   │   │   ├── 2b_modalites/
    │   │   │   ├── 2c_notes_bareme/
    │   │   │   ├── 2d_rattrapages_dispenses/
    │   │   │   ├── 2e_fraude_sanctions/
    │   │   │   ├── 2f_publication_resultats/
    │   │   │   ├── 2g_preparation_methodologie/
    │   │   │   ├── 2h_examens_enligne/
    │   │   │   └── 2i_accessibilite/
    │   │   │
    │   │   ├── 3_vie_etudiante/             [9 sous-thèmes]
    │   │   │   ├── 3a_clubs_associations/
    │   │   │   ├── 3b_logement_etudiant/
    │   │   │   ├── 3c_restauration/
    │   │   │   ├── 3d_activites_culturelles_sportives/
    │   │   │   ├── 3e_sante_accompagnement/
    │   │   │   ├── 3f_evenements_academiques/
    │   │   │   ├── 3g_vie_quotidienne/
    │   │   │   ├── 3h_engagement_citoyen/
    │   │   │   └── 3i_numerique_etudiant/
    │   │   │
    │   │   ├── 4_services_administratifs/   [9 sous-thèmes]
    │   │   │   ├── 4a_bibliotheque_ressources/
    │   │   │   ├── 4b_scolarite/
    │   │   │   ├── 4c_finances/
    │   │   │   ├── 4d_stages_partenariats/
    │   │   │   ├── 4e_diplomes_certifications/
    │   │   │   ├── 4f_relations_internationales/
    │   │   │   ├── 4g_support_informatique/
    │   │   │   ├── 4h_archives_memoire/
    │   │   │   └── 4i_communication_officielle/
    │   │   │
    │   │   ├── 5_programmes_academiques/    [4 sous-thèmes]
    │   │   │   ├── 5a_presentation_filieres/
    │   │   │   ├── 5b_organisation_cours/
    │   │   │   ├── 5c_encadrement_pedagogique/
    │   │   │   └── 5d_projets_tp/
    │   │   │
    │   │   ├── 6_infrastructures_ressources/ [4 sous-thèmes]
    │   │   │   ├── 6a_laboratoires/
    │   │   │   ├── 6b_internet_plateformes/
    │   │   │   ├── 6c_logiciels_licences/
    │   │   │   └── 6d_securite_maintenance/
    │   │   │
    │   │   ├── 7_carrieres_insertion/       [4 sous-thèmes]
    │   │   │   ├── 7a_stages_conventions/
    │   │   │   ├── 7b_partenariats_entreprises/
    │   │   │   ├── 7c_forums_emploi/
    │   │   │   └── 7d_reseau_alumni/
    │   │   │
    │   │   ├── 8_communication_vie_institutionnelle/ [4 sous-thèmes]
    │   │   │   ├── 8a_canaux_officiels/
    │   │   │   ├── 8b_reclamations_mediation/
    │   │   │   ├── 8c_actualites_annonces/
    │   │   │   └── 8d_participation_instances/
    │   │   │
    │   │   └── 9_vie_pratique/              [4 sous-thèmes]
    │   │       ├── 9a_transport_accessibilite/
    │   │       ├── 9b_securite_reglement/
    │   │       ├── 9c_cout_vie/
    │   │       └── 9d_services_annexes/
    │   │
    │   ├── archived/                         (Ancien système)
    │   ├── pending/                          (Ancien système - déprécié)
    │   ├── processing/                       (Ancien système - déprécié)
    │   └── validated/                        (Ancien système - déprécié)
    │
    ├── scripts/
    │   ├── import_validated.py
    │   ├── reset_and_import.py
    │   └── sync.py
    │
    └── tests/
        └── test_db.py

V2/
├── Gestion ChatBot FAQ.aux
├── Gestion ChatBot FAQ.tex
└── Gestion ChatBot FAQ.toc
```

---

## 📊 Métriques de Structuration V2

### Catégories et Sous-thèmes

| #         | Catégorie                             | Sous-thèmes | Cible Q/R     | Statut      |
| --------- | ------------------------------------- | ----------- | ------------- | ----------- |
| 1         | Inscriptions et Admissions            | 9           | 1000+         | ✅ Prêt     |
| 2         | Examens et Évaluations                | 9           | 1000+         | ✅ Prêt     |
| 3         | Vie Étudiante                         | 9           | 1000+         | ✅ Prêt     |
| 4         | Services Administratifs               | 9           | 1000+         | ✅ Prêt     |
| 5         | Programmes Académiques                | 4           | 500+          | ✅ Prêt     |
| 6         | Infrastructures et Ressources         | 4           | 500+          | ✅ Prêt     |
| 7         | Carrières et Insertion                | 4           | 400+          | ✅ Prêt     |
| 8         | Communication et Vie Institutionnelle | 4           | 400+          | ✅ Prêt     |
| 9         | Vie Pratique                          | 4           | 400+          | ✅ Prêt     |
| **TOTAL** |                                       | **52**      | **5000-9000** | ✅ **PRÊT** |

### Workflows par Sous-thème

Chaque sous-thème possède cette structure :

```
sous-theme/
├── pending/           [Entrée] Q/R en attente
├── processing/        [Révision] Validation en cours
├── validated/         [Sortie] Approuvé pour BD
└── archived/          [Stockage] Archivé/Supprimé
```

**Total de dossiers :** 52 × 4 = **208 dossiers de workflow**

---

## 🎯 Objectifs par Catégorie

### Tier 1 : Priorité Haute (Inscriptions, Examens, Vie Étudiante, Services)

- **Cible :** 1000+ Q/R par catégorie
- **Délai :** 4-5 sessions (12-15 semaines)
- **Équipes :** 3-4 équipes par catégorie
- **Raison :** Besoins critiques des étudiants

### Tier 2 : Priorité Moyenne (Programmes, Infrastructures)

- **Cible :** 500+ Q/R par catégorie
- **Délai :** 3 sessions (9 semaines)
- **Équipes :** 2-3 équipes par catégorie
- **Raison :** Informations importantes mais moins urgentes

### Tier 3 : Priorité Basse (Carrières, Communication, Vie Pratique)

- **Cible :** 400+ Q/R par catégorie
- **Délai :** 2-3 sessions (6-9 semaines)
- **Équipes :** 1-2 équipes par catégorie
- **Raison :** Intéressant mais moins critique

---

## 📁 Types de Fichiers V2

### Fichiers de Documentation (NOUVEAUX)

| Fichier                          | Localisation    | Rôle                       |
| -------------------------------- | --------------- | -------------------------- |
| `categories/README.md`           | Root categories | Décrire toute la structure |
| `categories/INDEX.md`            | Root categories | Navigation rapide          |
| `categories/TEMPLATE.csv`        | Root categories | Modèle pour créer CSV      |
| `docs/GUIDE_CONTRIBUTEURS_V2.md` | phase-1/docs    | Guide complet équipes      |
| `config/PROGRESSION_V2.json`     | phase-1/config  | Tracking des métriques     |

### Fichiers de Données (À REMPLIR)

Emplacement : `phase-1/data/categories/[CATEGORIE]/[SOUS_THEME]/pending/`

**Format :** `categorie_soustheme_equipeX_sessionY.csv`

**Exemple :** `inscriptions_admission_equipe1_session1.csv`

---

## 🚀 Phases de Déploiement

### Phase 1 : Initialisation (Janvier 2026) ✅ COMPLÈTE

- [x] Structure complète créée (52 sous-thèmes)
- [x] 208 dossiers de workflow configurés
- [x] Documentation rédigée
- [x] Modèles fournis
- [x] Guide contributeurs distribué

### Phase 2 : Collecte (Février-Avril 2026)

- [ ] Ateliers collaboratifs lancés
- [ ] CSV commencent à arriver
- [ ] Pré-validation IA en continu
- [ ] Cible : 2000-3000 Q/R brutes

### Phase 3 : Validation (Avril-Mai 2026)

- [ ] Révision échantillonnée
- [ ] Correction des doublets
- [ ] Enrichissement IA
- [ ] Cible : 1500-2000 Q/R validées

### Phase 4 : Intégration (Mai-Juin 2026)

- [ ] Fusion dans BD vectorielle
- [ ] Tests recherche sémantique
- [ ] Optimisation requêtes
- [ ] Cible : 1500-2000 Q/R en production

### Phase 5 : Déploiement Chatbot (Juin 2026)

- [ ] Interface utilisateur
- [ ] Tests utilisateurs
- [ ] Lancement production
- [ ] Monitoring et maintenance

---

## 💾 Espace Disque Requis

### Estimation

```
Catégories           : ~2 KB
Sous-thèmes (52)     : ~52 KB
Dossiers (208)       : ~8 KB
Documents V2         : ~250 KB
Fichiers CSV (5000)  : ~50-100 MB (selon contenu)
----------------------------------------
TOTAL ESTIMÉ         : ~100-150 MB
```

### Avant Optimisation

- Avec métadonnées
- Avec historiques

### Après Optimisation

- Après suppression archives
- Compression si nécessaire

---

## 🔐 Permissions et Accès

### Structure des Droits

```
phase-1/data/categories/

├── Lecture          : Tous les contributeurs
├── Écriture (pending/) : Équipes contributeurs
├── Révision (processing/) : Validateurs
└── Archivage (archived/) : Administrateurs
```

### Groupes d'Utilisateurs

1. **Contributeurs** : Créent et soumettent dans `pending/`
2. **Validateurs** : Déplacent vers `processing/` et `validated/`
3. **Administrateurs** : Gèrent archives et backups
4. **Analystes** : Consultent métriques et stats

---

## 📈 KPIs de Suivi

### À Tracker Mensuellement

```json
{
  "metriques": {
    "qr_pending_total": "Nombre en attente",
    "qr_processing_total": "Nombre en révision",
    "qr_validated_total": "Nombre validé",
    "taux_acceptance": "(validated/total) × 100",
    "vitesse_validation": "jours moyen",
    "categories_completes": "Nombre ≥ cible"
  }
}
```

---

## ✅ Checklist d'Intégration Complète

- [x] Créer 9 répertoires catégories
- [x] Créer 52 sous-répertoires
- [x] Créer 208 dossiers workflow (4 × 52)
- [x] Créer README categories
- [x] Créer INDEX rapide
- [x] Créer TEMPLATE.csv
- [x] Créer GUIDE_CONTRIBUTEURS_V2.md
- [x] Créer PROGRESSION_V2.json
- [x] Créer STRUCTURE_V2_COMPLETE.md (ce fichier)
- [x] Valider arborescence
- [x] Documenter tout
- [x] Prêt pour collecte !

---

## 📞 Support

**Responsable V2** : NKOUMOU Germain  
**Email** : germain.nkoumou@supptic.cm  
**Slack** : #chatbot-faq-v2  
**Docs** : Voir `categories/README.md` et `categories/INDEX.md`

---

**Version** : 2.0 (Janvier 2026)  
**Statut** : ✅ Structure Complète et Prête au Déploiement  
**Prochaine Étape** : Lancer ateliers collaboratifs phase 2
