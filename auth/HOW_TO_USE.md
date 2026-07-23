<h1 align="center">🔐 Service Auth — Keepr</h1>

<p align="center">
  <em>Guide d'utilisation complet</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT" />
  <img src="https://img.shields.io/badge/TOTP-6E44FF?style=for-the-badge" alt="TOTP" />
  <img src="https://img.shields.io/badge/Google_OAuth-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google OAuth" />
  <img src="https://img.shields.io/badge/42_OAuth-000000?style=for-the-badge&logo=42&logoColor=white" alt="42 OAuth" />
  <img src="https://img.shields.io/badge/httpx-000000?style=for-the-badge" alt="httpx" />
  <img src="https://img.shields.io/badge/Argon2%2FBcrypt-0057B7?style=for-the-badge" alt="Argon2/Bcrypt" />
</p>

<h1 align="center">Comment utiliser le service <code>auth</code></h1>

<p align="center"><em>Référence complète des routes exposées par le service <code>auth</code> — à l'usage du frontend et des autres services.</em></p>

<hr/>

<h2>📑 Sommaire</h2>

<ul>
  <li><a href="#taper">1. Où taper</a></li>
  <li><a href="#tokens">2. Les tokens</a></li>
  <li><a href="#stockage">3. Stockage des tokens</a></li>
  <li><a href="#routes-classiques">4. Routes — auth classique</a></li>
  <li><a href="#routes-oauth">5. Routes — connexion OAuth (Google &amp; 42)</a></li>
  <li><a href="#lookup">6. Route — recherche par email</a></li>
  <li><a href="#schemas">7. Schémas de données</a></li>
  <li><a href="#recap">8. Table récapitulative</a></li>
  <li><a href="#attention">9. Points d'attention</a></li>
</ul>

<hr/>

<h2 id="taper">1. Où taper</h2>

<p>Toutes les requêtes passent par la gateway :</p>

<pre>https://localhost:8443/api/auth/...</pre>

<p>Exemple complet : <code>https://localhost:8443/api/auth/signup</code>.</p>

<hr/>

<h2 id="tokens">2. Les tokens</h2>

<p>Chaque connexion complète (signup, login sans 2FA, login 2FA validé, ou login Google finalisé) donne <b>deux tokens</b> :</p>

<table>
  <tr><th></th><th><code>access_token</code></th><th><code>refresh_token</code></th></tr>
  <tr><td>Sert à</td><td>accéder aux routes protégées (<code>/me</code>, et les autres services qui valident ce même JWT)</td><td>obtenir un nouvel <code>access_token</code> sur <code>/refresh</code></td></tr>
  <tr><td>Durée de vie</td><td>15 min (configurable)</td><td>7 jours (configurable)</td></tr>
  <tr><td>Où l'envoyer</td><td>header <code>Authorization: Bearer &lt;access_token&gt;</code></td><td>paramètre de requête sur <code>/refresh</code> / <code>/logout</code></td></tr>
  <tr><td>Révocable ?</td><td>non</td><td>oui — stocké en base, supprimé au <code>logout</code> et remplacé à chaque <code>refresh</code></td></tr>
</table>

<p>Deux tokens <b>temporaires</b>, jamais stockés en base, qui n'interviennent qu'en étape intermédiaire :</p>

<table>
  <tr><th></th><th><code>pending_token</code></th><th><code>exchange_code</code></th></tr>
  <tr><td>Sert à</td><td>prouver qu'on a passé l'étape 1 du login (mot de passe, Google <b>ou</b> 42) et autoriser l'appel à <code>/login/2fa/verify</code></td><td>prouver que le callback OAuth (Google ou 42) a résolu un compte, et autoriser l'appel à <code>/oauth/exchange</code></td></tr>
  <tr><td>Durée de vie</td><td>~5 min (configurable)</td><td>~30 secondes (configurable)</td></tr>
  <tr><td>Où l'envoyer</td><td>header <code>Authorization: Bearer &lt;pending_token&gt;</code> sur <code>/login/2fa/verify</code></td><td>body JSON <code>{ "exchange_code": ... }</code> sur <code>/oauth/exchange</code></td></tr>
  <tr><td>Type interne</td><td><code>"2fa_pending"</code></td><td><code>"oauth_exchange"</code></td></tr>
</table>

<p><b>Flow standard</b> (compte sans 2FA) :</p>

<pre>
1. signup ou login
   → { tokens: { access_token, refresh_token }, user }
   → stocker les deux tokens + les infos user

2. chaque requête vers une route protégée
   → header "Authorization: Bearer &lt;access_token&gt;"

3. une requête renvoie 401 (access_token expiré ou invalide)
   → appeler /refresh avec le refresh_token
   → remplacer access_token ET refresh_token par les nouveaux reçus
   → rejouer la requête initiale

4. déconnexion
   → appeler /logout avec le refresh_token
   → effacer tokens + user côté client
</pre>

<p><b>Flow login avec 2FA</b> (mot de passe, Google ou 42, même mécanique) :</p>

<pre>
1. login (ou callback Google/42 si 2FA active)
   → { pending_token }        (PAS de tokens ni de user à ce stade)
   → conserver le pending_token en mémoire

2. login/2fa/verify
   → header "Authorization: Bearer &lt;pending_token&gt;" + body { code }
   → { tokens: { access_token, refresh_token }, user }
   → à partir d'ici, identique au flow standard
</pre>

<p>À chaque <code>refresh</code>, le <code>refresh_token</code> change (rotation) : l'ancien devient invalide immédiatement. Réutiliser un <code>refresh_token</code> déjà consommé renvoie <code>401</code>.</p>

<p>Si <code>/refresh</code> échoue, il n'y a pas de session récupérable : effacer la session locale et rediriger vers le login.</p>

<hr/>

<h2 id="stockage">3. Stockage des tokens</h2>

<p>Les tokens sont renvoyés dans le corps JSON de la réponse — le serveur ne pose aucun cookie <b>pour les tokens de session</b>. Le stockage (mémoire, <code>localStorage</code>, etc.) et le transport sont entièrement à la charge du client. Le <code>pending_token</code> et l'<code>exchange_code</code> sont éphémères et n'ont pas vocation à être persistés.</p>

<p>Les seuls cookies posés par le service sont des cookies techniques (<code>oauth_state_google</code> et <code>oauth_state_ft</code>, <code>httpOnly</code>), un par provider, utilisés en interne pour sécuriser respectivement le flow Google et le flow 42 — le frontend n'a jamais besoin de les lire ni de les manipuler, le navigateur s'en charge tout seul.</p>

<hr/>

<h2 id="routes-classiques">4. Routes — auth classique</h2>

<h3><code>POST /signup</code> — créer un compte</h3>

<p><b>Body</b> (JSON) :</p>
<pre>
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
</pre>
<p>Les 4 champs sont obligatoires. <code>email</code> doit être un email valide. Aucune règle de complexité n'est appliquée sur <code>password</code>.</p>

<p><b>Réponse succès — <code>200</code></b> : le compte est créé et l'utilisateur est directement connecté :</p>
<pre>
{
  "tokens": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "El1R_Kq5Y...",
    "token_type": "bearer"
  },
  "user": {
    "id": 1,
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "location": null,
    "avatar_id": 1,
    "is_2fa_enabled": false
  }
}
</pre>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>409</code></td><td>l'email existe déjà</td><td><code>{"detail": "Email already registered"}</code></td></tr>
  <tr><td><code>422</code></td><td>champ manquant ou email mal formé</td><td><code>{"detail": [{"type": "...", "loc": ["body", "email"], "msg": "..."}]}</code> — ici <code>detail</code> est une liste d'objets, pas une string</td></tr>
</table>

<hr/>

<h3><code>POST /login</code> — se connecter</h3>

<p><b>Body</b> (JSON) :</p>
<pre>
{
  "email": "ada@example.com",
  "password": "Sup3rSecret!"
}
</pre>

<p><b>Réponse succès — <code>200</code>, compte SANS 2FA</b> : identique à <code>signup</code> (<code>tokens</code> + <code>user</code>).</p>

<p><b>Réponse succès — <code>200</code>, compte AVEC 2FA activée</b> : la réponse n'est plus un <code>LoginResponse</code> :</p>
<pre>
{
  "pending_token": "eyJhbGciOi...2fa_pending..."
}
</pre>
<p>Ce <code>pending_token</code> doit être renvoyé (en header <code>Authorization: Bearer</code>, <b>pas</b> en query) à <code>/login/2fa/verify</code> avec le code TOTP pour obtenir les vrais tokens.</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td>mauvais mot de passe ou email inconnu (même message pour les deux, pour ne pas révéler quels emails existent)</td><td><code>{"detail": "Invalid credentials"}</code></td></tr>
</table>

<hr/>

<h3><code>POST /login/2fa/verify</code> — valider le second facteur au login</h3>

<p>Deuxième étape du login pour les comptes protégés par 2FA — que la première étape ait été <code>/login</code> (mot de passe) ou le callback Google/42 (§5).</p>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;pending_token&gt;</pre>

<p><b>Body</b> (JSON) :</p>
<pre>{ "code": "482913" }</pre>

<p><b>Réponse succès — <code>200</code></b> : identique à un login classique (<code>tokens</code> + <code>user</code>).</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td>code TOTP invalide</td><td><code>{"detail": "Invalid code"}</code></td></tr>
  <tr><td><code>401</code></td><td><code>pending_token</code> absent, invalide ou expiré</td><td><code>{"detail": "Invalid token"}</code> / <code>{"detail": "Token expired"}</code></td></tr>
  <tr><td><code>401</code></td><td>user du <code>pending_token</code> introuvable</td><td><code>{"detail": "User not found"}</code></td></tr>
</table>

<hr/>

<h3><code>GET /me</code> — profil de l'utilisateur connecté</h3>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "id": 1,
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "location": null,
  "avatar_id": 1,
  "is_2fa_enabled": false
}
</pre>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td>header <code>Authorization</code> absent</td><td><code>{"detail":"Not authenticated"}</code></td></tr>
  <tr><td><code>401</code></td><td>token invalide (signature fausse, malformé)</td><td><code>{"detail":"Invalid token"}</code></td></tr>
  <tr><td><code>401</code></td><td>token expiré</td><td><code>{"detail":"Token expired"}</code></td></tr>
</table>

<hr/>

<h3><code>POST /2fa/enable</code> — démarrer l'activation de la 2FA</h3>

<p>Génère un secret TOTP pour l'utilisateur connecté. <b>La 2FA n'est pas encore active</b> à ce stade : il faut confirmer avec <code>/2fa/enable/verify</code>.</p>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "secret": "JBSWY3DPEHPK3PXP",
  "otpauth_uri": "otpauth://totp/Keepr:ada@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Keepr"
}
</pre>
<ul>
  <li><code>secret</code> : la chaîne à saisir manuellement dans l'application d'authentification.</li>
  <li><code>otpauth_uri</code> : l'URI à encoder en <b>QR code côté client</b>. Le service ne génère pas d'image.</li>
</ul>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>409</code></td><td>la 2FA est déjà active sur ce compte</td><td><code>{"detail": "2FA already enabled"}</code></td></tr>
</table>

<hr/>

<h3><code>POST /2fa/enable/verify</code> — confirmer l'activation de la 2FA</h3>

<p>Confirme que l'application d'authentification est bien configurée. C'est seulement ici que <code>is_2fa_enabled</code> passe à <code>true</code>.</p>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Body</b> (JSON) :</p>
<pre>{ "code": "482913" }</pre>

<p><b>Réponse succès — <code>200</code></b>, body vide (<code>null</code>).</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td>code TOTP invalide</td><td><code>{"detail": "Invalid code"}</code></td></tr>
  <tr><td><code>401</code></td><td>2FA non configurée (aucun secret en attente)</td><td><code>{"detail": "2FA not configured"}</code></td></tr>
</table>

<hr/>

<h3><code>POST /2fa/disable</code> — désactiver la 2FA</h3>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Réponse succès — <code>200</code></b> : le <code>UserRead</code> à jour (<code>is_2fa_enabled</code> repassé à <code>false</code>).</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td>2FA non active sur ce compte</td><td><code>{"detail": "2FA not configured"}</code></td></tr>
</table>

<hr/>

<h3><code>PATCH /update</code> — mettre à jour le profil</h3>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Body</b> (JSON) :</p>
<pre>
{
  "location": "Paris",
  "avatar_id": 3
}
</pre>
<p><code>location</code> et <code>avatar_id</code> sont <b>tous les deux obligatoires</b> : pas de mise à jour partielle d'un seul champ.</p>

<p><b>Réponse succès — <code>200</code></b> : le <code>UserRead</code> à jour.</p>

<hr/>

<h3><code>POST /refresh</code> — renouveler l'access token</h3>

<p><code>refresh_token</code> est un <b>paramètre de requête</b>, pas un body JSON :</p>
<pre>POST /refresh?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY</pre>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "access_token": "nouveau-token...",
  "refresh_token": "nouveau-refresh-token...",
  "token_type": "bearer"
}
</pre>
<p>Les deux tokens précédemment stockés côté client doivent être remplacés — l'ancien <code>refresh_token</code> est invalidé côté serveur dès cet appel.</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td><code>refresh_token</code> invalide, déjà utilisé, ou inconnu</td><td><code>{"detail": "Invalid token"}</code></td></tr>
  <tr><td><code>401</code></td><td><code>refresh_token</code> expiré (plus de 7 jours)</td><td><code>{"detail": "Token expired"}</code></td></tr>
</table>

<hr/>

<h3><code>POST /logout</code> — déconnexion</h3>

<p><code>refresh_token</code> en paramètre de requête, comme pour <code>refresh</code> :</p>
<pre>POST /logout?refresh_token=El1R_Kq5YdjetznpohPSRbs5ywmZigcgIExwBNFtSMY</pre>

<p><b>Réponse succès — <code>200</code></b>, body vide (<code>null</code>). La réponse est <code>200</code> que le token existait ou non côté serveur — elle ne renseigne jamais sur ce point.</p>

<hr/>

<h2 id="routes-oauth">5. Routes — connexion OAuth (Google &amp; 42)</h2>

<p>Contrairement aux routes précédentes, ce flow <b>ne se résume pas à des appels <code>fetch</code> classiques</b> : il passe par de vraies redirections de navigateur, parce que le provider (Google ou 42) redirige lui-même l'utilisateur en dehors de l'application. Les deux providers suivent <b>exactement la même mécanique</b>, seuls les URLs et le nom du cookie technique changent.</p>

<pre>
1. GET /oauth/google/login   (ou GET /oauth/42/login)
   → { authorization_url: "https://accounts.google.com/..." }   (ou "https://api.intra.42.fr/oauth/authorize?...")
   → le frontend fait lui-même window.location.href = authorization_url

2. l'utilisateur se connecte / consent chez le provider
   → le service auth n'est pas impliqué à cette étape

3. le provider redirige le navigateur vers GET /oauth/google/callback (ou /oauth/42/callback)
   → le service auth résout le compte (déjà lié, à lier, ou nouveau)
   → il redirige À SON TOUR le navigateur vers le frontend :

   SI 2FA active sur ce compte :
     {FRONTEND_URL}/oauth/callback?pending_token=...
     → traiter EXACTEMENT comme l'étape 2 du flow 2FA classique (§4),
       en appelant /login/2fa/verify avec ce pending_token

   SINON :
     {FRONTEND_URL}/oauth/callback?exchange_code=...
     → le frontend lit ce paramètre dans l'URL et appelle :

4. POST /oauth/exchange { exchange_code }
   → { tokens: { access_token, refresh_token }, user }
   → identique à un login classique réussi, à partir d'ici
   → cette route est UNIQUE et partagée par les deux providers : elle ne fait que
     décoder le exchange_code (JWT type="oauth_exchange"), elle ne sait pas et n'a
     pas besoin de savoir d'où vient l'utilisateur
</pre>

<p><b>Ce que le frontend doit construire</b> : une page/route <code>{FRONTEND_URL}/oauth/callback</code> qui lit les query params de l'URL, commune aux deux providers :</p>
<pre>
const params = new URLSearchParams(window.location.search);
const pendingToken = params.get("pending_token");
const exchangeCode = params.get("exchange_code");
</pre>
<p>— pas besoin de décoder quoi que ce soit, ni de savoir si l'utilisateur vient de Google ou de 42 : la présence de l'un ou l'autre paramètre suffit à savoir quoi faire ensuite.</p>

<h3 id="routes-google">5.1 Google</h3>

<h4><code>GET /oauth/google/login</code> — démarrer la connexion Google</h4>

<p>Pas d'authentification, pas de body.</p>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=openid+email+profile&state=..."
}
</pre>
<p>Le frontend doit faire naviguer le navigateur vers cette URL (<code>window.location.href = ...</code>), pas juste afficher la réponse. Un cookie technique <code>oauth_state_google</code> (<code>httpOnly</code>, 10 min) est posé à cette étape.</p>

<hr/>

<h4><code>GET /oauth/google/callback</code> — jamais appelée directement par le frontend</h4>

<p>Cette route est le <code>redirect_uri</code> enregistré côté Google — elle n'est atteinte que par la redirection du navigateur suite au consentement Google, jamais par un <code>fetch</code> du frontend.</p>

<p><b>Réponse</b> : une redirection (<code>307</code>) vers <code>{FRONTEND_URL}/oauth/callback?pending_token=...</code> ou <code>?exchange_code=...</code>, selon que la 2FA est active ou non sur le compte résolu.</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td><code>state</code> absent, invalide, ou ne correspondant pas au cookie <code>oauth_state_google</code> posé par <code>/oauth/google/login</code></td><td><code>{"detail": "OAuth state error"}</code></td></tr>
  <tr><td><code>400</code></td><td>Google refuse le <code>code</code> (expiré, déjà utilisé, invalide)</td><td><code>{"detail": "Google authentication failed"}</code></td></tr>
</table>

<hr/>

<h3 id="routes-42">5.2 42</h3>

<h4><code>GET /oauth/42/login</code> — démarrer la connexion 42</h4>

<p>Pas d'authentification, pas de body. Même contrat de réponse que Google — le frontend ne devrait pas avoir besoin de distinguer les deux avant d'appeler <code>window.location.href</code>.</p>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "authorization_url": "https://api.intra.42.fr/oauth/authorize?client_id=...&redirect_uri=...&scope=public&state=..."
}
</pre>
<p>Le frontend doit faire naviguer le navigateur vers cette URL. Un cookie technique <code>oauth_state_ft</code> (<code>httpOnly</code>, 10 min) est posé à cette étape — distinct du cookie Google, les deux flows peuvent coexister sans se marcher dessus.</p>

<hr/>

<h4><code>GET /oauth/42/callback</code> — jamais appelée directement par le frontend</h4>

<p>Cette route est le <code>redirect_uri</code> enregistré côté 42 (intranet, <a href="https://profile.intra.42.fr/oauth/applications">profile.intra.42.fr/oauth/applications</a>) — elle n'est atteinte que par la redirection du navigateur suite au consentement 42, jamais par un <code>fetch</code> du frontend.</p>

<p><b>Réponse</b> : une redirection (<code>307</code>) vers <code>{FRONTEND_URL}/oauth/callback?pending_token=...</code> ou <code>?exchange_code=...</code>, selon que la 2FA est active ou non sur le compte résolu — identique à Google à partir d'ici.</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td><code>state</code> absent, invalide, ou ne correspondant pas au cookie <code>oauth_state_ft</code> posé par <code>/oauth/42/login</code></td><td><code>{"detail": "OAuth state error"}</code></td></tr>
  <tr><td><code>400</code></td><td>42 refuse le <code>code</code> (expiré, déjà utilisé, invalide)</td><td><code>{"detail": "42 authentication failed"}</code></td></tr>
</table>

<hr/>

<h3>5.3 Finaliser la connexion (partagé Google &amp; 42)</h3>

<h4><code>POST /oauth/exchange</code> — finaliser la connexion OAuth</h4>

<p><b>Body</b> (JSON) :</p>
<pre>{ "exchange_code": "eyJhbGciOi...oauth_exchange..." }</pre>
<p>Le <code>exchange_code</code> reçu en query param sur <code>{FRONTEND_URL}/oauth/callback</code>, qu'il vienne du callback Google ou du callback 42 — route unique, pas de variante par provider.</p>

<p><b>Réponse succès — <code>200</code></b> : identique à un login classique réussi (<code>tokens</code> + <code>user</code>).</p>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>401</code></td><td><code>exchange_code</code> invalide, mal formé, ou de mauvais type</td><td><code>{"detail": "Invalid token"}</code></td></tr>
  <tr><td><code>401</code></td><td><code>exchange_code</code> expiré (~30s)</td><td><code>{"detail": "Token expired"}</code></td></tr>
  <tr><td><code>401</code></td><td>user introuvable</td><td><code>{"detail": "User not found"}</code></td></tr>
</table>

<hr/>

<h2 id="lookup">6. Route — recherche par email</h2>

<h3><code>GET /users/by-email</code> — retrouver un utilisateur par email</h3>

<p>Pensée pour un usage inter-services (org, core) via la dépendance d'auth partagée, plutôt que pour un appel direct depuis l'UI — mais accessible à quiconque possède un <code>access_token</code> valide.</p>

<p><b>Headers requis :</b></p>
<pre>Authorization: Bearer &lt;access_token&gt;</pre>

<p><b>Query param :</b></p>
<pre>GET /users/by-email?email=ada@example.com</pre>

<p><b>Réponse succès — <code>200</code></b> :</p>
<pre>
{
  "id": 1,
  "email": "ada@example.com",
  "first_name": "Ada",
  "last_name": "Lovelace"
}
</pre>

<table>
  <tr><th>Code</th><th>Quand</th><th>Body</th></tr>
  <tr><td><code>404</code></td><td>aucun utilisateur avec cet email</td><td><code>{"detail": "No user with this email"}</code></td></tr>
  <tr><td><code>401</code></td><td>pas d'<code>access_token</code> valide</td><td><code>{"detail":"Invalid token"}</code> / <code>{"detail":"Not authenticated"}</code></td></tr>
</table>

<hr/>

<h2 id="schemas">7. Schémas de données</h2>

<table>
  <tr><th>Schéma</th><th>Champs</th><th>Utilisé dans</th></tr>
  <tr><td><code>UserCreate</code></td><td><code>first_name</code>, <code>last_name</code>, <code>email</code>, <code>password</code></td><td>entrée <code>/signup</code></td></tr>
  <tr><td><code>UserLogin</code></td><td><code>email</code>, <code>password</code></td><td>entrée <code>/login</code></td></tr>
  <tr><td><code>UserUpdate</code></td><td><code>location</code>, <code>avatar_id</code> (les deux obligatoires)</td><td>entrée <code>/update</code></td></tr>
  <tr><td><code>TwoFactorVerify</code></td><td><code>code</code></td><td>entrée <code>/login/2fa/verify</code>, <code>/2fa/enable/verify</code></td></tr>
  <tr><td><code>OAuthExchange</code></td><td><code>exchange_code</code></td><td>entrée <code>/oauth/exchange</code></td></tr>
  <tr><td><code>UserRead</code></td><td><code>id</code>, <code>first_name</code>, <code>last_name</code>, <code>email</code>, <code>location</code> (ou <code>null</code>), <code>avatar_id</code>, <code>is_2fa_enabled</code></td><td>sortie <code>/me</code>, <code>/update</code>, <code>/2fa/disable</code>, et <code>user</code> de <code>signup</code>/<code>login</code>/<code>login/2fa/verify</code>/<code>oauth/exchange</code>. Ne contient jamais mot de passe, hash, ou secret 2FA.</td></tr>
  <tr><td><code>UserLookup</code></td><td><code>id</code>, <code>email</code>, <code>first_name</code>, <code>last_name</code></td><td>sortie <code>/users/by-email</code></td></tr>
  <tr><td><code>TokenResponse</code></td><td><code>access_token</code>, <code>refresh_token</code>, <code>token_type</code> (toujours <code>"bearer"</code>)</td><td>sortie <code>/refresh</code>, et <code>tokens</code> de <code>signup</code>/<code>login</code>/<code>login/2fa/verify</code>/<code>oauth/exchange</code></td></tr>
  <tr><td><code>LoginResponse</code></td><td><code>tokens: TokenResponse</code> + <code>user: UserRead</code></td><td>sortie <code>/signup</code>, <code>/login</code> (sans 2FA), <code>/login/2fa/verify</code>, <code>/oauth/exchange</code></td></tr>
  <tr><td><code>TwoFactorRequired</code></td><td><code>pending_token</code></td><td>sortie <code>/login</code> et callback Google/42, quand la 2FA est active</td></tr>
  <tr><td><code>TwoFactorCredentials</code></td><td><code>secret</code>, <code>otpauth_uri</code></td><td>sortie <code>/2fa/enable</code></td></tr>
  <tr><td><code>OAuthRedirect</code></td><td><code>authorization_url</code></td><td>sortie <code>/oauth/google/login</code> et <code>/oauth/42/login</code></td></tr>
</table>

<hr/>

<h2 id="recap">8. Table récapitulative</h2>

<table>
  <tr><th>Méthode</th><th>Route</th><th>Auth requise</th><th>Body/Query</th><th>Réponse succès</th></tr>
  <tr><td><code>POST</code></td><td><code>/signup</code></td><td>non</td><td>body (<code>UserCreate</code>)</td><td><code>200</code> <code>LoginResponse</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/login</code></td><td>non</td><td>body (<code>UserLogin</code>)</td><td><code>200</code> <code>LoginResponse</code> ou <code>TwoFactorRequired</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/login/2fa/verify</code></td><td><code>Bearer &lt;pending_token&gt;</code></td><td>body (<code>TwoFactorVerify</code>)</td><td><code>200</code> <code>LoginResponse</code></td></tr>
  <tr><td><code>GET</code></td><td><code>/me</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>—</td><td><code>200</code> <code>UserRead</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/2fa/enable</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>—</td><td><code>200</code> <code>TwoFactorCredentials</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/2fa/enable/verify</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>body (<code>TwoFactorVerify</code>)</td><td><code>200</code> <code>null</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/2fa/disable</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>—</td><td><code>200</code> <code>UserRead</code></td></tr>
  <tr><td><code>PATCH</code></td><td><code>/update</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>body (<code>UserUpdate</code>)</td><td><code>200</code> <code>UserRead</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/refresh</code></td><td>non (refresh token fait foi)</td><td>query <code>?refresh_token=...</code></td><td><code>200</code> <code>TokenResponse</code></td></tr>
  <tr><td><code>POST</code></td><td><code>/logout</code></td><td>non (refresh token fait foi)</td><td>query <code>?refresh_token=...</code></td><td><code>200</code> <code>null</code></td></tr>
  <tr><td><code>GET</code></td><td><code>/oauth/google/login</code></td><td>non</td><td>—</td><td><code>200</code> <code>OAuthRedirect</code></td></tr>
  <tr><td><code>GET</code></td><td><code>/oauth/google/callback</code></td><td>non (appelée par Google)</td><td>query <code>?code=...&amp;state=...</code></td><td>redirection vers le frontend</td></tr>
  <tr><td><code>GET</code></td><td><code>/oauth/42/login</code></td><td>non</td><td>—</td><td><code>200</code> <code>OAuthRedirect</code></td></tr>
  <tr><td><code>GET</code></td><td><code>/oauth/42/callback</code></td><td>non (appelée par 42)</td><td>query <code>?code=...&amp;state=...</code></td><td>redirection vers le frontend</td></tr>
  <tr><td><code>POST</code></td><td><code>/oauth/exchange</code></td><td>non (exchange_code fait foi)</td><td>body (<code>OAuthExchange</code>)</td><td><code>200</code> <code>LoginResponse</code></td></tr>
  <tr><td><code>GET</code></td><td><code>/users/by-email</code></td><td><code>Bearer &lt;access_token&gt;</code></td><td>query <code>?email=...</code></td><td><code>200</code> <code>UserLookup</code></td></tr>
</table>

<hr/>

<h2 id="attention">9. Points d'attention</h2>

<ul>
  <li>Le flow de login <b>dépend de l'état 2FA</b> du compte, que la connexion se fasse par mot de passe, Google ou 42 : le client doit toujours gérer les deux formes de réponse possibles.</li>
  <li>Le champ <code>is_2fa_enabled</code> est exposé dans <code>UserRead</code>.</li>
  <li>L'activation de la 2FA se fait en <b>deux temps</b> (<code>/2fa/enable</code> puis <code>/2fa/enable/verify</code>) : le secret est généré à la première étape mais la 2FA n'est active qu'après confirmation d'un code, pour éviter de verrouiller un utilisateur dont l'application d'authentification serait mal configurée.</li>
  <li>Le service <b>ne génère pas d'image de QR code</b> : il renvoie l'<code>otpauth_uri</code>, à encoder en QR côté client.</li>
  <li>Google et 42 sont tous les deux implémentés, avec exactement la même mécanique (redirection → callback → <code>pending_token</code>/<code>exchange_code</code> → <code>/oauth/exchange</code>). Un compte Google et un compte 42 peuvent tous les deux se lier au même <code>User</code> s'ils partagent le même email.</li>
  <li>Les cookies techniques <code>oauth_state_google</code> et <code>oauth_state_ft</code> sont indépendants : lancer le flow Google puis le flow 42 (ou l'inverse) dans le même onglet ne casse rien, chaque callback ne regarde que son propre cookie.</li>
  <li>Aucun rate limiting ni lockout sur <code>/login</code>.</li>
  <li>Aucune configuration CORS explicite sur le service — passer par la gateway (<code>/api/auth/...</code>) pour éviter les erreurs CORS dans le navigateur.</li>
  <li>Les durées de tokens sont pilotées par les variables d'environnement <code>ACCESS_TOKEN_EXPIRE_MINUTES</code> (défaut 15 min), <code>REFRESH_TOKEN_EXPIRE_DAYS</code> (défaut 7 jours), <code>TEMPORARY_TOKEN_EXPIRE_MINUTES</code> (durée du <code>pending_token</code>, défaut ~5 min) et <code>OAUTH_EXCHANGE_EXPIRE_SECONDS</code> (durée de l'<code>exchange_code</code>, défaut ~30s).</li>
  <li><code>FRONTEND_URL</code> détermine où les callbacks Google et 42 redirigent le navigateur — à synchroniser avec l'équipe frontend si son URL change.</li>
</ul>

<p align="center"><a href="#taper">⬆ retour en haut</a></p>
