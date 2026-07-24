# frontend — Keepr web client

The **frontend** is the single-page web application for Keepr. It is the
user-facing surface of the platform: landing pages, authentication (including
2FA and OAuth), and the authenticated dashboard where users manage their
organisations, files, members and chat with the AI assistant.

It is a [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
app built with [Vite](https://vite.dev/). It talks to the backend exclusively
through the gateway under the **`/api/`** prefix (REST) and **`/ws/`**
(WebSocket); it never calls a service directly.

---

## Responsibilities

- **Routing & pages** — public landing and legal pages, `/login`, `/register`
  and the OAuth callback, plus a protected `/dashboard` tree (home, files,
  chat, admin, user) rendered behind an auth guard.
- **Authentication UX** — email/password sign-in and sign-up, the two-factor
  (TOTP) code step and enrolment (QR code), and Google / 42 OAuth entry
  points. Tokens are kept in `localStorage`; a 401 transparently refreshes the
  access token once and retries before falling back to `/login`.
- **Organisation context** — loads the user's organisations, remembers the
  last selected one, and derives the current role and permissions
  (admin / editor / reader) shared across the dashboard.
- **Files** — upload (drag-and-drop), paginated listing, inline preview
  (image / PDF / text), download, edit and delete, all scoped to the selected
  organisation and gated by role.
- **AI chat** — streams answers token by token over Server-Sent Events, renders
  Markdown with clickable `[n]` citations that open the cited file, and manages
  conversations (create, load, delete).
- **Realtime** — an authenticated WebSocket feeds a live audit log and an
  online/offline indicator for the user's connections, reconnecting with
  backoff.
- **Analytics** — a dashboard of file statistics (KPIs, files-by-type pie,
  uploads-over-time line) with date-range presets, polling and CSV export.

---

## Architecture

The app is organised by responsibility. The `api/` layer is the only place
that talks to the backend; components and pages consume it and never build
requests themselves.

```
frontend/
├── index.html                      # Vite entry HTML (mounts #root)
├── Dockerfile                      # multi-stage: dev (Vite) / build / prod (nginx)
├── nginx.conf                      # SPA fallback for the prod image
├── vite.config.ts                  # Vite + React + Tailwind plugins
├── eslint.config.js                # flat ESLint config (js + typescript-eslint + react)
├── tsconfig*.json                  # TS project references (app / node)
├── package.json / package-lock.json
├── public/                         # static assets served as-is (favicon, icons)
└── src/
    ├── main.tsx                    # React entry: renders <App/> into #root
    ├── App.tsx                     # mounts the router
    ├── index.css                   # Tailwind import, theme tokens, fonts
    ├── routes/
    │   └── AppRoutes.tsx           # route table (public + protected /dashboard)
    ├── api/                        # backend access layer (the ONLY caller of /api)
    │   ├── client.ts               # apiFetch wrapper: auth header, 401 refresh, errors
    │   ├── auth.ts                 # sign-up/in, 2FA, OAuth, tokens, /me
    │   ├── org.ts                  # organisations, members, roles, invitations
    │   ├── files.ts                # files CRUD, stats, content download
    │   ├── rag.ts                  # conversations + streaming chat (SSE)
    │   ├── realtime.ts             # audit WebSocket + connected-friends
    │   └── currentOrg.ts           # module-level selected-org id for api defaults
    ├── context/
    │   ├── OrgContext.tsx          # OrgProvider: loads orgs, role, permissions
    │   └── orgContextValue.ts      # OrgContext + useOrg hook
    ├── components/
    │   ├── auth/                   # AuthLayout, inputs, buttons, RequireAuth, ProtectedLayout
    │   ├── dashboard/              # Sidebar, Topbar, ChatMenu, MessageContent, panels…
    │   │   └── home/               # AnalyticsPanel, AuditPanel, Connections, Invitations
    │   ├── landing/                # Navbar, Hero, FeatureCards, DiscoverSection, Footer
    │   ├── icons/                  # inline SVG brand icons (Google, 42)
    │   └── *.tsx                   # Modal, forms (Upload/Edit/CreateOrg/Invite), FilePreview
    ├── pages/
    │   ├── dashboard/              # HomePage, FilesPage, ChatPage, AdminPage, UserPage
    │   └── *.tsx                   # Landing, Login, Register, OAuthCallback, legal pages
    ├── utils/                      # avatars (asset glob), validation helpers
    └── assets/                     # images and profile pictures bundled by Vite
```

Every function, component and hook is documented with a short description-only
TSDoc block (types live in the signatures, so `@param`/`@returns` are omitted).

### The API layer

All backend calls go through [`src/api/client.ts`](src/api/client.ts). Its
`apiFetch` helper prepends the `/api` base, attaches the stored access token,
parses the JSON (or 204) body, and throws a typed `ApiError` on failure. On a
`401` it refreshes the token **once** — deduplicating concurrent refreshes —
and retries; if the refresh fails it clears the session and redirects to
`/login`. The streaming chat and binary download paths deliberately bypass
`apiFetch` because they read a stream / blob rather than JSON.

### Auth & routing

`RequireAuth` verifies the session via `GET /api/auth/me` before rendering,
shows a spinner while checking, opens the realtime connection once
authenticated, and redirects to `/login` otherwise. `ProtectedLayout` wraps the
`/dashboard` routes with `RequireAuth` and the `OrgProvider`, so every
dashboard page has both a session and an organisation context.

### Organisation context

`OrgProvider` ([`src/context/OrgContext.tsx`](src/context/OrgContext.tsx))
loads the user's organisations, restores the last selected one from
`localStorage`, and exposes the current org, role, and the `isAdmin` /
`canWrite` permission flags via the `useOrg` hook. The selected org id is also
mirrored into `src/api/currentOrg.ts` so org-scoped API calls can default to it
without threading it through every call.

---

## Backend integration

The app is served and proxied by the **gateway**; it assumes these routes:

| Path prefix   | Proxied to        | Used by                                   |
| ------------- | ----------------- | ----------------------------------------- |
| `/api/auth/`  | auth service      | sign-up/in, 2FA, OAuth, `/me`, refresh    |
| `/api/org/`   | org service       | organisations, members, invitations       |
| `/api/core/`  | core service      | files CRUD, stats, content download        |
| `/api/rag/`   | rag service       | conversations, `POST /query/stream` (SSE)  |
| `/ws/`        | realtime service  | audit WebSocket, connected-friends          |
| `/`           | this frontend     | the SPA itself                              |

Because everything is same-origin behind the gateway, the app uses relative
URLs (`/api/...`, `/ws/...`) and needs no CORS handling or configured base URL.

---

## Tech stack

- **React 19** + **TypeScript**, bundled by **Vite**.
- **react-router-dom** for client-side routing.
- **Tailwind CSS v4** (via `@tailwindcss/vite`), with theme tokens and fonts
  declared in [`src/index.css`](src/index.css): the `keepr` brand blue and the
  Montserrat / Shippori Mincho / IBM Plex Mono font families.
- **lucide-react** for icons, **recharts** for the analytics charts,
  **react-markdown** for rendering chat answers, and **qrcode** for the 2FA
  enrolment QR code.

---

## Running

### With Docker (recommended)

The frontend is part of the root `docker-compose.yml` and comes in two flavours
selected by the compose profile (`PROFILE`, `dev` by default):

- **dev** (`frontend-dev`): runs the Vite dev server with HMR; the gateway
  proxies `/` to it (`BACKEND=http://frontend-dev:5173`).
- **prod** (`frontend-prod`): builds the static bundle and serves it with nginx
  (SPA fallback in [`nginx.conf`](nginx.conf)); the gateway proxies `/` to
  `http://frontend-prod:80`.

```bash
make run          # dev profile with HMR (default)
make prod         # prod profile (built bundle behind nginx)
```

Access the app through the gateway (not the frontend port directly):
`https://localhost:8443` (or `http://localhost:8080`).

### Locally (outside Docker)

```bash
cd frontend
npm install
npm run dev       # Vite dev server on http://localhost:5173
```

Running the dev server on its own serves the UI, but API/WebSocket calls expect
the gateway; run the full stack (or point the gateway at your dev server) for a
working backend.

```bash
npm run build     # type-check (tsc -b) + production build into dist/
npm run preview   # serve the built bundle locally
```

## Code quality

The app is checked with **ESLint** (flat config: `@eslint/js` +
`typescript-eslint` + React Hooks / React Refresh) and the **TypeScript**
compiler:

```bash
npm run lint                          # eslint .
npx tsc -p tsconfig.app.json --noEmit  # type-check without emitting
```
