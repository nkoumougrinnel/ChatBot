#!/usr/bin/env python3
"""Génère la présentation PowerPoint SUP'ONE AI — Club Informatique SUP'PTIC."""

from pathlib import Path

from pptx import Presentation
from pptx.oxml import parse_xml
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

# Palette SUP'PTIC
PRIMARY = RGBColor(0x1A, 0x45, 0x94)
PRIMARY_LIGHT = RGBColor(0x3B, 0x82, 0xF6)
DARK = RGBColor(0x07, 0x0F, 0x1F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0x64, 0x74, 0x8B)
ACCENT = RGBColor(0x22, 0xC5, 0x5E)

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "SUPONE_AI_Club_Informatique_SUPPTIC.pptx"
LOGO_PATH = Path(__file__).resolve().parent.parent / "frontend" / "advanced_chat" / "icone.png"


def set_slide_bg(slide, color: RGBColor) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_bar(slide, title: str, subtitle: str = "") -> None:
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(10), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY
    bar.line.fill.background()
    tf = bar.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.5), Inches(1.25), Inches(9), Inches(0.5))
        stf = sub.text_frame
        stf.text = subtitle
        stf.paragraphs[0].font.size = Pt(14)
        stf.paragraphs[0].font.color.rgb = MUTED


def add_bullets(slide, items: list[str], top: float = 1.9, size: int = 18) -> None:
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(8.8), Inches(5))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.level = 0
        p.font.size = Pt(size)
        p.font.color.rgb = DARK
        p.space_after = Pt(10)


def add_two_columns(slide, left_title: str, left_items: list[str], right_title: str, right_items: list[str]) -> None:
    for col, title, items, x in [
        (0, left_title, left_items, 0.5),
        (1, right_title, right_items, 5.2),
    ]:
        hdr = slide.shapes.add_textbox(Inches(x), Inches(1.8), Inches(4.3), Inches(0.4))
        htf = hdr.text_frame
        htf.text = title
        htf.paragraphs[0].font.size = Pt(16)
        htf.paragraphs[0].font.bold = True
        htf.paragraphs[0].font.color.rgb = PRIMARY
        box = slide.shapes.add_textbox(Inches(x), Inches(2.2), Inches(4.3), Inches(4.5))
        tf = box.text_frame
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(14)
            p.font.color.rgb = DARK
            p.space_after = Pt(6)


def set_slide_transition(slide, direction: str = "l") -> None:
    """
    Ajoute une transition de type 'Poussée' (Push) à la diapositive.
    Directions : 'l' (gauche), 'r' (droite), 't' (haut), 'b' (bas).
    """
    sld = slide._element
    # On définit la transition en XML (Push transition)
    transition_xml = (
        f'<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f'<p:push dir="{direction}"/></p:transition>'
    )
    transition = parse_xml(transition_xml)
    sld.insert(0, transition)


def add_logo(slide) -> None:
    """Ajoute le logo SUP'PTIC en bas à droite de la diapositive."""
    if LOGO_PATH.exists():
        # Position : Bas droite (ajusté pour une diapositive de 10x7.5 pouces)
        # Largeur fixée à 0.6 pouce, hauteur proportionnelle
        left = Inches(9.2)
        top = Inches(6.7)
        slide.shapes.add_picture(str(LOGO_PATH), left, top, width=Inches(0.6))


def add_progress_bar(slide, index: int, total: int) -> None:
    """Ajoute une barre de progression visuelle en bas de la diapositive."""
    # Fond de la barre (gris clair)
    full_width = 10
    bg_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.45), Inches(full_width), Inches(0.05)
    )
    bg_bar.fill.solid()
    bg_bar.fill.fore_color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
    bg_bar.line.fill.background()
    
    # Barre de progression (Bleu SUP'PTIC)
    progress_width = (index / total) * full_width
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.45), Inches(progress_width), Inches(0.05)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY_LIGHT
    # Supprimer la bordure
    bar.line.fill.background()


def add_footer(slide, index: int, total: int) -> None:
    """Ajoute un pied de page avec le numéro de diapositive au centre."""
    # Position : Bas centre sur toute la largeur (10 pouces)
    left = Inches(0)
    top = Inches(7.1)
    width = Inches(10)
    height = Inches(0.3)
    
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = f"SUP'ONE AI — Page {index} / {total}"
    p.font.size = Pt(9)
    p.font.color.rgb = MUTED
    p.alignment = PP_ALIGN.CENTER


def slide_title(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, DARK)
    accent = slide.shapes.add_shape(1, Inches(0), Inches(3.2), Inches(10), Inches(0.08))
    accent.fill.solid()
    accent.fill.fore_color.rgb = PRIMARY_LIGHT
    accent.line.fill.background()

    t1 = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(8.8), Inches(1.2))
    tf = t1.text_frame
    tf.text = "SUP'ONE AI"
    tf.paragraphs[0].font.size = Pt(48)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE

    t2 = slide.shapes.add_textbox(Inches(0.6), Inches(2.5), Inches(8.8), Inches(0.8))
    tf2 = t2.text_frame
    tf2.text = "Assistant intelligent FAQ — SUP'PTIC"
    tf2.paragraphs[0].font.size = Pt(22)
    tf2.paragraphs[0].font.color.rgb = PRIMARY_LIGHT

    t3 = slide.shapes.add_textbox(Inches(0.6), Inches(4.8), Inches(8.8), Inches(1))
    tf3 = t3.text_frame
    tf3.text = "Club Informatique SUP'PTIC\nPrésentation projet — 2026"
    for p in tf3.paragraphs:
        p.font.size = Pt(16)
        p.font.color.rgb = MUTED
        p.alignment = PP_ALIGN.LEFT


def slide_context(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Contexte & enjeux")
    add_bullets(
        slide,
        [
            "SUP'PTIC accueille chaque année de nombreux étudiants, parents et visiteurs.",
            "Les mêmes questions reviennent : inscriptions, frais, filières, examens, vie étudiante…",
            "Les services administratifs et pédagogiques sont sollicités de manière répétitive.",
            "Besoin d'un canal d'information accessible 24h/24, fiable et multicanal.",
            "Objectif : réduire la charge informative tout en améliorant l'expérience utilisateur.",
        ],
    )


def slide_solution(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "La solution : SUP'ONE AI")
    add_bullets(
        slide,
        [
            "Chatbot conversationnel dédié à l'établissement SUP'PTIC.",
            "Répond aux questions fréquentes à partir d'une base de FAQ structurée.",
            "Interface moderne type ChatGPT — web, PWA installable et application Android.",
            "Deux moteurs de réponse complémentaires : recherche classique + IA (RAG).",
            "Système de feedback pour améliorer continuellement les réponses.",
            "Déployable sur serveur interne (Docker) ou dans le cloud (Railway + Netlify).",
        ],
    )


def slide_features(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Fonctionnalités clés")
    add_two_columns(
        slide,
        "Pour les utilisateurs",
        [
            "Chat en français, streaming des réponses",
            "Suggestions de questions au démarrage",
            "Thème clair / sombre",
            "Installation PWA (mobile & bureau)",
            "Application Android (APK)",
            "Like / dislike + commentaire",
        ],
        "Pour l'administration",
        [
            "Base FAQ catégorisée (~11 000 entrées)",
            "API REST documentée",
            "Statistiques de satisfaction",
            "Indexation automatique TF-IDF + FAISS",
            "Pipeline RAG avec Gemini (optionnel)",
            "Déploiement Docker, Railway ou VPS",
        ],
    )


def slide_architecture(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Architecture globale", "Séparation frontend / backend / données")
    diagram = slide.shapes.add_textbox(Inches(0.5), Inches(1.7), Inches(9), Inches(4.8))
    tf = diagram.text_frame
    tf.text = (
        "┌─────────────────────────────────────────────────────────┐\n"
        "│  FRONTEND — React 19 + Vite + PWA + Capacitor (Android) │\n"
        "│  Interface ChatGPT · thèmes · feedback · suggestions    │\n"
        "└──────────────────────────┬──────────────────────────────┘\n"
        "                           │ HTTPS / REST / SSE\n"
        "┌──────────────────────────▼──────────────────────────────┐\n"
        "│  BACKEND — Django REST + Gunicorn + PostgreSQL          │\n"
        "│  Phase 1 (/api/)  ·  Gen3 RAG (/api/v2/)                │\n"
        "└──────────────────────────┬──────────────────────────────┘\n"
        "                           │\n"
        "┌──────────────────────────▼──────────────────────────────┐\n"
        "│  DONNÉES — FAQ JSON · vecteurs TF-IDF · index FAISS     │\n"
        "└─────────────────────────────────────────────────────────┘"
    )
    for p in tf.paragraphs:
        p.font.name = "Consolas"
        p.font.size = Pt(13)
        p.font.color.rgb = DARK


def slide_pipeline(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Pipeline Gen3 — RAG en 4 niveaux")
    add_bullets(
        slide,
        [
            "Niveau 1 — Règles conversationnelles : salutations, hors-sujet, intents métier.",
            "Niveau 2 — Recherche sémantique FAISS (embeddings MiniLM-L6-v2).",
            "Niveau 3 — Repli TF-IDF optimisé (gestion mémoire, ~11 000 FAQ).",
            "Niveau 4 — Génération LLM Google Gemini (réponses contextualisées).",
            "Cohérence question ↔ réponse : sélection intelligente + seuils de confiance.",
            "Si Gen3 indisponible → Phase 1 TF-IDF reste pleinement fonctionnelle.",
        ],
        top=1.85,
        size=17,
    )


def slide_tech(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Stack technique")
    add_two_columns(
        slide,
        "Backend",
        [
            "Python 3.13 · Django 4.2 · DRF",
            "scikit-learn · spaCy (fr)",
            "FAISS · sentence-transformers",
            "Google Gemini 1.5 Flash",
            "PostgreSQL · Gunicorn · Whitenoise",
        ],
        "Frontend & DevOps",
        [
            "React 19 · Vite 8 · PWA",
            "Capacitor 7 (APK Android)",
            "Docker Compose (3 services)",
            "Railway · Netlify · GitHub Actions",
            "Nginx · healthchecks · volumes ML",
        ],
    )


def slide_ui(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Interface utilisateur")
    add_bullets(
        slide,
        [
            "Design inspiré de ChatGPT — fil de discussion centré, épuré.",
            "Palette institutionnelle SUP'PTIC : bleu #1A4594, fond #070F1F.",
            "Messages utilisateur en pastille bleue · réponses assistant en texte libre.",
            "Composer type « prompt box » · suggestions en pills cliquables.",
            "Indicateur de statut serveur (en ligne / dégradé / hors ligne).",
            "Expérience identique sur navigateur, PWA installée et APK Android.",
        ],
    )


def slide_deployment(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Déploiement & mise en production")
    add_two_columns(
        slide,
        "Serveur SUP'PTIC (on-premise)",
        [
            "Docker Compose : Postgres + API + Nginx",
            "Volumes persistants (BDD, index FAISS)",
            "Bootstrap : import FAQ + indexation",
            "HTTPS via reverse proxy (Caddy / Certbot)",
            "Doc : docs/DOCKER.md",
        ],
        "Cloud (démonstration / pilote)",
        [
            "Backend : Railway + PostgreSQL",
            "Frontend : Netlify ou Vercel (PWA)",
            "APK Android : build Capacitor local",
            "CI : tests Django + build React",
            "Doc : docs/DEPLOIEMENT.md",
        ],
    )


def slide_demo(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Démonstration & chiffres")
    add_bullets(
        slide,
        [
            "Démarrage local : backend :8001 + frontend :5174",
            "Base FAQ : plus de 11 000 questions/réponses indexées",
            "Catégories : admissions, examens, filières, vie étudiante, règlements…",
            "Tests automatisés : 22 tests Django + suite Gen3/feedback",
            "Exemples de questions : « Comment s'inscrire ? », « Quels sont les frais ? »",
            "Endpoint santé : GET /api/health/ → status, phase1, gen3",
        ],
    )


def slide_section_header(prs: Presentation, title: str) -> None:
    """Ajoute une diapositive d'intermède avec un fond coloré pour séparer les sections."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, PRIMARY)
    t = slide.shapes.add_textbox(Inches(0.5), Inches(3.2), Inches(9), Inches(1.1))
    tf = t.text_frame
    tf.text = title
    p = tf.paragraphs[0]
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER


def slide_security_rgpd(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Sécurité & Protection des données (RGPD)")
    add_bullets(
        slide,
        [
            "Authentification sécurisée : Gestion par jetons (Tokens) et sessions isolées.",
            "Chiffrement des échanges : Communications intégrales via protocole HTTPS.",
            "Droit à l'oubli : Fonctionnalité de suppression complète de l'historique par l'utilisateur.",
            "Confidentialité : Anonymisation des feedbacks et protection des données personnelles.",
            "Conformité RGPD : Transparence, collecte minimale et contrôle des données par l'étudiant.",
            "Sécurisation infrastructure : Protection de la base de données et des accès API.",
        ],
    )


def slide_perspectives(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    add_title_bar(slide, "Perspectives & évolutions")
    add_bullets(
        slide,
        [
            "Intégration au site officiel SUP'PTIC et portail étudiant.",
            "Publication APK sur le Play Store (distribution officielle).",
            "Tableau de bord admin pour gérer les FAQ sans ligne de commande.",
            "Multilingue (français / anglais) pour les partenariats internationaux.",
            "Analyse des questions sans réponse pour enrichir la base.",
            "Renforcement sécurité & conformité (RGPD, logs d'audit).",
        ],
    )


def slide_closing(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, PRIMARY)
    t1 = slide.shapes.add_textbox(Inches(0.6), Inches(2.2), Inches(8.8), Inches(1.2))
    tf = t1.text_frame
    tf.text = "Merci pour votre attention"
    tf.paragraphs[0].font.size = Pt(40)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    t2 = slide.shapes.add_textbox(Inches(0.6), Inches(3.5), Inches(8.8), Inches(1.5))
    tf2 = t2.text_frame
    tf2.text = (
        "Club Informatique SUP'PTIC\n"
        "SUP'ONE AI — Assistant FAQ intelligent\n\n"
        "Documentation : docs/GUIDE_COMPLET.md · docs/DOCKER.md · docs/MOBILE.md"
    )
    for p in tf2.paragraphs:
        p.font.size = Pt(16)
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    slide_title(prs)
    slide_section_header(prs, "I. Introduction & Concept")
    slide_context(prs)
    slide_solution(prs)

    slide_section_header(prs, "II. Architecture & Pipeline")
    slide_features(prs)
    slide_architecture(prs)
    slide_pipeline(prs)

    slide_section_header(prs, "III. Technologies & Design")
    slide_tech(prs)
    slide_ui(prs)

    slide_section_header(prs, "IV. Mise en œuvre & Sécurité")
    slide_deployment(prs)
    slide_demo(prs)
    slide_security_rgpd(prs)
    slide_perspectives(prs)
    slide_closing(prs)

    # Ajout automatique du logo et du numéro de page sur toutes les diapositives
    total_slides = len(prs.slides)
    for i, slide in enumerate(prs.slides, start=1):
        add_logo(slide)
        add_footer(slide, i, total_slides)
        add_progress_bar(slide, i, total_slides)
        
        # On alterne les directions des transitions pour un effet 'intéressant'
        # Droite à gauche pour le corps, Bas en Haut pour les sections clés
        direction = "t" if i % 4 == 0 else "l"
        set_slide_transition(slide, direction)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"Présentation générée : {OUTPUT}")


if __name__ == "__main__":
    main()
