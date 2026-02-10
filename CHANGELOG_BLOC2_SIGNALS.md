# Bloc 2: Signaux et Amélioration des Scores

## Modifications

### `backend/faq/signals.py` (nouveau fichier)
- Signal `@receiver(post_save, sender=Feedback)` déclenché lors de chaque feedback
- Logique d'amélioration:
  - **Feedback positif**: 
    - `popularity += 1`
    - `norm *= 1.1` (augmente jusqu'à 1.0 max)
    - Score inchangé
  - **Feedback négatif**:
    - `popularity -= 1` (min 0)
    - `norm *= 0.9` (diminue jusqu'à 0.1 min)
    - `score_similarite *= 0.7` (réduit de 30% dans la BD)

### `backend/faq/apps.py`
- Import du signal dans `FaqConfig.ready()` pour activation automatique

## Résultat Mesuré
- Les feedbacks négatifs **réduisent avg_score** via la baisse du score_similarite
- Les FAQs "mal notées" ont un `norm` inférieur, affectant les recherches futures
- Boucle de rétroaction: mauvaise FAQ → scores bas → moins visible

## Impact
✓ Active learning: le système s'améliore avec chaque feedback
✓ avg_score reflect la satisfaction réelle (pas juste la similarité technique)
✓ Endpoint `/api/stats/` montre clairement les FAQs problématiques
