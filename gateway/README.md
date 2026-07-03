# gateway

> _README to be completed at the end of the project (see `MODULE.md` for the module work notes)._

SecureVault API gateway: single HTTPS entry point, WAF (Nginx + ModSecurity /
OWASP CRS) and reverse proxy routing to the internal services.

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
