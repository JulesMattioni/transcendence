# core — Profils & documents

Service central des données métier : profils utilisateurs, dépôt et gestion des documents dans les espaces partagés.

**Modules :**
- Framework backend (FastAPI) — Web — *Majeur (2 pts, partagé)*
- ORM (SQLAlchemy + Alembic) — Web — *Mineur (1 pt)*

## À faire
- Gestion des profils utilisateurs.
- Upload / stockage / téléchargement de documents.
- Filtrage des accès selon le RBAC (via le service `org`).
- Modèles + migrations Alembic.

**Stack :** Python + FastAPI, SQLAlchemy, Alembic, PostgreSQL
