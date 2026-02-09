from chatbot.preprocessing import TextPreprocessor

def preprocess_text(text: str):
    preproc = TextPreprocessor()
    return preproc.preprocess(text)
