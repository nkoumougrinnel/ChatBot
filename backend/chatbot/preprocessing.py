import spacy


class TextPreprocessor:
    def __init__(self, language_model="fr_core_news_sm"):
        """
        Initialiser le préprocesseur avec spaCy.
        
        Args:
            language_model (str): modèle spaCy à charger (défaut: français léger)
        """
        # Charger le modèle spaCy spécifié
        self.nlp = spacy.load(language_model)

    def preprocess(self, text: str):
        """
        Prétraiter un texte : tokenisation, suppression des stopwords, lemmatisation.
        
        Args:
            text (str): texte brut
        
        Returns:
            list[str]: liste de tokens prétraités
        """
        # Traiter le texte avec le pipeline spaCy
        doc = self.nlp(text)
        # Conserver les lemmes en minuscules, filtrer stopwords et tokens non alphabétiques
        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop and token.is_alpha
        ]
        return tokens
