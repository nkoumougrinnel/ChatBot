import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import Feedback, FAQ, Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Génère des feedbacks fictifs pour tester les statistiques'

    def handle(self, *args, **kwargs):
        self.stdout.write("Génération des données de test...")

        # 1. Récupérer ou créer un utilisateur de test
        user, _ = User.objects.get_or_create(username="test_user", email="test@example.com")

        # 2. Vérifier s'il y a des FAQ en base
        faqs = FAQ.objects.all()
        if not faqs.exists():
            self.stdout.write(self.style.ERROR("Aucune FAQ trouvée. Importez d'abord les CSV."))
            return
        
        # 3. Générer des feedbacks aléatoires
        feedbacks_created = 0
        for faq in faqs:
            # On génère entre 1 et 5 feedbacks par FAQ pour avoir des stats variés
            for _ in range(random.randint(1, 5)):
                score_similarite = random.uniform(0.4, 1.0)
                feedback_type = 'positif' if score_similarite >= 0.7 else 'negatif'

                Feedback.objects.create(
                    user=user,
                    faq=faq,
                    feedback_type=feedback_type,
                    score_similarite=round(score_similarite, 2),
                    comment="Commentaire de test automatique." if feedback_type == 'positif' else "")
                feedbacks_created += 1
        self.stdout.write(self.style.SUCCESS(f"Succès : {feedbacks_created} feedbacks générés !"))