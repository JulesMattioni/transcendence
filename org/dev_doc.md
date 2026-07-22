# Comment utiliser le service `org` (organisations & permissions)

Ce document décrit comment dialoguer avec le service `org` et son système de contrôle d'accès : les routes disponibles, ce qu'il faut envoyer, ce qu'on reçoit en retour, et comment fonctionnent les rôles et permissions.

Ce guide couvre : la création, la lecture, la mise à jour, la suppression d'organisations, la gestion des membres (ajout, changement de rôle, retrait, listing), le listing des organisations d'un utilisateur, et le système de rôles (Admin, Editor, Reader). Il documente aussi la route interne réservée aux appels service-à-service.

---

## 1. Où taper

Toutes les requêtes externes passent par la gateway, préfixées par `/api/org` :

```
https://localhost:8443/api/org/organisations/...
```

Exemple complet : `https://localhost:8443/api/org/organisations/`.

> ⚠️ Le router principal du service porte le préfixe `/organisations`. Via la gateway, le segment `/api/org/` est réécrit vers la racine du service, donc l'URL finale reste `/api/org/organisations/...`.

---

## 2. Le principe général : Sécurité & Rôles (RBAC)

L'identité de l'utilisateur n'est **pas** gérée par `org` : elle est déléguée au service `auth`. À chaque requête protégée, `org` transmet le header `Authorization` reçu à `auth` (`GET /me`) pour identifier l'appelant, puis vérifie son rôle dans l'organisation ciblée.

**Hiérarchie des rôles** (`app/schemas/roles.py`) :

| Rôle | `role_id` | Portée |
|---|---|---|
| `ADMIN` | `1` | Plein pouvoir : modifier/supprimer l'org, gérer les membres et leurs rôles |
| `EDITOR` | `2` | Membre standard (droits d'écriture métier, pas de gestion d'org) |
| `READER` | `3` | Lecture seule |

Le contrôle d'accès se fait via des dépendances FastAPI construites à partir d'un `RoleChecker` (`app/dependancies.py`) :

| Dépendance | Rôles autorisés |
|---|---|
| `required_admin_role` | `ADMIN` |
| `required_editor_role` | `ADMIN`, `EDITOR` |
| `required_reader_role` | `ADMIN`, `EDITOR`, `READER` (= tout membre de l'org) |

Flow d'une requête protégée :

```
1. Le client envoie sa requête avec "Authorization: Bearer <access_token>".
2. org appelle auth (GET /me) avec ce header pour identifier l'utilisateur.
   → si le token est absent/invalide : 401.
3. Le RoleChecker interroge la table OrganisationMember pour lire le rôle
   de cet utilisateur dans l'org ciblée (paramètre org_id de l'URL).
4. Si le rôle est dans la liste autorisée, la requête passe.
   Sinon → 403 Forbidden.
```

> Le contrôle de rôle s'appuie sur le paramètre `org_id` présent dans le chemin de la route. Une route sans `org_id` (ex. `GET /users/{user_id}/organisations`) ne passe pas par le `RoleChecker`.

---

## 3. Les routes

### `POST /organisations/` — Créer une organisation

**Auth :** utilisateur connecté (`Authorization: Bearer <access_token>`). Le créateur devient automatiquement `ADMIN` (`role_id=1`) de l'organisation.

**Body** (JSON) :
```json
{
  "name": "Mon Super Studio"
}
```
Le champ `name` est obligatoire.

**Réponse succès — `201 Created`** :
```json
{
  "id": 1,
  "name": "Mon Super Studio"
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié / token invalide | `{"detail": "..."}` (délégué à auth) |
| `422` | Champ manquant ou format invalide | `{"detail": [...]}` |

---

### `POST /organisations/{org_id}/users/{user_id}` — Ajouter un membre

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

Ajoute l'utilisateur `user_id` à l'organisation `org_id` avec le rôle `role_id`.

**Query :** `role_id` (int) — le rôle à attribuer (voir §2).

```
POST /organisations/5/users/12?role_id=2
```

**Réponse succès — `201 Created`** : le membre créé.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas ADMIN de l'org | `{"detail": "You don't have necessary permission "}` |

> ℹ️ Aujourd'hui l'ajout se fait par `user_id`. Les champs dénormalisés `email`/`first_name`/`last_name` du membre (voir §4) ne sont **pas** renseignés à ce stade — ils restent `null` jusqu'à la mise en place du système d'invitations (ajout par email avec lookup auth).

---

### `GET /organisations/{org_id}` — Récupérer une organisation par son ID

**Auth :** aucune (route publique). Pas de body.

**Réponse succès — `200 OK`** :
```json
{
  "id": 1,
  "name": "Mon Super Studio"
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

### `GET /organisations/{org_id}/users` — Lister les membres d'une organisation

> 🔒 **Réservé aux membres de l'org** (`required_reader_role` : ADMIN, EDITOR ou READER)

Retourne la liste des membres de l'organisation `org_id`.

Pas de body.

**Réponse succès — `200 OK`** : liste de `OrganisationMemberRead` :
```json
[
  {
    "user_id": 1,
    "role_id": 1,
    "email": null,
    "first_name": null,
    "last_name": null
  }
]
```

> Les champs `email`, `first_name`, `last_name` sont **dénormalisés** (copiés depuis `auth` au moment de l'ajout du membre). Ils peuvent valoir `null` tant que l'ajout par email (invitations) n'est pas en place — dans ce cas, le client se rabat sur `user_id`.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas membre de l'org | `{"detail": "You don't have necessary permission "}` |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

### `GET /organisations/users/{user_id}/organisations` — Lister les organisations d'un utilisateur

**Auth :** aucune (pas de `RoleChecker`, cette route n'a pas d'`org_id`). Pas de body.

**Réponse succès — `200 OK`** :
```json
{
  "user_id": 1,
  "organisation": [
    { "org_id": 8, "name": "Mon Super Studio", "role": 1 },
    { "org_id": 9, "name": "Autre Org", "role": 3 }
  ]
}
```

---

### `PATCH /organisations/{org_id}` — Modifier une organisation

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

**Body** (JSON) :
```json
{
  "name": "Nouveau Nom de Studio"
}
```

**Réponse succès — `200 OK`** :
```json
{
  "id": 1,
  "name": "Nouveau Nom de Studio"
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas ADMIN | `{"detail": "You don't have necessary permission "}` |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

### `PATCH /organisations/{org_id}/users/{user_id}` — Changer le rôle d'un membre

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

**Query :** `new_role` (int) — le nouveau `role_id`.

```
PATCH /organisations/5/users/12?new_role=1
```

**Réponse succès — `200 OK`** : résultat de la mise à jour.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas ADMIN | `{"detail": "You don't have necessary permission "}` |
| `404` | Le membre n'existe pas dans l'org | `{"detail": "User not in organisation"}` |

---

### `DELETE /organisations/{org_id}/users/{user_id}` — Retirer un membre

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

Pas de body.

**Réponse succès — `204 No Content`** : corps vide.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas ADMIN | `{"detail": "You don't have necessary permission "}` |
| `404` | Le membre n'existe pas dans l'org | `{"detail": "User not in organisation"}` |

---

### `DELETE /organisations/{org_id}` — Supprimer une organisation

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

Pas de body.

**Réponse succès — `204 No Content`** : corps vide. L'organisation (et ses membres, via `ON DELETE CASCADE`) est supprimée.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | Non authentifié | `{"detail": "..."}` |
| `403` | L'appelant n'est pas ADMIN | `{"detail": "You don't have necessary permission "}` |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

## 4. Route interne (service-à-service)

### `GET /internal/organisations/{org_id}/members` — Lister les membres (interne)

Route **non authentifiée**, destinée aux appels service-à-service (ex. `realtime` qui a besoin de la liste des membres d'une org sans disposer d'un token utilisateur).

**Elle n'est PAS exposée par la gateway** : la conf nginx renvoie `404` sur `/api/org/internal/...`. Elle n'est donc joignable que **depuis le réseau Docker interne**, en appelant directement `http://org:8000/internal/organisations/{org_id}/members`.

**Réponse succès — `200 OK`** : même format que `GET /organisations/{org_id}/users` (liste de `OrganisationMemberRead`).

```json
[
  { "user_id": 1, "role_id": 1, "email": null, "first_name": null, "last_name": null }
]
```

> ⚠️ Cette route ne fait **aucun** contrôle de rôle : elle donne accès à tous les membres de n'importe quelle org. Sa seule protection actuelle est le fait qu'elle n'est pas routée par la gateway. Un secret partagé (`X-Internal-Secret`) est envisagé comme deuxième couche de défense mais n'est pas encore en place.

---

## 5. Les schémas de données

- **`OrganisationCreate`** *(entrée de `POST /organisations/`)* : `name`.
- **`OrganisationUpdate`** *(entrée de `PATCH /organisations/{org_id}`)* : `name` (optionnel).
- **`OrganisationRead`** *(sortie standard)* : `id`, `name`.
- **`OrganisationMemberRead`** *(sortie de `GET /organisations/{org_id}/users` et de la route interne)* : `user_id`, `role_id`, `email` (string ou `null`), `first_name` (string ou `null`), `last_name` (string ou `null`).

Modèle de données `OrganisationMember` (`app/models/organisation.py`) : `id`, `org_id` (FK vers `organisation`, `ON DELETE CASCADE`), `user_id` (indexé), `role_id`, et les 3 champs dénormalisés `email` / `first_name` / `last_name` (tous nullable, copiés depuis `auth` au moment de l'ajout du membre — approche « snapshot »).

---

## 6. Table récapitulative

| Méthode | Route | Auth / Rôle requis | Body / Query | Réponse succès |
|---|---|---|---|---|
| `POST` | `/organisations/` | Connecté | body (`OrganisationCreate`) | `201` `OrganisationRead` |
| `POST` | `/organisations/{org_id}/users/{user_id}` | `ADMIN` | query `?role_id=` | `201` membre |
| `GET` | `/organisations/{org_id}` | Aucune | — | `200` `OrganisationRead` |
| `GET` | `/organisations/{org_id}/users` | Membre (`ADMIN`/`EDITOR`/`READER`) | — | `200` `list[OrganisationMemberRead]` |
| `GET` | `/organisations/users/{user_id}/organisations` | Aucune | — | `200` `{user_id, organisation[]}` |
| `PATCH` | `/organisations/{org_id}` | `ADMIN` | body (`OrganisationUpdate`) | `200` `OrganisationRead` |
| `PATCH` | `/organisations/{org_id}/users/{user_id}` | `ADMIN` | query `?new_role=` | `200` résultat |
| `DELETE` | `/organisations/{org_id}/users/{user_id}` | `ADMIN` | — | `204` `null` |
| `DELETE` | `/organisations/{org_id}` | `ADMIN` | — | `204` `null` |
| `GET` | `/internal/organisations/{org_id}/members` | **Interne** (hors gateway, sans token) | — | `200` `list[OrganisationMemberRead]` |

---

## 7. Points d'attention pour le client

- `org` **ne valide pas les tokens lui-même** : il délègue à `auth` via `GET /me` en repassant le header `Authorization`. Un `auth` indisponible fait remonter un `503` (`Auth service unavailable`).
- Le contrôle de rôle est **dynamique** et par organisation : le même utilisateur peut être `ADMIN` d'une org et `READER` d'une autre. Le rôle est toujours évalué pour l'`org_id` de l'URL.
- Rôles réels : `ADMIN=1`, `EDITOR=2`, `READER=3` (`app/schemas/roles.py`). ⚠️ D'anciennes docs mentionnaient « Moderator/Guest » — c'est obsolète.
- Les champs `email`/`first_name`/`last_name` d'un membre sont un **snapshot** pris au moment de l'ajout : ils peuvent être `null` (ajout par id) ou devenir périmés si l'utilisateur change ses infos dans `auth`. Le client doit gérer le cas `null` (fallback sur `user_id`).
- La route `/internal/...` ne doit **jamais** être appelée depuis le front : elle est réservée aux services internes et n'est pas joignable via la gateway.
- Aucune configuration CORS explicite sur le service — passer par la gateway (`/api/org/...`) pour éviter les erreurs CORS dans le navigateur.
