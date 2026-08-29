"""
Module de recherche FAQ - VERSION SIMPLIFIÉE v2.1 (CORRIGÉE)
Conçu pour 6500+ FAQs avec 1GB RAM (Railway: 1 worker, 2 threads)

ARCHITECTURE SIMPLIFIÉE (3 NIVEAUX):
═══════════════════════════════════════════════════════════════════════

NIVEAU 0: RÈGLES CONVERSATIONNELLES (JSON externe)
    Pattern matching simple, AVANT vectorisation
    Règles chargées depuis conversational_rules.json
    Performance: <5ms, RAM: 0 MB
    Résout: ~30% des requêtes

NIVEAU 1: CATÉGORIES PAR POPULARITÉ + CACHE
    Traite catégories par ordre de popularité décroissante
    1 catégorie à la fois (économise RAM)
    Cache: dernière catégorie avec meilleur score
    Commence par cache, puis catégories populaires
    Stop dès que score d'une catégorie = 0 (plus rien à trouver)
    Performance: <2s, RAM: 40-60 MB
    Résout: ~60% des requêtes

NIVEAU 2: FALLBACK GLOBAL
    Si aucune catégorie n'a donné de résultat
    Scan toutes catégories (batch de 3)
    Performance: <5s, RAM: 60-80 MB
    Résout: ~10% des requêtes

═══════════════════════════════════════════════════════════════════════
"""

import logging
import numpy as np
import json
from pathlib import Path
from django.db import models
from django.db.models import Count, Sum
from faq.models import FAQ, FAQVector, Category
from chatbot.vectorization import compute_tfidf_vector
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION GLOBALE
# ═══════════════════════════════════════════════════════════════════════

# Chemin du fichier JSON des règles conversationnelles
RULES_JSON_PATH = Path(__file__).parent.parent / 'data' / 'json' / 'conversational_rules.json'

# Seuil pour considérer un score comme bon
GOOD_SCORE_THRESHOLD = 0.7

# Cache global: dernière catégorie avec meilleur score
_CATEGORY_CACHE = {
    'category_id': None,
    'category_name': None,
    'last_score': 0.0
}


# ═══════════════════════════════════════════════════════════════════════
# CHARGEMENT RÈGLES CONVERSATIONNELLES
# ═══════════════════════════════════════════════════════════════════════

def load_conversational_rules():
    """
    Charger les règles conversationnelles depuis le fichier JSON.
    Gère les formats Liste [] et Dictionnaire {"conversational_rules": []}.
    
    Returns:
        list: Liste de règles
    """
    try:
        if RULES_JSON_PATH.exists():
            with open(RULES_JSON_PATH, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                # CORRECTION: Vérifier si data est une liste ou un dictionnaire
                if isinstance(data, list):
                    return data
                return data.get('conversational_rules', [])
        else:
            logger.warning("Fichier de règles non trouvé: %s", RULES_JSON_PATH)
            return []
    except Exception as e:
        logger.warning("Erreur chargement règles: %s", e)
        return []


# Charger les règles au démarrage du module
CONVERSATIONAL_RULES = load_conversational_rules()


# ═══════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════

def compute_similarity_batch(user_vec: np.ndarray, 
                             user_norm: float,
                             faq_vectors: List) -> List[Tuple[FAQ, float]]:
    """
    Calculer les similarités cosinus pour un batch de FAQVectors.
    """
    if not faq_vectors or user_norm == 0:
        return []
    
    # Construire matrice de vecteurs FAQ
    faqs = []
    norms = []
    vectors = []
    
    for faq_vec in faq_vectors:
        faqs.append(faq_vec.faq)
        norms.append(faq_vec.norm)
        vectors.append(faq_vec.tfidf_vector)
    
    # Conversion en numpy arrays (float32 pour économiser RAM)
    faq_matrix = np.array(vectors, dtype=np.float32)
    faq_norms = np.array(norms, dtype=np.float32)
    user_vec_f32 = user_vec.astype(np.float32)
    
    # Calcul vectorisé des similarités cosinus
    dot_products = faq_matrix @ user_vec_f32
    scores = dot_products / (faq_norms * user_norm)
    scores = np.clip(scores, 0.0, 1.0)
    
    # Créer liste de résultats
    results = [(faqs[i], float(scores[i])) for i in range(len(faqs))]
    
    # Trier par score décroissant
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Libérer mémoire explicitement
    del faq_matrix, faq_norms, vectors, scores, dot_products
    
    return results


# ═══════════════════════════════════════════════════════════════════════
# NIVEAU 0: RÈGLES CONVERSATIONNELLES
# ═══════════════════════════════════════════════════════════════════════

def match_conversational_rule(question: str) -> Optional[str]:
    """
    NIVEAU 0: Matcher une question contre les règles conversationnelles.
    Supporte les formats de clés: intent/patterns/response ET question/exemples/reponse_enrichie.
    """
    question_lower = question.lower().strip()
    
    # Chercher un match dans chaque règle
    for rule in CONVERSATIONAL_RULES:
        # Support multi-format pour les clés
        intent = rule.get('intent') or rule.get('id') or 'unknown'
        
        # Patterns: cherche 'patterns' ou 'exemples' ou la 'question' elle-même
        patterns = rule.get('patterns', []) or rule.get('exemples', [])
        main_q = rule.get('question')
        if main_q:
            if isinstance(patterns, list):
                patterns.append(main_q)
            else:
                patterns = [main_q]
                
        # Response: cherche 'response' ou 'reponse_enrichie' ou le premier de 'responses'
        response = (rule.get('response') or 
                   rule.get('reponse_enrichie') or 
                   (rule.get('responses', []) and rule.get('responses')[0]) or 
                   '')
        
        if not patterns or not response:
            continue

        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            pattern_norm = pattern.lower().strip()
            if pattern_norm and pattern_norm in question_lower:
                logger.debug(f"[Similarity L0] RÈGLE '{intent}' (match: '{pattern_norm}')")
                return response
    
    return None


# ═══════════════════════════════════════════════════════════════════════
# NIVEAU 1: CATÉGORIES PAR POPULARITÉ + CACHE
# ═══════════════════════════════════════════════════════════════════════

def get_categories_by_popularity():
    """
    Récupérer les catégories triées par popularité décroissante.
    """
    categories = Category.objects.filter(active=True).annotate(
        total_popularity=Sum('faq__popularity'),
        faq_count=Count('faq', filter=models.Q(faq__is_active=True))
    ).filter(faq_count__gt=0).order_by('-total_popularity')
    
    return list(categories)


def search_in_category(category: Category, user_vec: np.ndarray, user_norm: float,
                      top_k: int = 3) -> Tuple[List[Tuple[FAQ, float]], float]:
    """
    Rechercher dans une catégorie spécifique.
    """
    category_vectors = FAQVector.objects.filter(
        faq__category=category,
        faq__is_active=True
    ).select_related('faq').only(
        'tfidf_vector', 'norm',
        'faq__id', 'faq__question', 'faq__answer', 'faq__popularity'
    )
    
    if not category_vectors.exists():
        return [], 0.0
    
    results = compute_similarity_batch(user_vec, user_norm, list(category_vectors))
    
    if not results:
        return [], 0.0
    
    best_score = results[0][1]
    return results[:top_k], best_score


def search_by_popularity_with_cache(user_vec: np.ndarray, user_norm: float,
                                    top_k: int = 3) -> Optional[List[Dict]]:
    """
    NIVEAU 1: Recherche par catégories populaires avec cache.
    """
    global _CATEGORY_CACHE
    
    logger.debug(f"[Similarity L1] Recherche par catégories populaires...")
    
    best_results = None
    best_score = 0.0
    best_category = None
    
    categories = get_categories_by_popularity()
    
    if not categories:
        logger.debug("[Similarity L1] Aucune catégorie active trouvée")
        return None
    
    # 1. D'ABORD: Vérifier le cache
    if _CATEGORY_CACHE['category_id']:
        logger.debug(f"[Similarity L1] Vérification cache: '{_CATEGORY_CACHE['category_name']}'")
        
        try:
            cached_category = Category.objects.get(id=_CATEGORY_CACHE['category_id'])
            results, score = search_in_category(cached_category, user_vec, user_norm, top_k)
            
            if score > 0:
                logger.debug(f"[Similarity L1] Cache: score={score:.3f}")
                best_results = results
                best_score = score
                best_category = cached_category
                
                if score >= GOOD_SCORE_THRESHOLD:
                    logger.debug(f"[Similarity L1] TROUVÉ dans cache (score ≥ {GOOD_SCORE_THRESHOLD})")
                    return [{'faq': faq, 'score': s} for faq, s in best_results]
        
        except Category.DoesNotExist:
            logger.debug("[Similarity L1] Catégorie en cache n'existe plus")
            _CATEGORY_CACHE = {'category_id': None, 'category_name': None, 'last_score': 0.0}
    
    # 2. ENSUITE: Parcourir catégories par popularité
    logger.debug(f"[Similarity L1] Traitement de {len(categories)} catégories...")
    
    for category in categories:
        if _CATEGORY_CACHE['category_id'] == category.id:
            continue
        
        logger.debug(f"[Similarity L1] Catégorie: '{category.name}'")
        results, score = search_in_category(category, user_vec, user_norm, top_k)
        
        if score == 0:
            break
        
        logger.debug(f"[Similarity L1] Score: {score:.3f}")
        
        if score > best_score:
            best_results = results
            best_score = score
            best_category = category
            
            if score >= GOOD_SCORE_THRESHOLD:
                logger.debug(f"[Similarity L1] TROUVÉ (score ≥ {GOOD_SCORE_THRESHOLD})")
                break
    
    # 3. Mettre à jour le cache
    if best_category:
        _CATEGORY_CACHE = {
            'category_id': best_category.id,
            'category_name': best_category.name,
            'last_score': best_score
        }
        logger.debug(f"[Similarity L1] Cache mis à jour: '{best_category.name}' (score: {best_score:.3f})")
    
    # 4. Retourner meilleur résultat trouvé
    if best_results and best_score > 0:
        logger.debug(f"[Similarity L1] Meilleur résultat: {best_score:.3f} dans '{best_category.name}'")
        return [{'faq': faq, 'score': s} for faq, s in best_results]
    
    logger.debug("[Similarity L1] Aucun résultat trouvé")
    return None


# ═══════════════════════════════════════════════════════════════════════
# NIVEAU 2: FALLBACK GLOBAL
# ═══════════════════════════════════════════════════════════════════════

def search_fallback_global(user_vec: np.ndarray, user_norm: float,
                          top_k: int = 3) -> List[Dict]:
    """
    NIVEAU 2: Fallback - recherche dans TOUTES les catégories.
    """
    logger.debug(f"[Similarity L2] Fallback global...")
    
    all_vectors = FAQVector.objects.filter(
        faq__is_active=True
    ).select_related('faq', 'faq__category').only(
        'tfidf_vector', 'norm',
        'faq__id', 'faq__question', 'faq__answer', 'faq__category__name'
    )
    
    # Compter une seule fois au lieu de 3 queries séparées
    total = all_vectors.count()
    if total == 0:
        logger.debug("[Similarity L2] Aucune FAQ active")
        return []
    
    logger.debug(f"[Similarity L2] Recherche dans {total} FAQs...")
    
    batch_size = 500
    best_results = []
    best_score = 0.0
    
    for i in range(0, total, batch_size):
        batch = list(all_vectors[i:i+batch_size])
        results = compute_similarity_batch(user_vec, user_norm, batch)
        
        if results and results[0][1] > best_score:
            best_results = results[:top_k]
            best_score = results[0][1]
    
    if best_results:
        logger.debug(f"[Similarity L2] Meilleur score global: {best_score:.3f}")
        return [{'faq': faq, 'score': s} for faq, s in best_results]
    
    logger.debug("[Similarity L2] Aucun résultat trouvé")
    return []


# ═══════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════

def find_best_faq(question: str, top_k: int = 3, min_score: float = 0.0) -> List[Dict]:
    """
    Fonction principale de recherche FAQ.
    """
    logger.debug("=" * 70)
    logger.debug(f"[Similarity] RECHERCHE - '{question[:50]}...'")
    logger.debug("=" * 70)
    
    # NIVEAU 0: RÈGLES CONVERSATIONNELLES
    logger.debug("[Similarity L0] Vérification règles...")
    direct_response = match_conversational_rule(question)
    
    if direct_response:
        logger.debug("[Similarity L0] RÉPONSE DIRECTE")
        logger.debug("=" * 70)
        
        virtual_faq = type('VirtualFAQ', (), {
            'id': 0,
            'question': question,
            'answer': direct_response,
            'category': type('Category', (), {'name': 'conversationnel'})(),
            'popularity': 999
        })()
        
        return [{'faq': virtual_faq, 'score': 1.0}]
    
    logger.debug("[Similarity L0] Aucune règle ne correspond")
    
    # VECTORISATION
    logger.debug("[Similarity] Vectorisation...")
    user_vec, user_norm = compute_tfidf_vector(question)
    
    if user_norm == 0:
        logger.debug("[Similarity] Vecteur nul (mots inconnus)")
        logger.debug("=" * 70)
        
        virtual_faq = type('VirtualFAQ', (), {
            'id': 0,
            'question': question,
            'answer': "Je n'ai pas compris votre question. Pouvez-vous la reformuler avec plus de détails ?",
            'category': type('Category', (), {'name': 'système'})(),
            'popularity': 0
        })()
        
        return [{'faq': virtual_faq, 'score': 0.0}]
    
    # NIVEAU 1: CATÉGORIES PAR POPULARITÉ + CACHE
    results = search_by_popularity_with_cache(user_vec, user_norm, top_k)
    
    if results:
        logger.debug("[Similarity] TROUVÉ AU NIVEAU 1")
        logger.debug("=" * 70)
        return [r for r in results if r['score'] >= min_score]
    
    # NIVEAU 2: FALLBACK GLOBAL
    logger.debug("[Similarity] NIVEAU 2 (Fallback)...")
    results = search_fallback_global(user_vec, user_norm, top_k)
    
    logger.debug("[Similarity] RECHERCHE TERMINÉE")
    logger.debug("=" * 70)
    
    return [r for r in results if r['score'] >= min_score]


# ═══════════════════════════════════════════════════════════════════════
# COMPATIBILITÉ
# ═══════════════════════════════════════════════════════════════════════

def compute_cosine_similarity(vec1, vec2):
    """Fonction de compatibilité avec ancien code."""
    vec1 = np.asarray(vec1, dtype=np.float32)
    vec2 = np.asarray(vec2, dtype=np.float32)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    score = float(np.dot(vec1, vec2) / (norm1 * norm2))
    return max(0.0, min(1.0, score))
