# SecureVault — Document de projet

> Description du projet à usage interne (repo `docs/` ou racine, à adapter selon votre organisation). Le `README.md` final déposé à la racine du repo devra respecter le format imposé par le sujet 42 (première ligne en italique, sections obligatoires, **rédigé en anglais**) — ce présent document peut rester en français comme support de travail interne.

## 1. Concept

**SecureVault** est un coffre documentaire d'équipe sécurisé : une organisation y stocke ses documents sensibles, l'accès est contrôlé par rôle, chaque action est tracée en temps réel, et un assistant IA permet d'interroger les documents — en respectant les permissions de chacun.

## 2. Parcours utilisateur

1. L'utilisateur s'inscrit (email/mot de passe) et peut activer la **2FA (TOTP)**, ou se connecter via **OAuth** (Google/42).
2. Il crée une **organisation** et invite des collègues, en leur attribuant un **rôle** (admin / éditeur / lecteur / invité).
3. Il dépose des **documents** dans des espaces partagés au sein de l'organisation.
4. Le **RBAC** filtre ce que chacun peut voir ou modifier selon son rôle :
   - **Admin** — ajoute ou retire des membres de l'organisation.
   - **Éditeur** — ajoute et retire des documents.
   - **Lecteur** — consulte les documents sans pouvoir les modifier.
5. Un **flux d'audit en temps réel** (WebSockets) affiche qui fait quoi : connexions, consultations, changements de rôle.
6. L'utilisateur questionne un **assistant RAG** sur le contenu de l'organisation ; les réponses ne s'appuient que sur les documents auxquels il a accès, avec citations des sources. **Le lien entre les documents et le RAG est le cœur du produit** : c'est ce qui transforme un simple coffre-fort en assistant intelligent, et c'est l'élément le plus différenciant du projet.
7. L'utilisateur peut exporter ou demander la suppression de ses données (**GDPR**, si le temps le permet).

## 3. Architecture

Un point d'entrée HTTPS unique (**API Gateway** : Nginx + ModSecurity/WAF) route vers des services découplés :

- **Auth service** (FastAPI) — inscription/connexion, hash + sel des mots de passe, JWT, 2FA TOTP, OAuth2.
- **Org & RBAC service** (FastAPI) — organisations, membres, rôles, permissions.
- **Core service** (FastAPI) — profils, documents, upload de fichiers.
- **RAG service** (FastAPI) — ⭐ pièce centrale du produit. Ingestion des documents de l'organisation → embeddings → vector store → retrieval *filtré par permissions (rôle Lecteur minimum requis sur chaque document source)* → génération avec citations. Le lien documents ↔ RAG doit être direct et fiable : chaque réponse doit pouvoir être tracée aux documents qui l'ont générée.
- **Realtime service** (FastAPI + WebSockets) — présence en ligne, flux d'audit live.
- **Vault (HashiCorp)** — coffre centralisé pour tous les secrets : credentials DB, client secrets OAuth, clé API du LLM.
- **PostgreSQL + pgvector** — base relationnelle + stockage vectoriel pour le RAG.
- **Frontend** (React + Vite + TypeScript + Tailwind CSS) — consomme les API via la gateway.

**WAF** = filtre à l'entrée qui bloque les requêtes malveillantes (injections, XSS, etc.) avant qu'elles n'atteignent les services.
**Vault** = coffre-fort qui centralise et chiffre les secrets, distribués aux services qui en prouvent le besoin.

### Rôles utilisateur (RBAC)

| Rôle | Permissions |
|---|---|
| **Admin** | Ajoute ou retire des membres de l'organisation |
| **Éditeur** | Ajoute et retire des documents |
| **Lecteur** | Consulte les documents (lecture seule) |

> Le RAG s'appuie directement sur ces permissions : le retrieval ne doit renvoyer que les documents auxquels l'utilisateur courant a accès en lecture. C'est la brique la plus différenciante du projet — à traiter avec un soin particulier (cf. section Points de vigilance).

## 4. Stack technique

| Couche | Choix |
|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS |
| Backend | Python + FastAPI |
| Package manager Python | uv (dépendances + environnements virtuels) |
| ORM | SQLAlchemy (+ Alembic pour les migrations) |
| Base de données | PostgreSQL + extension pgvector |
| Temps réel | WebSockets |
| Gateway / sécurité | Nginx + ModSecurity, HashiCorp Vault |
| Conteneurisation | Docker Compose (lancement en une commande) |
| CI/CD | GitHub Actions |

## 5. Modules visés — 19 points

| Module | Catégorie | Poids |
|---|---|---|
| Framework frontend + backend | Web | Majeur (2) |
| Temps réel (WebSockets) | Web | Majeur (2) |
| ORM | Web | Mineur (1) |
| Gestion utilisateurs standard | User Management | Majeur (2) |
| Système d'organisations | User Management | Majeur (2) |
| Permissions avancées (RBAC) | User Management | Majeur (2) |
| 2FA (TOTP) | User Management | Mineur (1) |
| OAuth 2.0 | User Management | Mineur (1) |
| RAG complet | Artificial Intelligence | Majeur (2) |
| WAF/ModSecurity + Vault | Cybersecurity | Majeur (2) |
| Backend en microservices | DevOps | Majeur (2) |

## 6. Standards de code Python

- **Linting** : conformité **flake8** (PEP 8) sur tout le code Python, sans exception.
- **Typage** : typage strict avec **mypy** — toutes les fonctions et méthodes doivent avoir leurs annotations de type (paramètres et retour).
- **Paradigme** : le code backend est organisé en **programmation orientée objet** (classes pour les modèles, les services, les repositories, etc.), pas de scripts procéduraux.
- **Gestion des dépendances** : **uv** comme package manager Python pour tous les services. Les dépendances sont déclarées dans `pyproject.toml` et figées dans `uv.lock` (versionné). Installation reproductible via `uv sync` (y compris dans les Dockerfiles).
- Ces règles s'appliquent à tous les services FastAPI (`auth/`, `core/`, `org/`, `rag/`, `realtime/`), à intégrer dans la CI (job flake8 + mypy avant le build/test).

## 7. Standards de code Frontend

- **Linting** : **ESLint** avec le plugin `@typescript-eslint`, config stricte.
- **Formatage** : **Prettier**, appliqué de façon homogène sur tout le code.
- **Typage** : TypeScript en mode **strict** (`"strict": true` dans `tsconfig.json`) — pas de `any` implicite.
- **Paradigme** : composants fonctionnels + hooks (usage standard React moderne) — pas d'obligation de POO côté frontend.
- Ces règles s'appliquent à `frontend/`, à intégrer dans la CI (job ESLint + Prettier check + `tsc --noEmit` avant le build).

## 8. Structure de repo proposée

```
.
├── gateway/          # Nginx + config ModSecurity
├── auth/             # FastAPI — auth, JWT, 2FA, OAuth2
├── core/             # FastAPI — profils, documents, upload
├── org/              # FastAPI — organisations, RBAC
├── rag/              # FastAPI — ingestion, embeddings, retrieval, génération
├── realtime/         # FastAPI — WebSockets (présence, audit live)
├── frontend/         # React + Vite + TypeScript + Tailwind CSS
├── docker-compose.yml
├── .env.example
└── README.md         # README final du sujet 42 (en anglais)
```