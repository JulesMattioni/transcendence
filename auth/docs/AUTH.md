<p align="center">
  <img src="https://img.shields.io/badge/AUTH-SERVICE-111111?style=for-the-badge&labelColor=000000" alt="auth-service" />
</p>

<h1 align="center">🔐 Auth Service</h1>

<p align="center">
  A standalone authentication microservice — signup, login, JWT sessions, TOTP 2FA and OAuth 2.0 (Google &amp; 42) — built with FastAPI and wired into a React frontend.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT" />
  <img src="https://img.shields.io/badge/Google_OAuth-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google OAuth" />
  <img src="https://img.shields.io/badge/42_OAuth-000000?style=for-the-badge&logo=42&logoColor=white" alt="42 OAuth" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="pytest" />
  <img src="https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white" alt="uv" />
  <img src="https://img.shields.io/badge/mypy-strict-2A6DB2?style=for-the-badge" alt="mypy strict" />
  <img src="https://img.shields.io/badge/flake8-clean-yellowgreen?style=for-the-badge" alt="flake8" />
  <img src="https://img.shields.io/badge/HashiCorp_Vault-000000?style=for-the-badge&logo=vault&logoColor=white" alt="Vault" />
</p>

<hr/>

<h2>📑 Table of Contents</h2>

<ul>
  <li><a href="#overview">Overview</a></li>
  <li><a href="#tech-stack">Tech Stack</a></li>
  <li><a href="#features">Features</a></li>
  <li><a href="#api-reference">API Reference</a></li>
  <li><a href="#project-structure">Project Structure</a></li>
  <li><a href="#getting-started">Getting Started</a></li>
  <li><a href="#environment-variables">Environment Variables</a></li>
  <li><a href="#testing">Testing &amp; Quality</a></li>
  <li><a href="#security">Security Notes</a></li>
  <li><a href="#learning-resources">Learning Resources &amp; Documentation</a></li>
  <li><a href="#roadmap">Roadmap &amp; Branch Convention</a></li>
</ul>

<hr/>

<h2 id="overview">🧭 Overview</h2>

<p>
The <code>auth</code> service is the identity provider for the platform. It owns user accounts,
password credentials, session tokens, two-factor authentication, and third-party sign-in via
Google and 42. Other services (<code>org</code>, <code>core</code>, <code>rag</code>) validate the
JWTs it issues through a shared dependency instead of re-implementing auth logic.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-in_development-orange?style=flat-square" alt="status" />
  <img src="https://img.shields.io/badge/issues-26-blue?style=flat-square" alt="issues" />
  <img src="https://img.shields.io/badge/branches-1%3A1_with_issues-blue?style=flat-square" alt="branches" />
</p>

<hr/>

<h2 id="tech-stack">🧩 Tech Stack</h2>

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
    <th>Logo</th>
    <th>Purpose</th>
  </tr>
  <tr>
    <td>API framework</td>
    <td>FastAPI</td>
    <td><img src="https://img.shields.io/badge/-FastAPI-005571?style=flat-square&logo=fastapi&logoColor=white" /></td>
    <td>Routing, dependency injection, OpenAPI docs</td>
  </tr>
  <tr>
    <td>Validation</td>
    <td>Pydantic v2</td>
    <td><img src="https://img.shields.io/badge/-Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white" /></td>
    <td>Request/response schemas, kept separate from ORM models</td>
  </tr>
  <tr>
    <td>ORM &amp; migrations</td>
    <td>SQLAlchemy 2.0 + Alembic</td>
    <td><img src="https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white" /></td>
    <td>User / OAuth / refresh-token tables, versioned schema</td>
  </tr>
  <tr>
    <td>Database</td>
    <td>PostgreSQL</td>
    <td><img src="https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" /></td>
    <td>Persistent storage</td>
  </tr>
  <tr>
    <td>Password hashing</td>
    <td>passlib / argon2-cffi</td>
    <td><img src="https://img.shields.io/badge/-Argon2-0057B7?style=flat-square" /></td>
    <td>Salting &amp; hashing, OWASP-compliant storage</td>
  </tr>
  <tr>
    <td>Sessions</td>
    <td>JWT (PyJWT / python-jose)</td>
    <td><img src="https://img.shields.io/badge/-JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white" /></td>
    <td>Short-lived access token + revocable refresh token</td>
  </tr>
  <tr>
    <td>2FA</td>
    <td>pyotp + qrcode (TOTP, RFC 6238)</td>
    <td><img src="https://img.shields.io/badge/-TOTP-6E44FF?style=flat-square" /></td>
    <td>Time-based one-time codes, recovery codes</td>
  </tr>
  <tr>
    <td>OAuth 2.0</td>
    <td>Google Identity Platform</td>
    <td><img src="https://img.shields.io/badge/-Google-4285F4?style=flat-square&logo=google&logoColor=white" /></td>
    <td>Authorization Code flow, account linking</td>
  </tr>
  <tr>
    <td>OAuth 2.0</td>
    <td>42 Intra API</td>
    <td><img src="https://img.shields.io/badge/-42-000000?style=flat-square&logo=42&logoColor=white" /></td>
    <td>Authorization Code flow, account linking</td>
  </tr>
  <tr>
    <td>Frontend</td>
    <td>React + TypeScript</td>
    <td>
      <img src="https://img.shields.io/badge/-React-61DAFB?style=flat-square&logo=react&logoColor=black" />
      <img src="https://img.shields.io/badge/-TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" />
    </td>
    <td>Login/Register pages, global auth context, protected routes</td>
  </tr>
  <tr>
    <td>Package manager</td>
    <td>uv</td>
    <td><img src="https://img.shields.io/badge/-uv-DE5FE9?style=flat-square&logo=uv&logoColor=white" /></td>
    <td>Dependency resolution &amp; virtualenvs</td>
  </tr>
  <tr>
    <td>Quality &amp; CI</td>
    <td>flake8 + strict mypy + pytest</td>
    <td>
      <img src="https://img.shields.io/badge/-flake8-yellowgreen?style=flat-square" />
      <img src="https://img.shields.io/badge/-mypy-2A6DB2?style=flat-square" />
      <img src="https://img.shields.io/badge/-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" />
    </td>
    <td>Lint, static typing, async test suite</td>
  </tr>
  <tr>
    <td>Secrets (planned)</td>
    <td>HashiCorp Vault</td>
    <td><img src="https://img.shields.io/badge/-Vault-000000?style=flat-square&logo=vault&logoColor=white" /></td>
    <td>KV secrets engine, replacing raw <code>.env</code> reads</td>
  </tr>
</table>

<hr/>

<h2 id="features">✨ Features</h2>

<details>
  <summary><b>🧱 Foundations &amp; database</b></summary>
  <ul>
    <li>SQLAlchemy + Alembic wired to <code>DATABASE_URL</code>, first migration generates the schema</li>
    <li><code>User</code> model (id, unique email, hashed_password, is_active, is_2fa_enabled, created_at)</li>
    <li><code>UserRepository</code> — all DB access isolated from routers (no ORM calls in endpoints)</li>
    <li>Pydantic <code>UserCreate</code> / <code>UserRead</code> schemas kept separate from the ORM model</li>
  </ul>
</details>

<details>
  <summary><b>👤 Standard user management</b></summary>
  <ul>
    <li><code>POST /auth/signup</code> — email validation, password policy, hashed storage, <code>409</code> on duplicate email</li>
    <li><code>PasswordHasher</code> — isolated, independently testable hashing service (argon2/bcrypt)</li>
    <li><code>POST /auth/login</code> — credential check, access + refresh token issuance, failed-attempt throttling</li>
    <li><code>JWTService</code> — encode/decode, <code>sub</code>/<code>exp</code>/<code>iat</code>/<code>type</code> claims, refresh tokens persisted &amp; revocable</li>
    <li><code>POST /auth/refresh</code> — validates signature + DB state, <b>rotates</b> the refresh token on every use</li>
    <li><code>GET /auth/me</code> — returns the authenticated profile via a <code>get_current_user</code> dependency</li>
    <li>Shared auth dependency reusable by <code>org</code>, <code>core</code> and <code>rag</code></li>
  </ul>
</details>

<details>
  <summary><b>🔑 TOTP two-factor authentication</b></summary>
  <ul>
    <li><code>POST /auth/2fa/setup</code> — generates a TOTP secret + QR provisioning URI (pending confirmation)</li>
    <li><code>POST /auth/2fa/verify</code> — confirms the code, enables 2FA, issues recovery codes</li>
    <li>Login integration — when 2FA is active, <code>/auth/login</code> returns an intermediate state; a second call validates the TOTP code and issues the JWT</li>
    <li><code>POST /auth/2fa/disable</code> — requires re-verification (password or code)</li>
  </ul>
</details>

<details>
  <summary><b>🌐 OAuth 2.0 — Google &amp; 42</b></summary>
  <ul>
    <li><code>oauth_accounts</code> model — (provider, provider_user_id, user_id), with linking/merging on an existing email</li>
    <li>Google — <code>GET /auth/oauth/google/login</code> + <code>/callback</code>, Authorization Code flow</li>
    <li>42 — same flow against <code>api.intra.42.fr</code>, maps the 42 profile to <code>User</code></li>
  </ul>
</details>

<details>
  <summary><b>🖥️ Frontend integration</b></summary>
  <ul>
    <li><code>LoginPage.tsx</code> / <code>RegisterPage.tsx</code> wired to their respective endpoints (currently pure UI, no API calls)</li>
    <li>Global auth state via React Context — persisted session, protected routes, silent token refresh</li>
    <li>2FA UI — TOTP entry at login, QR code display at setup</li>
    <li>Functional "Connect with Google/42" buttons (currently inert <code>type="button"</code>)</li>
  </ul>
</details>

<details>
  <summary><b>🛡️ Security, quality &amp; infra</b></summary>
  <ul>
    <li>Rate limiting + account lockout on <code>/auth/login</code></li>
    <li>Dedicated CI job: flake8 + strict mypy for the <code>auth</code> service</li>
    <li>pytest suite: signup, login, refresh, 2FA, OAuth (mocked providers), error cases</li>
    <li>Complete <code>.env.example</code> (JWT secret, Google/42 client id &amp; secret) — Vault migration planned</li>
  </ul>
</details>

<hr/>

<h2 id="api-reference">📡 API Reference</h2>

<table>
  <tr><th>Method</th><th>Endpoint</th><th>Auth</th><th>Description</th></tr>
  <tr><td><code>POST</code></td><td><code>/auth/signup</code></td><td>—</td><td>Create a new account</td></tr>
  <tr><td><code>POST</code></td><td><code>/auth/login</code></td><td>—</td><td>Authenticate, issue access + refresh tokens (or intermediate 2FA state)</td></tr>
  <tr><td><code>POST</code></td><td><code>/auth/refresh</code></td><td>Refresh token</td><td>Rotate and reissue tokens</td></tr>
  <tr><td><code>GET</code></td><td><code>/auth/me</code></td><td>Access token</td><td>Return the current user's profile</td></tr>
  <tr><td><code>POST</code></td><td><code>/auth/2fa/setup</code></td><td>Access token</td><td>Generate TOTP secret + QR code</td></tr>
  <tr><td><code>POST</code></td><td><code>/auth/2fa/verify</code></td><td>Access token</td><td>Confirm code, enable 2FA, return recovery codes</td></tr>
  <tr><td><code>POST</code></td><td><code>/auth/2fa/disable</code></td><td>Access token + re-verification</td><td>Disable 2FA</td></tr>
  <tr><td><code>GET</code></td><td><code>/auth/oauth/google/login</code></td><td>—</td><td>Redirect to Google's consent screen</td></tr>
  <tr><td><code>GET</code></td><td><code>/auth/oauth/google/callback</code></td><td>—</td><td>Handle Google's authorization code</td></tr>
  <tr><td><code>GET</code></td><td><code>/auth/oauth/42/login</code></td><td>—</td><td>Redirect to 42's consent screen</td></tr>
  <tr><td><code>GET</code></td><td><code>/auth/oauth/42/callback</code></td><td>—</td><td>Handle 42's authorization code</td></tr>
</table>

<hr/>

<h2 id="project-structure">🗂️ Project Structure</h2>

<pre>
auth/
├── app/
│   ├── routers/
│   │   ├── health.py
│   │   ├── auth.py            # signup, login, refresh, me
│   │   ├── twofa.py           # 2FA setup/verify/disable
│   │   └── oauth.py           # google, 42
│   ├── models/                # SQLAlchemy models (User, OAuthAccount, RefreshToken)
│   ├── schemas/                # Pydantic UserCreate / UserRead / ...
│   ├── repositories/           # UserRepository, OAuthRepository
│   ├── services/                # PasswordHasher, JWTService, TOTPService
│   ├── dependencies.py          # get_current_user, shared auth dependency
│   └── main.py
├── alembic/
├── tests/
├── pyproject.toml
└── .env.example
</pre>

<hr/>

<h2 id="getting-started">🚀 Getting Started</h2>

<h3>Prerequisites</h3>
<p>
  <img src="https://img.shields.io/badge/-Python_3.12+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/-uv-DE5FE9?style=flat-square&logo=uv&logoColor=white" />
  <img src="https://img.shields.io/badge/-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
</p>

```bash
# install dependencies
uv sync

# configure environment
cp .env.example .env
# then fill in DATABASE_URL, JWT secret, Google/42 client id & secret

# run migrations
alembic upgrade head

# start the service
uv run uvicorn app.main:app --reload
```

<p>The interactive API docs are then available at <code>http://localhost:8000/docs</code>.</p>

<hr/>

<h2 id="environment-variables">🔧 Environment Variables</h2>

<table>
  <tr><th>Variable</th><th>Description</th></tr>
  <tr><td><code>DATABASE_URL</code></td><td>PostgreSQL connection string</td></tr>
  <tr><td><code>JWT_SECRET_KEY</code></td><td>Signing secret for access/refresh tokens</td></tr>
  <tr><td><code>JWT_ACCESS_EXPIRE_MINUTES</code></td><td>Access token lifetime</td></tr>
  <tr><td><code>JWT_REFRESH_EXPIRE_DAYS</code></td><td>Refresh token lifetime</td></tr>
  <tr><td><code>GOOGLE_CLIENT_ID</code> / <code>GOOGLE_CLIENT_SECRET</code></td><td>Google OAuth app credentials</td></tr>
  <tr><td><code>FORTYTWO_CLIENT_ID</code> / <code>FORTYTWO_CLIENT_SECRET</code></td><td>42 intra OAuth app credentials</td></tr>
</table>

<blockquote>
  A migration to <b>HashiCorp Vault</b> (KV secrets engine) is planned at the end of the project —
  avoid hard-coding secret reads in the meantime.
</blockquote>

<hr/>

<h2 id="testing">✅ Testing &amp; Quality</h2>

```bash
# run the test suite
uv run pytest

# lint
uv run flake8

# strict type checking
uv run mypy --strict app
```

<p>Coverage includes signup, login, refresh rotation, 2FA, and OAuth flows with mocked providers.</p>

<hr/>

<h2 id="security">🔒 Security Notes</h2>

<ul>
  <li>Passwords are salted and hashed (argon2/bcrypt) — plaintext and hashes are never returned in responses</li>
  <li>Refresh tokens are stored server-side and rotated on every use, so a leaked token can be revoked</li>
  <li>Frontend token storage prefers an <code>httpOnly</code> cookie over <code>localStorage</code></li>
  <li>Cookies are set with <code>httpOnly</code>, <code>Secure</code>, and <code>SameSite</code></li>
  <li>Login is rate-limited with account lockout after repeated failures</li>
</ul>

<hr/>

<h2 id="learning-resources">📚 Learning Resources &amp; Documentation</h2>

<p>Reference material to read before/while implementing each part of the service.</p>

<details open>
  <summary><b>🧱 FastAPI &amp; backend structure</b></summary>
  <table>
    <tr><th>Topic</th><th>Link</th></tr>
    <tr><td>FastAPI — routing, DI, <code>OAuth2PasswordBearer</code>, <code>HTTPException</code></td><td><a href="https://fastapi.tiangolo.com">fastapi.tiangolo.com</a></td></tr>
    <tr><td>Pydantic v2 — validation schemas</td><td><a href="https://docs.pydantic.dev">docs.pydantic.dev</a></td></tr>
    <tr><td>SQLAlchemy 2.0</td><td><a href="https://docs.sqlalchemy.org">docs.sqlalchemy.org</a></td></tr>
    <tr><td>Alembic (migrations)</td><td><a href="https://alembic.sqlalchemy.org">alembic.sqlalchemy.org</a></td></tr>
    <tr><td><code>uv</code> (Python package manager)</td><td><a href="https://docs.astral.sh/uv">docs.astral.sh/uv</a></td></tr>
    <tr><td>Strict mypy + flake8</td><td>project CI configuration, see <code>ci/auth-lint-typecheck</code></td></tr>
  </table>
</details>

<details>
  <summary><b>🔑 Passwords &amp; hashing</b></summary>
  <table>
    <tr><th>Topic</th><th>Link</th></tr>
    <tr><td>OWASP Password Storage Cheat Sheet</td><td><a href="https://cheatsheetseries.owasp.org">cheatsheetseries.owasp.org</a></td></tr>
    <tr><td><code>passlib</code> or <code>argon2-cffi</code></td><td>PyPI documentation</td></tr>
  </table>
</details>

<details>
  <summary><b>🪪 JWT</b></summary>
  <table>
    <tr><th>Topic</th><th>Link</th></tr>
    <tr><td>RFC 7519 (JWT spec)</td><td><a href="https://datatracker.ietf.org/doc/html/rfc7519">datatracker.ietf.org/doc/html/rfc7519</a></td></tr>
    <tr><td>OWASP JWT Cheat Sheet</td><td>cheatsheetseries.owasp.org</td></tr>
    <tr><td><code>PyJWT</code> or <code>python-jose</code></td><td>PyPI documentation</td></tr>
    <tr><td>Access/refresh token pattern, rotation &amp; revocation</td><td>see <code>JWTService</code> design notes above</td></tr>
  </table>
</details>

<details>
  <summary><b>📟 2FA / TOTP</b></summary>
  <table>
    <tr><th>Topic</th><th>Link</th></tr>
    <tr><td>RFC 6238 (TOTP)</td><td><a href="https://datatracker.ietf.org/doc/html/rfc6238">datatracker.ietf.org/doc/html/rfc6238</a></td></tr>
    <tr><td>RFC 4226 (HOTP)</td><td><a href="https://datatracker.ietf.org/doc/html/rfc4226">datatracker.ietf.org/doc/html/rfc4226</a></td></tr>
    <tr><td><code>pyotp</code> + <code>qrcode</code></td><td>PyPI documentation</td></tr>
  </table>
</details>

<details>
  <summary><b>🌐 OAuth 2.0</b></summary>
  <table>
    <tr><th>Topic</th><th>Link</th></tr>
    <tr><td>RFC 6749 (Authorization Code flow)</td><td><a href="https://datatracker.ietf.org/doc/html/rfc6749">datatracker.ietf.org/doc/html/rfc6749</a></td></tr>
    <tr><td>Google Identity Platform</td><td><a href="https://developers.google.com/identity/protocols/oauth2">developers.google.com/identity/protocols/oauth2</a></td></tr>
    <tr><td>42 API OAuth documentation</td><td><a href="https://api.intra.42.fr">api.intra.42.fr</a></td></tr>
  </table>
</details>

<details>
  <summary><b>🛡️ Cross-cutting security</b></summary>
  <ul>
    <li>Secure cookies: <code>httpOnly</code>, <code>Secure</code>, <code>SameSite</code></li>
    <li>Rate limiting / anti-brute-force patterns</li>
    <li>HashiCorp Vault (KV secrets engine)</li>
  </ul>
</details>

<details>
  <summary><b>🖥️ Frontend</b></summary>
  <ul>
    <li>Auth state management in React (Context API / Zustand) + protected routes via <code>react-router-dom</code></li>
    <li>API calls from React (fetch/axios, refresh-token interceptor)</li>
  </ul>
</details>

<details>
  <summary><b>✅ Tests</b></summary>
  <ul>
    <li><code>pytest</code> + <code>pytest-asyncio</code> + <code>httpx.AsyncClient</code></li>
  </ul>
</details>

<hr/>

<h2 id="roadmap">🗺️ Roadmap &amp; Branch Convention</h2>

<p>One branch per issue, one Pull Request per branch, linked to its Linear issue.</p>

<table>
  <tr><th>Prefix</th><th>Purpose</th></tr>
  <tr><td><code>feat/</code></td><td>New feature</td></tr>
  <tr><td><code>ci/</code></td><td>Continuous integration</td></tr>
  <tr><td><code>test/</code></td><td>Tests</td></tr>
  <tr><td><code>chore/</code></td><td>Maintenance / configuration</td></tr>
  <tr><td><code>docs/</code></td><td>Documentation</td></tr>
</table>

<h3>Issue ↔ Branch mapping (26 branches, 1:1 with issues)</h3>

<details open>
  <summary><b>Epic A — Foundations &amp; database</b></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>1</td><td>Add SQLAlchemy + Alembic</td><td><code>feat/auth-db-setup</code></td><td>feat</td></tr>
    <tr><td>2</td><td><code>User</code> model + repository</td><td><code>feat/auth-user-model</code></td><td>feat</td></tr>
  </table>
</details>

<details>
  <summary><b>Epic B — Standard user management</b> <sub>(Major, 2 pts)</sub></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>3</td><td><code>POST /auth/signup</code></td><td><code>feat/auth-signup</code></td><td>feat</td></tr>
    <tr><td>4</td><td>Password hashing &amp; salting (<code>PasswordHasher</code>)</td><td><code>feat/auth-password-hasher</code></td><td>feat</td></tr>
    <tr><td>5</td><td><code>POST /auth/login</code></td><td><code>feat/auth-login</code></td><td>feat</td></tr>
    <tr><td>6</td><td>JWT service (<code>JWTService</code>)</td><td><code>feat/auth-jwt-service</code></td><td>feat</td></tr>
    <tr><td>7</td><td><code>POST /auth/refresh</code></td><td><code>feat/auth-token-refresh</code></td><td>feat</td></tr>
    <tr><td>8</td><td><code>GET /auth/me</code></td><td><code>feat/auth-me-endpoint</code></td><td>feat</td></tr>
    <tr><td>9</td><td>Reusable auth dependency</td><td><code>feat/auth-shared-dependency</code></td><td>feat</td></tr>
  </table>
</details>

<details>
  <summary><b>Epic C — TOTP 2FA</b> <sub>(Minor, 1 pt)</sub></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>10</td><td><code>POST /auth/2fa/setup</code></td><td><code>feat/auth-2fa-setup</code></td><td>feat</td></tr>
    <tr><td>11</td><td><code>POST /auth/2fa/verify</code></td><td><code>feat/auth-2fa-verify</code></td><td>feat</td></tr>
    <tr><td>12</td><td>2FA integration in login</td><td><code>feat/auth-2fa-login</code></td><td>feat</td></tr>
    <tr><td>13</td><td><code>POST /auth/2fa/disable</code></td><td><code>feat/auth-2fa-disable</code></td><td>feat</td></tr>
  </table>
</details>

<details>
  <summary><b>Epic D — OAuth 2.0 Google &amp; 42</b> <sub>(Minor, 1 pt)</sub></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>14</td><td><code>oauth_accounts</code> model</td><td><code>feat/auth-oauth-accounts-model</code></td><td>feat</td></tr>
    <tr><td>15</td><td>Google OAuth</td><td><code>feat/auth-oauth-google</code></td><td>feat</td></tr>
    <tr><td>16</td><td>42 OAuth</td><td><code>feat/auth-oauth-42</code></td><td>feat</td></tr>
  </table>
</details>

<details>
  <summary><b>Epic E — Frontend ↔ auth integration</b></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>17</td><td>Wire up <code>LoginPage.tsx</code></td><td><code>feat/auth-frontend-login</code></td><td>feat</td></tr>
    <tr><td>18</td><td>Wire up <code>RegisterPage.tsx</code></td><td><code>feat/auth-frontend-register</code></td><td>feat</td></tr>
    <tr><td>19</td><td>Global auth state (React context)</td><td><code>feat/auth-frontend-context</code></td><td>feat</td></tr>
    <tr><td>20</td><td>2FA UI</td><td><code>feat/auth-frontend-2fa</code></td><td>feat</td></tr>
    <tr><td>21</td><td>Functional "Connect with Google/42" buttons</td><td><code>feat/auth-frontend-oauth-buttons</code></td><td>feat</td></tr>
  </table>
</details>

<details>
  <summary><b>Epic F — Security, quality, infra</b></summary>
  <table>
    <tr><th>#</th><th>Issue</th><th>Branch</th><th>Type</th></tr>
    <tr><td>22</td><td>Rate limiting on <code>/auth/login</code></td><td><code>feat/auth-rate-limiting</code></td><td>feat</td></tr>
    <tr><td>23</td><td>CI: flake8 + strict mypy</td><td><code>ci/auth-lint-typecheck</code></td><td>ci</td></tr>
    <tr><td>24</td><td>pytest test suite</td><td><code>test/auth-test-suite</code></td><td>test</td></tr>
    <tr><td>25</td><td>Complete <code>.env.example</code></td><td><code>chore/auth-env-example</code></td><td>chore</td></tr>
    <tr><td>26</td><td>Final <code>auth/</code> README in English</td><td><code>docs/auth-readme</code></td><td>docs</td></tr>
  </table>
</details>


<h3>Progress</h3>

- [ ] **A — Foundations & database** (`feat/auth-db-setup`, `feat/auth-user-model`)
- [ ] **B — Standard user management** (signup, login, JWT, refresh, `/me`, shared dependency)
- [ ] **C — TOTP 2FA** (setup, verify, login integration, disable)
- [ ] **D — OAuth 2.0** (oauth_accounts model, Google, 42)
- [ ] **E — Frontend ↔ auth integration** (login/register wiring, context, 2FA UI, OAuth buttons)
- [ ] **F — Security, quality & infra** (rate limiting, CI, test suite, `.env.example`, README)

<p align="center"><a href="#overview">⬆ back to top</a></p>