<p align="center">
  <img src="https://img.shields.io/badge/FASTAPI-COURSE-111111?style=for-the-badge&labelColor=000000" alt="fastapi course" />
</p>

<h1 align="center">FastAPI — Complete Course</h1>

<p align="center">
  Routing, data models, dependency injection, security: the foundations of a backend service in FastAPI.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/Starlette-000000?style=for-the-badge" alt="Starlette" />
  <img src="https://img.shields.io/badge/OpenAPI-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white" alt="OpenAPI" />
</p>

<hr/>

<h2>Table of Contents</h2>

<ul>
  <li><a href="#ch0">0. Prerequisites and basic vocabulary</a></li>
  <li><a href="#ch1">1. Anatomy of an HTTP request and response</a></li>
  <li><a href="#ch2">2. Routing: decorators and path operations</a></li>
  <li><a href="#ch3">3. Origin of data: Path, Query, Body, Header, Cookie</a></li>
  <li><a href="#ch4">4. Pydantic models: BaseModel and validation</a></li>
  <li><a href="#ch5">5. response_model: filtering and documenting the output</a></li>
  <li><a href="#ch6">6. Dependency injection: Depends</a></li>
  <li><a href="#ch7">7. Security of sensitive data</a></li>
  <li><a href="#annexA">Appendix A. Common pitfalls</a></li>
  <li><a href="#annexB">Appendix B. Glossary</a></li>
  <li><a href="#annexC">Appendix C. Synthesis exercises</a></li>
</ul>

<hr/>

<h2 id="ch0">0. Prerequisites and basic vocabulary</h2>

<h3>What is an HTTP request</h3>

<p>
A client sends an <b>HTTP request</b>: a method (<code>GET</code>, <code>POST</code>, <code>PUT</code>,
<code>PATCH</code>, <code>DELETE</code>...), a path, headers, and optionally a body. The server responds with
a <b>status code</b>, headers, and usually a body. <b>Routing</b> is the mechanism that maps a
(method, path) pair to a specific Python function.
</p>

<h3>Decorator, a quick Python reminder</h3>

<p>
A decorator is a function that takes another function as an argument and returns a function — the
<code>@something</code> syntax above a definition is syntactic sugar for this.
</p>

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

<p>
<code>app.get(...)</code> returns a decorator that, applied to <code>health</code>, <b>registers</b> the function
in FastAPI's route table — it does not execute it. It will only be called on an actual
<code>GET /health</code> request.
</p>

<h3>ASGI, in one sentence</h3>

<p>
<b>ASGI</b> (Asynchronous Server Gateway Interface) is the standard that lets a server (<code>uvicorn</code>)
talk to a Python application asynchronously: while one request is waiting on something slow
(a database call, a network call), the server can handle others in the meantime. That's why FastAPI functions
are declared with <code>async def</code> as soon as they perform I/O.
</p>

<hr/>

<h2 id="ch1">1. Anatomy of an HTTP request and response</h2>

<p>An HTTP request is plain text, organized into well-defined zones:</p>

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
  <tr><th>Zone</th><th>Role</th><th>Example</th></tr>
  <tr><td>Method</td><td>The requested action</td><td><code>POST</code></td></tr>
  <tr><td>Path</td><td>The targeted resource</td><td><code>/auth/login</code></td></tr>
  <tr><td>Query string</td><td>Optional filtering/sorting/pagination</td><td><code>?foo=bar</code></td></tr>
  <tr><td>Headers</td><td>Metadata about the request itself</td><td><code>Content-Type</code>, <code>Authorization</code></td></tr>
  <tr><td>Blank line</td><td>Separates headers from the body (mandatory)</td><td>—</td></tr>
  <tr><td>Body</td><td>The business content — what the user actually wants to do</td><td><code>{"email": "...", "password": "..."}</code></td></tr>
</table>

<h3>Header vs body: technical vs business data</h3>

<p>
A <b>header</b> describes the request itself — never the requested action. A <b>body</b> carries the
business content: the data that is part of what the user actually wants to accomplish.
</p>

<p><b>Test to decide:</b> if you remove this piece of data, does the user's request lose its meaning
(→ business, so body), or does only the transport mechanism break (→ technical, so header)?</p>

<table>
  <tr><th>Data</th><th>Category</th><th>Justification</th></tr>
  <tr><td><code>email</code>, <code>password</code></td><td>Body</td><td>Without them, "log in" no longer makes sense</td></tr>
  <tr><td><code>Content-Type</code></td><td>Header</td><td>Just says how to read the body, doesn't change the request</td></tr>
  <tr><td><code>Authorization: Bearer &lt;jwt&gt;</code></td><td>Header</td><td>Proof of identity, valid for any action</td></tr>
</table>

<h3>Why sensitive data never goes in the URL</h3>

<p>
URLs (path + query string) are logged in plain text by almost every web server, reverse proxy, and CDN,
and they show up in browser history. A password or a token must therefore <b>never</b> appear in a query
string — always in the body (for creation) or in a header (as proof of identity).
</p>

<hr/>

<h2 id="ch2">2. Routing: decorators and path operations</h2>

<h3>All path operation decorators, in brief</h3>

<p>One decorator per HTTP verb, available both on <code>app</code> and on an <code>APIRouter</code>:</p>

<table>
  <tr><th>Decorator</th><th>Typical use</th></tr>
  <tr><td><code>@app.get(...)</code></td><td>Read a resource, no side effect</td></tr>
  <tr><td><code>@app.post(...)</code></td><td>Create a resource</td></tr>
  <tr><td><code>@app.put(...)</code></td><td>Fully replace an existing resource</td></tr>
  <tr><td><code>@app.patch(...)</code></td><td>Partially update an existing resource</td></tr>
  <tr><td><code>@app.delete(...)</code></td><td>Delete a resource</td></tr>
  <tr><td><code>@app.options(...)</code></td><td>List the methods allowed on a path (often handled automatically, e.g. CORS preflight)</td></tr>
  <tr><td><code>@app.head(...)</code></td><td>Like <code>GET</code>, but with no response body (check whether a resource exists)</td></tr>
  <tr><td><code>@app.trace(...)</code></td><td>Network diagnostics, rarely used in practice</td></tr>
</table>

<h3>Other useful application-level decorators and mechanisms</h3>

<table>
  <tr><th>Mechanism</th><th>Role</th></tr>
  <tr>
    <td><code>@app.exception_handler(MyException)</code></td>
    <td>Defines a custom response for a specific exception type, instead of a generic 500 error</td>
  </tr>
  <tr>
    <td><code>@app.middleware("http")</code></td>
    <td>Runs code before/after <b>every</b> request (measuring response time, adding a common header...)</td>
  </tr>
  <tr>
    <td><code>@app.on_event("startup"/"shutdown")</code></td>
    <td>Older way of running code at server startup/shutdown — deprecated</td>
  </tr>
  <tr>
    <td><code>lifespan=...</code> (parameter of <code>FastAPI(...)</code>)</td>
    <td>Modern replacement for <code>on_event</code>, via an async context manager (<code>@asynccontextmanager</code>) — open a database connection at startup, close it at shutdown</td>
  </tr>
  <tr>
    <td><code>router.include_router(...)</code></td>
    <td>Not a decorator but a method: assembles several <code>APIRouter</code> instances into the main application</td>
  </tr>
</table>

<p>Example of <code>lifespan</code>, the currently recommended way to manage the application's lifecycle:</p>

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()   # runs at startup
    yield
    await database.disconnect()  # runs at shutdown

app = FastAPI(lifespan=lifespan)
```

<h3>How FastAPI decides where each parameter comes from</h3>

<table>
  <tr><th>The parameter is...</th><th>FastAPI treats it as</th></tr>
  <tr><td>Present in the path (<code>{user_id}</code>)</td><td>Path parameter</td></tr>
  <tr><td>A simple type (<code>str</code>, <code>int</code>...), absent from the path</td><td>Query parameter</td></tr>
  <tr><td>A Pydantic <code>BaseModel</code></td><td>Body (JSON)</td></tr>
  <tr><td>Explicitly <code>Query()</code>, <code>Path()</code>, <code>Body()</code>, <code>Header()</code>, <code>Cookie()</code></td><td>Whatever you declare, regardless of type</td></tr>
</table>

<h3>Route order matters</h3>

<p>FastAPI matches routes in declaration order; the first one that matches wins.</p>

```python
# wrong — /auth/me gets intercepted by /auth/{user_id}
@app.get("/auth/{user_id}")
async def get_user(user_id: str): ...

@app.get("/auth/me")
async def get_me(): ...   # never reached


# correct — the most specific route comes first
@app.get("/auth/me")
async def get_me(): ...

@app.get("/auth/{user_id}")
async def get_user(user_id: str): ...
```

<h3><code>APIRouter</code> — structuring a growing project</h3>

```python
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", status_code=201)
async def signup(payload: UserCreate): ...
```

```python
app.include_router(router)
```

<p>
A dependency can be applied to an entire router at once, protecting all of its endpoints in a single
line:
</p>

```python
router = APIRouter(prefix="/auth/2fa", dependencies=[Depends(get_current_user)])
```

<hr/>

<h2 id="ch3">3. Origin of data: Path, Query, Body, Header, Cookie</h2>

<p>
For each parameter, there are two independent pieces of information: the <b>type</b> (what kind of value)
and the <b>origin</b> (where it comes from, with what rules). <code>Query()</code>, <code>Path()</code>,
<code>Body()</code>, <code>Header()</code>, <code>Cookie()</code>, <code>Depends()</code> are not
types — they are configuration markers, never received as-is by the function.
</p>

```python
limit: int = Query(default=20, ge=1, le=100)
#      ^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#      type  origin + constraints
```

<h3>What happens, in order</h3>

<ol>
  <li>At startup, FastAPI inspects the signature and spots these markers.</li>
  <li>On each request, it extracts the raw data, validates it against the given rules, then replaces it with the final converted value.</li>
  <li>The function is called with this value — never with the configuration object itself.</li>
  <li>If validation fails, the function is never called: FastAPI returns a <code>422</code> response directly.</li>
</ol>

<h3>Detail by origin</h3>

<table>
  <tr><th>Origin</th><th>Role</th><th>Example</th></tr>
  <tr>
    <td><code>Path</code></td>
    <td>Identifies a precise resource; always required</td>
    <td><code>session_id: int = Path(gt=0)</code></td>
  </tr>
  <tr>
    <td><code>Query</code></td>
    <td>Filters, sorts, paginates; usually optional</td>
    <td><code>limit: int = Query(default=20, ge=1, le=100)</code></td>
  </tr>
  <tr>
    <td><code>Body</code></td>
    <td>Structured/sensitive data to create or update; via a <code>BaseModel</code>, detected automatically</td>
    <td><code>payload: UserCreate</code></td>
  </tr>
  <tr>
    <td><code>Header</code></td>
    <td>Metadata about the request (auth, format); in practice read through <code>Depends</code> rather than by hand</td>
    <td><code>Authorization: Bearer &lt;jwt&gt;</code></td>
  </tr>
  <tr>
    <td><code>Cookie</code></td>
    <td>Token auto-sent by the browser, protected from JavaScript with <code>httpOnly</code></td>
    <td><code>refresh_token: str = Cookie()</code></td>
  </tr>
  <tr>
    <td><code>Depends</code></td>
    <td>A value computed by a server-side function, not read directly from the request</td>
    <td><code>current_user: User = Depends(get_current_user)</code></td>
  </tr>
</table>

<h3>Decision table</h3>

<table>
  <tr><th>Data</th><th>Origin</th><th>Why</th></tr>
  <tr><td>Identifies a precise resource</td><td>Path</td><td>Without it, the URL doesn't make sense</td></tr>
  <tr><td>Filters/sorts/paginates, optional</td><td>Query</td><td>Refines a result, doesn't designate anything specific</td></tr>
  <tr><td>Sensitive or structured, for creation/update</td><td>Body</td><td>Never in a URL (logs, browser history)</td></tr>
  <tr><td>Concerns the request itself</td><td>Header</td><td>Technical context, not business content</td></tr>
  <tr><td>Must survive across requests without the frontend</td><td>Cookie</td><td>Auto-sent by the browser</td></tr>
  <tr><td>Computed by already-written logic</td><td>Depends</td><td>Doesn't come directly from the client</td></tr>
</table>

<hr/>

<h2 id="ch4">4. Pydantic models: BaseModel and validation</h2>

<h3>Class and instance, a reminder</h3>

<p>
A class is a mold — the shape data must take. An instance is what you get by using that mold. A plain
Python class validates nothing; <code>BaseModel</code> adds a <b>validation and conversion</b> step at the
moment the instance is built.
</p>

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

<h3>Constraints with <code>Field</code></h3>

```python
class TotpVerify(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")
```

<p>
A TOTP code is stored as a <code>str</code>, never as an <code>int</code>: a number doesn't keep leading
zeros (<code>042917</code> would become <code>42917</code>). Any sequence of digits that is never used in
a calculation is text, not a number.
</p>

<h3>Why several classes for "one" user</h3>

<p>
A class doesn't represent a real-world concept — it represents the <b>shape data takes at a given moment
in its lifecycle</b>, for a given use. The same user has three different shapes depending on the moment:
</p>

<table>
  <tr><th>Class</th><th>Question it answers</th><th>Used where</th></tr>
  <tr><td><code>UserCreate</code></td><td>What should I ask the client to create an account?</td><td>Body, on input</td></tr>
  <tr><td><code>User</code></td><td>What should I keep in the database about this person?</td><td>Internal model, never exposed as-is</td></tr>
  <tr><td><code>UserRead</code></td><td>What am I allowed to reveal?</td><td><code>response_model</code>, on output</td></tr>
</table>

<p>
Using <code>User</code> (the full class) as the body would force the client to send an <code>id</code> it
doesn't have yet, or a <code>hashed_password</code> it has no business computing. Using it as the
<code>response_model</code> would expose the password hash. These aren't duplicates — three answers to
three different questions.
</p>

<hr/>

<h2 id="ch5">5. response_model: filtering and documenting the output</h2>

<p>
<code>response_model</code> is an argument of the <b>decorator</b>, not a function parameter — it applies
to any method (<code>GET</code>, <code>POST</code>...), not only <code>GET</code>.
</p>

```python
@app.post("/auth/signup", response_model=UserRead, status_code=201)
async def signup(payload: UserCreate):
    user = await user_repo.create(payload)
    return user  # full object, including hashed_password
```

<h3>What happens, step by step</h3>

<ol>
  <li>The function runs and returns a value — a full ORM object, a dictionary, anything.</li>
  <li>FastAPI intercepts this value before sending it to the client.</li>
  <li>It builds an instance of <code>response_model</code> from that value, keeping only the declared fields.</li>
  <li>Only this rebuilt instance is converted to JSON and sent.</li>
</ol>

<h3><code>response_model</code> vs return type annotation</h3>

<p>
There are two ways to declare an output schema: <code>response_model=X</code> in the decorator, or
<code>-> X</code> as the function's return type. If both are present, <code>response_model</code> takes
priority at runtime; the return annotation then only serves the editor and tools like mypy.
<code>response_model</code> is used separately as soon as the function returns an object different from the
output schema (an ORM <code>User</code> filtered into <code>UserRead</code>, for instance) — otherwise the
editor would flag a type mismatch.
</p>

<p>
If the returned data doesn't match the declared schema (missing field, wrong type), the function has
already finished executing: FastAPI returns a <b>500</b> error (a bug on the server side), as opposed to a
<b>422</b> error on invalid input data (a mistake on the client's side).
</p>

<h3>What the automatically generated Swagger docs are for</h3>

<p>
FastAPI generates an interactive page at <code>/docs</code>, built from the Pydantic classes and the actual
decorators — never out of date compared to the code, unlike a hand-written document. It lets a frontend
developer know the exact expected shape of an endpoint without reading the backend code, and test a request
directly from the browser.
</p>

<hr/>

<h2 id="ch6">6. Dependency injection: Depends</h2>

<h3>The principle</h3>

<p>
<code>Depends()</code> tells FastAPI: run this other function first, and give me its result as a parameter.
</p>

```python
def get_greeting() -> str:
    return "Hello"

@app.get("/hello")
async def hello(greeting: str = Depends(get_greeting)):
    return {"message": f"{greeting}, world"}
```

<h3>Applied to authentication</h3>

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
If <code>get_current_user</code> raises an exception, FastAPI builds the error response directly —
<code>get_me</code> is never called. This isn't an undefined variable inside the function: the function
simply never starts executing.
</p>

<h3>Sub-dependencies</h3>

<p>
A dependency can itself depend on something else. FastAPI resolves the chain from the deepest to the
shallowest: <code>oauth2_scheme</code> is called first, its result feeds <code>get_current_user</code>,
whose result finally feeds the route function.
</p>

<h3>Parameterized dependencies</h3>

<p>
To pass a parameter to a dependency, you use a function that <b>manufactures</b> a dependency on demand — a
Python closure keeps the value in memory.
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

<h2 id="ch7">7. Security of sensitive data</h2>

<h3>The role of TLS, distinct from that of Pydantic classes</h3>

<p>
A Pydantic class (<code>LoginRequest</code>) secures the <b>structure</b> of the data — it encrypts
nothing. What protects a password during its network trip is a completely separate layer: <b>TLS</b>
(the "S" in HTTPS), handled by the web server and the browser, before FastAPI ever sees anything.
Without HTTPS, anyone on the same network can read a request in plain text.
</p>

<h3>The journey of a password, from client to database</h3>

<ol>
  <li>The client sends <code>email</code> + <code>password</code> in the body.</li>
  <li>FastAPI parses the JSON into a <code>payload</code> object.</li>
  <li>The function reads <code>payload.password</code> (an ordinary Python string, at this stage).</li>
  <li><code>PasswordHasher</code> hashes the password (argon2/bcrypt).</li>
  <li>Only the hash is stored in the database — the raw password is never logged or returned.</li>
</ol>

<h3>Three rules to follow once the data has been read</h3>

<ul>
  <li>Never log the whole object that contains a sensitive field.</li>
  <li>Never include it in an output schema (<code>response_model</code>).</li>
  <li>Never store it in plain text — only the hashing result is kept.</li>
</ul>

<hr/>

<h2 id="annexA">Appendix A. Common pitfalls</h2>

<details open>
  <summary>Forgetting <code>default=</code> in <code>Query()</code>/<code>Path()</code></summary>

```python
limit: int = Query(gt=0, le=100)              # becomes required, 422 if missing
limit: int = Query(default=20, ge=1, le=100)  # correct, optional, default 20
```
</details>

<details>
  <summary><code>Depends(function())</code> instead of <code>Depends(function)</code></summary>

```python
current_user: User = get_current_user()          # called only once, when the file loads
current_user: User = Depends(get_current_user)    # called on every request
```
</details>

<details>
  <summary>A <code>BaseModel</code> without explicit <code>Depends</code> = body expected from the client</summary>

```python
async def get_me(user: UserRead):                          # wrong, FastAPI expects a body
async def get_me(user: User = Depends(get_current_user)):  # correct, computed server-side
```
</details>

<details>
  <summary><code>Query(ge=0)</code> when it should be strictly positive</summary>

```python
user_id: int = Query(ge=0)   # accepts 0, invalid for a database ID
user_id: int = Query(gt=0)   # strictly positive
```
</details>

<details>
  <summary>Confusing 401, 403 and 404</summary>

<table>
  <tr><th>Code</th><th>Meaning</th><th>Example</th></tr>
  <tr><td>401</td><td>I don't know who you are (missing/invalid token)</td><td>Missing <code>Authorization</code> header</td></tr>
  <tr><td>403</td><td>I know who you are, but you're not allowed to</td><td>Revoking another user's session</td></tr>
  <tr><td>404</td><td>This resource doesn't exist at all</td><td>Unknown <code>session_id</code> in the database</td></tr>
</table>
</details>

<details>
  <summary>Mutable default value in plain Python (a general pitfall, not specific to Pydantic)</summary>

```python
def add(item, items=[]):   # the same list is reused across calls
    items.append(item)
    return items
```

In Pydantic, a value factory is used instead of an already-built value:

```python
recovery_codes: List[str] = Field(default_factory=list)
```
</details>

<hr/>

<h2 id="annexB">Appendix B. Glossary</h2>

<table>
  <tr><th>Term</th><th>Definition</th></tr>
  <tr><td>Decorator</td><td>A function that takes another function as an argument and returns a function, applied via <code>@name</code></td></tr>
  <tr><td>Type hint</td><td>Annotation after the colon in a signature, indicating the expected type — ignored by Python alone, used by FastAPI/Pydantic</td></tr>
  <tr><td>ASGI</td><td>Standard for asynchronous communication between a server and a Python application</td></tr>
  <tr><td>WSGI</td><td>Older synchronous equivalent of ASGI, used by frameworks like classic Flask/Django</td></tr>
  <tr><td>Path operation</td><td>The combination of (HTTP method, path) associated with a function</td></tr>
  <tr><td>Body</td><td>The content of a request, located after the blank line that follows the headers</td></tr>
  <tr><td>Header</td><td>Metadata about the request or response itself, never the business content</td></tr>
  <tr><td>response_model</td><td>Decorator parameter that filters and documents the shape of the response</td></tr>
  <tr><td>Dependency Injection (DI)</td><td>Mechanism by which FastAPI calls a function before yours and injects its result as a parameter</td></tr>
  <tr><td>Sub-dependency</td><td>A dependency that itself depends on another dependency</td></tr>
  <tr><td>Closure</td><td>An inner function that keeps access to the variables of the outer function that created it</td></tr>
  <tr><td>TLS</td><td>Network transport encryption layer, the "S" in HTTPS — distinct from Pydantic validation</td></tr>
</table>

<hr/>

<h2 id="annexC">Appendix C. Synthesis exercises</h2>

<p>For each parameter, identify the type and the role of the marker (origin, constraint, or both):</p>

<ol>
  <li><code>email: str = Query(min_length=5)</code></li>
  <li><code>payload: UserCreate</code></li>
  <li><code>current_user: User = Depends(get_current_user)</code></li>
  <li><code>session_id: int = Path(gt=0)</code></li>
  <li><code>refresh_token: str = Cookie()</code></li>
</ol>

<p>For each scenario, pick the most appropriate HTTP status code (401, 403, 404, 422, or 500):</p>

<ol>
  <li>The client sends a 4-digit <code>code</code> instead of a 6-digit TOTP code.</li>
  <li>The client provides no <code>Authorization</code> header on a protected endpoint.</li>
  <li>An authenticated client tries to delete another user's session.</li>
  <li>The client requests a session whose identifier doesn't exist in the database.</li>
  <li>The server returns an object that doesn't match the declared <code>response_model</code>.</li>
</ol>

<p align="center"><a href="#ch0">Back to top</a></p>
