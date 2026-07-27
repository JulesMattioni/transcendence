# auth — Keepr identity service

The **auth** service is the identity provider of Keepr. It owns sign-up,
login, JWT session issuance, TOTP two-factor authentication, and OAuth login
(Google / 42), and it notifies the other services (realtime) whenever a user
logs in or out.

It is a [FastAPI](https://fastapi.tiangolo.com/) application exposed inside
the Docker network on port `8000`, and reachable from the outside through the
gateway under the prefix **`/api/auth/`** (e.g. `POST /api/auth/login`).

---

## Responsibilities

- **Sign-up & login** — register users with email + password, authenticate
  them, and issue **JWT access/refresh tokens**.
- **Two-factor authentication** — optional **TOTP 2FA** on login, compatible
  with any authenticator app (Google Authenticator, Authy, ...).
- **OAuth login** — authenticate via **Google** and **42**, automatically
  linking or creating accounts by email.
- **Public profile API** — expose a minimal user profile to other services
  (`/me`, `/users/by-email`).
- **Cross-service notification** (fire-and-forget, never blocks the request):
  after a successful login or logout, `POST {REALTIME_BASE_URL}/internal/events`
  so connected clients receive an `auth.login` / `auth.logout` event.
- **`/health`** liveness endpoint.

---

## Architecture

The code follows a strict layered layout (router → service → repository /
client). Only the repositories talk SQL; only the clients perform outbound
HTTP; `core/` holds stateless helpers with no state of their own.

```
auth/
├── main.py                       # FastAPI app, routers, exception handlers
├── Dockerfile                    # python:3.12-slim + uv, copies shared/
├── pyproject.toml / uv.lock      # dependencies (managed with uv)
└── app/
    ├── config.py                 # env-driven settings (secrets, URLs, TTLs)
    ├── dependencies.py           # FastAPI Depends() wiring (DI root)
    ├── exceptions.py             # business exceptions (AuthError hierarchy)
    ├── clients/
    │   └── realtime_client.py    # async push of login/logout events to realtime
    ├── core/
    │   ├── security.py           # password hashing, TOTP verification
    │   ├── tokens.py              # JWT encode/decode
    │   ├── google_oauth.py         # Google profile fetch
    │   └── ft_oauth.py              # 42 profile fetch
    ├── routers/
    │   ├── health.py              # GET /health
    │   ├── auth.py                  # signup, login, 2FA, refresh, logout, profile
    │   └── oauth.py                  # Google / 42 redirect, callback, exchange
    ├── services/
    │   ├── health_service.py        # HealthService (BaseService)
    │   └── auth_service.py           # AuthService: orchestration + transactions
    ├── repositories/
    │   ├── user_repository.py         # User persistence
    │   ├── token_repository.py         # RefreshToken persistence
    │   └── oauth_repository.py          # OAuthAccount persistence
    ├── models/
    │   └── auth.py                       # SQLAlchemy models: User, RefreshToken, OAuthAccount
    └── schemas/                            # Pydantic schemas (Create/Read/Update/Response)
```

Shared code (`shared/base_service.py`, `shared/database.py`) is copied into
the image at build time and provides the `BaseService` base class, the
declarative `Base` and the `get_session` async-session dependency. Database
migrations are **not** handled here: they live in the top-level `migrations/`
service (shared Alembic), which runs before auth starts.

### Request lifecycle & transactions

Each request builds an `AuthService` through the `get_auth_service`
dependency (one `AsyncSession` per request via `shared.database.get_session`).
The service owns the transaction boundary: repository methods only `flush`,
and the service commits or rolls back. Refresh is a **rotation, not a
reissue**: the old `RefreshToken` row is deleted and a new one inserted in the
same transaction, so the old refresh token is unusable immediately.

### Error handling

Business exceptions inherit `AuthError`, defined in `app/exceptions.py`, and
are translated to HTTP responses by handlers registered in `main.py`. A few
auth-header errors are raised as plain `HTTPException` directly in
`dependencies.py` / `core/tokens.py`, but return the same `{"detail": ...}`
shape.

| Exception                     | HTTP status | Meaning                                        |
| ------------------------------ | ----------- | ----------------------------------------------- |
| `EmailAlreadyExistsError`        | `409`       | Signup with an email already in use            |
| `InvalidCredentialsError`         | `401`       | Login with an unknown email or wrong password  |
| `InvalidTokenError`                 | `401`       | Token type mismatch                            |
| `TokenExpiredError`                   | `401`       | Refresh token past `expired_at`                |
| `Auth2faError`                          | `401`       | Wrong or expired TOTP code                     |
| `UserNotFoundError`                       | `401`       | Token references a user that no longer exists  |
| `TwoFactorAlreadyEnabledError`              | `409`       | `/2fa/enable` called while 2FA is already on    |
| `TwoFactorNotConfiguredError`                 | `401`       | 2FA action with no secret registered           |
| `InvalidOAuthStateError`                        | `401`       | The `state` query param doesn't match the CSRF cookie |
| `GoogleAuthError`                                 | `400`       | Google token/profile request fails             |
| `FtAuthError`                                       | `400`       | 42 token/profile request fails                 |
| `UserByEmailNotFoundError`                            | `404`       | `/users/by-email` with no match                |
| *(raw)* `HTTPException`                                 | `401`       | Missing, malformed, wrong-type, or expired bearer token |

---

## API reference

All routes below are served by auth on port `8000`; from the outside, prefix
them with `/api/auth` (gateway). Interactive docs are available at `/docs`
(Swagger UI) and `/redoc`.

> **Note on parameters.** Endpoints below that take a bare scalar parameter
> (`refresh_token`, `email`) declare it as a plain `str` with no `Body()`
> annotation. FastAPI treats un-annotated scalar parameters as **query
> parameters**, even on `POST` — so these must be sent as `?refresh_token=...`,
> not as a JSON body. Anything typed as a Pydantic model (`UserCreate`,
> `UserLogin`, ...) is sent as a JSON body, as usual.

### Authentication & session

| Method | Path                | Auth                    | Request                          | Response                            | Description |
| ------ | -------------------- | ------------------------ | --------------------------------- | ------------------------------------ | ----------- |
| POST   | `/signup`             | -                         | `UserCreate` (body)                | `LoginResponse`                      | Register a user, hash the password, issue tokens, emit `auth.login`. |
| POST   | `/login`               | -                         | `UserLogin` (body)                 | `LoginResponse` \| `TwoFactorRequired` | Authenticate with email/password. Returns tokens directly, or a `pending_token` if 2FA is enabled. |
| POST   | `/login/2fa/verify`    | Bearer `pending_token`    | `TwoFactorVerify` (body)           | `LoginResponse`                      | Complete login by verifying the TOTP code. Emits `auth.login`. |
| POST   | `/refresh`             | -                         | `refresh_token` (query)            | `TokenResponse`                      | Rotate a refresh token: old one deleted, new access/refresh pair issued. |
| POST   | `/logout`              | -                         | `refresh_token` (query)            | -                                     | Revoke a refresh token (no-op if unknown). Emits `auth.logout`. |
| GET    | `/me`                  | Bearer access token       | -                                  | `UserRead`                           | Return the authenticated user's profile. |
| PATCH  | `/update`              | Bearer access token       | `UserUpdate` (body)                 | `UserRead`                           | Update `location` and `avatar_id`. |
| GET    | `/users/by-email`      | Bearer access token       | `email` (query)                    | `UserLookup`                          | Look up another user's public info by email (used by other services). |

### Two-factor authentication (TOTP)

| Method | Path                | Auth                  | Request                 | Response                | Description |
| ------ | -------------------- | ----------------------- | ------------------------- | -------------------------- | ----------- |
| POST   | `/2fa/enable`         | Bearer access token       | -                          | `TwoFactorCredentials`      | Generate a TOTP secret + provisioning URI. 2FA is **not** active yet. |
| POST   | `/2fa/enable/verify`  | Bearer access token       | `TwoFactorVerify` (body)   | -                            | Verify the first code and set `is_2fa_enabled = true`. |
| POST   | `/2fa/disable`        | Bearer access token       | -                          | `UserRead`                   | Disable 2FA for the current user. |

### OAuth (Google & 42)

| Method | Path                    | Auth | Request                                                     | Response                              | Description |
| ------ | ------------------------ | ---- | ------------------------------------------------------------ | --------------------------------------- | ----------- |
| GET    | `/oauth/google/login`     | -    | -                                                              | `OAuthRedirect` (+ sets `oauth_state_google` cookie) | Build the Google authorization URL, set a CSRF state cookie. |
| GET    | `/oauth/google/callback`  | -    | `code`, `state` (query) + `oauth_state_google` cookie          | 302 → frontend                          | Validate `state`, fetch the profile, redirect with `pending_token` or `exchange_code`. |
| GET    | `/oauth/42/login`         | -    | -                                                              | `OAuthRedirect` (+ sets `oauth_state_ft` cookie) | Same flow, 42. |
| GET    | `/oauth/42/callback`      | -    | `code`, `state` (query) + `oauth_state_ft` cookie               | 302 → frontend                          | Same flow, 42. |
| POST   | `/oauth/exchange`         | -    | `OAuthExchange` (body: `exchange_code`)                          | `LoginResponse`                          | Exchange the one-time code for real tokens. Emits `auth.login`. |

### Health

| Method | Path      | Auth | Response                                     | Description |
| ------ | ---------- | ---- | ---------------------------------------------- | ----------- |
| GET    | `/health`   | -    | `{"status": "ok", "service": "auth"}`            | Liveness check. |

---

## Authentication model

### Token types & lifetimes

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

### Bearer scheme

`OAuth2PasswordBearer(tokenUrl="login")` ([dependencies.py](app/dependencies.py))
only tells Swagger UI which endpoint issues tokens for its "Authorize" button;
token *extraction* works the same for any `Authorization: Bearer <token>`
header regardless of which endpoint issued it. `get_current_user` requires a
`type: access` token; `get_pending_user_id` requires `type: 2fa_pending`.

### Logout semantics

Logout requires no caller identity — presenting a valid `refresh_token`
string is the only requirement; there is no check that it belongs to the
caller.

---

## Two-factor authentication flow

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

---

## OAuth flow (Google & 42)

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

---

## Realtime event notifications

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

---

## Data model

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

---

## Configuration

All settings live in [`app/config.py`](app/config.py) and are read from the
environment (injected through the root `.env` via docker-compose).

**Core**

| Variable                      | Default                                | Description |
| ------------------------------- | ----------------------------------------- | ----------- |
| `SECRET_KEY`                       | random per process start ⚠️                 | HMAC key signing every JWT. Set explicitly outside local dev. |
| `ALGORITHM`                          | `HS256`                                       | JWT signing algorithm. |
| `FRONTEND_URL`                         | `https://localhost:8443`                        | Base URL the OAuth callbacks redirect to. |
| `REALTIME_BASE_URL`                      | `http://realtime:8000`                            | Base URL of the `realtime` service. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`              | `15`                                                | Access token lifetime. |
| `TEMPORARY_TOKEN_EXPIRE_MINUTES`             | `5`                                                   | Pending-2FA token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS`                    | `7`                                                     | Refresh token lifetime. |
| `OAUTH_EXCHANGE_EXPIRE_SECONDS`                  | `30`                                                      | OAuth exchange code lifetime. |

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

---

## Running

### With Docker (recommended)

The service is part of the root `docker-compose.yml`:

```bash
make run          # or: docker compose up --build
```

It waits for PostgreSQL to be healthy and for the shared `migrations` service
to complete, then listens on port `8000` inside the network (`expose`, not
published — access goes through the gateway).

### Locally

```bash
cd auth
uv sync
uv run uvicorn main:app --reload
```

The `shared/` package must be importable (it sits at the repository root; in
Docker it is copied next to the app and `PYTHONPATH=/app`).

## Code quality

The module is checked with **flake8** (default 79-char limit) and **mypy**:

```bash
flake8 main.py app/
mypy main.py app/
```

## Related documentation

- [Root README](../README.md) — platform overview, full architecture, all
  services.
- [docs/DEV_DOC.md](../docs/DEV_DOC.md) — local dev workflow, database
  migrations.
- [migrations/README.md](../migrations/README.md) — how the shared Alembic
  chain works, and how to add a model.
- [gateway/README.md](../gateway/README.md) — reverse proxy, WAF, and the
  `/api/auth/*` routing this service sits behind.
- [realtime/README.md](../realtime/README.md) — consumer of the
  `auth.login` / `auth.logout` events described in
  [Realtime event notifications](#realtime-event-notifications).
