# Structure des Categories - Phase 2

## Vue d'ensemble

Cette structure organise tous les Q/R en **9 categories majeures** avec leurs **sous-themes respectifs**. Chaque sous-theme contient des fichiers CSV avec les questions et reponses.

## Hiérarchie des Catégories

### 1. **Inscriptions et Admissions** (1_inscriptions_admissions)

- 1a_conditions_admission
- 1b_procedure_enligne
- 1c_documents_requis
- 1d_frais_paiements
- 1e_reinscription_cas_particuliers
- 1f_etudiants_etrangers
- 1g_orientation_choix_filiere
- 1h_cas_particuliers_handicap
- 1i_plateformes_numeriques

### 2. **Examens et Évaluations** (2_examens_evaluations)

- 2a_calendrier_examens
- 2b_modalites
- 2c_notes_bareme
- 2d_rattrapages_dispenses
- 2e_fraude_sanctions
- 2f_publication_resultats
- 2g_preparation_methodologie
- 2h_examens_enligne
- 2i_accessibilite

### 3. **Vie Étudiante** (3_vie_etudiante)

- 3a_clubs_associations
- 3b_logement_etudiant
- 3c_restauration
- 3d_activites_culturelles_sportives
- 3e_sante_accompagnement
- 3f_evenements_academiques
- 3g_vie_quotidienne
- 3h_engagement_citoyen
- 3i_numerique_etudiant

### 4. **Services Administratifs** (4_services_administratifs)

- 4a_bibliotheque_ressources
- 4b_scolarite
- 4c_finances
- 4d_stages_partenariats
- 4e_diplomes_certifications
- 4f_relations_internationales
- 4g_support_informatique
- 4h_archives_memoire
- 4i_communication_officielle

### 5. **Programmes Académiques** (5_programmes_academiques)

- 5a_presentation_filieres
- 5b_organisation_cours
- 5c_encadrement_pedagogique
- 5d_projets_tp

### 6. **Infrastructures et Ressources** (6_infrastructures_ressources)

- 6a_laboratoires
- 6b_internet_plateformes
- 6c_logiciels_licences
- 6d_securite_maintenance

### 7. **Carrières et Insertion Professionnelle** (7_carrieres_insertion)

- 7a_stages_conventions
- 7b_partenariats_entreprises
- 7c_forums_emploi
- 7d_reseau_alumni

### 8. **Communication et Vie Institutionnelle** (8_communication_vie_institutionnelle)

- 8a_canaux_officiels
- 8b_reclamations_mediation
- 8c_actualites_annonces
- 8d_participation_instances

### 9. **Vie Pratique** (9_vie_pratique)

- 9a_transport_accessibilite
- 9b_securite_reglement
- 9c_cout_vie
- 9d_services_annexes

## Workflow des Fichiers CSV

Chaque sous-theme contient des fichiers CSV organisés directement dans le dossier.

```
sous-theme/
├── fichier1.csv
├── fichier2.csv
└── ...
```

## Convention de Nommage

Les fichiers CSV doivent suivre cette nomenclature :

```
categorie_soustheme_equipeX_sessionY.csv
```

### Exemples :

- `inscriptions_conditions_equipe1_session1.csv`
- `examens_modalites_equipe2_session1.csv`
- `vieetudiante_logement_equipe3_session2.csv`
- `services_scolarite_equipe4_session1.csv`
- `programmes_filieres_equipe5_session1.csv`
- `infrastructures_logiciels_equipe6_session1.csv`
- `carrieres_stages_equipe7_session2.csv`
- `communication_canaux_equipe8_session1.csv`
- `viepratique_transport_equipe9_session1.csv`

## Format CSV Standard

```
Question,Reponse,Categorie,SousTheme,Source
```

### Description des colonnes :

| Colonne       | Description                   | Contraintes                                                                                                       |
| ------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Question**  | Formulation claire et concise | Max 200 caractères, mot interrogatif                                                                              |
| **Reponse**   | Réponse précise et complète   | 2-3 phrases maximum                                                                                               |
| **Categorie** | Grande catégorie              | inscriptions, examens, vieetudiante, services, programmes, infrastructures, carrieres, communication, viepratique |
| **SousTheme** | Sous-catégorie précise        | Selon taxonomie définie                                                                                           |
| **Source**    | Origine de l'information      | Site SUP'PTIC, IA, Communiqué, Atelier                                                                            |

## Processus de Traitement

Les fichiers CSV sont traites directement dans leurs dossiers respectifs.
## Objectifs par Catégorie

| Catégorie       | Cible Q/R     | Priorité |
| --------------- | ------------- | -------- |
| Inscriptions    | 1000+         | Haute    |
| Examens         | 1000+         | Haute    |
| Vie Étudiante   | 1000+         | Haute    |
| Services        | 1000+         | Haute    |
| Programmes      | 500+          | Moyenne  |
| Infrastructures | 500+          | Moyenne  |
| Carrières       | 400+          | Moyenne  |
| Communication   | 400+          | Basse    |
| Vie Pratique    | 400+          | Basse    |
| **TOTAL**       | **5000-9000** |          |

## Structure Complète du Projet

```
phase-1/
├── config/              → Configuration et cles
├── data/
│   ├── categories/      → Structure Phase 2 (ce dossier)
│   │   ├── 1_inscriptions_admissions/
│   │   ├── 2_examens_evaluations/
│   │   ├── 3_vie_etudiante/
│   │   ├── 4_services_administratifs/
│   │   ├── 5_programmes_academiques/
│   │   ├── 6_infrastructures_ressources/
│   │   ├── 7_carrieres_insertion/
│   │   ├── 8_communication_vie_institutionnelle/
│   │   ├── 9_vie_pratique/
│   │   ├── category_manager.py  → Outil de gestion
│   │   └── README.md            → Ce fichier
│   └── v1_collecte/     → Archive historique collecte v1
├── scripts/             → Outils de traitement
└── tests/               → Tests unitaires
```

## Utilisation Pratique

### Pour generer des statistiques :

```bash
python category_manager.py count    # Compte Q/R par categorie
python category_manager.py list     # Liste les categories
python category_manager.py cat 1    # Details categorie 1
python category_manager.py check    # Verifie structure
```

## Notes Importantes

- Chaque sous-theme est independant et peut etre traite en parallele
- La structure permet une scalabilite massive
- Les fichiers sont en format CSV universel (compatible Excel, Python, etc.)

---

**Version** : 2.0 (Janvier 2026)
