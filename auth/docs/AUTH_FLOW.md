<h1 align="center">🔐 Service Auth — Keepr</h1>

<p align="center">
  <em>Guide d'implémentation complet : de la base de données au JWT.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/Alembic-6BA81E?style=for-the-badge&logo=alembic&logoColor=white" alt="Alembic"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic"/>
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT"/>
  <img src="https://img.shields.io/badge/Passlib-2C3E50?style=for-the-badge&logo=keepassxc&logoColor=white" alt="Passlib"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Vault-FFEC6E?style=for-the-badge&logo=vault&logoColor=black" alt="Vault"/>
</p>

---

## 🧭 Sommaire

1. [Le flow d'authentification](#-1--le-flow-dauthentification)
2. [PostgreSQL & le relationnel](#-2--postgresql--le-relationnel)
3. [SQLAlchemy — les modèles & la session](#-3--sqlalchemy--les-modèles--la-session)
4. [Alembic — les migrations](#-4--alembic--les-migrations)
5. [FastAPI — Pydantic, Depends, endpoints](#-5--fastapi--pydantic-depends-endpoints)
6. [Le hachage des mots de passe](#-6--le-hachage-des-mots-de-passe)
7. [JWT — fabriquer & vérifier](#-7--jwt--fabriquer--vérifier)
8. [OAuth2 / Bearer & la route protégée](#-8--oauth2--bearer--la-route-protégée)
9. [⚠️ Exceptions & points d'attention (À LIRE)](#️-9--exceptions--points-dattention)
10. [🎯 Ma boîte à outils Auth](#-10--ma-boîte-à-outils-auth)

---

## 🔄 1 — Le flow d'authentification

```
REGISTER : password_clair ─► [Pydantic valide] ─► [bcrypt HASH] ─► INSERT users(hash)
LOGIN    : password_clair ─► SELECT user WHERE email ─► verify(clair, hash)
                          ─► si OK : émet ACCESS token (JWT, court ~15min) + REFRESH token (long ~7j)
PROTÉGÉ  : GET /me   Header: Authorization: Bearer <access>
                          ─► oauth2_scheme extrait le token ─► jwt.decode (signature + exp)
                          ─► sub = id ─► session.get(User, id) ─► réponse
REFRESH  : access expiré ─► POST /refresh {refresh} ─► vérifie ─► nouvel access
```

**Deux tokens, deux rôles :**

| | Access token (JWT) | Refresh token |
|---|---|---|
| Rôle | accéder aux routes protégées | obtenir un nouvel access token |
| Durée | courte (~15 min) | longue (~7 jours) |
| Stocké en base ? | **non** (auto-porteur, signature suffit) | **oui** (pour pouvoir le révoquer) |
| Révocable ? | non → d'où le "court" | oui (supprimer sa ligne) |

---

## 🐘 2 — PostgreSQL & le relationnel

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)

**Les tables vivent dans le conteneur `postgres`, pas dans mon service.** Tous les services (auth, org, core…) se connectent à la **même base partagée** via le réseau Docker (`host = "postgres"`, le nom du service).

**Contraintes = garanties déléguées à la base :**

| Contrainte | Rôle |
|---|---|
| `PRIMARY KEY` | id unique (⇒ `NOT NULL` + `UNIQUE` + index auto) |
| `NOT NULL` | interdit l'absence de valeur (`NULL` ≠ 0 ≠ `''`) |
| `UNIQUE` | pas deux lignes identiques (⇒ index auto) |
| `DEFAULT x` | valeur si omise (`now()` pour `created_at`) |
| `FOREIGN KEY` | pointe vers une autre table (intégrité référentielle) |

**FOREIGN KEY + `ON DELETE` :**

| `ON DELETE …` | À la suppression du parent |
|---|---|
| `CASCADE` | supprime aussi les enfants (tokens sans user = inutiles) |
| `RESTRICT` | refuse tant qu'il y a des enfants (garder l'historique) |
| `SET NULL` | détache l'enfant (⚠️ colonne **nullable** obligatoire) |

**Relations :** 1-1 (FK + `UNIQUE`) · 1-N (FK côté « many ») · N-N (**table de jonction** : 2 FK + PK composite).

**JOIN :** `INNER` = intersection · `LEFT` = tout à gauche + ce qui matche.
**Transaction :** tout ou rien (`BEGIN … COMMIT` / `ROLLBACK`). **ACID** = Atomicité, Cohérence, Isolation, Durabilité.

---

## 🧱 3 — SQLAlchemy — les modèles & la session

![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)

### Anatomie d'un attribut : `nom : Mapped[X] = droite`

- **GAUCHE `Mapped[X]`** → type + nullabilité : `Mapped[str]` = NOT NULL · `Mapped[str | None]` = NULLABLE · `Mapped[list["X"]]` = « vers plusieurs ».
- **DROITE** → `mapped_column(...)` = **vraie colonne** · `relationship(...)` = **raccourci** (zéro colonne).

> **Le mot après le `=` décide tout** : `mapped_column` crée une colonne, `relationship` non.

### Les 3 briques

- **Engine** = pool de connexions (1 par processus/service, tous vers la même base).
- **Session** = une transaction (une par requête, fabriquée par l'usine `session_factory`).
- **Modèles** = classes héritant du **`Base` partagé**.

```python
# shared/database.py (importé, PAS réécrit)
engine = create_async_engine(_database_url(), echo=False)   # ne se connecte qu'à la 1re requête
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():                 # 1 session par requête + fermeture auto via yield
    async with session_factory() as session:
        yield session

class Base(DeclarativeBase):             # partagé → tous les modèles dans le même Base.metadata
    pass
```

### FK + relationship + back_populates (1-N)

```python
class User(Base):
    __tablename__ = "users"
    id:            Mapped[int] = mapped_column(primary_key=True)
    email:         Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id:      Mapped[int] = mapped_column(primary_key=True)
    token:   Mapped[str] = mapped_column(Text, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="tokens")
```

- `ForeignKey` = **la vraie donnée** (une seule, côté « many »). `relationship` = confort qui la *lit*.
- `back_populates` = nomme **l'attribut d'en face** (en croix) : `User.tokens` ↔ `RefreshToken.user`.

### Cycle de session

**4 états** : transient (neuf) → pending (`add`) → persistent (en base) → detached (session fermée).
Un objet **persistent** (chargé via `get`) n'est **jamais réinséré**.

**flush vs commit :**

| | `flush()` | `commit()` |
|---|---|---|
| Envoie le SQL | oui | oui |
| Remplit l'id auto | oui | oui |
| Valide définitivement | **non** (annulable) | **oui** |

→ `flush` uniquement quand j'ai besoin d'un id auto **au milieu** de la transaction (ex. `Profile(user_id=user.id)`). Sinon `commit` suffit.
**UPDATE** = modifier l'attribut + `commit` (dirty checking, pas d'UPDATE à écrire). **DELETE** = `await session.delete(obj)`.

### Requêtes

```python
user  = await session.get(User, 1)                                   # par PK → objet ou None
user  = (await session.scalars(select(User).where(User.email == e))).first()  # objet ou None
users = (await session.scalars(select(User))).all()                  # liste (vide [] si rien)
```

- `scalars` = objets entiers · `execute` = colonnes précises (tuples).
- `.first()` → objet/`None` · `.all()` → liste/`[]`.
- Tri : `.order_by(User.created_at.desc())` · `.limit(10)` · plusieurs `.where()` = AND.

### Lazy vs Eager (⚠️ crucial en async)

```python
# ❌ N+1 (1 requête + 1 par user) et INTERDIT en async :
for u in users: print(u.tokens)

# ✅ eager, obligatoire en async dès que j'accède à une relation :
stmt = select(User).options(selectinload(User.tokens))
```

- `selectinload` → collections (listes) · `joinedload` → relation « vers-un ».

### `await` : la règle

`await` sur tout ce qui **touche la base** (`get`, `scalars`, `commit`, `flush`, `refresh`, `delete`), jamais sur la construction (`select`, `User(...)`, `add`, modifier un attribut). Uniquement dans une fonction `async def`.

---

## 🔀 4 — Alembic — les migrations

![Alembic](https://img.shields.io/badge/Alembic-6BA81E?style=flat-square&logo=alembic&logoColor=white)

**J'écris mes tables UNE fois (les modèles). Alembic génère les migrations en les lisant.**

- `Base.metadata` = catalogue de toutes les tables (état **voulu**). La base = état **réel**. Alembic vit dans l'écart.
- Un modèle **doit être importé** (`models_registry.py`) pour être dans `Base.metadata`, sinon Alembic l'ignore.
- Le service `migrations` (conteneur dédié) lance `alembic upgrade head` au `make up` → construit/met à jour les tables pour **tous** les services, **avant** qu'ils démarrent.

**Workflow quand je change un modèle :**
```
1. modifier le modèle              2. l'importer dans models_registry.py (si nouveau)
3. docker compose build migrations 4. make migration m="..."   (Alembic GÉNÈRE)
5. RELIRE le fichier généré        6. make migrate             (applique)
7. git add ...versions/            (le fichier est du code source)
```

**Le versioning :** table `alembic_version` (dans Postgres) = marque-page de la dernière migration appliquée. La chaîne `revision`/`down_revision` = l'ordre. `upgrade head` applique tout ce qui manque entre le marque-page et le dernier maillon → **idempotent** (relançable sans danger). Je ne touche **jamais** `alembic_version` à la main.

---

## ⚡ 5 — FastAPI — Pydantic, Depends, endpoints

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white)

### Sources des données d'une requête

| Source | Où | Déclaration |
|---|---|---|
| path | `/users/{id}` | `user_id: int` (nom dans le chemin) |
| query | `?limit=20` | `limit: int = 10` (pas dans le chemin) |
| body | corps JSON | `data: UserCreate` (modèle Pydantic) |
| header | `Authorization: Bearer …` | via `oauth2_scheme` |

### Pydantic ≠ SQLAlchemy

- `class User(Base)` → SQLAlchemy, la **table**.
- `class UserCreate(BaseModel)` → Pydantic, la **validation** des données d'API.

**Séparer entrée et sortie** (règle d'or) :
```python
class UserCreate(BaseModel):    # ENTRÉE : contient le password
    email: EmailStr
    password: str

class UserRead(BaseModel):      # SORTIE : JAMAIS le hash
    id: int
    email: EmailStr
    model_config = {"from_attributes": True}   # lit depuis un objet SQLAlchemy
```

`response_model=UserRead` = filtre de sortie → même si je renvoie l'objet `User` complet, seuls `id`+`email` sortent. **Le `password_hash` ne peut jamais fuiter.**

### Depends (injection de dépendances)

`Depends(fn)` = **fournit une valeur** en appelant `fn`. Marche dans une route **ET** dans une dépendance (imbrication récursive). Si la dépendance `raise`, l'endpoint ne s'exécute pas.
Le `yield` de `get_session` = ouvre avant / **ferme après** l'endpoint (garanti même si erreur, car `finally` caché dans `async with`). C'est FastAPI qui « reprend » la fonction après le yield.

---

## 🔒 6 — Le hachage des mots de passe

![Passlib](https://img.shields.io/badge/Passlib-2C3E50?style=flat-square&logo=keepassxc&logoColor=white)

- **Jamais en clair.** **Hachage** (irréversible, pour vérifier) ≠ **chiffrement** (réversible, pour réafficher).
- **bcrypt/argon2**, pas SHA-256 : volontairement **lents** (anti brute-force) + **salt intégré**.
- **Salt** = aléatoire par user → deux users au même mot de passe ont des hash **différents** → rainbow tables inutiles. bcrypt le gère seul, rangé **dans** la chaîne du hash (une seule colonne `password_hash`).

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pwd: str) -> str:          return pwd_context.hash(pwd)
def verify_password(pwd: str, h: str) -> bool: return pwd_context.verify(pwd, h)
```

**`verify` ne déhache pas** : il rehache le mot de passe fourni avec le salt **extrait** du hash stocké, puis compare (en temps constant → anti timing-attack).

Méthodes : `hash(secret) -> str` · `verify(secret, hash) -> bool` · `needs_update(hash) -> bool` · `verify_and_update(secret, hash) -> (bool, str|None)`.
Le coût `bcrypt__rounds=N` → **2^N** itérations (+1 = ×2 le temps). Laisser le défaut (12) au début. Doc : `passlib.readthedocs.io/en/stable/narr/quickstart.html`.

---

## 🎫 7 — JWT — fabriquer & vérifier

![JWT](https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)

Lib : **PyJWT** (`import jwt`). Doc : `pyjwt.readthedocs.io/en/stable/usage.html`.

```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = ...           # depuis Vault / env — JAMAIS en dur
ALGORITHM = "HS256"

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)                 # UTC obligatoire
    payload = {
        "sub": str(user_id),                         # id user (en STRING)
        "iat": now,
        "exp": now + timedelta(minutes=15),          # access = court
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)   # → str (le token)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # → dict (le payload)
```

- Le **payload** = un dictionnaire (`sub`, `iat`, `exp`). `encode` le met dedans, `decode` le rend.
- `decode` vérifie **automatiquement** la signature + l'expiration, et **lève une exception** si problème.
- Le payload est **lisible par tous** (base64 ≠ chiffrement) → aucun secret dedans.
- Chaque token est unique car `iat`/`exp` changent → même id + même clé donnent des signatures différentes.

---

## 🛡️ 8 — OAuth2 / Bearer & la route protégée

![Vault](https://img.shields.io/badge/Vault-FFEC6E?style=flat-square&logo=vault&logoColor=black)

- **OAuth2 = autorisation** (pas authentification). **Bearer** = « au porteur » : quiconque présente un token valide est autorisé → le serveur vérifie **le token, pas l'expéditeur** (d'où : token court, HTTPS, révocation).
- `oauth2_scheme` lit le header `Authorization: Bearer <token>`, enlève `Bearer `, renvoie le token nu (ou lève 401 si absent). `tokenUrl="login"` = juste pour la doc Swagger.

```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),             # token depuis le header
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:                # SPÉCIFIQUE d'abord
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:                    # GÉNÉRIQUE ensuite
        raise HTTPException(401, "Invalid token")

    user = await session.get(User, int(payload["sub"]))   # sub est str → int()
    if user is None:                                 # token valide mais user disparu
        raise HTTPException(401, "User not found")
    return user

@app.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):     # tout est caché dans la dépendance
    return user
```

---

## ⚠️ 9 — Exceptions & points d'attention

### 🔴 Exceptions à connaître et gérer

| Exception | Vient de | Quand | Réaction |
|---|---|---|---|
| `jwt.ExpiredSignatureError` | PyJWT | token expiré (`exp` passé) | `HTTPException(401)` → client doit refresh |
| `jwt.InvalidTokenError` | PyJWT | signature fausse, token malformé/falsifié (**classe parente**) | `HTTPException(401)` |
| `IntegrityError` (`ForeignKeyViolation`) | SQLAlchemy | FK vers un id inexistant, au **commit** | `rollback` + `HTTPException(400)` |
| `IntegrityError` (`UniqueViolation`) | SQLAlchemy | email déjà pris (`unique`), au **commit** | `rollback` + `HTTPException(409)` |
| `DataError` | SQLAlchemy | valeur du mauvais type en base, au **commit** | corriger la donnée |
| `DetachedInstanceError` | SQLAlchemy | accès à une relation après `close()` | charger en eager avant |
| `MissingGreenlet` | SQLAlchemy async | **lazy loading en async** (accès relation non chargée) | eager (`selectinload`) |
| `ValidationError` → **422** | Pydantic | données d'entrée invalides | géré **automatiquement** par FastAPI |

> **Ordre des `except` : du plus SPÉCIFIQUE au plus GÉNÉRAL.** `ExpiredSignatureError` est une sous-classe de `InvalidTokenError` → le spécifique d'abord, sinon il n'est jamais atteint.

### 🟠 Points d'attention (les pièges vérifiés en soutenance)

**Sécurité mot de passe / tokens**
- [ ] `password_hash` stocké, **jamais** le mot de passe en clair.
- [ ] `password_hash` **jamais** renvoyé au client → `UserCreate` ≠ `UserRead` + `response_model`.
- [ ] JWT : **rien de secret dans le payload** (base64 ≠ chiffrement).
- [ ] `algorithms=["HS256"]` **toujours** en liste explicite (jamais déduit du token → attaque `alg=none`).
- [ ] `SECRET_KEY` depuis **Vault**/env, jamais en dur, assez longue.
- [ ] Timestamps JWT en **UTC** (`datetime.now(timezone.utc)`), sinon `exp` faussé.
- [ ] Login : **même message d'erreur** si email inconnu OU mauvais mot de passe (ne pas révéler quels emails existent).
- [ ] Access token **court** + refresh **stocké** (révocable). Bearer = token = clé → protéger (HTTPS).

**Base de données / SQLAlchemy**
- [ ] `commit()` systématique — sinon `ROLLBACK` implicite → rien écrit.
- [ ] `await` sur tout ce qui touche la base, dans des fonctions `async def`.
- [ ] Relations chargées en **eager** (`selectinload`) — lazy interdit en async.
- [ ] `== ` (comparaison) dans `.where()`, jamais `=` (affectation → SyntaxError).
- [ ] `sub` lu en `int(payload["sub"])` (stocké en string).
- [ ] Vérifier `if user is None` après un `get` (par id ou depuis un token).
- [ ] FK côté « many » + `ON DELETE` cohérent (`SET NULL` ⇒ colonne nullable).
- [ ] Modèle hérite du **`Base` partagé** + importé dans `models_registry.py`.
- [ ] `Mapped[int]` non vérifié par Python → la vraie validation type se fait en base au commit (ou via Pydantic à l'entrée).

**Alembic**
- [ ] **Relire** chaque migration générée (renommage = `drop+add` → perte de données, corriger avec `op.alter_column`).
- [ ] Rebuild l'image migrations après un changement de modèle.
- [ ] `downgrade()` défait `upgrade()` dans l'ordre inverse (enfant avant parent pour les FK).

**FastAPI / Depends**
- [ ] Échec dans une dépendance = `raise HTTPException`, **jamais** `return`.
- [ ] `except` du plus spécifique au plus général.
- [ ] `HTTPException(status_code=..., detail=...)` pour les erreurs (401, 403, 404, 409, 422).

---

## 🎯 10 — Ma boîte à outils Auth

### Les modèles
```python
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.database import Base

class User(Base):
    __tablename__ = "users"
    id:            Mapped[int]      = mapped_column(primary_key=True)
    email:         Mapped[str]      = mapped_column(String(255), unique=True)
    password_hash: Mapped[str]      = mapped_column(Text)
    is_active:     Mapped[bool]     = mapped_column(default=True)
    created_at:    Mapped[datetime] = mapped_column(server_default=func.now())
    tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id:         Mapped[int]      = mapped_column(primary_key=True)
    token:      Mapped[str]      = mapped_column(Text, unique=True)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="tokens")
```

### Les opérations types

```python
# REGISTER
user = User(email=data.email, password_hash=hash_password(data.password))
session.add(user)
await session.commit()
await session.refresh(user)          # récupère l'id généré

# LOGIN (email → verify → tokens)
user = (await session.scalars(select(User).where(User.email == data.email))).first()
if user is None or not verify_password(data.password, user.password_hash):
    raise HTTPException(401, "Invalid credentials")   # message unique
# → create_access_token(user.id) + refresh token stocké

# STOCKER un refresh token
user.tokens.append(RefreshToken(token=jeton, expires_at=dans_7_jours))
await session.commit()

# RÉVOQUER (logout)
rt = (await session.scalars(select(RefreshToken).where(RefreshToken.token == jeton))).first()
if rt:
    await session.delete(rt)
    await session.commit()

# USER COURANT (route protégée) → voir get_current_user en section 8
```

### Les endpoints à concevoir

| Endpoint | Entrée | Sortie | Notes |
|---|---|---|---|
| `POST /register` | `UserCreate` | `UserRead` | hash le password, gère email déjà pris (409) |
| `POST /login` | form/`UserLogin` | `{access, refresh}` | verify, émet les 2 tokens |
| `GET /me` | header Bearer | `UserRead` | `Depends(get_current_user)` |
| `POST /refresh` | `{refresh}` | `{access}` | vérifie le refresh (en base), émet un access |
| `POST /logout` | header/`{refresh}` | 204 | supprime le refresh token (révocation) |

---

<p align="center"><em>Comprendre d'abord, coder ensuite. Chaque brique de ce document a été construite pour être maîtrisée, pas copiée.</em></p>