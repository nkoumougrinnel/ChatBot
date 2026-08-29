#!/usr/bin/env python3
"""Génère le PDF de démonstration SUP'ONE AI."""

import os
import sys
from pathlib import Path

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:
    print("Erreur : La bibliothèque 'fpdf2' est requise.")
    print("Installez-la avec : pip install fpdf2")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = ROOT / "frontend" / "advanced_chat" / "icone.png"
OUTPUT_PATH = ROOT / "docs" / "SUPONE_AI_Demonstration.pdf"

class DemoPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("helvetica", "B", 10)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, "SUP'ONE AI - Assistant Intelligent SUP'PTIC", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

def create_pdf():
    pdf = DemoPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- Page 1: Couverture ---
    pdf.add_page()
    pdf.set_fill_color(7, 15, 31) # DARK palette
    pdf.rect(0, 0, 210, 297, "F")
    
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=75, y=60, w=60)
    
    pdf.set_y(140)
    pdf.set_font("helvetica", "B", 36)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "SUP'ONE AI", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(59, 111, 212) # PRIMARY_LIGHT
    pdf.cell(0, 10, "Assistant Intelligent FAQ", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_y(240)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 10, "Club Informatique SUP'PTIC", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, "Démonstration du Projet - 2026", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 2: Introduction ---
    pdf.add_page()
    pdf.set_text_color(26, 69, 148) # PRIMARY
    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 20, "1. Pourquoi SUP'ONE AI ?", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("helvetica", "", 12)
    content = (
        "Le projet SUP'ONE AI répond à un besoin critique : désengorger les services "
        "d'accueil de SUP'PTIC en automatisant les réponses aux questions récurrentes "
        "(frais de scolarité, inscriptions, examens, vie pratique).\n\n"
        "L'assistant offre une interface moderne, ultra-rapide et disponible en permanence "
        "sur tous les supports (Web, Mobile, PWA)."
    )
    pdf.multi_cell(0, 10, content)
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Objectifs clés :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, "- Centralisation de l'information officielle.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, "- Support multicanal (Navigateur & Application Android).", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, "- Pipeline IA hybride garantissant précision et fluidité.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Page 3: Technologie RAG ---
    pdf.add_page()
    pdf.set_text_color(26, 69, 148)
    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 20, "2. Intelligence Hybride (RAG)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 10, "Contrairement aux chatbots classiques, SUP'ONE AI ne 'devine' pas ses réponses. Il utilise une architecture RAG (Retrieval-Augmented Generation) :")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Niveau 1 & 2 : Précision Chirurgicale", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 8, "Le système interroge d'abord la base FAQ officielle via FAISS (recherche vectorielle) et TF-IDF. Si une correspondance exacte existe, la réponse validée est servie immédiatement.")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Niveau 3 : Synthèse Gemini 1.5 Flash", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 8, "Pour les questions complexes, l'IA récupère les documents pertinents et utilise le modèle Gemini pour synthétiser une réponse naturelle et structurée en streaming SSE.")

    # --- Page 4: Sécurité & RGPD ---
    pdf.add_page()
    pdf.set_text_color(26, 69, 148)
    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 20, "3. Sécurité & Protection (RGPD)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 10, "Conformément aux standards européens et locaux, la plateforme intègre :")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "- Authentification sécurisée :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 8, "Chaque utilisateur dispose d'un espace privé avec historique chiffré et synchronisé via Token JWT.")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 10, "- Maîtrise des données :", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 8, "Possibilité de supprimer l'intégralité de l'historique et anonymisation des données de feedback pour l'amélioration continue du moteur.")

    # --- Page 5: Conclusion ---
    pdf.add_page()
    pdf.set_fill_color(26, 69, 148)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_y(120)
    pdf.set_font("helvetica", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "SUP'ONE AI v2.0", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 16)
    pdf.cell(0, 10, "L'excellence académique par l'IA", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT_PATH))
    print(f"PDF de démonstration généré : {OUTPUT_PATH}")

if __name__ == "__main__":
    create_pdf()