# gateway

> _README to be completed at the end of the project (see `MODULE.md` for the module work notes)._

SecureVault API gateway: single HTTPS entry point, WAF (Nginx + ModSecurity /
OWASP CRS) and reverse proxy routing to the internal services.

## WAF (ModSecurity + OWASP CRS)

The gateway is the project's **single entry point**: no service is reachable
from outside without going through it. This is enforced two ways:

- Backend services (`auth`, `org`, `core`, `rag`, `realtime`) use `expose` (not
  `ports`) in `docker-compose.yml` — reachable only on the internal Docker
  network, never from the host.
- All inbound traffic is inspected by ModSecurity before reaching any service.

### Base image

Built from `owasp/modsecurity:nginx` (see `Dockerfile`), which ships Nginx with
the ModSecurity v3 module already compiled. The OWASP Core Rule Set (CRS) is
added on top from `gateway/crs/` (cloned from the coreruleset repo — git-ignored,
fetched automatically by `make crs`, which `run`/`up`/`build` depend on).

> Note: the `owasp/modsecurity-crs:nginx` image was **not** usable here — it is
> only published for `linux/386`, which fails on our `amd64` hosts. We build on
> `owasp/modsecurity:nginx` (multi-arch) and add the CRS ourselves instead.

### Hardening (strict configuration)

Required by the subject ("Configure strict ModSecurity/WAF"):

| Setting | Value | Where |
|---|---|---|
| Rule engine | `On` (blocking, not `DetectionOnly`) | `MODSEC_RULE_ENGINE` env in compose |
| Rule set | OWASP CRS (25 rule files) | `Dockerfile` → `/etc/modsecurity.d/rules/` |
| Paranoia level | **2** (stricter than the default 1) | `crs-setup.conf` via `Dockerfile` |
| Rules loading | injected in `setup.conf.template` | `conf/setup.conf.template` |

The CRS is loaded through a **custom `setup.conf.template`**: the base image
regenerates `setup.conf` from that template at startup, so the CRS `Include`
directives must live in the template (editing the generated file at build time
would be overwritten).

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

> Paranoia level 2 is stricter and can produce **false positives** (legit
> requests blocked). When a real request returns 403 unexpectedly, check
> `docker compose logs gateway` for the matched rule id and whitelist it in
> `crs-setup.conf`.

## TLS certificates

The gateway needs a self-signed certificate for local HTTPS. Generate it from
the repo root:

```bash
make certs
```

This creates `gateway/certs/server.crt` and `gateway/certs/server.key` (both
git-ignored). Each teammate regenerates their own.

## Routing

Defined in `conf/default.conf.template`:

- `GET /api/auth/…`  → auth service
- `GET /api/org/…`   → org service
- `GET /api/core/…`  → core service
- `GET /api/rag/…`   → rag service
- `/ws/…`            → realtime service (WebSockets)
- `/`                → frontend (everything else)

## Ports

- `8443` — HTTPS (self-signed cert)
- `8080` — HTTP
