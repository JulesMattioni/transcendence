# gateway — Keepr API gateway & WAF

The **gateway** is the single entry point of Keepr. Every request from the
outside world — the web app, API calls, WebSockets — reaches the platform
through it and nothing else: it terminates TLS, inspects all traffic with a
Web Application Firewall (ModSecurity + OWASP CRS), and reverse-proxies each
request to the right internal service.

It is an [Nginx](https://nginx.org/) server with the
[ModSecurity](https://github.com/owasp-modsecurity/ModSecurity) v3 module,
built from `owasp/modsecurity:nginx`. It listens on `443` (HTTPS) and `80`
(HTTP → HTTPS redirect) inside the Docker network, published to the host as
`8443` and `8080`.

---

## Responsibilities

- **Single entry point** — no backend service is reachable from the host. The
  services (`auth`, `org`, `core`, `rag`, `realtime`) use `expose` (not
  `ports`) in `docker-compose.yml`, so they live only on the internal Docker
  network; the gateway is the only container that publishes ports.
- **TLS termination** — serves HTTPS with a self-signed certificate and
  redirects all plain HTTP to HTTPS.
- **Web Application Firewall** — inspects every inbound request with
  ModSecurity and the OWASP Core Rule Set in **blocking** mode before it ever
  reaches a service, rejecting malicious traffic (XSS, SQLi, LFI/RFI, …) with
  a `403`.
- **Reverse-proxy routing** — dispatches each path prefix to its service
  (auth / org / core / rag / realtime) and everything else to the frontend,
  upgrading WebSocket connections where needed.
- **Internal-route shielding** — blocks service-internal endpoints (e.g.
  `/api/org/internal/`) from being reached through the public entry point.

---

## Architecture

```
gateway/
├── Dockerfile                      # owasp/modsecurity:nginx + CRS + config + certs
├── conf/
│   ├── default.conf.template       # nginx server blocks: TLS, routing, proxying
│   ├── setup.conf.template         # loads modsecurity.conf, overrides and the CRS
│   └── modsecurity-override.conf   # targeted CRS false-positive exclusions
├── crs/                            # OWASP Core Rule Set (git-ignored, fetched by `make crs`)
│   ├── rules/                      # the CRS rule files (25 .conf)
│   └── crs-setup.conf.example      # CRS base configuration
├── certs/                          # self-signed TLS cert/key (git-ignored, `make certs`)
│   ├── server.crt
│   └── server.key
└── README.md
```

The base image regenerates its runtime config from the
`/etc/nginx/templates/**` files at container startup (envsubst), so
configuration lives in **templates** and environment variables, not in files
baked at build time. The `Dockerfile` copies the CRS, the certificate, and the
three config templates into the image; the CRS itself is not committed (it is
cloned into `crs/` by `make crs`, which `run` / `up` / `build` depend on).

### Routing

Defined in [`conf/default.conf.template`](conf/default.conf.template). The HTTP
server redirects everything to HTTPS; the HTTPS server proxies by prefix:

| Path prefix          | Proxied to                | Notes                                   |
| -------------------- | ------------------------- | --------------------------------------- |
| `/api/auth/`         | `auth:8000`               |                                         |
| `/api/org/internal/` | — (returns `404`)         | internal route, never exposed publicly  |
| `/api/org/`          | `org:8000`                |                                         |
| `/api/core/`         | `core:8000`               |                                         |
| `/api/rag/`          | `rag:8000`                | includes the `/query/stream` SSE route  |
| `/ws/`               | `realtime:8000`           | WebSocket upgrade headers set           |
| `/`                  | `${BACKEND}` (frontend)   | the SPA and its assets                  |

`/api/org/internal/` is declared **before** `/api/org/` and returns `404`, so
service-to-service internal endpoints cannot be reached from outside even
though they share the `/api/org/` prefix. `client_max_body_size 0` removes
Nginx's body-size cap so large file uploads reach core unmodified. In the dev
profile, Vite's HMR asset paths (`/@vite/`, `/src/`, …) are proxied with
`modsecurity off` so the dev server's traffic is not firewalled.

### WAF (ModSecurity + OWASP CRS)

The WAF is loaded through a **custom `setup.conf.template`**: the base image
regenerates `setup.conf` from that template at startup, so the CRS `Include`
directives must live in the template — editing the generated file would be
overwritten. [`conf/setup.conf.template`](conf/setup.conf.template) includes
the ModSecurity base config, our override file, the CRS setup, and every CRS
rule file.

Hardening (as required by the subject — "Configure strict ModSecurity/WAF"):

| Setting          | Value                                            | Where |
| ---------------- | ------------------------------------------------ | ----- |
| Rule engine      | `On` (blocking, not `DetectionOnly`)             | `MODSEC_RULE_ENGINE` env in compose |
| Rule set         | OWASP CRS (25 rule files)                         | `Dockerfile` → `/etc/modsecurity.d/rules/` |
| Paranoia level   | **2** (stricter than the default 1)               | `SecAction` appended in `Dockerfile` |
| Allowed methods  | `GET HEAD POST OPTIONS PUT PATCH DELETE`          | `SecAction` appended in `Dockerfile` |

> The CRS default method allowlist blocks `PUT`/`PATCH`/`DELETE`, which the
> core files API needs. The `Dockerfile` re-allows them via `tx.allowed_methods`
> — without this, editing or deleting a file would be rejected by the WAF.

#### False-positive handling

Paranoia level 2 is stricter and can block legitimate requests. Rather than
lowering it, specific false positives are scoped out narrowly in
[`conf/modsecurity-override.conf`](conf/modsecurity-override.conf): the Google
OAuth callback carries a `scope` parameter full of URLs and `.profile`, which
CRS misreads as LFI/RFI/RCE, so those exact rule targets are removed **only**
for `/api/auth/oauth/` paths — the WAF stays fully active everywhere else.

> When a real request unexpectedly returns `403`, check
> `docker compose logs gateway` for the matched rule id, then add a narrowly
> scoped exclusion in `modsecurity-override.conf` (or `crs-setup.conf`) rather
> than weakening the rule set globally.

#### Base-image note

`owasp/modsecurity-crs:nginx` (which bundles the CRS) is **not** used here: it
is only published for `linux/386`, which fails on our `amd64` hosts. Instead we
build on the multi-arch `owasp/modsecurity:nginx` and add the CRS ourselves.

---

## Configuration

Set on the gateway service in `docker-compose.yml`:

| Variable            | Value                                   | Purpose                                   |
| ------------------- | --------------------------------------- | ----------------------------------------- |
| `PORT`              | `80`                                    | HTTP listener (redirects to HTTPS)        |
| `SSL_PORT`          | `443`                                   | HTTPS listener                            |
| `SERVER_NAME`       | `localhost`                             | Nginx `server_name`                       |
| `BACKEND`           | `http://frontend-dev:5173` (default)    | frontend target for `/`; `frontend-prod:80` in the prod profile |
| `PROXY_SSL_CERT`    | `/etc/nginx/conf/server.crt`            | TLS certificate path                      |
| `PROXY_SSL_CERT_KEY`| `/etc/nginx/conf/server.key`            | TLS key path                              |
| `MODSEC_RULE_ENGINE`| `On`                                    | ModSecurity in blocking mode              |

### TLS certificates

The gateway needs a self-signed certificate for local HTTPS. Generate it from
the repo root:

```bash
make certs
```

This creates `gateway/certs/server.crt` and `gateway/certs/server.key` (both
git-ignored). Each teammate regenerates their own.

### CRS rule set

The OWASP CRS lives under `gateway/crs/` but is **not** committed. It is cloned
automatically by:

```bash
make crs
```

which `run` / `up` / `build` depend on, so a normal `make run` fetches it for
you.

---

## Running

The gateway is part of the root `docker-compose.yml` and depends on all backend
services:

```bash
make run          # build + start the whole stack (dev profile), gateway included
```

`make certs` and `make crs` run automatically as prerequisites. The gateway is
then reachable from the host at:

- **`https://localhost:8443`** — HTTPS (self-signed cert; expect a browser
  warning locally)
- **`http://localhost:8080`** — HTTP, redirected to HTTPS

### Verifying the WAF

```bash
# Legit request → 200
curl -sk https://localhost:8443/api/auth/health

# XSS attempt → blocked by ModSecurity (403)
curl -sk -o /dev/null -w "%{http_code}\n" \
  "https://localhost:8443/?x=<script>alert(1)</script>"

# Direct access to a backend → refused (isolation works)
curl -s --max-time 2 http://localhost:8000/health   # connection refused
```
