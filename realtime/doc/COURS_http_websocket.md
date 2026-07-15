# Cours condensé — HTTP, WebSocket & réseau pour le module `realtime`

> Complément du `GUIDE_fastapi.py` (qui couvre FastAPI : async/def, path/query/body,
> Pydantic, ConnectionManager). Ce cours couvre ce qu'il y a **autour** : le protocole
> HTTP en profondeur, le protocole WebSocket, l'auth JWT sur WS (étape 5), et la
> plomberie réseau (Docker + gateway). À lire avec le `MODULE.md` sous les yeux.

---

## 1. HTTP — les fondamentaux

### Anatomie d'une requête
Une requête HTTP = 4 morceaux :

```
POST /internal/events HTTP/1.1        ← ligne : MÉTHODE + CHEMIN + version
Host: realtime:8000                   ← headers (métadonnées)
Content-Type: application/json
Authorization: Bearer eyJhbGci...
                                      ← ligne vide = fin des headers
{"event_type": "auth.login", ...}     ← body (corps, optionnel)
```

La réponse a la même forme :
```
HTTP/1.1 200 OK                       ← version + STATUS CODE
Content-Type: application/json
                                      ← ligne vide
{"event_id": "3f9c...", ...}          ← body
```

**HTTP est *stateless*** : chaque requête est indépendante, le serveur ne « se
souvient » de rien entre deux requêtes. C'est *la* raison pour laquelle on transporte
un JWT dans le header `Authorization` à chaque appel (il n'y a pas de « session
ouverte »). Et c'est aussi *la* limite que WebSocket vient lever (voir §3).

### Les méthodes (verbes) — quand utiliser quoi

| Verbe | Sens | Idempotent ? | Ton projet |
|-------|------|--------------|-----------|
| **GET** | lire, ne modifie rien | oui | `/health` |
| **POST** | créer / déclencher une action | non | `/internal/events` ✅ |
| **PUT** | remplacer entièrement une ressource | oui | — |
| **PATCH** | modifier partiellement | non | — |
| **DELETE** | supprimer | oui | — |

Pour realtime tu n'utilises en pratique que **GET** (`/health`) et **POST**
(`/internal/events`). « Idempotent » = rejouer la requête N fois donne le même état ;
un POST qui crée un event à chaque appel ne l'est pas.

### Où mettre les données — 4 emplacements
Une même info peut voyager à 4 endroits, et FastAPI les lit différemment :

| Emplacement | Exemple | FastAPI | Usage |
|-------------|---------|---------|-------|
| **Path** | `/users/42` | `def f(user_id: int)` | identifier une ressource |
| **Query** | `/search?q=chat&limit=5` | `def f(q: str, limit: int = 10)` | filtres, options |
| **Header** | `Authorization: Bearer ...` | `def f(authorization: str = Header())` | auth, méta |
| **Body** | `{"event_type": ...}` | `def f(event: EventIn)` | données structurées ✅ |

Ton `POST /internal/events` reçoit son event dans le **body** (JSON → Pydantic), et
lira le **token JWT** dans le **header** (ou query pour la WS, voir §4).

### Status codes — ceux que tu dois connaître
Le premier chiffre donne la famille :

- **2xx = succès**
  - `200 OK` — réponse standard avec body
  - `201 Created` — une ressource a été créée (sémantiquement correct pour un POST qui crée un event)
  - `204 No Content` — succès sans body
- **4xx = le client a fait une erreur** (c'est SA faute)
  - `400 Bad Request` — requête malformée
  - `401 Unauthorized` — pas/mauvais token → *« je ne sais pas qui tu es »*
  - `403 Forbidden` — authentifié mais pas le droit → *« je sais qui tu es, mais non »*
  - `404 Not Found`
  - `422 Unprocessable Entity` — **FastAPI le renvoie tout seul** quand le JSON ne colle pas au modèle Pydantic (mauvais type, champ manquant)
- **5xx = le serveur a planté** (c'est TA faute)
  - `500 Internal Server Error` — exception non gérée

Dans FastAPI tu forces un code avec `raise HTTPException(status_code=401, detail="...")`
ou `@app.post(..., status_code=201)`.

### Headers importants
- `Content-Type: application/json` — « mon body est du JSON ». Indispensable sinon le
  serveur ne sait pas parser.
- `Authorization: Bearer <token>` — la convention pour transporter un JWT.

---

## 2. Rappel FastAPI (l'essentiel — détails dans `GUIDE_fastapi.py`)

Les 4 réflexes à garder :
1. `async def` **dès que tu fais `await`** (réseau, sockets, broadcast) ; `def` pour un
   calcul mémoire (`/health`). **WebSocket = toujours `async`.**
2. **Jamais** de code bloquant (`time.sleep`, boucle CPU lourde) dans un `async def` →
   gèle tout le serveur.
3. Arguments remplis automatiquement selon leur source (path/query/header/body).
4. `BaseModel` (Pydantic) = validation gratuite + doc auto sur `/docs`.

### La brique en plus : `Depends` (dependency injection)
Non couverte par le GUIDE, indispensable pour l'auth. Mécanisme FastAPI pour
factoriser de la logique réutilisable — typiquement **« récupère l'utilisateur courant
à partir du token »**. Tu écris une fonction, et tu la « branches » sur un endpoint :

```python
from fastapi import Depends, HTTPException

# La dependency : mockée pour l'instant (étape 5), rebranchée sur le vrai JWT plus tard
async def get_current_user(token: str) -> dict:
    if token != "fake-token":
        raise HTTPException(status_code=401, detail="invalid token")
    return {"user_id": 42, "username": "mock"}

@app.get("/whoami")
async def whoami(user: dict = Depends(get_current_user)):
    return user   # FastAPI a appelé get_current_user et injecté le résultat
```

Avantage : la vérif du token est écrite **une fois**, réutilisée partout, et testable
isolément. Le jour où auth est prêt, tu changes **seulement** le corps de
`get_current_user`.

---

## 3. WebSocket — le protocole

### Pourquoi WebSocket et pas HTTP
HTTP = **le client demande, le serveur répond, fin**. Le serveur **ne peut pas**
t'envoyer quelque chose spontanément. Or ton flux d'audit live, c'est exactement
l'inverse : **le serveur veut pousser** un event vers le navigateur au moment où il
arrive, sans que le navigateur ait rien demandé.

Le polling (« t'as du nouveau ? » toutes les 2s) est lourd et lent. WebSocket résout ça :

| | HTTP | WebSocket |
|---|------|-----------|
| Connexion | ouverte/fermée à chaque requête | **persistante** (reste ouverte) |
| Sens | client → serveur → client | **bidirectionnel**, les deux poussent |
| Serveur peut initier ? | **non** | **oui** ← c'est ce qui te sert |
| Format | requête/réponse | flux de **messages** |

### Le handshake — WebSocket *commence* en HTTP
Point crucial pour comprendre ta gateway : une connexion WebSocket démarre comme une
**requête HTTP GET spéciale** qui demande une « montée en grade » (*upgrade*) :

```
GET /ws/audit HTTP/1.1
Host: localhost:8443
Upgrade: websocket              ← "je veux passer en WebSocket"
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHN...
```
Le serveur répond avec un status spécial **`101 Switching Protocols`** :
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
```
**À partir de là, ce n'est plus du HTTP** : le même tuyau TCP reste ouvert et les deux
côtés s'échangent des « frames » WebSocket dans les deux sens, aussi longtemps qu'ils
veulent.

👉 **C'est pour ça que ta gateway nginx doit passer les headers `Upgrade` et
`Connection`** (`MODULE.md`) : sans eux, nginx traiterait ça comme un GET HTTP normal
et le handshake échouerait. Le tunnel WS ne « marche à travers la gateway » que grâce
à ça.

### ws:// vs wss://
Comme `http://` / `https://` : `wss://` = WebSocket **chiffré** (TLS). Ton navigateur
se connecte sur `wss://localhost:8443/ws/…` (chiffré, via la gateway) ; en interne
c'est du `ws://` en clair.

### Les types de messages (frames)
Une fois connecté, ce qui circule ce sont des **frames**. Types :
- **Text** — une string (souvent du JSON encodé) → `receive_text()` / `send_text()` / `send_json()`
- **Binary** — des octets bruts → `receive_bytes()` / `send_bytes()`
- **Ping / Pong** — battements de cœur pour vérifier que la connexion est vivante
  (**gérés automatiquement**, tu n'y touches pas)
- **Close** — signal de fermeture propre → côté FastAPI ça lève `WebSocketDisconnect`

Pour toi : **tout est du JSON en text**. Tu envoies avec `await ws.send_json(event_out)`,
le navigateur reçoit du texte JSON.

### Le cycle de vie d'une WS (côté serveur)
C'est exactement le squelette de ton `/ws/audit` :

```python
@app.websocket("/ws/audit")
async def ws_audit(ws: WebSocket):
    await ws.accept()              # 1. accepter le handshake (OBLIGATOIRE)
    try:
        while True:                # 2. boucle : rester connecté
            data = await ws.receive_text()   # bloque jusqu'à message OU fermeture
            # ... (pour toi le navigateur ne fait quasi qu'écouter)
    except WebSocketDisconnect:    # 3. le navigateur a fermé
        ...                        # 4. nettoyer (retirer de la liste)
```

Points clés :
- **`accept()` est obligatoire** — tant que tu ne l'appelles pas, la connexion n'est
  pas établie.
- **La boucle `while True`** maintient la connexion ouverte. Sans elle, la fonction
  retourne et la WS se ferme immédiatement.
- **`WebSocketDisconnect`** est l'exception normale quand l'utilisateur ferme l'onglet
  — tu dois la catcher pour retirer la socket de ton `ConnectionManager` (sinon tu
  broadcast plus tard vers une socket morte → erreur).

### Le pattern broadcast (le cœur de ton module)
Ton `ConnectionManager` garde `active: list[WebSocket]`. À chaque event ingéré :
```python
async def broadcast(self, message: dict):
    for ws in list(self.active):        # copie : un envoi peut modifier la liste
        await ws.send_json(message)
```
Le lien entre tes deux flux : **`POST /internal/events` (HTTP)** reçoit un event →
l'enrichit → appelle **`broadcast()` (WS)** qui le pousse à tous les navigateurs.
Un flux HTTP entre, N flux WS sortent.

---

## 4. Auth JWT sur WebSocket (étape 5 — le piège classique)

Problème : **une WebSocket ne peut pas envoyer de header `Authorization` custom depuis
le navigateur.** L'API JS `new WebSocket(url)` ne laisse pas ajouter de headers. Donc
le pattern `Authorization: Bearer` de HTTP **ne marche pas** tel quel. Trois solutions
usuelles :

1. **Token en query param** (le plus simple, courant en dev) :
   `wss://localhost:8443/ws/audit?token=eyJhbGci...`
   ```python
   @app.websocket("/ws/audit")
   async def ws_audit(ws: WebSocket, token: str):
       user = verify_token(token)          # ta dependency mockée pour l'instant
       if not user:
           await ws.close(code=1008)       # 1008 = policy violation
           return
       await ws.accept()
       ...
   ```
   ⚠️ Le token apparaît dans l'URL (logs) — acceptable en dev/projet école, à noter.

2. **Token dans le premier message** après connexion : tu `accept()`, puis le 1er
   `receive` doit contenir le token, sinon tu `close()`. Plus propre, plus de code.

3. **Sous-protocole WebSocket** (`Sec-WebSocket-Protocol`) : possible mais overkill ici.

Pour un projet 42, **la solution 1 (query param) + une dependency mockée** est le bon
choix pour commencer, exactement comme prévu dans ton `MODULE.md` : commence avec un
`verify_token` factice qui accepte `"fake-token"`, et rebranche-le sur le vrai module
auth plus tard sans toucher au reste.

**Codes de fermeture WS** (l'équivalent des status HTTP) : `1000` = normal, `1008` =
violation de politique (auth refusée), `1011` = erreur serveur.

---

## 5. La plomberie réseau (Docker + gateway)

Ton module vit dans un système multi-conteneurs. Deux notions à avoir en tête.

**Deux réseaux, deux chemins** (ton schéma `MODULE.md`) :
- **Ingestion (interne)** : `core`/`auth` appellent
  `POST http://realtime:8000/internal/events` **de conteneur à conteneur** sur le
  réseau Docker. `realtime:8000` = le nom du service Docker fait office de hostname
  (DNS interne Docker). Ça **ne passe pas** par la gateway → pas de TLS, pas de
  ModSecurity. C'est pour ça que `/internal/events` **n'est jamais exposé**
  publiquement : il est protégé par le simple fait d'être injoignable de l'extérieur.
- **Diffusion (public)** : le navigateur passe par `wss://localhost:8443/ws/…` →
  **gateway nginx** → `realtime:8000`. La gateway fait le TLS et route `/ws/` en
  préservant les headers `Upgrade`/`Connection` (cf. §3 le handshake).

**À retenir** : un service qui veut publier un event fait un **POST HTTP interne** — il
**n'ouvre jamais** de WebSocket. Les WebSockets sont réservées aux navigateurs.
HTTP entre (ingestion), WS sort (diffusion).

---

## 6. Récap ultra-condensé — checklist mentale

| Concept | Ce qu'il faut retenir |
|---------|----------------------|
| **HTTP** | stateless ; méthode + path + headers + body ; status 2xx/4xx/5xx |
| **Données** | path (id) / query (filtres) / header (auth) / body (JSON→Pydantic) |
| **422** | FastAPI le renvoie seul si le body ne colle pas au modèle |
| **WebSocket** | connexion persistante + bidirectionnelle ; le serveur **push** |
| **Handshake** | démarre en HTTP GET + `Upgrade` → `101` ; d'où les headers nginx |
| **Cycle WS** | `accept()` → `while True: receive` → `except WebSocketDisconnect` |
| **Broadcast** | 1 POST HTTP entre → N `send_json` WS sortent |
| **Auth WS** | pas de header possible → **token en query param** + dependency mockée |
| **Réseau** | ingestion = interne conteneur↔conteneur ; diffusion = via gateway |
| **async** | `await` = réseau/socket → `async def` ; jamais de blocage dedans |

---

Ordre de dev (rappel `MODULE.md`) : echo WS → ConnectionManager → schémas Pydantic →
endpoint d'ingestion → auth JWT mockée. Le `GUIDE_fastapi.py` couvre le FastAPI, ce
cours couvre le HTTP/WS/réseau autour.
