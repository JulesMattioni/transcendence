# Comment utiliser le service `organisations` & `permissions`

Ce document décrit comment dialoguer avec le service `organisations` et son système de contrôle d'accès : les routes disponibles, ce qu'il faut envoyer, ce qu'on reçoit en retour, et comment fonctionnent les rôles et permissions.

Ce guide couvre : la création, la lecture, la mise à jour, la suppression d'organisations, ainsi que la gestion des membres et le système de rôles (Admin, Moderator, Guest).

---

## 1. Où taper

Toutes les requêtes passent par la gateway :

```
https://localhost:8443/api/organisations/...

```

Exemple complet : `https://localhost:8443/api/organisations/`.

---

## 2. Le principe général : Sécurité & Rôles (RBAC)

Les routes sensibles nécessitent d'être authentique et d'avoir le rôle requis au sein de l'organisation.

* **Hiérarchie des rôles** :
* `ADMIN` (1) : Plein pouvoir (création, modification, suppression, gestion des membres).
* `MODERATOR` (3) : Droits de modération (selon les implémentations futures).
* `GUEST` (2) : Accès en lecture seule.



Flow d'une requête protégée :

```
1. L'utilisateur envoie sa requête avec son token d'authentification.
2. Le système vérifie l'identité de l'utilisateur (via le service auth).
3. Le `RoleChecker` interroge la table de liaison `OrganisationMember` pour récupérer le rôle de l'utilisateur dans l'organisation ciblée.
4. Si le rôle correspond (ex: `ADMIN` pour un patch/delete), la requête passe. Sinon, le serveur renvoie `403 Forbidden`.

```

---

## 3. Les routes

### `POST /` — Créer une organisation

**Body** (JSON) :

```json
{
  "name": "Mon Super Studio"
}

```

Le champ `name` est obligatoire.

**Réponse succès — `201 Created**` :

```json
{
  "id": 1,
  "name": "Mon Super Studio"
}

```

**Erreurs :**

| Code | Quand | Body |
| --- | --- | --- |
| `422` | Champ manquant ou format invalide | `{"detail": [...]}` |

---

### `GET /{org_id}` — Récupérer une organisation par son ID

Pas de body requis.

**Réponse succès — `200 OK**` :

```json
{
  "id": 1,
  "name": "Mon Super Studio"
}

```

**Erreurs :**

| Code | Quand | Body |
| --- | --- | --- |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

### `PATCH /{org_id}` — Modifier une organisation

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

**Body** (JSON) :

```json
{
  "name": "Nouveau Nom de Studio"
}

```

**Réponse succès — `200 OK**` :

```json
{
  "id": 1,
  "name": "Nouveau Nom de Studio"
}

```

**Erreurs :**

| Code | Quand | Body |
| --- | --- | --- |
| `401` | Non authentifié / Token invalide | `{"detail": "Not authenticated"}` (ou équivalent auth) |
| `403` | L'utilisateur n'est pas ADMIN de cette organisation | `{"detail": "You don't have necessary permission"}` |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

### `DELETE /{org_id}` — Supprimer une organisation

> 🔒 **Réservé aux administrateurs** (`required_admin_role`)

Pas de body requis.

**Réponse succès — `204 No Content**` : Corps vide. L'organisation est supprimée de la base de données.

**Erreurs :**

| Code | Quand | Body |
| --- | --- | --- |
| `401` | Non authentifié | `{"detail": "Not authenticated"}` |
| `403` | L'utilisateur n'est pas ADMIN | `{"detail": "You don't have necessary permission"}` |
| `404` | L'organisation n'existe pas | `{"detail": "Organisation not found"}` |

---

## 4. Les schémas de données

* **`OrganisationCreate`** *(entrée pour la création)* : `name`.
* **`OrganisationUpdate`** *(entrée pour la modification)* : `name` (optionnel/partiel).
* **`OrganisationRead`** *(sortie standard)* : `id`, `name`.

---

## 5. Table récapitulative

| Méthode | Route | Auth / Rôle requis | Body | Réponse succès |
| --- | --- | --- | --- | --- |
| `POST` | `/` | Non spécifié / Connecté | body JSON (`OrganisationCreate`) | `201` `OrganisationRead` |
| `GET` | `/{org_id}` | Aucun | — | `200` `OrganisationRead` |
| `PATCH` | `/{org_id}` | `ADMIN` (`required_admin_role`) | body JSON (`OrganisationUpdate`) | `200` `OrganisationRead` |
| `DELETE` | `/{org_id}` | `ADMIN` (`required_admin_role`) | — | `204` `null` |

---

## 6. Points d'attention pour le client

* Les routes de modification (`PATCH`) et de suppression (`DELETE`) évaluent dynamiquement si l'utilisateur connecté possède le rôle `ADMIN` dans l'organisation ciblée via la base de données.
* L'architecture repose sur l'injection de dépendances FastAPI (`Depends`) : le service gère la logique métier et les commits, le repository gère les requêtes SQLAlchemy brutes.