#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Navigator pour Structure V2 - ChatBot FAQ SUP'PTIC
Utilise: python cli_navigator.py [commande]
"""

import os
import json
from pathlib import Path
from datetime import datetime

class CategoryNavigator:
    
    BASE_PATH = Path(__file__).parent.absolute()
    
    CATEGORIES = {
        "1": {
            "name": "Inscriptions et Admissions",
            "path": "1_inscriptions_admissions",
            "cible": 1000,
            "priorite": "Haute"
        },
        "2": {
            "name": "Examens et Évaluations",
            "path": "2_examens_evaluations",
            "cible": 1000,
            "priorite": "Haute"
        },
        "3": {
            "name": "Vie Étudiante",
            "path": "3_vie_etudiante",
            "cible": 1000,
            "priorite": "Haute"
        },
        "4": {
            "name": "Services Administratifs",
            "path": "4_services_administratifs",
            "cible": 1000,
            "priorite": "Haute"
        },
        "5": {
            "name": "Programmes Académiques",
            "path": "5_programmes_academiques",
            "cible": 500,
            "priorite": "Moyenne"
        },
        "6": {
            "name": "Infrastructures et Ressources",
            "path": "6_infrastructures_ressources",
            "cible": 500,
            "priorite": "Moyenne"
        },
        "7": {
            "name": "Carrières et Insertion",
            "path": "7_carrieres_insertion",
            "cible": 400,
            "priorite": "Moyenne"
        },
        "8": {
            "name": "Communication et Vie Institutionnelle",
            "path": "8_communication_vie_institutionnelle",
            "cible": 400,
            "priorite": "Basse"
        },
        "9": {
            "name": "Vie Pratique",
            "path": "9_vie_pratique",
            "cible": 400,
            "priorite": "Basse"
        }
    }
    
    def list_categories(self):
        """Afficher toutes les catégories"""
        print("\n" + "="*70)
        print("📚 CATÉGORIES DISPONIBLES - Phase 1 V2")
        print("="*70 + "\n")
        
        total_cible = 0
        for num, info in self.CATEGORIES.items():
            print(f"[{num}] {info['name']}")
            print(f"    Path: {info['path']}")
            print(f"    Cible: {info['cible']} Q/R | Priorité: {info['priorite']}")
            total_cible += info['cible']
            print()
        
        print(f"TOTAL CIBLE: {total_cible} Q/R\n")
    
    def list_subcategories(self, cat_num):
        """Lister les sous-thèmes d'une catégorie"""
        if cat_num not in self.CATEGORIES:
            print(f"❌ Catégorie {cat_num} non trouvée")
            return
        
        cat_info = self.CATEGORIES[cat_num]
        cat_path = self.BASE_PATH / cat_info['path']
        
        if not cat_path.exists():
            print(f"❌ Dossier {cat_path} n'existe pas")
            return
        
        print(f"\n{'='*70}")
        print(f"📂 {cat_info['name']}")
        print(f"{'='*70}\n")
        
        subdirs = sorted([d.name for d in cat_path.iterdir() if d.is_dir()])
        
        for subdir in subdirs:
            subpath = cat_path / subdir
            # Compter les fichiers
            pending = len(list((subpath / "pending").glob("*.csv"))) if (subpath / "pending").exists() else 0
            processing = len(list((subpath / "processing").glob("*.csv"))) if (subpath / "processing").exists() else 0
            validated = len(list((subpath / "validated").glob("*.csv"))) if (subpath / "validated").exists() else 0
            
            print(f"  {subdir}/")
            print(f"    pending: {pending} | processing: {processing} | validated: {validated}")
    
    def count_files(self):
        """Compter tous les fichiers CSV"""
        print(f"\n{'='*70}")
        print("📊 STATISTIQUES FICHIERS CSV")
        print(f"{'='*70}\n")
        
        total_pending = 0
        total_processing = 0
        total_validated = 0
        total_archived = 0
        
        for cat_num, cat_info in self.CATEGORIES.items():
            cat_path = self.BASE_PATH / cat_info['path']
            
            if not cat_path.exists():
                continue
            
            pending = len(list(cat_path.glob("*/pending/*.csv")))
            processing = len(list(cat_path.glob("*/processing/*.csv")))
            validated = len(list(cat_path.glob("*/validated/*.csv")))
            archived = len(list(cat_path.glob("*/archived/*.csv")))
            
            total_pending += pending
            total_processing += processing
            total_validated += validated
            total_archived += archived
            
            if pending + processing + validated + archived > 0:
                print(f"[{cat_num}] {cat_info['name'][:40]:40} → "
                      f"P:{pending} | R:{processing} | V:{validated} | A:{archived}")
        
        total_files = total_pending + total_processing + total_validated + total_archived
        total_qr = (total_pending + total_processing + total_validated + total_archived) * 30  # Moyenne 30 Q/R par fichier
        
        print(f"\n{'─'*70}")
        print(f"TOTAUX:")
        print(f"  Pending    : {total_pending} fichiers")
        print(f"  Processing : {total_processing} fichiers")
        print(f"  Validated  : {total_validated} fichiers")
        print(f"  Archived   : {total_archived} fichiers")
        print(f"  ─" * 35)
        print(f"  TOTAL      : {total_files} fichiers (~{total_qr} Q/R estimées)")
        print()
    
    def check_structure(self):
        """Vérifier que la structure est correcte"""
        print(f"\n{'='*70}")
        print("✅ VÉRIFICATION STRUCTURE V2")
        print(f"{'='*70}\n")
        
        expected_dirs = 0
        found_dirs = 0
        
        for cat_num, cat_info in self.CATEGORIES.items():
            cat_path = self.BASE_PATH / cat_info['path']
            
            if cat_path.exists():
                print(f"✅ [{cat_num}] {cat_info['name'][:40]:40} → PRÉSENT")
                found_dirs += 1
            else:
                print(f"❌ [{cat_num}] {cat_info['name'][:40]:40} → MANQUANT")
            
            expected_dirs += 1
        
        print(f"\n{'─'*70}")
        print(f"Catégories trouvées: {found_dirs}/{expected_dirs}")
        
        if found_dirs == expected_dirs:
            print("✅ Structure V2 COMPLÈTE et OPÉRATIONNELLE")
        else:
            print(f"⚠️  Structure incomplète: {expected_dirs - found_dirs} catégories manquantes")
        
        print()
    
    def show_help(self):
        """Afficher l'aide"""
        print(f"\n{'='*70}")
        print("🆘 AIDE CLI - Structure V2 ChatBot FAQ")
        print(f"{'='*70}\n")
        
        print("USAGE: python cli_navigator.py [commande]\n")
        
        print("COMMANDES:")
        print("  list              → Lister toutes les catégories")
        print("  stats             → Voir statistiques fichiers CSV")
        print("  check             → Vérifier intégrité structure")
        print("  cat [NUM]         → Afficher sous-thèmes catégorie N")
        print("  help              → Afficher cette aide")
        print("\nEXEMPLES:")
        print("  python cli_navigator.py list")
        print("  python cli_navigator.py cat 1")
        print("  python cli_navigator.py stats")
        print("\n")

def main():
    import sys
    
    nav = CategoryNavigator()
    
    if len(sys.argv) < 2:
        nav.show_help()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        nav.list_categories()
    elif command == "stats":
        nav.count_files()
    elif command == "check":
        nav.check_structure()
    elif command == "cat":
        if len(sys.argv) < 3:
            print("❌ Usage: python cli_navigator.py cat [NUMERO]")
            print("Exemple: python cli_navigator.py cat 1")
            return
        nav.list_subcategories(sys.argv[2])
    elif command == "help":
        nav.show_help()
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Tapez: python cli_navigator.py help")

if __name__ == "__main__":
    main()
