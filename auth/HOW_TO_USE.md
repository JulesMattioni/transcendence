# Auth Service — Usage Guide

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Auth](https://img.shields.io/badge/auth-JWT%20%2B%20TOTP%20%2B%20OAuth-8A2BE2)
![Status](https://img.shields.io/badge/status-active-brightgreen)

_Complete reference of the routes exposed by the `auth` service — for the
frontend and other services consuming it. For architecture, the data model
and configuration, see [README.md](README.md)._

## Table of contents

1. [Base URL](#1-base-url)
2. [Tokens](#2-tokens)
3. [Token storage](#3-token-storage)
4. [Routes — classic auth](#4-routes--classic-auth)
5. [Routes — OAuth login (Google & 42)](#5-routes--oauth-login-google--42)
6. [Route — email lookup](#6-route--email-lookup)
7. [Data schemas](#7-data-schemas)
8. [Summary table](#8-summary-table)
9. [Points of attention](#9-points-of-attention)

## 1. Base URL

All requests go through the gateway:

```
https://localhost:8443/api/auth/...
```

Full example: `https://localhost:8443/api/auth/signup`.

## 2. Tokens

Every completed login (signup, login without 2FA, login with 2FA verified, or
a finished Google/42 login) returns **two tokens**:

|                    | `access_token`                                                                | `refresh_token`                                                          |
| -------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Purpose               | Access protected routes (`/me`, and any other service validating the same JWT)     | Obtain a new `access_token` via `/refresh`                                      |
| Lifetime               | 15 min (configurable)                                                               | 7 days (configurable)                                                              |
| Where to send it         | `Authorization: Bearer <access_token>` header                                        | Query parameter on `/refresh` / `/logout`                                           |
| Revocable?                | No                                                                                      | Yes — stored in the DB, deleted on `logout`, replaced on every `refresh`               |

Two **temporary** tokens, never persisted, used only as an intermediate step:

|                    | `pending_token`                                                                                        | `exchange_code`                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Purpose               | Proves step 1 of login succeeded (password, Google **or** 42) and authorizes calling `/login/2fa/verify`     | Proves the OAuth callback (Google or 42) resolved an account and authorizes calling `/oauth/exchange` |
| Lifetime               | ~5 min (configurable)                                                                                          | ~30 seconds (configurable)                                                                     |
| Where to send it         | `Authorization: Bearer <pending_token>` header on `/login/2fa/verify`                                           | JSON body `{ "exchange_code": ... }` on `/oauth/exchange`                                        |
| Internal `type`           | `"2fa_pending"`                                                                                                    | `"oauth_exchange"`                                                                                  |

**Standard flow** (account without 2FA):

```text
1. signup or login
   -> { tokens: { access_token, refresh_token }, user }
   -> store both tokens + user info

2. every request to a protected route
   -> header "Authorization: Bearer <access_token>"

3. a request comes back 401 (access_token expired or invalid)
   -> call /refresh with the refresh_token
   -> replace BOTH access_token AND refresh_token with the new ones received
   -> retry the original request

4. logout
   -> call /logout with the refresh_token
   -> clear tokens + user on the client
```

**Login flow with 2FA** (password, Google or 42 — same mechanics):

```text
1. login (or Google/42 callback, if 2FA is enabled on the account)
   -> { pending_token }        (NO tokens, NO user at this stage)
   -> keep the pending_token in memory

2. login/2fa/verify
   -> header "Authorization: Bearer <pending_token>" + body { code }
   -> { tokens: { access_token, refresh_token }, user }
   -> identical to the standard flow from here on
```

On every `refresh`, the `refresh_token` changes (rotation): the old one
becomes invalid immediately. Reusing an already-consumed `refresh_token`
returns `401`.

If `/refresh` fails, there is no recoverable session: clear the local
session and redirect to login.

## 3. Token storage

Tokens are returned in the JSON response body — the server sets **no
cookie for session tokens**. Storage (memory, `localStorage`, etc.) and
transport are entirely the client's responsibility. The `pending_token` and
`exchange_code` are ephemeral and not meant to be persisted.

The only cookies set by the service are technical ones (`oauth_state_google`
and `oauth_state_ft`, `httpOnly`), one per provider, used internally to
secure the Google and 42 flows respectively — the frontend never needs to
read or handle them, the browser manages them on its own.

## 4. Routes — classic auth

### `POST /signup` — create an account

**Body** (JSON):

```json
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
```

All 4 fields are required. `email` must be a valid email address. No
complexity rule is enforced on `password`.

**Success response — `200`**: the account is created and the user is logged
in directly:

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

| Code  | When                              | Body |
| ------ | ----------------------------------- | ---- |
| `409`   | Email already exists                  | `{"detail": "Email already registered"}` |
| `422`   | Missing field or malformed email        | `{"detail": [{"type": "...", "loc": ["body", "email"], "msg": "..."}]}` — here `detail` is a list of objects, not a string |

### `POST /login` — log in

**Body** (JSON):

```json
{
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
```

**Success response — `200`, account WITHOUT 2FA**: identical to `signup`
(`tokens` + `user`).

**Success response — `200`, account WITH 2FA enabled**: the response is no
longer a `LoginResponse`:

```json
{
  "pending_token": "eyJhbGciOi...2fa_pending..."
}
```

This `pending_token` must be sent back (as an `Authorization: Bearer`
header, **not** a query param) to `/login/2fa/verify` along with the TOTP
code, to obtain real tokens.

| Code  | When                                                                       | Body |
| ------ | ----------------------------------------------------------------------------- | ---- |
| `401`   | Wrong password or unknown email (same message for both, to avoid revealing which emails exist) | `{"detail": "Invalid credentials"}` |

### `POST /login/2fa/verify` — verify the second factor at login

Second step of login for accounts protected by 2FA — whether the first step
was `/login` (password) or the Google/42 callback (§5).

**Required headers:**

```
Authorization: Bearer <pending_token>
```

**Body** (JSON):

```json
{ "code": "482913" }
```

**Success response — `200`**: identical to a classic login (`tokens` +
`user`).

| Code  | When                                        | Body |
| ------ | ---------------------------------------------- | ---- |
| `401`   | Invalid TOTP code                                 | `{"detail": "Invalid code"}` |
| `401`   | `pending_token` missing, invalid or expired         | `{"detail": "Invalid token"}` / `{"detail": "Token expired"}` |
| `401`   | User referenced by the `pending_token` not found      | `{"detail": "User not found"}` |

### `GET /me` — current user's profile

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Success response — `200`**:

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

| Code  | When                                       | Body |
| ------ | --------------------------------------------- | ---- |
| `401`   | `Authorization` header missing                   | `{"detail":"Not authenticated"}` |
| `401`   | Invalid token (bad signature, malformed)            | `{"detail":"Invalid token"}` |
| `401`   | Expired token                                          | `{"detail":"Token expired"}` |

### `POST /2fa/enable` — start enabling 2FA

Generates a TOTP secret for the current user. **2FA is not active yet** at
this stage — it must be confirmed via `/2fa/enable/verify`.

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Success response — `200`**:

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "otpauth_uri": "otpauth://totp/Keepr:ada@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Keepr"
}
```

- `secret`: the string to type manually into an authenticator app.
- `otpauth_uri`: the URI to encode as a **QR code on the client side**. The
  service does not generate an image.

| Code  | When                              | Body |
| ------ | ------------------------------------ | ---- |
| `409`   | 2FA is already enabled on this account | `{"detail": "2FA already enabled"}` |

### `POST /2fa/enable/verify` — confirm enabling 2FA

Confirms the authenticator app is correctly configured. Only here does
`is_2fa_enabled` flip to `true`.

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Body** (JSON):

```json
{ "code": "482913" }
```

**Success response — `200`**, empty body (`null`).

| Code  | When                                    | Body |
| ------ | ------------------------------------------ | ---- |
| `401`   | Invalid TOTP code                             | `{"detail": "Invalid code"}` |
| `401`   | 2FA not configured (no pending secret)          | `{"detail": "2FA not configured"}` |

### `POST /2fa/disable` — disable 2FA

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Success response — `200`**: the updated `UserRead` (`is_2fa_enabled` back
to `false`).

| Code  | When                          | Body |
| ------ | -------------------------------- | ---- |
| `401`   | 2FA is not enabled on this account | `{"detail": "2FA not configured"}` |

### `PATCH /update` — update the profile

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Body** (JSON):

```json
{
  "location": "Paris",
  "avatar_id": 3
}
```

`location` and `avatar_id` are **both required** — no partial update of a
single field.

**Success response — `200`**: the updated `UserRead`.

### `POST /refresh` — renew the access token

`refresh_token` is a **query parameter**, not a JSON body:

```
POST /refresh?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY
```

**Success response — `200`**:

```json
{
  "access_token": "new-token...",
  "refresh_token": "new-refresh-token...",
  "token_type": "bearer"
}
```

Both tokens previously stored on the client must be replaced — the old
`refresh_token` is invalidated server-side as soon as this call is made.

| Code  | When                                          | Body |
| ------ | ------------------------------------------------ | ---- |
| `401`   | `refresh_token` invalid, already used, or unknown   | `{"detail": "Invalid token"}` |
| `401`   | `refresh_token` expired (older than 7 days)           | `{"detail": "Token expired"}` |

### `POST /logout` — log out

`refresh_token` is a query parameter, same as `refresh`:

```
POST /logout?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY
```

**Success response — `200`**, empty body (`null`). The response is `200`
whether or not the token existed server-side — it never reveals which.

## 5. Routes — OAuth login (Google & 42)

Unlike the routes above, this flow **is not a series of plain `fetch`
calls**: it involves real browser redirects, because the provider (Google or
42) itself redirects the user outside of the application. Both providers
follow **the exact same mechanics** — only the URLs and the technical
cookie's name differ.

```text
1. GET /oauth/google/login   (or GET /oauth/42/login)
   -> { authorization_url: "https://accounts.google.com/..." }   (or "https://api.intra.42.fr/oauth/authorize?...")
   -> the frontend itself does window.location.href = authorization_url

2. the user logs in / consents with the provider
   -> the auth service is not involved at this stage

3. the provider redirects the browser to GET /oauth/google/callback (or /oauth/42/callback)
   -> the auth service resolves the account (already linked, to be linked, or brand new)
   -> it redirects the browser AGAIN, this time to the frontend:

   IF 2FA is enabled on this account:
     {FRONTEND_URL}/oauth/callback?pending_token=...
     -> handle it EXACTLY like step 2 of the classic 2FA flow (§4),
        calling /login/2fa/verify with this pending_token

   OTHERWISE:
     {FRONTEND_URL}/oauth/callback?exchange_code=...
     -> the frontend reads this parameter from the URL and calls:

4. POST /oauth/exchange { exchange_code }
   -> { tokens: { access_token, refresh_token }, user }
   -> identical to a successful classic login, from here on
   -> this route is UNIQUE and shared by both providers: it only decodes the
      exchange_code (JWT type="oauth_exchange"), it doesn't know and doesn't
      need to know where the user came from
```

**What the frontend must build**: a `{FRONTEND_URL}/oauth/callback`
page/route that reads the URL's query params, common to both providers:

```js
const params = new URLSearchParams(window.location.search);
const pendingToken = params.get("pending_token");
const exchangeCode = params.get("exchange_code");
```

No need to decode anything, or to know whether the user came from Google or
42 — the presence of one parameter or the other is enough to know what to do
next.

### 5.1 Google

#### `GET /oauth/google/login` — start Google login

No authentication, no body.

**Success response — `200`**:

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=openid+email+profile&state=..."
}
```

The frontend must navigate the browser to this URL
(`window.location.href = ...`), not just display the response. A technical
`oauth_state_google` cookie (`httpOnly`, 10 min) is set at this stage.

#### `GET /oauth/google/callback` — never called directly by the frontend

This route is the `redirect_uri` registered with Google — it is only ever
reached by the browser's redirect following Google's consent screen, never
by a `fetch` from the frontend.

**Response**: a redirect (`307`) to
`{FRONTEND_URL}/oauth/callback?pending_token=...` or
`?exchange_code=...`, depending on whether 2FA is enabled on the resolved
account.

| Code  | When                                                                                    | Body |
| ------ | -------------------------------------------------------------------------------------------- | ---- |
| `401`   | `state` missing, invalid, or not matching the `oauth_state_google` cookie set by `/oauth/google/login` | `{"detail": "OAuth state error"}` |
| `400`   | Google rejects the `code` (expired, already used, invalid)                                       | `{"detail": "Google authentication failed"}` |

### 5.2 42

#### `GET /oauth/42/login` — start 42 login

No authentication, no body. Same response contract as Google — the frontend
shouldn't need to distinguish the two before calling
`window.location.href`.

**Success response — `200`**:

```json
{
  "authorization_url": "https://api.intra.42.fr/oauth/authorize?client_id=...&redirect_uri=...&scope=public&state=..."
}
```

The frontend must navigate the browser to this URL. A technical
`oauth_state_ft` cookie (`httpOnly`, 10 min) is set at this stage — distinct
from the Google cookie, so both flows can coexist without interfering.

#### `GET /oauth/42/callback` — never called directly by the frontend

This route is the `redirect_uri` registered on the 42 intranet
([profile.intra.42.fr/oauth/applications](https://profile.intra.42.fr/oauth/applications))
— it is only ever reached by the browser's redirect following 42's consent
screen, never by a `fetch` from the frontend.

**Response**: a redirect (`307`) to
`{FRONTEND_URL}/oauth/callback?pending_token=...` or `?exchange_code=...`,
depending on whether 2FA is enabled on the resolved account — identical to
Google from here on.

| Code  | When                                                                            | Body |
| ------ | ------------------------------------------------------------------------------------ | ---- |
| `401`   | `state` missing, invalid, or not matching the `oauth_state_ft` cookie set by `/oauth/42/login` | `{"detail": "OAuth state error"}` |
| `400`   | 42 rejects the `code` (expired, already used, invalid)                                   | `{"detail": "42 authentication failed"}` |

### 5.3 Finalizing the login (shared by Google & 42)

#### `POST /oauth/exchange` — finalize the OAuth login

**Body** (JSON):

```json
{ "exchange_code": "eyJhbGciOi...oauth_exchange..." }
```

The `exchange_code` received as a query param on
`{FRONTEND_URL}/oauth/callback`, whether it came from the Google or the 42
callback — a single shared route, no per-provider variant.

**Success response — `200`**: identical to a successful classic login
(`tokens` + `user`).

| Code  | When                                             | Body |
| ------ | ----------------------------------------------------- | ---- |
| `401`   | `exchange_code` invalid, malformed, or of the wrong type | `{"detail": "Invalid token"}` |
| `401`   | `exchange_code` expired (~30s)                             | `{"detail": "Token expired"}` |
| `401`   | User not found                                                | `{"detail": "User not found"}` |

## 6. Route — email lookup

### `GET /users/by-email` — find a user by email

Designed for inter-service use (org, core) via the shared auth dependency,
rather than for direct calls from the UI — but reachable by anyone holding a
valid `access_token`.

**Required headers:**

```
Authorization: Bearer <access_token>
```

**Query param:**

```
GET /users/by-email?email=ada@example.com
```

**Success response — `200`**:

```json
{
  "id": 1,
  "email": "ada@example.com",
  "first_name": "Ada",
  "last_name": "Lovelace"
}
```

| Code  | When                              | Body |
| ------ | ------------------------------------ | ---- |
| `404`   | No user with this email                | `{"detail": "No user with this email"}` |
| `401`   | No valid `access_token`                  | `{"detail":"Invalid token"}` / `{"detail":"Not authenticated"}` |

## 7. Data schemas

| Schema                | Fields                                                                                         | Used in |
| ------------------------ | -------------------------------------------------------------------------------------------------- | ------- |
| `UserCreate`               | `first_name`, `last_name`, `email`, `password`                                                       | `/signup` input |
| `UserLogin`                | `email`, `password`                                                                                     | `/login` input |
| `UserUpdate`                | `location`, `avatar_id` (both required)                                                                  | `/update` input |
| `TwoFactorVerify`             | `code`                                                                                                      | `/login/2fa/verify`, `/2fa/enable/verify` input |
| `OAuthExchange`                | `exchange_code`                                                                                               | `/oauth/exchange` input |
| `UserRead`                       | `id`, `first_name`, `last_name`, `email`, `location` (or `null`), `avatar_id`, `is_2fa_enabled`                | `/me`, `/update`, `/2fa/disable` output, and the `user` field of `signup`/`login`/`login/2fa/verify`/`oauth/exchange`. Never contains a password, hash, or 2FA secret. |
| `UserLookup`                       | `id`, `email`, `first_name`, `last_name`                                                                          | `/users/by-email` output |
| `TokenResponse`                       | `access_token`, `refresh_token`, `token_type` (always `"bearer"`)                                                    | `/refresh` output, and the `tokens` field of `signup`/`login`/`login/2fa/verify`/`oauth/exchange` |
| `LoginResponse`                          | `tokens: TokenResponse` + `user: UserRead`                                                                             | `/signup`, `/login` (no 2FA), `/login/2fa/verify`, `/oauth/exchange` output |
| `TwoFactorRequired`                        | `pending_token`                                                                                                            | `/login` and Google/42 callback output, when 2FA is enabled |
| `TwoFactorCredentials`                        | `secret`, `otpauth_uri`                                                                                                       | `/2fa/enable` output |
| `OAuthRedirect`                                  | `authorization_url`                                                                                                              | `/oauth/google/login` and `/oauth/42/login` output |

## 8. Summary table

| Method | Route                       | Auth required                | Body/Query                    | Success response |
| ------- | ----------------------------- | -------------------------------- | -------------------------------- | ------------------- |
| `POST`   | `/signup`                       | no                                  | body (`UserCreate`)                 | `200` `LoginResponse` |
| `POST`   | `/login`                         | no                                  | body (`UserLogin`)                    | `200` `LoginResponse` or `TwoFactorRequired` |
| `POST`   | `/login/2fa/verify`               | `Bearer <pending_token>`              | body (`TwoFactorVerify`)                | `200` `LoginResponse` |
| `GET`    | `/me`                               | `Bearer <access_token>`                 | —                                          | `200` `UserRead` |
| `POST`   | `/2fa/enable`                         | `Bearer <access_token>`                   | —                                            | `200` `TwoFactorCredentials` |
| `POST`   | `/2fa/enable/verify`                    | `Bearer <access_token>`                     | body (`TwoFactorVerify`)                        | `200` `null` |
| `POST`   | `/2fa/disable`                            | `Bearer <access_token>`                       | —                                                  | `200` `UserRead` |
| `PATCH`  | `/update`                                    | `Bearer <access_token>`                         | body (`UserUpdate`)                                   | `200` `UserRead` |
| `POST`   | `/refresh`                                      | no (refresh token is the credential)              | query `?refresh_token=...`                              | `200` `TokenResponse` |
| `POST`   | `/logout`                                          | no (refresh token is the credential)                | query `?refresh_token=...`                                | `200` `null` |
| `GET`    | `/oauth/google/login`                                 | no                                                     | —                                                            | `200` `OAuthRedirect` |
| `GET`    | `/oauth/google/callback`                                 | no (called by Google)                                    | query `?code=...&state=...`                                    | redirect to the frontend |
| `GET`    | `/oauth/42/login`                                           | no                                                          | —                                                                  | `200` `OAuthRedirect` |
| `GET`    | `/oauth/42/callback`                                           | no (called by 42)                                             | query `?code=...&state=...`                                          | redirect to the frontend |
| `POST`   | `/oauth/exchange`                                                 | no (exchange_code is the credential)                             | body (`OAuthExchange`)                                                  | `200` `LoginResponse` |
| `GET`    | `/users/by-email`                                                    | `Bearer <access_token>`                                            | query `?email=...`                                                        | `200` `UserLookup` |

## 9. Points of attention

- The login flow **depends on the account's 2FA state**, whether the login
  happens by password, Google, or 42: the client must always handle both
  possible response shapes.
- The `is_2fa_enabled` field is exposed in `UserRead`.
- Enabling 2FA happens in **two steps** (`/2fa/enable` then
  `/2fa/enable/verify`): the secret is generated at the first step, but 2FA
  only becomes active after a code is confirmed — this avoids locking out a
  user whose authenticator app was misconfigured.
- The service **does not generate a QR code image**: it returns the
  `otpauth_uri`, to be encoded as a QR code on the client.
- Google and 42 are both implemented with the exact same mechanics
  (redirect → callback → `pending_token`/`exchange_code` →
  `/oauth/exchange`). A Google account and a 42 account can both link to the
  same `User` if they share the same email.
- The `oauth_state_google` and `oauth_state_ft` technical cookies are
  independent: starting the Google flow then the 42 flow (or vice versa) in
  the same tab doesn't break anything — each callback only looks at its own
  cookie.
- No rate limiting or lockout on `/login`.
- No explicit CORS configuration on the service — go through the gateway
  (`/api/auth/...`) to avoid browser CORS errors.
- Token lifetimes are controlled by the environment variables
  `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15 min), `REFRESH_TOKEN_EXPIRE_DAYS`
  (default 7 days), `TEMPORARY_TOKEN_EXPIRE_MINUTES` (`pending_token`
  lifetime, default ~5 min) and `OAUTH_EXCHANGE_EXPIRE_SECONDS`
  (`exchange_code` lifetime, default ~30s).
- `FRONTEND_URL` determines where the Google and 42 callbacks redirect the
  browser — keep it in sync with the frontend team if that URL changes.

[Back to top](#auth-service--usage-guide)
