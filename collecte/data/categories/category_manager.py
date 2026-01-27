#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Category Manager - Gestion structure Phase 2 ChatBot FAQ
Usage: python category_manager.py [commande]
"""

import os
from pathlib import Path
from datetime import datetime

class CategoryManager:
    
    BASE_PATH = Path(__file__).parent.absolute()
    
    CATEGORIES = {
        "1": {
            "name": "Inscriptions et Admissions",
            "path": "1_inscriptions_admissions",
        },
        "2": {
            "name": "Examens et Evaluations",
            "path": "2_examens_evaluations",
        },
        "3": {
            "name": "Vie Etudiante",
            "path": "3_vie_etudiante",
        },
        "4": {
            "name": "Services Administratifs",
            "path": "4_services_administratifs",
        },
        "5": {
            "name": "Programmes Academiques",
            "path": "5_programmes_academiques",
        },
        "6": {
            "name": "Infrastructures et Ressources",
            "path": "6_infrastructures_ressources",
        },
        "7": {
            "name": "Carrieres et Insertion",
            "path": "7_carrieres_insertion",
        },
        "8": {
            "name": "Communication et Vie Institutionnelle",
            "path": "8_communication_vie_institutionnelle",
        },
        "9": {
            "name": "Vie Pratique",
            "path": "9_vie_pratique",
        }
    }
    
    def count_csv_rows(self, filepath):
        """Compter le nombre de lignes (Q/R) dans un fichier CSV"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return max(0, len(lines) - 1)  # Soustraire header
        except:
            return 0
    
    def list_categories(self):
        """Afficher toutes les categories"""
        print("\n" + "="*80)
        print("CATEGORIES DISPONIBLES - Phase 2")
        print("="*80 + "\n")
        
        for num, info in self.CATEGORIES.items():
            cat_path = self.BASE_PATH / info['path']
            exists = "[OK]" if cat_path.exists() else "[MANQUANT]"
            print("[{num}] {name:45} {status}".format(
                num=num,
                name=info['name'],
                status=exists
            ))
        print()
    
    def list_subcategories(self, cat_num):
        """Lister les sous-themes d'une categorie"""
        if cat_num not in self.CATEGORIES:
            print("[ERREUR] Categorie {0} non trouvee".format(cat_num))
            return
        
        cat_info = self.CATEGORIES[cat_num]
        cat_path = self.BASE_PATH / cat_info['path']
        
        if not cat_path.exists():
            print("[ERREUR] Dossier {0} n'existe pas".format(cat_path))
            return
        
        print("\n" + "="*80)
        print("[{0}] {1}".format(cat_num, cat_info['name']))
        print("="*80 + "\n")
        
        subdirs = sorted([d.name for d in cat_path.iterdir() if d.is_dir()])
        
        for subdir in subdirs:
            subpath = cat_path / subdir
            csv_files = list(subpath.glob("*.csv"))
            total_rows = sum(self.count_csv_rows(f) for f in csv_files)
            
            print("  {name:50} | Fichiers: {count:2} | Q/R: {qr}".format(
                name=subdir,
                count=len(csv_files),
                qr=total_rows
            ))
        print()
    
    def count_all_qr(self):
        """Compter toutes les Q/R du projet"""
        print("\n" + "="*80)
        print("STATISTIQUES Q/R PAR CATEGORIE")
        print("="*80 + "\n")
        
        totals = {}
        grand_total_files = 0
        grand_total_qr = 0
        
        for cat_num, cat_info in self.CATEGORIES.items():
            cat_path = self.BASE_PATH / cat_info['path']
            
            if not cat_path.exists():
                continue
            
            cat_files = 0
            cat_qr = 0
            
            for subdir in cat_path.iterdir():
                if subdir.is_dir():
                    csv_files = list(subdir.glob("*.csv"))
                    cat_files += len(csv_files)
                    cat_qr += sum(self.count_csv_rows(f) for f in csv_files)
            
            if cat_files > 0:
                totals[cat_num] = {"files": cat_files, "qr": cat_qr}
                grand_total_files += cat_files
                grand_total_qr += cat_qr
                print("[{num}] {name:40} | {files:3} fichiers | {qr:5} Q/R".format(
                    num=cat_num,
                    name=cat_info['name'],
                    files=cat_files,
                    qr=cat_qr
                ))
        
        print("\n" + "-"*80)
        print("TOTAL GENERAL: {0} fichiers | {1} Q/R".format(grand_total_files, grand_total_qr))
        print()
    
    def check_structure(self):
        """Verifier que la structure est correcte"""
        print("\n" + "="*80)
        print("VERIFICATION STRUCTURE")
        print("="*80 + "\n")
        
        found = 0
        expected = len(self.CATEGORIES)
        
        for cat_num, cat_info in self.CATEGORIES.items():
            cat_path = self.BASE_PATH / cat_info['path']
            
            if cat_path.exists():
                print("[OK] [{num}] {name}".format(num=cat_num, name=cat_info['name']))
                found += 1
            else:
                print("[MANQUANT] [{num}] {name}".format(num=cat_num, name=cat_info['name']))
        
        print("\n" + "-"*80)
        print("Categories trouvees: {0}/{1}".format(found, expected))
        
        if found == expected:
            print("Structure complete et operationnelle")
        else:
            print("Attention: {0} categories manquantes".format(expected - found))
        print()
    
    def show_help(self):
        """Afficher l'aide"""
        print("\n" + "="*80)
        print("CATEGORY MANAGER - Structure Phase 2 ChatBot FAQ")
        print("="*80 + "\n")
        
        print("USAGE: python category_manager.py [commande]\n")
        
        print("COMMANDES:")
        print("  list       → Lister toutes les categories")
        print("  count      → Compter Q/R par categorie")
        print("  check      → Verifier structure integrite")
        print("  cat NUM    → Afficher sous-themes categorie N")
        print("  help       → Afficher cette aide")
        print("\nEXEMPLES:")
        print("  python category_manager.py list")
        print("  python category_manager.py cat 1")
        print("  python category_manager.py count")
        print()

def main():
    import sys
    
    mgr = CategoryManager()
    
    if len(sys.argv) < 2:
        mgr.show_help()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        mgr.list_categories()
    elif command == "count":
        mgr.count_all_qr()
    elif command == "check":
        mgr.check_structure()
    elif command == "cat":
        if len(sys.argv) < 3:
            print("[ERREUR] Usage: python category_manager.py cat [NUMERO]")
            print("Exemple: python category_manager.py cat 1")
            return
        mgr.list_subcategories(sys.argv[2])
    elif command == "help":
        mgr.show_help()
    else:
        print("[ERREUR] Commande inconnue: {0}".format(command))
        print("Tapez: python category_manager.py help")

if __name__ == "__main__":
    main()
