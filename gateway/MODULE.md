# gateway — API Gateway & WAF

Point d'entrée HTTPS unique du projet. **Nginx** route vers les services découplés, **ModSecurity (WAF)** filtre les requêtes malveillantes (injections, XSS…) avant qu'elles n'atteignent le backend.

**Module :** WAF/ModSecurity + Vault — Cybersecurity — *Majeur (2 pts)*

## À faire
- Reverse proxy Nginx : routage `/auth`, `/core`, `/org`, `/rag`, `/ws` vers les services.
- Terminaison TLS (HTTPS).
- ModSecurity + OWASP CRS activés en amont des services.

**Stack :** Nginx + ModSecurity
