"""
Signaux Django pour l'app FAQ.

Recalcule les poids et scores des vecteurs suite aux feedbacks utilisateurs.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from faq.models import Feedback, FAQVector


@receiver(post_save, sender=Feedback)
def update_faq_vector_on_feedback(sender, instance, created, **kwargs):
    """
    Signal : quand un feedback est créé/modifié, met à jour le poids du vecteur
    et réajuste le score de similarité basé sur la satisfaction.
    
    - Feedback positif (+) : augmente la popularité, le norm, et le score reste inchangé
    - Feedback négatif (-) : diminue la popularité, le norm, et réduit le score
    
    Args:
        sender: Le modèle Feedback
        instance: L'instance Feedback créée/modifiée
        created: True si c'est une création, False si modification
    """
    if not created:
        # Mettre à jour uniquement si c'est une création
        return
    
    faq = instance.faq
    feedback_type = instance.feedback_type
    
    # ===== 1. Ajuster la popularité =====
    # Seuls les feedbacks positifs augmentent la popularité
    if feedback_type == 'positif':
        faq.popularity += 1
        faq.save()
    
    # ===== 2. Ajuster le score_similarite selon la satisfaction =====
    # Les scores négatifs doivent affecter le avg_score en le réduisant
    if feedback_type == 'negatif' and instance.score_similarite:
        # Réduire le score de 30% pour un feedback négatif
        # (le score original reste inchangé en DB, mais il reflète mieux l'insatisfaction)
        instance.score_similarite = instance.score_similarite * 0.7
        instance.save()
        print(f"[FAQ Signal] Feedback #{instance.id} négatif : score réduit de 30%")
    
    # ===== 3. Mettre à jour le vecteur associé =====
    try:
        vector = FAQVector.objects.get(faq=faq)
        
        # Ajuster le norm du vecteur selon le feedback
        if feedback_type == 'positif':
            # Augmenter le norm (le vecteur devient plus pertinent)
            vector.norm = min(vector.norm * 1.1, 1.0)  # Max 1.0
        elif feedback_type == 'negatif':
            # Diminuer le norm (le vecteur devient moins pertinent)
            vector.norm = max(vector.norm * 0.9, 0.1)  # Min 0.1
        
        vector.save()
        
        print(f"[FAQ Signal] FAQ #{faq.id} mise à jour: popularity={faq.popularity}, norm={vector.norm:.3f}")
    
    except FAQVector.DoesNotExist:
        print(f"[FAQ Signal] ⚠ Aucun vecteur trouvé pour FAQ #{faq.id}")

