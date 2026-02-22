# Comparaison : NLTK vs spaCy pour le prétraitement

## Résumé rapide

- **NLTK** : boîte à outils complète pour le NLP — modules variés (tokenize, stopwords, lemmatize), beaucoup de ressources éducatives et de corpus. Plus granulaire mais nécessite d'assembler plusieurs composants.
- **spaCy** : pipeline industriel prêt à l'emploi (tokenisation, lemmatisation, POS, stopwords, vecteurs), optimisé pour la performance et l'utilisation en production.

## Différences principales

- **API & ergonomie** : spaCy fournit un objet `Doc` central et des attributs (`token.lemma_`, `token.is_stop`, etc.) ; NLTK propose des fonctions séparées à composer.
- **Performance** : spaCy est nettement plus rapide pour le traitement en lot et convient mieux aux applications en production.
- **Qualité de la lemmatisation (FR)** : spaCy utilise des modèles linguistiques entraînés spécifiquement pour chaque langue (par ex. `fr_core_news_sm`) — généralement plus adaptés au français que le lemmatizer WordNet (conçu pour l'anglais) utilisé seul avec NLTK.
- **Taille & dépendances** : spaCy nécessite l'installation d'un modèle (taille supplémentaire). NLTK demande de télécharger des corpus/ressources (punkt, stopwords, wordnet) mais reste modulaire.
- **Cas d'usage** :
  - Utiliser spaCy quand vous visez performance, robustesse et rapidité de développement pour la production.
  - Utiliser NLTK pour expérimentations fines, travaux pédagogiques ou si vous avez besoin d'un corpus particulier fourni par NLTK.

## Limitations pratiques

- Pour la langue française, la combinaison NLTK + WordNet n'est pas optimale — il faudra parfois des outils complémentaires (stemmers/lemmatizers dédiés au français).
- spaCy impose de télécharger un modèle pré-entraîné (`fr_core_news_sm` ou plus grand) avant usage.

## Instructions pour tester la version spaCy (depuis la racine du projet dans le `venv`)

1. Installer spaCy et le modèle (si pas déjà fait) :

```powershell
pip install spacy
python -m spacy download fr_core_news_sm
```

2. Lancer le shell Django et exécuter les 3 lignes de test :

```powershell
python backend/manage.py shell
```

Puis dans le shell Python :

```python
from chatbot.preprocessing import TextPreprocessor

preproc = TextPreprocessor()
print(preproc.preprocess("Les étudiants mangeaient rapidement leurs repas dans la cafétéria."))
```

Ce test doit afficher la liste des lemmes filtrés (stopwords retirés, tokens alphabétiques).

## Remarque sur l'approche NLTK précédente

- Si vous revenez à la version NLTK, assurez-vous d'installer `nltk` et de télécharger les ressources nécessaires :

```powershell
pip install nltk
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```