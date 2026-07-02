# auth — Service d'authentification

Gère l'inscription, la connexion et l'identité des utilisateurs. Émet les **JWT** consommés par les autres services.

**Modules :**
- Gestion utilisateurs standard — User Management — *Majeur (2 pts)*
- 2FA (TOTP) — User Management — *Mineur (1 pt)*
- OAuth 2.0 (Google / 42) — User Management — *Mineur (1 pt)*

## À faire
- Inscription / connexion email + mot de passe (hash + sel).
- Émission et vérification des JWT.
- 2FA TOTP (activation, vérification).
- OAuth2 (Google, 42).

**Stack :** Python + FastAPI, SQLAlchemy, secrets via Vault
