# Comment utiliser le service `auth`

Ce document décrit comment dialoguer avec le service `auth` : les routes disponibles, ce qu'il faut envoyer, ce qu'on reçoit en retour, et comment gérer les tokens côté client.

Ce guide couvre : signup, login, login 2FA, refresh, logout, `/me`, la gestion de la 2FA (activation, confirmation, désactivation) et la mise à jour du profil. Il n'existe aucune route OAuth (Google/42) dans le service.

---

## 1. Où taper

Toutes les requêtes passent par la gateway :

```
https://localhost:8443/api/auth/...
```

Exemple complet : `https://localhost:8443/api/auth/signup`.

---

## 2. Le principe général : deux tokens

Chaque connexion complète (signup, ou login sans 2FA, ou login 2FA validé) donne **deux tokens**, avec des rôles différents :

| | `access_token` | `refresh_token` |
|---|---|---|
| Sert à | accéder aux routes protégées (`/me`, et les autres services qui valident ce même JWT) | obtenir un nouvel `access_token` sur `/refresh` |
| Durée de vie | 15 minutes (configurable, voir §7) | 7 jours (configurable, voir §7) |
| Où l'envoyer | header `Authorization: Bearer <access_token>` | paramètre de requête sur `/refresh` / `/logout` |
| Révocable ? | non | oui — stocké en base, supprimé au `logout` et remplacé à chaque `refresh` |

Il existe un **troisième** token, temporaire, utilisé uniquement pour le login des comptes protégés par 2FA :

| | `pending_token` |
|---|---|
| Sert à | prouver qu'on a passé l'étape 1 du login (email + mot de passe) et autoriser l'appel à `/login/2fa/verify` |
| Durée de vie | ~5 minutes (configurable, voir §7) |
| Où l'envoyer | header `Authorization: Bearer <pending_token>` sur `/login/2fa/verify` |
| Type interne | `"2fa_pending"` (distinct de l'access token) |

Flow standard (compte **sans** 2FA) :

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

Flow login (compte **avec** 2FA activée) :

```
1. login (email + password)
   → { pending_token }        (PAS de tokens ni de user à ce stade)
   → conserver le pending_token en mémoire

2. login/2fa/verify
   → header "Authorization: Bearer <pending_token>" + body { code }
   → { tokens: { access_token, refresh_token }, user }
   → à partir d'ici, identique au flow standard
```

À chaque `refresh`, le `refresh_token` change (rotation) : l'ancien devient invalide immédiatement. Réutiliser un `refresh_token` déjà consommé renvoie `401`.

Si `/refresh` échoue, il n'y a pas de session récupérable : effacer la session locale et rediriger vers le login.

---

## 3. Stockage des tokens

Les tokens sont renvoyés dans le corps JSON de la réponse — le serveur ne pose aucun cookie. Le stockage (mémoire, `localStorage`, etc.) et le transport sont entièrement à la charge du client. Le `pending_token` est éphémère (~5 min) et n'a pas vocation à être persisté : garde-le en mémoire le temps de l'étape `/login/2fa/verify`.

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
    "email": "ada@example.com",
    "location": null,
    "avatar_id": 1,
    "is_2fa_enabled": false
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

**Réponse succès — `200`, compte SANS 2FA** : identique à `signup` (`tokens` + `user`).

**Réponse succès — `200`, compte AVEC 2FA activée** : la réponse **n'est plus** un `LoginResponse`. Elle contient uniquement un `pending_token` :
```json
{
  "pending_token": "eyJhbGciOi...2fa_pending..."
}
```
Ce `pending_token` doit être renvoyé (en header `Authorization: Bearer`, **pas** en query) à `/login/2fa/verify` avec le code TOTP pour obtenir les vrais tokens. Tant que cette étape n'est pas faite, l'utilisateur n'est pas connecté.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | mauvais mot de passe ou email inconnu | `{"detail": "Invalid credentials"}` |

Le message est identique dans les deux cas (email inconnu / mauvais mot de passe) : le serveur ne permet pas de distinguer les deux, pour ne pas révéler quels emails sont enregistrés.

---

### `POST /login/2fa/verify` — valider le second facteur au login

Deuxième étape du login pour les comptes protégés par 2FA.

**Headers requis :**
```
Authorization: Bearer <pending_token>
```
(le `pending_token` reçu de `/login`, **pas** l'access token)

**Body** (JSON) :
```json
{
  "code": "482913"
}
```

**Réponse succès — `200`** : identique à un login classique (`tokens` + `user`) :
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
    "email": "ada@example.com",
    "location": null,
    "avatar_id": 1,
    "is_2fa_enabled": true
  }
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | code TOTP invalide | `{"detail": "Invalid code"}` |
| `401` | `pending_token` absent, invalide ou expiré | `{"detail": "Invalid token"}` / `{"detail": "Token expired"}` |
| `401` | user du `pending_token` introuvable | `{"detail": "User not found"}` |

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
  "email": "ada@example.com",
  "location": null,
  "avatar_id": 1,
  "is_2fa_enabled": false
}
```

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | header `Authorization` absent | `{"detail":"Not authenticated"}` |
| `401` | token invalide (signature fausse, malformé) | `{"detail":"Invalid token"}` |
| `401` | token expiré | `{"detail":"Token expired"}` |

---

### `POST /2fa/enable` — démarrer l'activation de la 2FA

Génère un secret TOTP pour l'utilisateur connecté et renvoie de quoi configurer une application d'authentification. **La 2FA n'est pas encore active** à ce stade : il faut confirmer avec `/2fa/enable/verify`.

**Headers requis :**
```
Authorization: Bearer <access_token>
```
Pas de body.

**Réponse succès — `200`** :
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "otpauth_uri": "otpauth://totp/Keepr:ada@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Keepr"
}
```
- `secret` : la chaîne à saisir manuellement dans l'application d'authentification.
- `otpauth_uri` : l'URI à encoder en **QR code côté client**. Le service ne génère pas d'image — le frontend transforme cette chaîne en QR (librairie JS de type `qrcode`).

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `409` | la 2FA est déjà active sur ce compte | `{"detail": "2FA already enabled"}` |

---

### `POST /2fa/enable/verify` — confirmer l'activation de la 2FA

Confirme que l'application d'authentification est bien configurée en validant un premier code. C'est seulement ici que `is_2fa_enabled` passe à `True`.

**Headers requis :**
```
Authorization: Bearer <access_token>
```

**Body** (JSON) :
```json
{
  "code": "482913"
}
```

**Réponse succès — `200`**, body vide (`null`) : la 2FA est désormais active sur le compte.

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | code TOTP invalide | `{"detail": "Invalid code"}` |
| `401` | 2FA non configurée (aucun secret en attente) | `{"detail": "2FA not configured"}` |

---

### `POST /2fa/disable` — désactiver la 2FA

Désactive la 2FA pour l'utilisateur connecté.

**Headers requis :**
```
Authorization: Bearer <access_token>
```
Pas de body.

**Réponse succès — `200`** : le `UserRead` à jour (`is_2fa_enabled` repassé à `false`).

**Erreurs :**

| Code | Quand | Body |
|---|---|---|
| `401` | 2FA non active sur ce compte | `{"detail": "2FA not configured"}` |

---

### `PATCH /update` — mettre à jour le profil

Met à jour le `location` et l'`avatar_id` de l'utilisateur connecté.

**Headers requis :**
```
Authorization: Bearer <access_token>
```

**Body** (JSON) :
```json
{
  "location": "Paris",
  "avatar_id": 3
}
```
`location` et `avatar_id` sont **tous les deux obligatoires** : il n'y a pas de mise à jour partielle d'un seul champ.

**Réponse succès — `200`** : le `UserRead` à jour.

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
- **`UserUpdate`** *(entrée de `/update`)* : `location`, `avatar_id` (les deux obligatoires).
- **`TwoFactorVerify`** *(entrée de `/login/2fa/verify` et `/2fa/enable/verify`)* : `code`.
- **`UserRead`** *(sortie, dans `/me`, `/update`, `/2fa/disable` et dans `user` de `signup`/`login`/`login/2fa/verify`)* : `id`, `first_name`, `last_name`, `email`, `location` (string ou `null`), `avatar_id` (int), `is_2fa_enabled` (bool). Ne contient jamais le mot de passe, son hash, ni le secret 2FA.
- **`TokenResponse`** *(sortie de `/refresh`, et dans `tokens` de `signup`/`login`/`login/2fa/verify`)* : `access_token`, `refresh_token`, `token_type` (toujours `"bearer"`).
- **`LoginResponse`** *(sortie de `/signup`, `/login` sans 2FA, et `/login/2fa/verify`)* : `tokens: TokenResponse` + `user: UserRead`.
- **`TwoFactorRequired`** *(sortie de `/login` quand la 2FA est active)* : `pending_token`.
- **`TwoFactorCredentials`** *(sortie de `/2fa/enable`)* : `secret`, `otpauth_uri`.

---

## 6. Table récapitulative

| Méthode | Route | Auth requise | Body/Query | Réponse succès |
|---|---|---|---|---|
| `POST` | `/signup` | non | body JSON (`UserCreate`) | `200` `LoginResponse` |
| `POST` | `/login` | non | body JSON (`UserLogin`) | `200` `LoginResponse` (sans 2FA) ou `TwoFactorRequired` (avec 2FA) |
| `POST` | `/login/2fa/verify` | `Bearer <pending_token>` | body JSON (`TwoFactorVerify`) | `200` `LoginResponse` |
| `GET` | `/me` | `Bearer <access_token>` | — | `200` `UserRead` |
| `POST` | `/2fa/enable` | `Bearer <access_token>` | — | `200` `TwoFactorCredentials` |
| `POST` | `/2fa/enable/verify` | `Bearer <access_token>` | body JSON (`TwoFactorVerify`) | `200` `null` |
| `POST` | `/2fa/disable` | `Bearer <access_token>` | — | `200` `UserRead` |
| `PATCH` | `/update` | `Bearer <access_token>` | body JSON (`UserUpdate`) | `200` `UserRead` |
| `POST` | `/refresh` | non (le refresh token fait foi) | query `?refresh_token=...` | `200` `TokenResponse` |
| `POST` | `/logout` | non (le refresh token fait foi) | query `?refresh_token=...` | `200` `null` |

---

## 7. Points d'attention

- Le flow de login **dépend de l'état 2FA** du compte : sans 2FA, `/login` renvoie directement les tokens ; avec 2FA, il renvoie un `pending_token` à valider via `/login/2fa/verify`. Le client doit gérer les deux cas (tester la présence de `pending_token` vs `tokens` dans la réponse).
- Le champ `is_2fa_enabled` est désormais **exposé dans `UserRead`** (utile pour que le front sache s'il doit afficher le flow 2FA).
- L'activation de la 2FA se fait en **deux temps** (`/2fa/enable` puis `/2fa/enable/verify`) : le secret est généré à la première étape mais la 2FA n'est active qu'après confirmation d'un code, pour éviter de verrouiller un utilisateur dont l'application d'authentification serait mal configurée.
- Le service **ne génère pas d'image de QR code** : il renvoie l'`otpauth_uri`, à encoder en QR côté client.
- Aucune route OAuth (Google/42) n'existe.
- Aucun rate limiting ni lockout sur `/login`.
- Aucune configuration CORS explicite sur le service — passer par la gateway (`/api/auth/...`) pour éviter les erreurs CORS dans le navigateur.
- Les durées de tokens sont désormais pilotées par les variables d'environnement `ACCESS_TOKEN_EXPIRE_MINUTES` (défaut 15 min), `REFRESH_TOKEN_EXPIRE_DAYS` (défaut 7 jours) et `TEMPORARY_TOKEN_EXPIRE_MINUTES` (durée du `pending_token`, défaut ~5 min). Elles sont bien prises en compte par le service.