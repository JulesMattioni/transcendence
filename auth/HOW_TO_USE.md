# Comment utiliser le service `auth`

Ce document décrit comment dialoguer avec le service `auth` : les routes disponibles, ce qu'il faut envoyer, ce qu'on reçoit en retour, et comment gérer les tokens côté client.

Ce guide couvre : signup, login, refresh, logout, `/me`. Il n'existe aucune route de 2FA ni d'OAuth (Google/42) dans le service.

---

## 1. Où taper

Toutes les requêtes passent par la gateway :

```
https://localhost:8443/api/auth/...
```

Exemple complet : `https://localhost:8443/api/auth/signup`.

---

## 2. Le principe général : deux tokens

Chaque connexion (signup ou login) donne **deux tokens**, avec des rôles différents :

| | `access_token` | `refresh_token` |
|---|---|---|
| Sert à | accéder aux routes protégées (`/me`, et les autres services qui valident ce même JWT) | obtenir un nouvel `access_token` sur `/refresh` |
| Durée de vie | 15 minutes | 7 jours |
| Où l'envoyer | header `Authorization: Bearer <access_token>` | paramètre de requête sur `/refresh` / `/logout` |
| Révocable ? | non | oui — stocké en base, supprimé au `logout` et remplacé à chaque `refresh` |

Flow :

```
1. signup ou login
   → { tokens: { access_token, refresh_token }, user }
   → stocker les deux tokens + les infos user

2. chaque requête vers une route protégée
   → header "Authorization: Bearer <access_token>"

3. une requête renvoie 401 (access_token expiré ou invalide)
   → appeler /refresh avec le refresh_token
   → remplacer access_token ET refresh_token par les nouveaux reçus
   → rejouer la requête initiale

4. déconnexion
   → appeler /logout avec le refresh_token
   → effacer tokens + user côté client
```

À chaque `refresh`, le `refresh_token` change (rotation) : l'ancien devient invalide immédiatement. Réutiliser un `refresh_token` déjà consommé renvoie `401`.

Si `/refresh` échoue, il n'y a pas de session récupérable : effacer la session locale et rediriger vers le login.

---

## 3. Stockage des tokens

Les deux tokens sont renvoyés dans le corps JSON de la réponse — le serveur ne pose aucun cookie. Le stockage (mémoire, `localStorage`, etc.) et le transport sont entièrement à la charge du client.

---

## 4. Les routes

### `POST /signup` — créer un compte

**Body** (JSON) :
```json
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
```
Les 4 champs sont obligatoires. `email` doit être un email valide. Aucune règle de complexité n'est appliquée sur `password`.

**Réponse succès — `200`** : le compte est créé et l'utilisateur est directement connecté (pas d'appel `/login` séparé nécessaire) :
```json
{
  "tokens": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "El1R_Kq5Y...",
    "token_type": "bearer"
  },
  "user": {
    "id": 1,
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com"
  }
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `409` | l'email existe déjà | `{"detail": "Email already registered"}` |
| `422` | champ manquant ou email mal formé | `{"detail": [{"type": "...", "loc": ["body", "email"], "msg": "..."}]}` — ici `detail` est une liste d'objets, pas une string |

---

### `POST /login` — se connecter

**Body** (JSON) :
```json
{
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
```

**Réponse succès — `200`** : identique à `signup` (`tokens` + `user`).

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | mauvais mot de passe ou email inconnu | `{"detail": "Invalid credentials"}` |

Le message est identique dans les deux cas (email inconnu / mauvais mot de passe) : le serveur ne permet pas de distinguer les deux, pour ne pas révéler quels emails sont enregistrés.

---

### `GET /me` — profil de l'utilisateur connecté

**Headers requis :**
```
Authorization: Bearer <access_token>
```
Pas de body.

**Réponse succès — `200`** :
```json
{
  "id": 1,
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com"
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | header `Authorization` absent | `{"detail":"Not authenticated"}` |
| `401` | token invalide (signature fausse, malformé) | `{"detail":"Invalid token"}` |
| `401` | token expiré | `{"detail":"Token expired"}` |

---

### `POST /refresh` — renouveler l'access token

`refresh_token` est un **paramètre de requête**, pas un body JSON :
```
POST /refresh?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY
```

**Réponse succès — `200`** :
```json
{
  "access_token": "nouveau-token...",
  "refresh_token": "nouveau-refresh-token...",
  "token_type": "bearer"
}
```
Les deux tokens précédemment stockés côté client doivent être remplacés par ceux-ci — l'ancien `refresh_token` est invalidé côté serveur dès cet appel.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | `refresh_token` invalide, déjà utilisé, ou inconnu | `{"detail": "Invalid token"}` |
| `401` | `refresh_token` expiré (plus de 7 jours) | `{"detail": "Token expired"}` |

---

### `POST /logout` — déconnexion

`refresh_token` en paramètre de requête, comme pour `refresh` :
```
POST /logout?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY
```

**Réponse succès — `200`**, body vide (`null`). Le `refresh_token` est supprimé côté serveur. La réponse est `200` que le token existait ou non côté serveur — elle ne renseigne jamais sur ce point.

---

## 5. Les schémas de données

- **`UserCreate`** *(entrée de `/signup`)* : `first_name`, `last_name`, `email`, `password`.
- **`UserLogin`** *(entrée de `/login`)* : `email`, `password`.
- **`UserRead`** *(sortie, dans `/me` et dans `user` de `signup`/`login`)* : `id`, `first_name`, `last_name`, `email`. Ne contient jamais le mot de passe ou son hash.
- **`TokenResponse`** *(sortie de `/refresh`, et dans `tokens` de `signup`/`login`)* : `access_token`, `refresh_token`, `token_type` (toujours `"bearer"`).
- **`LoginResponse`** *(sortie de `/signup` et `/login`)* : `tokens: TokenResponse` + `user: UserRead`.

---

## 6. Table récapitulative

| Méthode | Route | Auth requise | Body/Query | Réponse succès |
|---|---|---|---|---|
| `POST` | `/signup` | non | body JSON (`UserCreate`) | `200` `LoginResponse` |
| `POST` | `/login` | non | body JSON (`UserLogin`) | `200` `LoginResponse` |
| `GET` | `/me` | `Bearer <access_token>` | — | `200` `UserRead` |
| `POST` | `/refresh` | non (le refresh token fait foi) | query `?refresh_token=...` | `200` `TokenResponse` |
| `POST` | `/logout` | non (le refresh token fait foi) | query `?refresh_token=...` | `200` `null` |

---

## 7. Points d'attention

- Aucune route 2FA n'existe. Le modèle `User` a un champ `is_2fa_enabled`, mais il n'est pas exposé dans `UserRead` et aucun endpoint n'en dépend.
- Aucune route OAuth (Google/42) n'existe.
- Aucun rate limiting ni lockout sur `/login`.
- Aucune configuration CORS explicite sur le service — passer par la gateway (`/api/auth/...`) pour éviter les erreurs CORS dans le navigateur.
- Les durées de tokens (15 min / 7 jours) sont fixes dans le code du service, indépendamment des variables d'environnement `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS`.
