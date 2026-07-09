<p align="center">
  <img src="https://img.shields.io/badge/FASTAPI-COURS-111111?style=for-the-badge&labelColor=000000" alt="cours fastapi" />
</p>

<h1 align="center">FastAPI — Cours complet</h1>

<p align="center">
  Routing, modèles de données, injection de dépendances, sécurité : les fondations d'un service backend en FastAPI.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/Starlette-000000?style=for-the-badge" alt="Starlette" />
  <img src="https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white" alt="OpenAPI" />
</p>

<hr/>

<h2>Table des matières</h2>

<ul>
  <li><a href="#ch0">0. Prérequis et vocabulaire de base</a></li>
  <li><a href="#ch1">1. Anatomie d'une requête et d'une réponse HTTP</a></li>
  <li><a href="#ch2">2. Routing : décorateurs et path operations</a></li>
  <li><a href="#ch3">3. Origine des données : Path, Query, Body, Header, Cookie</a></li>
  <li><a href="#ch4">4. Modèles Pydantic : BaseModel et validation</a></li>
  <li><a href="#ch5">5. response_model : filtrer et documenter la sortie</a></li>
  <li><a href="#ch6">6. Injection de dépendances : Depends</a></li>
  <li><a href="#ch7">7. Sécurité des données sensibles</a></li>
  <li><a href="#annexeA">Annexe A. Pièges fréquents</a></li>
  <li><a href="#annexeB">Annexe B. Glossaire</a></li>
  <li><a href="#annexeC">Annexe C. Exercices de synthèse</a></li>
</ul>

<hr/>

<h2 id="ch0">0. Prérequis et vocabulaire de base</h2>

<h3>Qu'est-ce qu'une requête HTTP</h3>

<p>
Un client envoie une <b>requête HTTP</b> : une méthode (<code>GET</code>, <code>POST</code>, <code>PUT</code>,
<code>PATCH</code>, <code>DELETE</code>...), un path, des headers, et éventuellement un body. Le serveur répond avec
un <b>status code</b>, des headers, et généralement un body. Le <b>routing</b> est le mécanisme qui associe une
paire (méthode, path) à une fonction Python précise.
</p>

<h3>ASGI, en une phrase</h3>

<p>
<b>ASGI</b> (Asynchronous Server Gateway Interface) est le standard qui permet à un serveur (<code>uvicorn</code>)
de communiquer avec une application Python de façon asynchrone : pendant qu'une requête attend une opération lente
(base de données, appel réseau), le serveur peut en traiter d'autres. C'est pour cela que les fonctions FastAPI
sont déclarées avec <code>async def</code> dès qu'elles font de l'I/O.
</p>

<hr/>

<h2 id="ch1">1. Anatomie d'une requête et d'une réponse HTTP</h2>

<p>Une requête HTTP est du texte brut, structuré en zones bien définies :</p>

```
POST /auth/login?foo=bar HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGci...

{
  "email": "bob@mail.com",
  "password": "hunter2"
}
```

<table>
  <tr><th>Zone</th><th>Rôle</th><th>Exemple</th></tr>
  <tr><td>Méthode</td><td>L'action demandée</td><td><code>POST</code></td></tr>
  <tr><td>Chemin (path)</td><td>La ressource visée</td><td><code>/auth/login</code></td></tr>
  <tr><td>Query string</td><td>Filtre/tri/pagination optionnels</td><td><code>?foo=bar</code></td></tr>
  <tr><td>Headers</td><td>Métadonnées sur la requête elle-même</td><td><code>Content-Type</code>, <code>Authorization</code></td></tr>
  <tr><td>Ligne vide</td><td>Sépare les headers du body (obligatoire)</td><td>—</td></tr>
  <tr><td>Body</td><td>Le contenu métier, ce que le client veut faire</td><td><code>{"email": "...", "password": "..."}</code></td></tr>
</table>

<h3>Header vs body : technique contre métier</h3>

<p>
Un <b>header</b> décrit la requête elle-même — jamais l'action demandée. Un <b>body</b> contient le contenu
métier : les données qui font partie de ce que l'utilisateur veut réellement accomplir.
</p>

<p><b>Test pour trancher :</b> si on retire cette donnée, est-ce que la demande de l'utilisateur perd son sens
(→ métier, donc body), ou est-ce juste le mécanisme de transport qui casse (→ technique, donc header) ?</p>

<table>
  <tr><th>Donnée</th><th>Catégorie</th><th>Justification</th></tr>
  <tr><td><code>email</code>, <code>password</code></td><td>Body</td><td>Sans eux, "se connecter" n'a plus de sens</td></tr>
  <tr><td><code>Content-Type</code></td><td>Header</td><td>Dit juste comment lire le body, ne change pas la demande</td></tr>
  <tr><td><code>Authorization: Bearer &lt;jwt&gt;</code></td><td>Header</td><td>Preuve d'identité, valable pour n'importe quelle action</td></tr>
</table>

<h3>Pourquoi les données sensibles ne vont jamais dans l'URL</h3>

<p>
Les URLs (path + query string) sont loggées en clair par la quasi-totalité des serveurs web, reverse proxies et
CDN, et apparaissent dans l'historique du navigateur. Un mot de passe ou un token ne doit donc <b>jamais</b>
apparaître en query string — toujours en body (pour une création) ou en header (pour une preuve d'identité).
</p>

<hr/>

<h2 id="ch2">2. Routing : décorateurs et path operations</h2>

<h3>Tous les décorateurs de path operation, en bref</h3>

<p>Un décorateur par verbe HTTP, disponibles à la fois sur <code>app</code> et sur un <code>APIRouter</code> :</p>

<table>
  <tr><th>Décorateur</th><th>Usage typique</th></tr>
  <tr><td><code>@app.get(...)</code></td><td>Lire une ressource, sans effet de bord</td></tr>
  <tr><td><code>@app.post(...)</code></td><td>Créer une ressource</td></tr>
  <tr><td><code>@app.put(...)</code></td><td>Remplacer entièrement une ressource existante</td></tr>
  <tr><td><code>@app.patch(...)</code></td><td>Modifier partiellement une ressource existante</td></tr>
  <tr><td><code>@app.delete(...)</code></td><td>Supprimer une ressource</td></tr>
  <tr><td><code>@app.options(...)</code></td><td>Lister les méthodes autorisées sur un path (souvent géré automatiquement, ex. CORS preflight)</td></tr>
  <tr><td><code>@app.head(...)</code></td><td>Comme <code>GET</code>, mais sans body de réponse (vérifier l'existence d'une ressource)</td></tr>
  <tr><td><code>@app.trace(...)</code></td><td>Diagnostic réseau, rarement utilisé en pratique</td></tr>
</table>

<h3>Autres décorateurs et mécanismes utiles de l'application</h3>

<table>
  <tr><th>Mécanisme</th><th>Rôle</th></tr>
  <tr>
    <td><code>@app.exception_handler(MonException)</code></td>
    <td>Définit une réponse personnalisée pour un type d'exception précis, plutôt qu'une erreur 500 générique</td>
  </tr>
  <tr>
    <td><code>@app.middleware("http")</code></td>
    <td>Exécute du code avant/après <b>chaque</b> requête (mesurer un temps de réponse, ajouter un header commun...)</td>
  </tr>
  <tr>
    <td><code>@app.on_event("startup"/"shutdown")</code></td>
    <td>Ancienne façon de lancer du code au démarrage/arrêt du serveur — dépréciée</td>
  </tr>
  <tr>
    <td><code>lifespan=...</code> (paramètre de <code>FastAPI(...)</code>)</td>
    <td>Façon moderne de remplacer <code>on_event</code>, via un gestionnaire de contexte async (<code>@asynccontextmanager</code>) — ouvrir une connexion base de données au démarrage, la fermer à l'arrêt</td>
  </tr>
  <tr>
    <td><code>router.include_router(...)</code></td>
    <td>N'est pas un décorateur mais une méthode : assemble plusieurs <code>APIRouter</code> dans l'application principale</td>
  </tr>
</table>

<p>Exemple de <code>lifespan</code>, la façon actuellement recommandée de gérer le cycle de vie de l'application :</p>

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()   # exécuté au démarrage
    yield
    await database.disconnect()  # exécuté à l'arrêt

app = FastAPI(lifespan=lifespan)
```

<h3>Comment FastAPI décide d'où vient chaque paramètre</h3>

<table>
  <tr><th>Le paramètre est...</th><th>FastAPI le traite comme</th></tr>
  <tr><td>Présent dans le path (<code>{user_id}</code>)</td><td>Path parameter</td></tr>
  <tr><td>Type simple (<code>str</code>, <code>int</code>...), absent du path</td><td>Query parameter</td></tr>
  <tr><td><code>BaseModel</code> Pydantic</td><td>Body (JSON)</td></tr>
  <tr><td>Explicitement <code>Query()</code>, <code>Path()</code>, <code>Body()</code>, <code>Header()</code>, <code>Cookie()</code></td><td>Ce que tu déclares, peu importe le type</td></tr>
</table>

<h3>L'ordre des routes compte</h3>

<p>FastAPI matche les routes dans l'ordre de déclaration ; la première qui correspond gagne.</p>

```python
# incorrect — /auth/me est intercepté par /auth/{user_id}
@app.get("/auth/{user_id}")
async def get_user(user_id: str): ...

@app.get("/auth/me")
async def get_me(): ...   # jamais atteint


# correct — la route la plus spécifique d'abord
@app.get("/auth/me")
async def get_me(): ...

@app.get("/auth/{user_id}")
async def get_user(user_id: str): ...
```

<h3><code>APIRouter</code> — structurer un projet qui grossit</h3>

```python
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", status_code=201)
async def signup(payload: UserCreate): ...
```

```python
app.include_router(router)
```

<p>
Une dépendance peut être appliquée à tout un routeur d'un coup, pour protéger tous ses endpoints en une seule
ligne :
</p>

```python
router = APIRouter(prefix="/auth/2fa", dependencies=[Depends(get_current_user)])
```

<hr/>

<h2 id="ch3">3. Origine des données : Path, Query, Body, Header, Cookie</h2>

<p>
Sur chaque paramètre, il y a deux informations indépendantes : le <b>type</b> (quelle sorte de valeur) et
l'<b>origine</b> (d'où elle vient, avec quelles règles). <code>Query()</code>, <code>Path()</code>,
<code>Body()</code>, <code>Header()</code>, <code>Cookie()</code>, <code>Depends()</code> ne sont pas des
types — ce sont des marqueurs de configuration, jamais reçus tels quels par la fonction.
</p>

```python
limit: int = Query(default=20, ge=1, le=100)
#      ^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#      type  origine + contraintes
```

<h3>Ce qui se passe, dans l'ordre</h3>

<ol>
  <li>Au démarrage, FastAPI inspecte la signature et repère ces marqueurs.</li>
  <li>À chaque requête, il extrait la donnée brute, la valide selon les règles données, puis la remplace par la valeur finale convertie.</li>
  <li>La fonction est appelée avec cette valeur — jamais avec l'objet de configuration lui-même.</li>
  <li>Si la validation échoue, la fonction n'est jamais appelée : réponse <code>422</code> directe.</li>
</ol>

<h3>Détail par origine</h3>

<table>
  <tr><th>Origine</th><th>Rôle</th><th>Exemple</th></tr>
  <tr>
    <td><code>Path</code></td>
    <td>Identifie une ressource précise ; toujours obligatoire</td>
    <td><code>session_id: int = Path(gt=0)</code></td>
  </tr>
  <tr>
    <td><code>Query</code></td>
    <td>Filtre, trie, pagine ; généralement optionnel</td>
    <td><code>limit: int = Query(default=20, ge=1, le=100)</code></td>
  </tr>
  <tr>
    <td><code>Body</code></td>
    <td>Données structurées/sensibles pour créer ou modifier ; via un <code>BaseModel</code>, détecté automatiquement</td>
    <td><code>payload: UserCreate</code></td>
  </tr>
  <tr>
    <td><code>Header</code></td>
    <td>Métadonnée sur la requête (auth, format) ; en pratique lu via <code>Depends</code> plutôt qu'à la main</td>
    <td><code>Authorization: Bearer &lt;jwt&gt;</code></td>
  </tr>
  <tr>
    <td><code>Cookie</code></td>
    <td>Token auto-renvoyé par le navigateur, protégé du JavaScript avec <code>httpOnly</code></td>
    <td><code>refresh_token: str = Cookie()</code></td>
  </tr>
  <tr>
    <td><code>Depends</code></td>
    <td>Valeur calculée par une fonction serveur, pas lue directement de la requête</td>
    <td><code>current_user: User = Depends(get_current_user)</code></td>
  </tr>
</table>

<h3>Tableau décisionnel</h3>

<table>
  <tr><th>Donnée</th><th>Origine</th><th>Pourquoi</th></tr>
  <tr><td>Identifie une ressource précise</td><td>Path</td><td>Sans elle, l'URL n'a pas de sens</td></tr>
  <tr><td>Filtre/trie/pagine, optionnel</td><td>Query</td><td>Affine un résultat, ne désigne rien de précis</td></tr>
  <tr><td>Sensible ou structurée, pour créer/modifier</td><td>Body</td><td>Jamais dans une URL (logs, historique)</td></tr>
  <tr><td>Concerne la requête elle-même</td><td>Header</td><td>Contexte technique, pas contenu métier</td></tr>
  <tr><td>Doit survivre entre requêtes sans le frontend</td><td>Cookie</td><td>Auto-renvoyé par le navigateur</td></tr>
  <tr><td>Calculée par de la logique déjà écrite</td><td>Depends</td><td>Ne vient pas directement du client</td></tr>
</table>

<hr/>

<h2 id="ch4">4. Modèles Pydantic : BaseModel et validation</h2>

<h3>Classe et instance, rappel</h3>

<p>
Une classe est un moule — la forme que doit avoir la donnée. Une instance est ce qu'on obtient en utilisant ce
moule. Une classe Python normale ne vérifie rien ; <code>BaseModel</code> ajoute une étape de <b>validation et
conversion</b> au moment où l'instance est construite.
</p>

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

<h3>Contraintes avec <code>Field</code></h3>

```python
class TotpVerify(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")
```

<p>
Un code TOTP est stocké en <code>str</code>, jamais en <code>int</code> : un nombre ne conserve pas les zéros de
tête (<code>042917</code> deviendrait <code>42917</code>). Toute suite de chiffres qui ne sert jamais à un calcul
est du texte, pas un nombre.
</p>

<h3>Pourquoi plusieurs classes pour "un même" utilisateur</h3>

<p>
Une classe ne représente pas un concept du monde réel — elle représente la <b>forme des données à un instant
donné du cycle de vie</b>, pour un usage donné. Le même utilisateur a trois formes différentes selon le moment :
</p>

<table>
  <tr><th>Classe</th><th>Question à laquelle elle répond</th><th>Utilisée où</th></tr>
  <tr><td><code>UserCreate</code></td><td>Que demander au client pour créer un compte ?</td><td>Body, en entrée</td></tr>
  <tr><td><code>User</code></td><td>Que garder en base sur cette personne ?</td><td>Modèle interne, jamais exposé tel quel</td></tr>
  <tr><td><code>UserRead</code></td><td>Que suis-je autorisé à révéler ?</td><td><code>response_model</code>, en sortie</td></tr>
</table>

<p>
Utiliser <code>User</code> (la classe complète) comme body forcerait le client à envoyer un <code>id</code> qu'il
n'a pas encore, ou un <code>hashed_password</code> qu'il n'a pas à calculer. L'utiliser comme
<code>response_model</code> exposerait le hash du mot de passe. Ce ne sont pas des doublons — trois réponses à
trois questions différentes.
</p>

<hr/>

<h2 id="ch5">5. response_model : filtrer et documenter la sortie</h2>

<p>
<code>response_model</code> est un argument du <b>décorateur</b>, pas un paramètre de la fonction — il s'applique
à n'importe quelle méthode (<code>GET</code>, <code>POST</code>...), pas seulement <code>GET</code>.
</p>

```python
@app.post("/auth/signup", response_model=UserRead, status_code=201)
async def signup(payload: UserCreate):
    user = await user_repo.create(payload)
    return user  # objet complet, avec hashed_password
```

<h3>Ce qu'il se passe, étape par étape</h3>

<ol>
  <li>La fonction s'exécute et retourne une valeur — un objet ORM complet, un dictionnaire, peu importe.</li>
  <li>FastAPI intercepte cette valeur avant de l'envoyer au client.</li>
  <li>Il construit une instance de <code>response_model</code> à partir de cette valeur, en ne gardant que les champs déclarés.</li>
  <li>Seule cette instance reconstruite est convertie en JSON et envoyée.</li>
</ol>

<h3><code>response_model</code> vs annotation de retour</h3>

<p>
Il existe deux façons de déclarer un schéma de sortie : <code>response_model=X</code> dans le décorateur, ou
<code>-> X</code> comme type de retour de la fonction. Si les deux sont présents,
<code>response_model</code> est prioritaire à l'exécution ; l'annotation de retour ne sert alors qu'à l'éditeur
et aux outils comme mypy. On utilise <code>response_model</code> séparément dès que la fonction retourne un objet
différent du schéma de sortie (un objet ORM `User` filtré en `UserRead`, par exemple) — sinon l'éditeur signalerait
une incohérence de type.
</p>

<p>
Si la donnée retournée ne correspond pas au schéma déclaré (champ manquant, mauvais type), la fonction a déjà
fini de s'exécuter : FastAPI renvoie une erreur <b>500</b> (bug côté serveur), à distinguer d'une erreur
<b>422</b> sur une donnée d'entrée invalide (faute du client).
</p>

<h3>À quoi sert la documentation Swagger générée automatiquement</h3>

<p>
FastAPI génère une page interactive sur <code>/docs</code>, à partir des classes Pydantic et des décorateurs
réels — jamais en retard sur le code, contrairement à un document écrit à la main. Elle permet à un développeur
frontend de connaître exactement la forme attendue d'un endpoint sans lire le code backend, et de tester une
requête directement depuis le navigateur.
</p>

<hr/>

<h2 id="ch6">6. Injection de dépendances : Depends</h2>

<h3>Le principe</h3>

<p>
<code>Depends()</code> permet de dire à FastAPI : exécute d'abord cette autre fonction, et donne-moi son résultat
en paramètre.
</p>

```python
def get_greeting() -> str:
    return "Bonjour"

@app.get("/hello")
async def hello(greeting: str = Depends(get_greeting)):
    return {"message": f"{greeting}, monde"}
```

<h3>Appliqué à l'authentification</h3>

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt_service.decode(token)
    user = await user_repo.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@app.get("/auth/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

<p>
Si <code>get_current_user</code> lève une exception, FastAPI construit directement la réponse d'erreur —
<code>get_me</code> n'est jamais appelée. Ce n'est pas une variable non définie à l'intérieur de la fonction :
la fonction ne démarre tout simplement jamais son exécution.
</p>

<h3>Sous-dépendances</h3>

<p>
Une dépendance peut elle-même dépendre d'autre chose. FastAPI résout la chaîne du plus profond au plus
superficiel : <code>oauth2_scheme</code> est appelé en premier, son résultat alimente
<code>get_current_user</code>, dont le résultat alimente enfin la fonction de route.
</p>

<h3>Dépendances paramétrées</h3>

<p>
Pour passer un paramètre à une dépendance, on utilise une fonction qui <b>fabrique</b> une dépendance à la
demande — une fermeture (closure) Python garde la valeur en mémoire.
</p>

```python
def require_min_role(min_role: str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != min_role:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(require_min_role("admin"))):
    ...
```

<hr/>

<h2 id="ch7">7. Sécurité des données sensibles</h2>

<h3>Le rôle de TLS, distinct de celui des classes Pydantic</h3>

<p>
Une classe Pydantic (<code>LoginRequest</code>) sécurise la <b>structure</b> des données — elle ne chiffre rien.
Ce qui protège un mot de passe pendant son trajet réseau est une couche complètement séparée : <b>TLS</b>
(le "S" de HTTPS), gérée par le serveur web et le navigateur, avant même que FastAPI ne voie quoi que ce soit.
Sans HTTPS, n'importe qui sur le même réseau peut lire une requête en clair.
</p>

<h3>Le trajet d'un mot de passe, du client à la base</h3>

<ol>
  <li>Le client envoie <code>email</code> + <code>password</code> dans le body.</li>
  <li>FastAPI parse le JSON en objet <code>payload</code>.</li>
  <li>La fonction lit <code>payload.password</code> (une string Python ordinaire, à ce stade).</li>
  <li><code>PasswordHasher</code> hache le mot de passe (argon2/bcrypt).</li>
  <li>Seul le hash est stocké en base — le mot de passe brut n'est jamais loggé ni renvoyé.</li>
</ol>

<h3>Trois règles à respecter une fois la donnée lue</h3>

<ul>
  <li>Ne jamais logger l'objet qui contient un champ sensible en entier.</li>
  <li>Ne jamais l'inclure dans un schéma de sortie (<code>response_model</code>).</li>
  <li>Ne jamais le stocker en clair — seul le résultat du hachage est conservé.</li>
</ul>

<hr/>

<h2 id="annexeA">Annexe A. Pièges fréquents</h2>

<details open>
  <summary>Oublier le <code>default=</code> dans <code>Query()</code>/<code>Path()</code></summary>

```python
limit: int = Query(gt=0, le=100)              # devient obligatoire, 422 si absent
limit: int = Query(default=20, ge=1, le=100)  # correct, optionnel, défaut 20
```
</details>

<details>
  <summary><code>Depends(fonction())</code> au lieu de <code>Depends(fonction)</code></summary>

```python
current_user: User = get_current_user()          # appelée une seule fois, au chargement du fichier
current_user: User = Depends(get_current_user)    # appelée à chaque requête
```
</details>

<details>
  <summary>Un <code>BaseModel</code> sans <code>Depends</code> explicite = body attendu du client</summary>

```python
async def get_me(user: UserRead):                          # incorrect, FastAPI attend un body
async def get_me(user: User = Depends(get_current_user)):  # correct, calculé côté serveur
```
</details>

<details>
  <summary><code>Query(ge=0)</code> quand il fallait strictement positif</summary>

```python
user_id: int = Query(ge=0)   # accepte 0, invalide pour un ID de base de données
user_id: int = Query(gt=0)   # strictement positif
```
</details>

<details>
  <summary>Confondre 401, 403 et 404</summary>

<table>
  <tr><th>Code</th><th>Signification</th><th>Exemple</th></tr>
  <tr><td>401</td><td>Je ne sais pas qui tu es (token absent/invalide)</td><td>Header <code>Authorization</code> manquant</td></tr>
  <tr><td>403</td><td>Je sais qui tu es, mais tu n'as pas le droit</td><td>Révoquer la session d'un autre utilisateur</td></tr>
  <tr><td>404</td><td>Cette ressource n'existe pas du tout</td><td><code>session_id</code> inconnu en base</td></tr>
</table>
</details>

<details>
  <summary>Valeur par défaut mutable en Python pur (piège général, pas spécifique à Pydantic)</summary>

```python
def ajouter(item, liste=[]):   # la même liste est réutilisée entre les appels
    liste.append(item)
    return liste
```

En Pydantic, on utilise une fabrique de valeur plutôt qu'une valeur déjà construite :

```python
recovery_codes: List[str] = Field(default_factory=list)
```
</details>

<hr/>

<h2 id="annexeB">Annexe B. Glossaire</h2>

<table>
  <tr><th>Terme</th><th>Définition</th></tr>
  <tr><td>Décorateur</td><td>Fonction qui prend une autre fonction en argument et retourne une fonction, appliquée via <code>@nom</code></td></tr>
  <tr><td>Type hint</td><td>Annotation après les deux-points dans une signature, indiquant le type attendu — ignorée par Python seul, exploitée par FastAPI/Pydantic</td></tr>
  <tr><td>ASGI</td><td>Standard de communication asynchrone entre un serveur et une application Python</td></tr>
  <tr><td>WSGI</td><td>Équivalent synchrone plus ancien d'ASGI, utilisé par des frameworks comme Flask/Django classiques</td></tr>
  <tr><td>Path operation</td><td>La combinaison (méthode HTTP, path) associée à une fonction</td></tr>
  <tr><td>Body</td><td>Le contenu d'une requête, situé après la ligne vide qui suit les headers</td></tr>
  <tr><td>Header</td><td>Métadonnée sur la requête ou la réponse elle-même, jamais le contenu métier</td></tr>
  <tr><td>response_model</td><td>Paramètre du décorateur qui filtre et documente la forme de la réponse</td></tr>
  <tr><td>Dependency Injection (DI)</td><td>Mécanisme par lequel FastAPI appelle une fonction avant la tienne et t'injecte son résultat en paramètre</td></tr>
  <tr><td>Sous-dépendance</td><td>Une dépendance qui dépend elle-même d'une autre dépendance</td></tr>
  <tr><td>Closure (fermeture)</td><td>Fonction interne qui garde accès aux variables de la fonction externe qui l'a créée</td></tr>
  <tr><td>TLS</td><td>Couche de chiffrement du transport réseau, le "S" de HTTPS — distincte de la validation Pydantic</td></tr>
</table>

<hr/>

<h2 id="annexeC">Annexe C. Exercices de synthèse</h2>

<p>Pour chaque paramètre, identifie le type et le rôle du marqueur (origine, contrainte, ou les deux) :</p>

<ol>
  <li><code>email: str = Query(min_length=5)</code></li>
  <li><code>payload: UserCreate</code></li>
  <li><code>current_user: User = Depends(get_current_user)</code></li>
  <li><code>session_id: int = Path(gt=0)</code></li>
  <li><code>refresh_token: str = Cookie()</code></li>
</ol>

<p>Pour chaque scénario, choisis le code de statut HTTP le plus approprié (401, 403, 404, 422, ou 500) :</p>

<ol>
  <li>Le client envoie un <code>code</code> TOTP de 4 chiffres au lieu de 6.</li>
  <li>Le client ne fournit aucun header <code>Authorization</code> sur un endpoint protégé.</li>
  <li>Le client authentifié tente de supprimer la session d'un autre utilisateur.</li>
  <li>Le client demande une session dont l'identifiant n'existe pas en base.</li>
  <li>Le serveur retourne un objet qui ne correspond pas au <code>response_model</code> déclaré.</li>
</ol>

<p align="center"><a href="#ch0">Retour en haut</a></p>s