# rag — Assistant RAG ⭐

**Pièce centrale du produit.** Répond aux questions des utilisateurs à partir du contenu des documents de leur organisation, avec citations des sources.

**Module :** RAG complet — Artificial Intelligence — *Majeur (2 pts)*

## À faire
- Ingestion des documents → embeddings → **vector store (pgvector)**.
- Retrieval **filtré par permissions** : ne renvoyer que les documents accessibles en lecture (rôle Lecteur min.) à l'utilisateur courant.
- Génération de réponses avec **citations traçables** aux documents sources.

> ⚠️ Le lien documents ↔ RAG doit être direct et fiable : c'est l'élément le plus différenciant du projet. Aucune fuite de document non autorisé dans le retrieval.

**Stack :** Python + FastAPI, PostgreSQL + pgvector, LLM (clé API via Vault)
