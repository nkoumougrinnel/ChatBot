"""
Module de prétraitement de texte pour le chatbot FAQ.
Ce module fournit une classe TextPreprocessor qui normalise, nettoie et 
tokenize le texte français pour l'indexation TF-IDF et la recherche sémantique.
"""

# Importation de la bibliothèque de traitement d'expressions régulières
import re
# Importation de NLTK (Natural Language Toolkit) pour le traitement du langage naturel
import nltk
# Importation de la liste des mots vides (stopwords) pour le français
from nltk.corpus import stopwords
# Importation du lemmatiseur pour réduire les mots à leur forme canonique
from nltk.stem import WordNetLemmatizer

# Télécharger les ressources NLTK nécessaires (punkt, stopwords, wordnet)
# Ces ressources sont téléchargées une seule fois et cachées localement
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)


class TextPreprocessor:
    """
    Classe pour prétraiter et normaliser le texte français.
    Elle effectue le nettoyage, la tokenization, la suppression des stopwords
    et la lemmatization.
    """
    
    def __init__(self, language="french"):
        """
        Initialiser le préprocesseur avec les ressources NLTK.
        
        Args:
            language (str): Langue pour les stopwords (défaut: "french")
        """
        # Charger la liste des mots vides (stopwords) pour la langue spécifiée
        self.stopwords = set(stopwords.words(language))
        # Initialiser le lemmatiseur WordNet
        self.lemmatizer = WordNetLemmatizer()

    def clean_text(self, text: str) -> str:
        """
        Nettoyer le texte en le mettant en minuscules et en supprimant 
        les caractères spéciaux (conserve les accents français).
        
        Args:
            text (str): Texte brut à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        # Convertir tout le texte en minuscules
        text = text.lower()
        # Supprimer tous les caractères sauf les lettres minuscules, accents français et espaces
        text = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ\s]", "", text)
        return text

    def tokenize(self, text: str):
        """
        Découper le texte en mots (tokens).
        
        Args:
            text (str): Texte nettoyé
            
        Returns:
            list: Liste de mots
        """
        # Utiliser le tokenizer NLTK pour découper le texte en tokens (mots)
        return nltk.word_tokenize(text)

    def remove_stopwords(self, tokens):
        """
        Supprimer les mots vides (articles, prépositions, etc.) de la liste de tokens.
        
        Args:
            tokens (list): Liste de mots
            
        Returns:
            list: Liste de mots sans stopwords
        """
        # Filtrer les tokens en gardant seulement ceux qui ne sont pas dans la liste des stopwords
        return [t for t in tokens if t not in self.stopwords]

    def lemmatize(self, tokens):
        """
        Réduire chaque mot à sa forme canonique (lemme).
        
        Args:
            tokens (list): Liste de mots
            
        Returns:
            list: Liste de lemmes
        """
        # Appliquer la lemmatization à chaque token
        return [self.lemmatizer.lemmatize(t) for t in tokens]

    def preprocess(self, text: str):
        """
        Pipeline complet de prétraitement du texte:
        nettoyage → tokenization → suppression des stopwords → lemmatization.
        
        Args:
            text (str): Texte brut à prétraiter
            
        Returns:
            list: Liste de tokens nettoyés et normalisés
        """
        # Étape 1 : nettoyer le texte (minuscules, caractères spéciaux)
        text = self.clean_text(text)
        # Étape 2 : découper en tokens (mots individuels)
        tokens = self.tokenize(text)
        # Étape 3 : supprimer les mots vides (articles, prépositions, etc.)
        tokens = self.remove_stopwords(tokens)
        # Étape 4 : réduire les mots à leur forme canonique (lemmatization)
        tokens = self.lemmatize(tokens)
        # Retourner la liste finale de tokens nettoyés et normalisés
        return tokens
