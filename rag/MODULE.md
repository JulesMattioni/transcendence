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

## Barème visé (sujet §IV.4 « Artificial Intelligence ») — DEUX Major distincts

Ce service peut valider **deux modules Major** du sujet, pas un seul :

1. **RAG complet** — « Interact with a large dataset / Users can ask questions and get relevant answers / Implement proper context retrieval and response generation. » → **largement couvert** par le pipeline actuel (ingestion + retrieval filtré org + génération sourcée).
2. **LLM system interface** — trois critères :
   - « Generate text and/or images based on user input » → ✅ **fait** (`OpenAICompatibleService` → Groq).
   - « Handle streaming responses properly » → ❌ **manquant** (c'est l'objet de l'étape 7a ci-dessous).
   - « Implement error handling and rate limiting » → ✅ **fait** (`KeyManager` + rotation 429 / backoff dans le client).

  → **2 critères sur 3 déjà acquis** ; il ne manque que le **streaming** pour valider ce 2e Major.

> ⚠️ La **mémoire conversationnelle** (historique, résumé glissant) est une feature UX **hors barème** : ni le module RAG ni le module LLM interface ne la demandent. Le **streaming**, lui, valide un critère de module **et** donne l'effet « Claude.ai » recherché → on le priorise.

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
1. ✅ Branche `rag` + modèle `Chunk` + migration pgvector (extension + table).
   - Table nommée `chunks` (pas `document_chunks`). Colonnes : id, file_id, organisation_id, chunk_index, content, embedding `vector(384)`, created_at.
   - ⚠️ Le modèle `Chunk` côté rag ne déclare **PAS** de `ForeignKey("files.id")` : rag ne connaît pas le modèle `File`, ça faisait planter le flush (`NoReferencedTableError`). La vraie contrainte FK + `ON DELETE CASCADE` vit **en base** (posée par la migration), rag n'a pas besoin de la re-déclarer côté ORM.
2. ✅ Dépendances rag (`sentence-transformers`, `torch`, `httpx`, `pypdf`) + chargement du modèle au boot via `lifespan`.
3. ✅ Couche embeddings : `EmbeddingService(BaseService)` — instance module `embedding_service`, méthodes `embed_text` (query) / `embed_texts` (batch), `normalize_embeddings=True`, sortie `list[float]` dim 384.
4. ✅ Client LLM maison : `OpenAICompatibleService(BaseService)` async (`httpx.AsyncClient`) dans `app/services/llm/` (+ `KeyManager` pool de clés, `LlmResponse`). Clé via `.env` (`GROQ_API_KEY`). Modèle Groq = `meta-llama/llama-4-scout-17b-16e-instruct`.
5. ✅ Ingestion : `POST /ingest` (`IngestService` + `ChunkRepository` + `ReaderStorage`) + déclencheur fire-and-forget côté core (`RagClient` dans `FileService.create`).
   - Transport : volume `core_uploads` monté **:ro** dans rag ; core passe `{file_id, organisation_id, filepath, content_type}` dans le payload (rag ne touche jamais la table `files`).
   - Formats : PDF (`pypdf`) + texte ; fichier au `content_type` inconnu → tentative de décodage UTF-8 strict (texte → ingéré, binaire → 415).
   - Idempotence : `DELETE` des chunks du `file_id` puis ré-insertion (rejouable, sans doublon). Commit/rollback au niveau service.
6. ⏳ Retrieval + génération : `POST /query`. **Objectif : RAG solide.** Pipeline visé, construit de façon **incrémentale** (chaque sous-étape testable, RAG fonctionnel à tout moment) :
   - **6a — Socle** : embed question → recherche pgvector top-k (filtrée `organisation_id`) → Groq → réponse + citations. Testé bout-en-bout **avant** d'ajouter le reste.
   - **6b — Query expansion + fusion** : 1 appel Groq génère 3 reformulations + 1 passage HyDE (réponse hypothétique) → embed chaque variante → top-10 pgvector **par variante** (~40-50 candidats) → fusion **RRF** (Reciprocal Rank Fusion, dédup → ~20-25 chunks uniques pré-classés).
   - **6c — Re-ranking** : cross-encoder **multilingue** (`mmarco-mMiniLM`, cohérent avec l'embedding FR/EN, chargé au boot) re-score `(question, chunk)` → garde le **`k_final = 6`** → envoyé à Groq.
   - **Nombres** : `k` par variante = 10 ; pool après fusion ~20-25 ; **`k_final = 6`** envoyé au LLM (chunks ~800 car → ~4800 car de contexte). Au-delà de ~8 chunks la qualité **baisse** (dilution + « lost in the middle »). Principe : **récupérer large, filtrer serré.**
   - Réutilise : `embedding_service` (3), `OpenAICompatibleService`/Groq (4), table `chunks` (1). Nouveau : recherche vectorielle dans `ChunkRepository` (filtrée `organisation_id`), schémas `QueryRequest`/`QueryResponse`, `QueryService(BaseService)`.
7. ⏳ **Chat type Claude.ai/Gemini** — décidé 2026-07-15/16. UX cible : bulles, texte qui s'écrit progressivement, sessions rechargeables, questions de suivi contextuelles. **Ordre décidé : 7a streaming → 7b persistance → 7c mémoire** (le barème d'abord, chaque étage testable). Le pipeline RAG 6a/6b/6c NE CHANGE PAS, on l'enveloppe.

   **7a — Streaming (valide le module LLM interface + effet Claude.ai) — ~70% backend, PAS juste visuel.**
   - `OpenAICompatibleService` : **nouvelle** méthode `generate_stream()` **à côté** de `generate()` (on ne remplace pas — `generate()` reste pour les appels internes qui veulent le résultat complet : query expansion, query rewriting). Payload `"stream": true`, `httpx.AsyncClient.stream("POST", ...)`, parse le SSE Groq (lignes `data: {...}`, `data: [DONE]` = fin, texte dans `choices[0].delta.content`). C'est un **générateur async** (`async def` + `yield`), pas un `return`.
   - Limite assumée : une fois des tokens émis, plus de rotation de clé possible → on ne gère que l'erreur AVANT le 1er token (status ≠ 200).
   - `QueryService` : variante streamée de `query()` qui relaie les tokens. Endpoint renvoie une **`StreamingResponse`** FastAPI (SSE) au lieu du JSON.
   - **Design des sources** : elles sont connues **avant** la génération (après retrieval) mais le texte arrive **pendant** → protocole : émettre les `sources` en **premier event**, puis streamer le texte.

   **7b — Persistance des conversations (sessions rechargeables).**
   - 2 tables (migration Alembic partagée, patron `chunks` ; ⚠️ ici la FK `messages.conversation_id → conversations.id` PEUT être déclarée en ORM car les 2 tables sont dans le `Base.metadata` de rag — cas différent de `chunks→files`) : `conversations` (id, organisation_id, user_id mock, title, created_at) ; `messages` (id, conversation_id FK ON DELETE CASCADE, role user/assistant, content, sources JSON, created_at).
   - Couches patron core : `ConversationRepository`, `ConversationService(BaseService)`, endpoints REST `POST/GET/GET{id}/DELETE /conversations`.
   - **Titre** : auto depuis les ~60 premiers caractères de la 1re question (pas d'appel LLM).
   - **Interaction avec 7a** : en streaming il faut **accumuler** les tokens côté serveur pour sauver le message assistant complet en base à la fin du flux.
   - **Contrat `/query` future-proof** : `{question, organisation_id, conversation_id?}` → sources + texte streamé + `conversation_id`. `conversation_id` absent = nouvelle conversation créée ; présent = on continue.

   **7c — Mémoire conversationnelle (questions de suivi) — hors barème, raffinement.**
   - **Point crucial** : le *query rewriting* se fait **AVANT** le retrieval. Une question de suivi vague (« et sa différence avec l'autre ? ») doit être réécrite en question autonome via l'historique, SINON le retrieval échoue (la phrase seule n'a aucun mot-clé). Réutilise la logique de `_expand_query`.
   - Déclenché **seulement si** `conversation_id` + historique existant (pas d'appel LLM inutile sur la 1re question).
   - Fenêtre d'historique injectée dans le prompt : via une méthode `_build_history()` **isolée**. v1 = N derniers messages (simple) OU résumé glissant (l'utilisateur penche pour le résumé glissant — À TRANCHER au moment de 7c ; le corps de `_build_history()` est remplaçable sans refonte). Note : le résumé glissant ajoute des appels LLM autour d'un flux déjà complexe → à peser.

### Dépendances externes / points ouverts
- **Filtrage par RÔLE (« Lecteur min. »)** : dépend du service `org/` (non fait). Pour l'instant on filtre seulement par `organisation_id` (comme le RBAC de core), avec l'utilisateur mocké. Le filtre par rôle se greffe quand `org/` est prêt.
- **Vrai utilisateur** : dépend du service `auth/` (non fait). `organisation_id` vient d'un mock côté client pour l'instant ; à dériver du JWT plus tard.
- **Robustesse ingestion** : version 1 = fire-and-forget (log si échec). Version robuste plus tard = statut `ingestion_status` sur le fichier + relance, éventuellement via le service `realtime`.
