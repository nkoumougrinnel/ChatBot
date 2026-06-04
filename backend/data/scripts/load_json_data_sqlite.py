"""
Script de chargement des données FAQ au format JSON depuis data/json.
Usage: python load_json_data.py
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Configuration Django
BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SKIP_FAQ_VECTORIZER', '1')

import django
from django.db import transaction
from django.db.models import Q

django.setup()

from django.apps import apps
Category = apps.get_model('faq', 'Category')
FAQ = apps.get_model('faq', 'FAQ')
User = apps.get_model('users', 'CustomUser')


def clear_database():
    """Vider les tables FAQ et Category avant l'import et réinitialiser les séquences."""
    print("\n Vidage de la base de données...")
    faq_count = FAQ.objects.count()
    cat_count = Category.objects.count()
    FAQ.objects.all().delete()
    Category.objects.all().delete()
    print(f"  OK Supprimé {faq_count} FAQs et {cat_count} Catégories")
    
    # Réinitialiser les séquences/auto-increment
    from django.db import connection
    cursor = connection.cursor()
    
    # SQLite
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='faq_faq'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='faq_category'")
    print("  OK Réinitialisé les séquences de la BD")
    print("=" * 80)


def create_admin_user():
    """Créer ou réinitialiser le superuser admin."""
    print("\nCréation du superuser admin...")
    
    # Supprimer l'admin existant s'il existe
    User.objects.filter(username='admin').delete()
    
    # Créer le nouvel admin
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin'
    )
    print(f"  OK Superuser admin créé (password: admin)")
    print("=" * 80)


SKIP_FAQ_IMPORT_NAMES = frozenset({
    'conversational_rules.json',
})


def classify_json_for_faq_import(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        if 'conversational_rules' in data:
            return 'conversational_rules'
        return 'unsupported'
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return 'faq_list'
    if isinstance(data, list):
        return 'faq_list'
    return 'unsupported'


def filter_faq_json_files(paths: list[Path]) -> list[Path]:
    kept = []
    for path in paths:
        if path.name in SKIP_FAQ_IMPORT_NAMES:
            print(
                f"[SKIP] {path.name} - regles conversationnelles "
                "(utilise par le chatbot, pas import FAQ)"
            )
            continue
        kind = classify_json_for_faq_import(path)
        if kind == 'conversational_rules':
            print(f"[SKIP] {path.name} - regles conversationnelles")
            continue
        if kind != 'faq_list':
            print(f"[SKIP] {path.name} - format non FAQ")
            continue
        kept.append(path)
    return kept


class FAQJsonImporter:
    """Importateur de données FAQ depuis un fichier JSON."""
    
    def __init__(self, json_path=None):
        self.json_path = json_path
        self.stats = {
            'categories_crees': 0,
            'categories_existantes': 0,
            'faqs_crees': 0,
            'faqs_mises_a_jour': 0,
            'faqs_ignorees': 0,
            'erreurs': 0
        }
        self.categories_cache = {}
        
    def load_json(self, path=None):
        """Charger et valider le fichier JSON."""
        if path:
            self.json_path = Path(path)
        
        if not self.json_path or not self.json_path.exists():
            raise FileNotFoundError(f"Fichier JSON non trouvé: {self.json_path}")
        
        print(f"[FICHIER] Chargement du fichier: {self.json_path.name}")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validation basique
        if not isinstance(data, list):
            raise ValueError("Le fichier JSON doit contenir une liste d'objets FAQ")
        
        print(f"   OK {len(data)} FAQ(s) trouvée(s)")
        return data
    
    def normaliser_chaine(self, texte):
        """Normaliser une chaîne pour éviter les doublons."""
        if not texte:
            return ""
        # Supprimer les espaces superflus et normaliser
        return ' '.join(texte.strip().split())
    
    def get_or_create_categorie(self, nom_categorie):
        """Récupérer ou créer une catégorie avec mise en cache."""
        nom_normalise = self.normaliser_chaine(nom_categorie)
        
        if not nom_normalise:
            nom_normalise = "Non catégorisé"
            print("   [ATTENTION] Catégorie vide, utilisation de 'Non catégorisé'")
        
        # Vérifier le cache
        if nom_normalise in self.categories_cache:
            return self.categories_cache[nom_normalise]
        
        # Chercher dans la base
        try:
            category = Category.objects.get(
                Q(name__iexact=nom_normalise) | 
                Q(name__iexact=nom_normalise.replace('&', 'et'))
            )
            self.stats['categories_existantes'] += 1
            created = False
        except Category.DoesNotExist:
            # Créer la catégorie
            category = Category.objects.create(
                name=nom_normalise,
                description=f"Questions sur {nom_normalise.lower()}",
                active=True
            )
            self.stats['categories_crees'] += 1
            created = True
            print(f"   - Nouvelle catégorie créée: '{nom_normalise[:80]}...'")
        except Category.MultipleObjectsReturned:
            # Prendre la première en cas de doublon
            category = Category.objects.filter(
                Q(name__iexact=nom_normalise) | 
                Q(name__iexact=nom_normalise.replace('&', 'et'))
            ).first()
            self.stats['categories_existantes'] += 1
        
        # Mettre en cache
        self.categories_cache[nom_normalise] = category
        return category
    
    def normaliser_champs_faq(self, item):
        """Normaliser les champs d'une FAQ (supporte ancien et nouveau format)."""
        
        # NOUVEAU FORMAT: Détecter le format intent/examples/responses
        if 'intent' in item and 'examples' in item and 'responses' in item:
            # C'est le nouveau format, retourner None pour traitement spécial
            return None
        
        # ANCIEN FORMAT: Mapper les différentes variations possibles de noms de champs
        mapping_champs = {
            'question': ['question', 'Question', 'QUESTIONS', 'q', 'Q'],
            'reponse': ['reponse', 'Reponse', 'RÉPONSE', 'answer', 'Answer', 'réponse'],
            'categorie': ['categorie', 'Categorie', 'CATEGORIE', 'category', 'Category'],
            'sous_theme': ['sous_theme', 'Sous_theme', 'SOUS_THEME', 'subtheme', 'Subtheme'],
            'source': ['source', 'Source', 'SOURCE', 'src']
        }
        
        faq_normalisee = {}
        
        for champ_dest, variations in mapping_champs.items():
            valeur = None
            for var in variations:
                if var in item and item[var]:
                    valeur = item[var]
                    break
            
            if valeur is not None:
                # Nettoyer la valeur
                if isinstance(valeur, str):
                    valeur = self.normaliser_chaine(valeur)
                faq_normalisee[champ_dest] = valeur
            else:
                # Champ optionnel
                if champ_dest in ['sous_theme', 'source']:
                    faq_normalisee[champ_dest] = ''
                else:
                    # Champ obligatoire manquant
                    raise ValueError(f"Champ obligatoire manquant: {champ_dest}")
        
        return faq_normalisee
    
    def traiter_intent(self, item, idx, total):
        """Traiter un item au nouveau format (intent/examples/responses)."""
        intent = item.get('intent', f'unknown_{idx}')
        examples = item.get('examples', [])
        responses = item.get('responses', [])
        metadata = item.get('metadata', {})
        
        if not examples:
            raise ValueError(f"Intent '{intent}' sans examples")
        
        if not responses:
            raise ValueError(f"Intent '{intent}' sans responses")
        
        # Extraire les métadonnées
        categorie = metadata.get('categorie', 'Non catégorisé')
        sous_theme = metadata.get('sous_theme', '')
        source = metadata.get('source', '')
        
        faqs_creees = 0
        faqs_maj = 0
        faqs_ignorees = 0
        
        # Créer une FAQ pour chaque example
        for ex_idx, example in enumerate(examples):
            # Utiliser la première réponse ou rotation si plusieurs
            response = responses[0] if len(responses) == 1 else responses[ex_idx % len(responses)]
            
            try:
                # Créer l'objet donnee comme l'ancien format
                donnee = {
                    'question': self.normaliser_chaine(example),
                    'reponse': self.normaliser_chaine(response),
                    'categorie': categorie,
                    'sous_theme': sous_theme,
                    'source': source
                }
                
                # Vérifier si existe
                faq_existant = self.faq_existe(donnee['question'])
                
                if faq_existant:
                    modifie, statut = self.mettre_a_jour_faq(faq_existant, donnee)
                    if modifie:
                        faqs_maj += 1
                    else:
                        faqs_ignorees += 1
                else:
                    self.creer_faq(donnee)
                    faqs_creees += 1
                    
            except Exception as e:
                self.stats['erreurs'] += 1
                print(f"   [ERREUR] Erreur pour example '{example[:60]}...': {e}")
        
        # Afficher résumé pour cet intent
        print(f"[OK] [{idx}/{total}] Intent '{intent}': {faqs_creees} créées, {faqs_maj} MAJ, {faqs_ignorees} ignorées")
        
        return faqs_creees, faqs_maj, faqs_ignorees
    
    def faq_existe(self, question):
        """Vérifier si une FAQ existe déjà (insensible à la casse)."""
        question_normalisee = self.normaliser_chaine(question)
        return FAQ.objects.filter(question__iexact=question_normalisee).first()
    
    def mettre_a_jour_faq(self, faq, nouvelle_donnee):
        """Mettre à jour une FAQ existante si nécessaire."""
        modifie = False
        
        # Mettre à jour la catégorie si différente
        nouvelle_categorie = self.get_or_create_categorie(nouvelle_donnee['categorie'])
        if faq.category_id != nouvelle_categorie.id:
            faq.category = nouvelle_categorie
            modifie = True
        
        # Mettre à jour la réponse si vide
        if nouvelle_donnee.get('reponse') and not faq.answer:
            faq.answer = nouvelle_donnee['reponse']
            modifie = True
        
        # Mettre à jour le sous-thème si vide
        if nouvelle_donnee.get('sous_theme') and not faq.subtheme:
            faq.subtheme = nouvelle_donnee['sous_theme']
            modifie = True
        
        # Mettre à jour la source si vide
        if nouvelle_donnee.get('source') and not faq.source:
            faq.source = nouvelle_donnee['source']
            modifie = True
        
        if modifie:
            faq.save()
            self.stats['faqs_mises_a_jour'] += 1
            return True, "Mise à jour"
        else:
            self.stats['faqs_ignorees'] += 1
            return False, "Déjà à jour"
    
    def creer_faq(self, donnee):
        """Créer une nouvelle FAQ."""
        categorie = self.get_or_create_categorie(donnee['categorie'])
        
        faq = FAQ.objects.create(
            question=donnee['question'],
            answer=donnee.get('reponse', ''),
            category=categorie,
            subtheme=donnee.get('sous_theme', ''),
            source=donnee.get('source', ''),
            is_active=True,
            popularity=0
        )
        
        self.stats['faqs_crees'] += 1
        return faq
    
    @transaction.atomic
    def importer(self, json_path=None):
        """Importer toutes les FAQs du fichier JSON (ancien ou nouveau format)."""
        data = self.load_json(json_path)
        total = len(data)
        
        print("\nDÉBUT DE L'IMPORTATION")
        print("=" * 80)
        
        # Détecter le format du fichier
        if data and 'intent' in data[0] and 'examples' in data[0]:
            print("[FORMAT] Format détecté: NOUVEAU (intent/examples/responses)")
            format_type = 'nouveau'
        else:
            print("[FORMAT] Format détecté: ANCIEN (question/reponse)")
            format_type = 'ancien'
        
        print()
        
        for idx, item in enumerate(data, 1):
            try:
                # Traitement selon le format
                if format_type == 'nouveau':
                    # Nouveau format avec intent/examples/responses
                    self.traiter_intent(item, idx, total)
                else:
                    # Ancien format classique
                    donnee = self.normaliser_champs_faq(item)
                    
                    # Vérifier si la FAQ existe déjà
                    faq_existant = self.faq_existe(donnee['question'])
                    
                    if faq_existant:
                        # Mise à jour
                        modifie, statut = self.mettre_a_jour_faq(faq_existant, donnee)
                        prefix = "[MAJ]" if modifie else "[SKIP]"
                        print(f"{prefix} [{idx}/{total}] FAQ #{faq_existant.id}: {donnee['question'][:80]}... [{statut}]")
                    else:
                        # Création
                        faq = self.creer_faq(donnee)
                        print(f"[OK] [{idx}/{total}] FAQ #{faq.id} créée: {donnee['question'][:80]}...")
                
            except Exception as e:
                self.stats['erreurs'] += 1
                print(f"[ERREUR] [{idx}/{total}] ERREUR: {e}")
                print(f"   Donnée: {json.dumps(item, ensure_ascii=False)[:200]}...")
        
        print("\n" + "=" * 80)
        print("[RESUME] RÉSUMÉ DE L'IMPORTATION")
        print("=" * 80)
        print(f" Catégories:")
        print(f"   - Créées: {self.stats['categories_crees']}")
        print(f"   OK Existantes: {self.stats['categories_existantes']}")
        print(f"❓ FAQs:")
        print(f"   [OK] Créées: {self.stats['faqs_crees']}")
        print(f"   [MAJ] Mises à jour: {self.stats['faqs_mises_a_jour']}")
        print(f"   [IGNORE]  Ignorées (déjà à jour): {self.stats['faqs_ignorees']}")
        if self.stats['erreurs'] > 0:
            print(f"   [ERREUR] Erreurs: {self.stats['erreurs']}")
        
        return self.stats
    
    def dry_run(self, json_path=None):
        """Simuler l'import sans écrire en base."""
        data = self.load_json(json_path)
        print("\nSIMULATION D'IMPORT (dry run)")
        print("=" * 80)
        
        categories_uniques = set()
        doublons_questions = set()
        questions_vues = set()
        
        for item in data:
            try:
                donnee = self.normaliser_champs_faq(item)
                categories_uniques.add(donnee['categorie'])
                
                # Détecter les doublons
                if donnee['question'] in questions_vues:
                    doublons_questions.add(donnee['question'][:100])
                else:
                    questions_vues.add(donnee['question'])
                    
            except Exception as e:
                print(f"[ERREUR] Erreur dans l'item: {e}")
        
        print(f"\n[RESUME] Statistiques:")
        print(f"   • Total FAQ dans fichier: {len(data)}")
        print(f"   • Catégories uniques: {len(categories_uniques)}")
        print(f"   • Doublons de questions: {len(doublons_questions)}")
        
        if doublons_questions:
            print("\n[ATTENTION]  Doublons détectés (seront mis à jour):")
            for q in list(doublons_questions)[:5]:
                print(f"   • {q[:100]}...")
        
        print("\n Catégories trouvées:")
        for cat in sorted(categories_uniques):
            print(f"   • {cat}")
        
        return {
            'total': len(data),
            'categories': len(categories_uniques),
            'doublons': len(doublons_questions)
        }


def split_fichier_par_categorie(json_path, output_dir=None):
    """Sépare un fichier JSON unique en plusieurs fichiers par catégorie."""
    if output_dir is None:
        output_dir = Path(json_path).parent / 'split'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Grouper par catégorie
    par_categorie = defaultdict(list)
    for item in data:
        cat = item.get('categorie', 'Non categorise')
        # Nettoyer le nom pour le fichier
        nom_fichier = cat.lower().replace(' ', '_').replace('&', 'et')
        nom_fichier = ''.join(c for c in nom_fichier if c.isalnum() or c == '_')
        par_categorie[nom_fichier].append(item)
    
    fichiers_crees = []
    for nom, items in par_categorie.items():
        output_path = output_dir / f"{nom}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        fichiers_crees.append(output_path)
        print(f"[OK] Créé: {output_path.name} ({len(items)} FAQ)")
    
    return fichiers_crees


def verifier_integrite_base():
    """Vérifier l'intégrité des données en base."""
    print("\n[VERIF] VÉRIFICATION DE L'INTÉGRITÉ")
    print("=" * 80)
    
    # Catégories orphelines
    categories_orphelines = []
    for cat in Category.objects.all():
        if cat.faq_set.count() == 0:
            categories_orphelines.append(cat.name)
    
    if categories_orphelines:
        print(f"[ATTENTION]  Catégories sans FAQ: {len(categories_orphelines)}")
        for cat in categories_orphelines[:10]:
            print(f"   • {cat[:100]}...")
    
    # FAQs sans catégorie valide
    faqs_orphelines = FAQ.objects.filter(category__isnull=True).count()
    if faqs_orphelines > 0:
        print(f"[ERREUR] FAQs sans catégorie: {faqs_orphelines}")
    
    # FAQs en double (même question exacte)
    from django.db.models import Count
    doublons = FAQ.objects.values('question').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if doublons:
        print(f"[ATTENTION]  FAQs en double (même question): {len(doublons)}")
        for d in doublons[:5]:
            print(f"   • {d['question'][:100]}... ({d['count']} fois)")
    
    print("[OK] Vérification terminée")


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chargement des FAQs depuis data/json')
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans import')
    parser.add_argument('--split', action='store_true', help='Séparer le fichier par catégorie')
    parser.add_argument('--verify', action='store_true', help='Vérifier l\'intégrité de la base')
    parser.add_argument('--skip-clear', action='store_true', help='Ne pas vider la base avant import')
    
    args = parser.parse_args()
    
    # Trouver le répertoire data/json
    data_json_dir = Path(__file__).resolve().parent.parent / 'json'
    
    if not data_json_dir.exists():
        print(f"[ERREUR] Répertoire non trouvé: {data_json_dir}")
        return
    
    all_json = sorted(data_json_dir.glob('*.json'))
    json_files = filter_faq_json_files(all_json)
    
    if not all_json:
        print(f"[ERREUR] Aucun fichier JSON trouvé dans {data_json_dir}")
        return
    if not json_files:
        print(f"[ERREUR] Aucun fichier FAQ importable dans {data_json_dir}")
        return
    
    print(f"[DOSSIER] Répertoire data/json: {data_json_dir}")
    print(f"[FICHIER] Fichiers FAQ à importer: {len(json_files)} / {len(all_json)}")
    for f in json_files:
        print(f"   • {f.name}")
    
    # Mode vérification
    if args.verify:
        verifier_integrite_base()
        return
    
    # Mode import
    importer = FAQJsonImporter()
    
    # Vider la base (sauf si skip-clear)
    if not args.skip_clear:
        clear_database()
        #create_admin_user()
    
    # Importer tous les fichiers JSON
    total_stats = {
        'categories_crees': 0,
        'categories_existantes': 0,
        'faqs_crees': 0,
        'faqs_mises_a_jour': 0,
        'faqs_ignorees': 0,
        'erreurs': 0
    }
    
    print("\nDÉBUT DE L'IMPORTATION DES FICHIERS JSON")
    print("=" * 80)
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"\n[FICHIER] [{idx}/{len(json_files)}] Import de: {json_file.name}")
        print("-" * 80)
        
        if args.dry_run:
            importer.dry_run(json_file)
        else:
            stats = importer.importer(json_file)
            # Cumuler les statistiques
            for key in total_stats:
                total_stats[key] += stats[key]
    
    # Afficher le résumé final si pas de dry-run
    if not args.dry_run:
        print("\n" + "=" * 80)
        print("[RESUME] RÉSUMÉ FINAL DE L'IMPORTATION")
        print("=" * 80)
        print(f" Catégories:")
        print(f"   - Créées: {total_stats['categories_crees']}")
        print(f"   OK Existantes: {total_stats['categories_existantes']}")
        print(f"❓ FAQs:")
        print(f"   [OK] Créées: {total_stats['faqs_crees']}")
        print(f"   [MAJ] Mises à jour: {total_stats['faqs_mises_a_jour']}")
        print(f"   [IGNORE]  Ignorées: {total_stats['faqs_ignorees']}")
        if total_stats['erreurs'] > 0:
            print(f"   [ERREUR] Erreurs: {total_stats['erreurs']}")
        
        verifier_integrite_base()


if __name__ == '__main__':
    main()