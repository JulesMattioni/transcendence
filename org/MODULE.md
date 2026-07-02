# org — Organisations & RBAC

Gère les organisations, leurs membres et les permissions par rôle. C'est le service qui répond à « cet utilisateur a-t-il le droit de faire X ? ».

**Modules :**
- Système d'organisations — User Management — *Majeur (2 pts)*
- Permissions avancées (RBAC) — User Management — *Majeur (2 pts)*

## À faire
- CRUD organisations, invitation de membres.
- Rôles : **Admin** (gère les membres), **Éditeur** (gère les documents), **Lecteur** (lecture seule).
- API de vérification de permissions (consommée par `core` et `rag`).

**Stack :** Python + FastAPI, SQLAlchemy
