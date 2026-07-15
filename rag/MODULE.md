# rag — Assistant RAG ⭐

**Pièce centrale du produit.** Répond aux questions des utilisateurs à partir du contenu des documents de leur organisation, avec citations des sources.

**Module :** RAG complet — Artificial Intelligence — *Majeur (2 pts)*

## À faire
- Ingestion des documents → embeddings → **vector store (pgvector)**.
- Retrieval **filtré par permissions** : ne renvoyer que les documents accessibles en lecture (rôle Lecteur min.) à l'utilisateur courant.
- Génération de réponses avec **citations traçables** aux documents sources.

> ⚠️ Le lien documents ↔ RAG doit être direct et fiable : c'est l'élément le plus différenciant du projet. Aucune fuite de document non autorisé dans le retrieval.

**Stack :** Python + FastAPI, PostgreSQL + pgvector, LLM (clé API via Vault)

---

## Plan de mise en œuvre

### Décisions actées (2026-07-14)
- **Embeddings LOCAUX** via `sentence-transformers`, modèle `paraphrase-multilingual-MiniLM-L12-v2` (**384 dimensions**, multilingue FR/EN). Tourne dans le container rag (CPU, pas de clé API). Le modèle est chargé une fois au démarrage.
- **LLM = Groq** (API compatible OpenAI). **Client HTTP maison** (`httpx`), PAS de SDK. On construit les requêtes à la main. Clé API via Vault.
- **Vector store = pgvector**, déjà présent (image Docker `pgvector/pgvector:pg16`). Il reste à activer l'extension (`CREATE EXTENSION vector`) via une migration.
- **Déclenchement de l'ingestion = PUSH depuis core** : quand un fichier est uploadé, `core` appelle en HTTP `POST /rag/ingest {file_id, organisation_id}`. On ingère AU MOMENT de l'upload (une fois), pas à la demande à chaque question → les questions restent rapides. Appel « fire-and-forget » : si rag est down, l'upload réussit quand même (à confirmer à l'implémentation).

### Architecture du pipeline
```
Upload  → core stocke le fichier (déjà fait)
        → core POST /rag/ingest {file_id, organisation_id}
        → rag lit le contenu, découpe en chunks, calcule les embeddings, stocke dans pgvector

Question → POST /rag/query {question, organisation_id}
        → rag embed la question, recherche par similarité (filtrée par organisation)
        → Groq génère la réponse + citations aux documents sources
```

### Schéma de données (à créer)
Table `document_chunks` :
- `id`, `file_id` (FK vers `files.id`, **ON DELETE CASCADE** → les chunks disparaissent avec le fichier), `organisation_id` (dupliqué + indexé, pour filtrer le retrieval sans JOIN), `chunk_index`, `content` (texte), `embedding vector(384)`, `created_at`.
- Migration Alembic PARTAGÉE (voir la note migrations du projet). Workflow : créer le **modèle SQLAlchemy** d'abord → `make migration` (autogenerate) → ajouter à la main `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` en tête de `upgrade()` (autogenerate ne génère jamais le CREATE EXTENSION). Le paquet Python `pgvector` doit être dispo pour le service qui applique les migrations.
- Pas d'index vectoriel (IVFFlat/HNSW) au départ : à ajouter dans une migration ultérieure une fois qu'il y a du volume (l'index a besoin de données pour se calibrer).

### Étapes (dans l'ordre, on valide chacune avant la suivante)
1. Branche `rag` + modèle `DocumentChunk` + migration pgvector (extension + table).
2. Dépendances rag (`sentence-transformers`, `torch`, `httpx`) + chargement du modèle au boot.
3. Couche embeddings (wrapper sentence-transformers, testable seule).
4. Client Groq maison (httpx, testable avec une requête simple).
5. Ingestion : endpoint `/rag/ingest` (chunk + embed + stocke) + déclencheur côté core.
6. Retrieval + génération : endpoint `/rag/query` (embed question → similarité filtrée org → Groq → réponse + citations).
7. Frontend : page « Assistant » (champ question, affichage réponse + sources).

### Dépendances externes / points ouverts
- **Filtrage par RÔLE (« Lecteur min. »)** : dépend du service `org/` (non fait). Pour l'instant on filtre seulement par `organisation_id` (comme le RBAC de core), avec l'utilisateur mocké. Le filtre par rôle se greffe quand `org/` est prêt.
- **Vrai utilisateur** : dépend du service `auth/` (non fait). `organisation_id` vient d'un mock côté client pour l'instant ; à dériver du JWT plus tard.
- **Robustesse ingestion** : version 1 = fire-and-forget (log si échec). Version robuste plus tard = statut `ingestion_status` sur le fichier + relance, éventuellement via le service `realtime`.
