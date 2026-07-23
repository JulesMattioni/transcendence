# Auth Service

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Auth](https://img.shields.io/badge/auth-JWT%20%2B%20TOTP%20%2B%20OAuth-8A2BE2)
![Status](https://img.shields.io/badge/status-active-brightgreen)

_Identity provider for the [Keepr](../README.md) platform — sign-up, login, JWT
sessions, TOTP two-factor authentication, and OAuth (Google / 42)._

This service owns everything related to **who a user is**: credentials,
sessions and identity federation. It does not know about organisations,
documents or permissions — that's [`org`](../org/README.md) and
[`core`](../core/README.md). See the [root README](../README.md) for how it
fits into the rest of the platform.

## Table of contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Features](#3-features)
4. [Tech stack](#4-tech-stack)
5. [API reference](#5-api-reference)
6. [Authentication model](#6-authentication-model)
7. [Two-factor authentication flow](#7-two-factor-authentication-flow)
8. [OAuth flow (Google & 42)](#8-oauth-flow-google--42)
9. [Realtime event notifications](#9-realtime-event-notifications)
10. [Data model](#10-data-model)
11. [Error reference](#11-error-reference)
12. [Configuration](#12-configuration)
13. [Project structure](#13-project-structure)
14. [Getting started](#14-getting-started)
15. [Related documentation](#15-related-documentation)

## 1. Overview

### 1.1 Responsibilities

- Register users and authenticate them with **email + password**.
- Issue and rotate **JWT access/refresh tokens**.
- Enforce optional **TOTP two-factor authentication** on login.
- Authenticate users via **OAuth** (Google, 42) and link/create accounts.
- Expose a minimal **public user profile** to other services (`/me`,
  `/users/by-email`).
- Notify the `realtime` service of login/logout events (best-effort).

### 1.2 Non-goals

- **No authorization/RBAC** — role and organisation membership checks live in
  [`org`](../org/README.md). This service only answers "who is this user?",
  never "what can they do?".
- **No document or business data** — it stores users, tokens and OAuth links
  only.
- **No token introspection endpoint for other services** — services validate
  JWTs themselves (shared `SECRET_KEY`/`ALGORITHM`); `auth` doesn't proxy that.

## 2. Architecture

### 2.1 Where it sits in the platform

```
 Browser ──HTTPS──▶ gateway (Nginx + WAF) ──/api/auth/*──▶ auth (this service)
                                                                │
                                          ┌─────────────────────┼───────────────────────┐
                                          ▼                     ▼                        ▼
                                    PostgreSQL 16          realtime service        Google / 42
                                 (users, tokens,          (auth.login /            OAuth providers
                                  oauth_accounts)           auth.logout,
                                                             best-effort)
```

The gateway is the only public entry point ([gateway/README.md](../gateway/README.md));
`auth` itself is only reachable on the internal Docker network. All routes
documented below are **relative to this service** — externally they're
prefixed with `/api/auth` (e.g. `POST /login` → `POST /api/auth/login`).

### 2.2 Internal layering

```
routers/            HTTP layer — request parsing, status codes, response models
  auth.py             signup, login, 2FA, refresh, logout, profile
  oauth.py             Google / 42 redirect, callback, code exchange
  health.py             liveness check
        │
        ▼
services/
  auth_service.py     business logic — orchestrates repositories + the
                       realtime client, owns DB transactions (commit/rollback)
        │
        ▼
repositories/
  user_repository.py      User persistence
  token_repository.py     RefreshToken persistence
  oauth_repository.py     OAuthAccount persistence
        │
        ▼
     PostgreSQL (shared database — see migrations/)
```

Alongside the repositories, two more building blocks are injected into
`AuthService` via FastAPI's `Depends()` (see [`dependencies.py`](app/dependencies.py)):

- **`clients/realtime_client.py`** — outbound HTTP client that notifies the
  `realtime` service of auth events (see [§9](#9-realtime-event-notifications)).
- **`core/`** — stateless helpers with no state of their own: password hashing
  (`security.py`), JWT encode/decode (`tokens.py`), and OAuth profile fetching
  (`google_oauth.py`, `ft_oauth.py`).

## 3. Features

- Email/password signup and login.
- JWT access tokens + rotating refresh tokens.
- TOTP-based 2FA (enable, verify, disable), compatible with any authenticator
  app (Google Authenticator, Authy, ...).
- OAuth login via **Google** and **42**, with automatic account creation or
  linking by email.
- Profile update (location, avatar).
- Public user lookup by email (for other services to resolve a name/id).
- Best-effort realtime notification of login/logout events.
- `/health` liveness endpoint.

## 4. Tech stack

| Layer            | Choice                                              |
| ----------------- | --------------------------------------------------- |
| Framework         | [FastAPI](https://fastapi.tiangolo.com/) (async)    |
| ORM               | SQLAlchemy 2.0 (async) + [asyncpg](https://github.com/MagicStack/asyncpg) |
| Migrations         | Alembic (shared chain, see [migrations/](../migrations/README.md)) |
| Validation         | Pydantic v2                                         |
| Passwords          | Passlib (bcrypt)                                     |
| JWT                | PyJWT (HS256)                                       |
| 2FA / TOTP         | PyOTP                                                |
| Outbound HTTP      | httpx (async)                                       |
| Server             | Uvicorn                                             |

## 5. API reference

> **Note on parameters.** Endpoints below that take a bare scalar parameter
> (`refresh_token`, `email`) declare it as a plain `str` with no `Body()`
> annotation. FastAPI treats un-annotated scalar parameters as **query
> parameters**, even on `POST` — so these must be sent as `?refresh_token=...`,
> not as a JSON body. Anything typed as a Pydantic model (`UserCreate`,
> `UserLogin`, ...) is sent as a JSON body, as usual.

### 5.1 Authentication & session

| Method | Path                | Auth                    | Request                          | Response                            | Description |
| ------ | -------------------- | ------------------------ | --------------------------------- | ------------------------------------ | ----------- |
| POST   | `/signup`             | —                         | `UserCreate` (body)                | `LoginResponse`                      | Register a user, hash the password, issue tokens, emit `auth.login`. |
| POST   | `/login`               | —                         | `UserLogin` (body)                 | `LoginResponse` \| `TwoFactorRequired` | Authenticate with email/password. Returns tokens directly, or a `pending_token` if 2FA is enabled. |
| POST   | `/login/2fa/verify`    | Bearer `pending_token`    | `TwoFactorVerify` (body)           | `LoginResponse`                      | Complete login by verifying the TOTP code. Emits `auth.login`. |
| POST   | `/refresh`             | —                         | `refresh_token` (query)            | `TokenResponse`                      | Rotate a refresh token: old one deleted, new access/refresh pair issued. |
| POST   | `/logout`              | —                         | `refresh_token` (query)            | —                                     | Revoke a refresh token (no-op if unknown). Emits `auth.logout`. |
| GET    | `/me`                  | Bearer access token       | —                                  | `UserRead`                           | Return the authenticated user's profile. |
| PATCH  | `/update`              | Bearer access token       | `UserUpdate` (body)                 | `UserRead`                           | Update `location` and `avatar_id`. |
| GET    | `/users/by-email`      | Bearer access token       | `email` (query)                    | `UserLookup`                          | Look up another user's public info by email (used by other services). |

### 5.2 Two-factor authentication (TOTP)

| Method | Path                | Auth                  | Request                 | Response                | Description |
| ------ | -------------------- | ----------------------- | ------------------------- | -------------------------- | ----------- |
| POST   | `/2fa/enable`         | Bearer access token       | —                          | `TwoFactorCredentials`      | Generate a TOTP secret + provisioning URI. 2FA is **not** active yet. |
| POST   | `/2fa/enable/verify`  | Bearer access token       | `TwoFactorVerify` (body)   | —                            | Verify the first code and set `is_2fa_enabled = true`. |
| POST   | `/2fa/disable`        | Bearer access token       | —                          | `UserRead`                   | Disable 2FA for the current user. |

### 5.3 OAuth (Google & 42)

| Method | Path                    | Auth | Request                                                     | Response                              | Description |
| ------ | ------------------------ | ---- | ------------------------------------------------------------ | --------------------------------------- | ----------- |
| GET    | `/oauth/google/login`     | —    | —                                                              | `OAuthRedirect` (+ sets `oauth_state_google` cookie) | Build the Google authorization URL, set a CSRF state cookie. |
| GET    | `/oauth/google/callback`  | —    | `code`, `state` (query) + `oauth_state_google` cookie          | 302 → frontend                          | Validate `state`, fetch the profile, redirect with `pending_token` or `exchange_code`. |
| GET    | `/oauth/42/login`         | —    | —                                                              | `OAuthRedirect` (+ sets `oauth_state_ft` cookie) | Same flow, 42. |
| GET    | `/oauth/42/callback`      | —    | `code`, `state` (query) + `oauth_state_ft` cookie               | 302 → frontend                          | Same flow, 42. |
| POST   | `/oauth/exchange`         | —    | `OAuthExchange` (body: `exchange_code`)                          | `LoginResponse`                          | Exchange the one-time code for real tokens. Emits `auth.login`. |

### 5.4 Health

| Method | Path      | Auth | Response                                     | Description |
| ------ | ---------- | ---- | ---------------------------------------------- | ----------- |
| GET    | `/health`   | —    | `{"status": "ok", "service": "auth"}`            | Liveness check. |

## 6. Authentication model

### 6.1 Token types & lifetimes

| Type                 | `type` claim    | Issued by                                        | Default lifetime                        | Purpose |
| --------------------- | ---------------- | -------------------------------------------------- | ------------------------------------------ | ------- |
| Access token           | `access`          | signup, login, login_2fa, refresh, oauth exchange   | 15 min (`ACCESS_TOKEN_EXPIRE_MINUTES`)      | Bearer token for authenticated endpoints. |
| Refresh token           | *(opaque string, not a JWT)* | same as above                          | 7 days (`REFRESH_TOKEN_EXPIRE_DAYS`), persisted in `tokens` | Exchanged via `/refresh`; revoked via `/logout`. |
| Pending-2FA token       | `2fa_pending`     | `/login` when `is_2fa_enabled` is true              | 5 min (`TEMPORARY_TOKEN_EXPIRE_MINUTES`)    | Identifies the user while completing `/login/2fa/verify`. |
| OAuth exchange code     | `oauth_exchange`  | OAuth callback (Google/42)                          | 30 sec (`OAUTH_EXCHANGE_EXPIRE_SECONDS`)    | One-time code handed to the frontend in a redirect URL, swapped for real tokens via `/oauth/exchange` — keeps long-lived tokens out of the URL/browser history. |

All JWTs are signed **HS256** (`ALGORITHM`) with `SECRET_KEY`.

> ⚠️ **`SECRET_KEY`.** If unset, [`config.py`](app/config.py) generates a
> random key at process startup. Every restart without an explicit
> `SECRET_KEY` silently invalidates every token issued so far. Always set it
> explicitly outside local dev.

### 6.2 Bearer scheme

`OAuth2PasswordBearer(tokenUrl="login")` ([dependencies.py](app/dependencies.py))
only tells Swagger UI which endpoint issues tokens for its "Authorize" button;
token *extraction* works the same for any `Authorization: Bearer <token>`
header regardless of which endpoint issued it. `get_current_user` requires a
`type: access` token; `get_pending_user_id` requires `type: 2fa_pending`.

### 6.3 Refresh & logout semantics

- **Refresh is a rotation, not a reissue**: the old `RefreshToken` row is
  deleted and a new one inserted in the same transaction — the old refresh
  token is unusable immediately, no reuse window.
- **Logout requires no caller identity** — presenting a valid `refresh_token`
  string is the only requirement; there is no check that it belongs to the
  caller (pre-existing behaviour, not introduced by the realtime-notification
  work).

## 7. Two-factor authentication flow

1. **Enable** — `POST /2fa/enable` generates a TOTP secret and an `otpauth://`
   provisioning URI (scannable QR in the frontend). 2FA is **not** active yet.
2. **Confirm** — the user scans it, then `POST /2fa/enable/verify` with the
   first code sets `is_2fa_enabled = true`.
3. **Login with 2FA** — `POST /login` returns `TwoFactorRequired` (a
   `pending_token`) instead of tokens. The client calls
   `POST /login/2fa/verify` with that token + a TOTP code to get real tokens.
4. **Disable** — `POST /2fa/disable` turns it back off.

Codes are verified with `pyotp`, `valid_window=1` — accepting one 30-second
step of clock drift on either side of the current window.

## 8. OAuth flow (Google & 42)

1. `GET /oauth/{provider}/login` builds the provider's authorization URL and
   sets an `httponly`, `secure`, `samesite=lax` CSRF state cookie (10 min TTL).
2. The provider redirects back to `GET /oauth/{provider}/callback` with
   `code` + `state`. The `state` query param is checked against the cookie
   (`InvalidOAuthStateError` → 401 on mismatch) before anything else happens.
3. The service fetches the provider profile and resolves the user, in order:
   - an existing `OAuthAccount` for that provider/provider-user-id → use its
     linked user;
   - otherwise an existing `User` matching the profile's email → link a new
     `OAuthAccount` to it;
   - otherwise create a brand new `User` **and** link the `OAuthAccount`.
4. The callback redirects to the frontend with either `?pending_token=...`
   (2FA required) or `?exchange_code=...` (login complete).
5. The frontend calls `POST /oauth/exchange` with that code to get real
   tokens. Emits `auth.login`.

> **Note.** Users created via OAuth get `hashed_password="IMPOSSIBLE"` — a
> sentinel that can never match a bcrypt comparison. This is intentional: it
> blocks password-based `/login` for accounts that only exist through OAuth,
> without needing a nullable `hashed_password` column.

## 9. Realtime event notifications

`AuthService` notifies the [`realtime`](../realtime/README.md) service of
login/logout events through `RealtimeClient` ([clients/realtime_client.py](app/clients/realtime_client.py)).

| Event         | Emitted from                                              | Trigger |
| -------------- | ------------------------------------------------------------ | ------- |
| `auth.login`    | `register`, `login` (2FA disabled), `login_2fa`, `exchange_oauth_code` | Every fully-completed login, password or OAuth. |
| `auth.logout`   | `logout`                                                       | A refresh token is successfully revoked. |

Payload POSTed to `${REALTIME_BASE_URL}/internal/events` (default
`http://realtime:8000`):

```json
{
  "event_type": "auth.login",
  "user_id": 42,
  "first_name": "Ada",
  "last_name": "Lovelace"
}
```

**This is best-effort and non-blocking**: the call is scheduled with
`asyncio.create_task` and never awaited by the caller, has a 2s timeout, and
any failure (`httpx` error or otherwise) is caught and logged
(`logger.warning`) rather than propagated. A `realtime` outage never breaks
login, signup, 2FA or logout.

## 10. Data model

Three tables, defined in [`models/auth.py`](app/models/auth.py):

**`users`**

| Column             | Type        | Notes |
| -------------------- | ------------- | ----- |
| `id`                  | PK             | |
| `first_name` / `last_name` | `varchar(255)` | |
| `email`                | `varchar(255)` | unique |
| `location`             | `varchar`, nullable | |
| `avatar_id`             | `int`          | default `1` |
| `hashed_password`        | `text`         | bcrypt hash, or the OAuth sentinel `"IMPOSSIBLE"` |
| `is_2fa_enabled`         | `bool`         | default `false` |
| `secret_2fa`             | `varchar`, nullable | TOTP secret, set once 2FA setup starts |
| `created_at`             | `timestamptz`  | server default `now()` |

**`tokens`** (refresh tokens)

| Column      | Type   | Notes |
| ------------ | ------- | ----- |
| `id`          | PK       | |
| `token`        | `text`   | opaque, `secrets.token_urlsafe(32)` |
| `user_id`       | FK → `users.id` | `ON DELETE CASCADE` |
| `created_at`     | `timestamptz` | |
| `expired_at`      | `timestamptz` | |

**`oauth_accounts`**

| Column               | Type   | Notes |
| ---------------------- | ------- | ----- |
| `id`                    | PK       | |
| `provider`               | `varchar(50)` | `"google"` or `"42"` |
| `provider_user_id`        | `varchar(255)` | ID from the provider |
| `user_id`                  | FK → `users.id` | `ON DELETE CASCADE` |
| `created_at`                | `timestamptz` | |

Unique constraint on (`provider`, `provider_user_id`) — one link per external
account. Deleting a `User` cascades to their tokens and OAuth links at the
database level.

## 11. Error reference

All custom exceptions inherit `AuthError` and are mapped to a response in
[`main.py`](main.py); a few auth-header errors are raised as plain
`HTTPException` directly in [`dependencies.py`](app/dependencies.py) /
[`core/tokens.py`](app/core/tokens.py) but return the same `{"detail": ...}`
shape.

| Exception                        | Status | Detail                        | Raised when |
| ---------------------------------- | ------ | -------------------------------- | ----------- |
| `EmailAlreadyExistsError`            | 409    | Email already registered           | Signup with an email already in use. |
| `InvalidCredentialsError`             | 401    | Invalid credentials                | Login with an unknown email or wrong password. |
| `InvalidTokenError`                    | 401    | Invalid token                       | Token type mismatch (e.g. a `2fa_pending` token used where an `oauth_exchange` token is expected). |
| `TokenExpiredError`                      | 401    | Token expired                        | Refresh token past `expired_at`. |
| `Auth2faError`                            | 401    | Invalid code                          | Wrong or expired TOTP code. |
| `UserNotFoundError`                        | 401    | User not found                         | Token references a user that no longer exists. |
| `TwoFactorAlreadyEnabledError`               | 409    | 2FA already enabled                      | `/2fa/enable` called while 2FA is already on. |
| `TwoFactorNotConfiguredError`                  | 401    | 2FA not configured                         | `/2fa/enable/verify` or `/2fa/disable` with no secret registered. |
| `InvalidOAuthStateError`                         | 401    | OAuth state error                            | The `state` query param doesn't match the CSRF cookie. |
| `GoogleAuthError`                                  | 400    | Google authentication failed                    | Google token/profile request fails. |
| `FtAuthError`                                        | 400    | 42 authentication failed                          | 42 token/profile request fails. |
| `UserByEmailNotFoundError`                             | 404    | No user with this email                             | `/users/by-email` with no match. |
| *(raw)* `HTTPException`                                  | 401    | Invalid token / Token expired / User not found        | Missing, malformed, wrong-type, or expired bearer token on a protected route. |

## 12. Configuration

Environment variables read in [`config.py`](app/config.py) — set at the
project root (`.env`, see [`.env.example`](../.env.example)).

**Core**

| Variable                          | Default                                                  | Description |
| ------------------------------------ | ----------------------------------------------------------- | ----------- |
| `SECRET_KEY`                           | random per process start ⚠️                                  | HMAC key signing every JWT. Set explicitly outside local dev. |
| `ALGORITHM`                              | `HS256`                                                       | JWT signing algorithm. |
| `FRONTEND_URL`                             | `https://localhost:8443`                                        | Base URL the OAuth callbacks redirect to. |
| `REALTIME_BASE_URL`                          | `http://realtime:8000`                                            | Base URL of the `realtime` service (see [§9](#9-realtime-event-notifications)). |
| `ACCESS_TOKEN_EXPIRE_MINUTES`                  | `15`                                                                | Access token lifetime. |
| `TEMPORARY_TOKEN_EXPIRE_MINUTES`                 | `5`                                                                   | Pending-2FA token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS`                        | `7`                                                                     | Refresh token lifetime. |
| `OAUTH_EXCHANGE_EXPIRE_SECONDS`                      | `30`                                                                      | OAuth exchange code lifetime. |

**OAuth — Google**

| Variable                | Default | Description |
| -------------------------- | ------- | ----------- |
| `GOOGLE_CLIENT_ID`            | `""`     | OAuth client ID. |
| `GOOGLE_CLIENT_SECRET`          | `""`     | OAuth client secret. |
| `GOOGLE_REDIRECT_URI`             | `https://localhost:8443/api/auth/oauth/google/callback` | Must match the URI registered with Google. |

**OAuth — 42**

| Variable         | Default | Description |
| -------------------- | ------- | ----------- |
| `FT_CLIENT_ID`          | `""`     | OAuth client ID. |
| `FT_CLIENT_SECRET`        | `""`     | OAuth client secret. |
| `FT_REDIRECT_URI`           | `https://localhost:8443/api/auth/oauth/42/callback` | Must match the URI registered on the 42 intranet. |

**Database** (read from [`shared/database.py`](../shared/database.py), not `auth`-specific)

| Variable            | Default    | Description |
| ---------------------- | ---------- | ----------- |
| `POSTGRES_USER`           | *required*  | No fallback — startup fails without it. |
| `POSTGRES_PASSWORD`         | *required*  | No fallback — startup fails without it. |
| `POSTGRES_DB`                  | *required*  | No fallback — startup fails without it. |
| `POSTGRES_HOST`                  | `postgres`   | |
| `POSTGRES_PORT`                    | `5432`        | |

## 13. Project structure

```
auth/
├── main.py                     FastAPI app, routers, exception handlers
├── app/
│   ├── config.py                 Environment variables
│   ├── dependencies.py             FastAPI Depends() wiring (DI root)
│   ├── exceptions.py                 Custom AuthError hierarchy
│   ├── clients/
│   │   └── realtime_client.py          Outbound client → realtime service
│   ├── core/                          Stateless helpers (no DB, no state)
│   │   ├── security.py                  Password hashing, TOTP verification
│   │   ├── tokens.py                     JWT encode/decode
│   │   ├── google_oauth.py                Google profile fetch
│   │   └── ft_oauth.py                     42 profile fetch
│   ├── models/
│   │   └── auth.py                       SQLAlchemy models: User, RefreshToken, OAuthAccount
│   ├── repositories/                    DB access, one per aggregate
│   │   ├── user_repository.py
│   │   ├── token_repository.py
│   │   └── oauth_repository.py
│   ├── routers/                         HTTP layer
│   │   ├── auth.py                        signup, login, 2FA, refresh, logout, profile
│   │   ├── oauth.py                        Google / 42 OAuth
│   │   └── health.py
│   ├── schemas/                         Pydantic request/response models
│   └── services/
│       ├── auth_service.py                Business logic
│       └── health_service.py
└── pyproject.toml
```

## 14. Getting started

The recommended way to run this service is as part of the full stack — it
needs PostgreSQL, and (for OAuth) the `gateway` for the correct redirect
URIs:

```bash
# from the repository root
cp .env.example .env    # fill in SECRET_KEY, GOOGLE_*, FT_* as needed
make run
```

See the [root README](../README.md#getting-started) for the full launch
sequence. Once running:

```bash
curl -sk https://localhost:8443/api/auth/health
# {"status":"ok","service":"auth"}
```

**Standalone** (needs a reachable Postgres and the env vars from
[§12](#12-configuration) exported manually):

```bash
cd auth
uv sync
uv run uvicorn main:app --reload
```

## 15. Related documentation

- [Root README](../README.md) — platform overview, full architecture, all
  services.
- [docs/DEV_DOC.md](../docs/DEV_DOC.md) — local dev workflow, database
  migrations.
- [migrations/README.md](../migrations/README.md) — how the shared Alembic
  chain works, and how to add a model.
- [gateway/README.md](../gateway/README.md) — reverse proxy, WAF, and the
  `/api/auth/*` routing this service sits behind.
- [realtime/README.md](../realtime/README.md) — consumer of the
  `auth.login` / `auth.logout` events described in [§9](#9-realtime-event-notifications).
