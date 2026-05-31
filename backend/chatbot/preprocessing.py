import spacy
from typing import List


class TextPreprocessor:
    def __init__(self, language_model: str = "fr_core_news_sm"):
        """
        Initialiser le préprocesseur avec spaCy.
        
        Note: la charge du modèle spaCy peut être coûteuse. Préférez
        utiliser la fonction `get_preprocessor()` pour obtenir une instance
        réutilisable plutôt que d'instancier à chaque appel.
        """
        self.nlp = spacy.load(language_model)

    def preprocess(self, text: str) -> List[str]:
        """
        Prétraiter un texte : tokenisation, suppression des stopwords, lemmatisation.
        
        Args:
            text (str): texte brut
        
        Returns:
            list[str]: liste de tokens prétraités
        """
        doc = self.nlp(text)
        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop and token.is_alpha
        ]
        return tokens


# Instance partagée (lazy) pour éviter de recharger le modèle spaCy à chaque appel
_shared_preprocessor: TextPreprocessor | None = None


def get_preprocessor() -> TextPreprocessor:
    """Retourne une instance singleton de `TextPreprocessor` (initialisée à la première utilisation)."""
    global _shared_preprocessor
    if _shared_preprocessor is None:
        _shared_preprocessor = TextPreprocessor()
    return _shared_preprocessor


def preprocess_text(text: str) -> List[str]:
    """
    Prétraite un texte en utilisant l'instance partagée du préprocesseur.
    
    Cette fonction est sûre à appeler fréquemment — le modèle spaCy n'est
    chargé qu'une seule fois.
    """
    preproc = get_preprocessor()
    return preproc.preprocess(text)
