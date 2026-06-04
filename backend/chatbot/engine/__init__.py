"""
Pipeline RAG Gen3 du chatbot SUP'ONE.

Seul ``rag_pipeline`` doit être importé par les vues Django ; les autres
modules (embedder, faiss_search, prompt_builder, tfidf_fallback, llm_client)
sont des composants internes orchestrés par le pipeline.
"""
