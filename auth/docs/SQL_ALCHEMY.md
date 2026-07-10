<p align="center">
  <img src="https://img.shields.io/badge/SQLALCHEMY_2.0-COURSE-111111?style=for-the-badge&labelColor=000000" alt="sqlalchemy course" />
</p>

<h1 align="center">SQLAlchemy 2.0 (async) — Complete Course</h1>

<p align="center">
  From zero: what an ORM is, how to define models, connect to a database, and run queries — using the modern async 2.0 API.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/asyncpg-2E8B57?style=for-the-badge" alt="asyncpg" />
  <img src="https://img.shields.io/badge/asyncio-FFD43B?style=for-the-badge&logo=python&logoColor=black" alt="asyncio" />
</p>

<hr/>

<h2>Table of Contents</h2>

<ul>
  <li><a href="#ch0">0. What problem SQLAlchemy solves</a></li>
  <li><a href="#ch1">1. The four core objects: Engine, Session, Base, Model</a></li>
  <li><a href="#ch2">2. Connecting: the async engine</a></li>
  <li><a href="#ch3">3. Defining a model with Mapped and mapped_column</a></li>
  <li><a href="#ch4">4. Column options: keys, uniqueness, nullability, defaults</a></li>
  <li><a href="#ch5">5. The Session: your workspace</a></li>
  <li><a href="#ch6">6. Creating rows (INSERT)</a></li>
  <li><a href="#ch7">7. Reading rows (SELECT)</a></li>
  <li><a href="#ch8">8. Updating and deleting rows</a></li>
  <li><a href="#ch9">9. commit, flush, refresh, rollback</a></li>
  <li><a href="#ch10">10. Relationships between tables</a></li>
  <li><a href="#annexA">Appendix A. Common pitfalls</a></li>
  <li><a href="#annexB">Appendix B. Glossary</a></li>
  <li><a href="#annexC">Appendix C. Synthesis exercises</a></li>
</ul>

<hr/>

<h2 id="ch0">0. What problem SQLAlchemy solves</h2>

<p>
A database stores data <b>durably on disk</b>, organized into <b>tables</b> (like spreadsheets): each table has
<b>columns</b> (attributes) and <b>rows</b> (records). Databases speak <b>SQL</b>, a language separate from Python:
</p>

```sql
SELECT * FROM users WHERE email = 'bob@mail.com';
```

<p>
Your application speaks Python and manipulates <b>objects</b>. Without a bridge, you would constantly translate
by hand between Python objects and SQL text. An <b>ORM</b> (Object-Relational Mapping) does that translation
automatically, in both directions: you write Python, it generates the SQL.
</p>

<table>
  <tr><th>Approach</th><th>What you write</th></tr>
  <tr><td>Without ORM</td><td><code>db.execute("SELECT * FROM users WHERE email = 'bob@mail.com'")</code> + rebuild objects by hand</td></tr>
  <tr><td>With SQLAlchemy</td><td><code>await session.scalar(select(User).where(User.email == "bob@mail.com"))</code> → returns a ready <code>User</code> object</td></tr>
</table>

<p>
<b>SQLAlchemy is that ORM.</b> This course uses the modern <b>2.0 async</b> API, the one designed to work
naturally with an async framework like FastAPI.
</p>

<hr/>

<h2 id="ch1">1. The four core objects: Engine, Session, Base, Model</h2>

<p>Everything in SQLAlchemy revolves around four kinds of object. Understand these four names and the rest follows:</p>

<table>
  <tr><th>Object</th><th>Role</th><th>Analogy</th></tr>
  <tr><td><b>Engine</b></td><td>The connection to the database; created once, at startup</td><td>The phone line to the database</td></tr>
  <tr><td><b>Model</b></td><td>A Python class that describes one table (its columns and types)</td><td>The blueprint of a table</td></tr>
  <tr><td><b>Base</b></td><td>The common parent class all models inherit from; collects every model's metadata</td><td>The registry of all blueprints</td></tr>
  <tr><td><b>Session</b></td><td>A short-lived workspace where you add, read, and modify objects before saving</td><td>A single phone call on the line</td></tr>
</table>

<p>The rest of the course builds these one at a time, in this order: Engine → Base → Model → Session.</p>

<hr/>

<h2 id="ch2">2. Connecting: the async engine</h2>

<p>
The <b>engine</b> holds the information needed to reach the database. It is created <b>once</b>, when the
application starts, and reused for every query afterwards.
</p>

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/mydatabase",
    echo=True,
)
```

<h3>Reading the connection string</h3>

<p>The long string is a <b>database URL</b>. Each part means something:</p>

<table>
  <tr><th>Part</th><th>Meaning</th></tr>
  <tr><td><code>postgresql</code></td><td>The database type</td></tr>
  <tr><td><code>+asyncpg</code></td><td>The async driver used to talk to PostgreSQL (needed for the async API)</td></tr>
  <tr><td><code>user:password</code></td><td>Database credentials</td></tr>
  <tr><td><code>localhost</code></td><td>Where the database runs</td></tr>
  <tr><td><code>mydatabase</code></td><td>The database name</td></tr>
</table>

<p>
<code>echo=True</code> makes SQLAlchemy print every SQL statement it generates — very useful while learning, so you
can see the actual SQL behind your Python. Turn it off in production.
</p>

<p>
The <code>+asyncpg</code> part is what makes this <b>async</b>. Without it (plain <code>postgresql://</code>), the
engine would be synchronous and would block on every query — incompatible with an async FastAPI service.
</p>

<hr/>

<h2 id="ch3">3. Defining a model with Mapped and mapped_column</h2>

<p>
A <b>model</b> is a Python class that describes a table. First you create the <b>Base</b> class every model
inherits from:
</p>

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

<p>Then a model:</p>

```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
```

<h3>Line by line</h3>

<table>
  <tr><th>Element</th><th>Meaning</th></tr>
  <tr><td><code>class User(Base)</code></td><td>This model inherits from <code>Base</code>, so SQLAlchemy knows about it</td></tr>
  <tr><td><code>__tablename__ = "users"</code></td><td>The name of the table in the database</td></tr>
  <tr><td><code>id: Mapped[int]</code></td><td>The <b>Python type</b> of the column, wrapped in <code>Mapped[...]</code></td></tr>
  <tr><td><code>= mapped_column(...)</code></td><td>The <b>column configuration</b> (constraints, defaults). Optional if there is nothing special to say</td></tr>
</table>

<h3>Why the double declaration (<code>Mapped[int]</code> AND <code>mapped_column</code>)</h3>

<p>
This mirrors exactly what you saw in FastAPI (<code>limit: int = Query(...)</code>): two independent pieces of
information on one line. <code>Mapped[int]</code> declares the <b>type</b>; <code>mapped_column(...)</code>
declares the <b>column options</b>. When a column has no special options, you can omit <code>mapped_column</code>
entirely — <code>hashed_password: Mapped[str]</code> is a complete, valid column.
</p>

<p>
<b>Note:</b> this is the SQLAlchemy model, describing the <b>table</b> — it is a different thing from a Pydantic
<code>BaseModel</code>, which describes the shape of <b>HTTP data</b>. They look similar but serve different layers.
</p>

<hr/>

<h2 id="ch4">4. Column options: keys, uniqueness, nullability, defaults</h2>

<table>
  <tr><th>Option</th><th>Effect</th></tr>
  <tr><td><code>primary_key=True</code></td><td>This column uniquely identifies each row (usually <code>id</code>). One per table.</td></tr>
  <tr><td><code>unique=True</code></td><td>No two rows may share the same value (e.g. two users can't have the same email)</td></tr>
  <tr><td><code>default=...</code></td><td>Value used if none is provided when creating the row</td></tr>
  <tr><td><code>index=True</code></td><td>Speeds up lookups on this column (at a small write cost)</td></tr>
  <tr><td><code>ForeignKey("other.id")</code></td><td>This column points to a row in another table (see chapter 10)</td></tr>
</table>

<h3>Nullability comes from the type</h3>

<p>
Whether a column can be empty (<code>NULL</code>) is decided by the Python type itself, via <code>Optional</code>
(or <code>| None</code>):
</p>

```python
first_name: Mapped[str]              # required — cannot be NULL
middle_name: Mapped[str | None]      # optional — may be NULL
```

<p>
This is elegant: the same type hint that tells your editor "this might be None" also tells the database "this
column is nullable". One declaration, two effects.
</p>

<hr/>

<h2 id="ch5">5. The Session: your workspace</h2>

<p>
The <b>session</b> is a temporary workspace for one unit of work. You create objects, add them to the session,
read from it, and at the end you <b>commit</b> (save to the database) or <b>rollback</b> (discard).
</p>

<p>You don't create sessions directly; you set up a <b>factory</b> once, then open sessions from it:</p>

```python
from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

<p>
<code>expire_on_commit=False</code> matters for async: without it, SQLAlchemy would "expire" your objects after a
commit, and reading an attribute afterwards would try to reload it from the database — which fails silently under
async. Setting it to <code>False</code> lets you keep using the object after committing.
</p>

<p>Opening a session, the recommended pattern:</p>

```python
async with AsyncSessionLocal() as session:
    ...  # do your work here
    # the session is automatically closed when the block exits
```

<p>
<code>async with</code> guarantees the session is properly closed even if an error occurs — you never leak an open
connection.
</p>

<hr/>

<h2 id="ch6">6. Creating rows (INSERT)</h2>

<p>To add a new row, you create a Python object, add it to the session, and commit:</p>

```python
async with AsyncSessionLocal() as session:
    new_user = User(email="bob@mail.com", hashed_password="$2b$12$...")
    session.add(new_user)
    await session.commit()
```

<h3>Step by step</h3>

<ol>
  <li><code>User(...)</code> — create a plain Python object (nothing has touched the database yet)</li>
  <li><code>session.add(new_user)</code> — tell the session "I want to save this" (still nothing sent)</li>
  <li><code>await session.commit()</code> — <b>now</b> the SQL <code>INSERT</code> is sent and the row is written</li>
</ol>

<p>
Notice you didn't set <code>id</code> — it's the primary key, generated by the database. After the commit, you can
read it back: <code>new_user.id</code> will hold the value the database assigned.
</p>

<hr/>

<h2 id="ch7">7. Reading rows (SELECT)</h2>

<p>Reading is done in two steps: build a <code>select(...)</code> statement, then execute it.</p>

<h3>Get one row by a condition</h3>

```python
from sqlalchemy import select

async with AsyncSessionLocal() as session:
    stmt = select(User).where(User.email == "bob@mail.com")
    user = await session.scalar(stmt)   # returns one User, or None
```

<h3>Get one row by primary key (shortcut)</h3>

```python
user = await session.get(User, 1)   # the user whose id is 1, or None
```

<h3>Get several rows</h3>

```python
stmt = select(User).where(User.is_active == True)
result = await session.scalars(stmt)
users = result.all()   # a list of User objects
```

<h3>The vocabulary of results</h3>

<table>
  <tr><th>Method</th><th>Returns</th></tr>
  <tr><td><code>session.scalar(stmt)</code></td><td>The first single object, or <code>None</code></td></tr>
  <tr><td><code>session.scalars(stmt)</code> then <code>.all()</code></td><td>A list of objects</td></tr>
  <tr><td><code>session.scalars(stmt)</code> then <code>.first()</code></td><td>The first object, or <code>None</code></td></tr>
  <tr><td><code>session.scalars(stmt)</code> then <code>.one()</code></td><td>Exactly one object, or an error if zero or many</td></tr>
  <tr><td><code>session.get(Model, pk)</code></td><td>One object by primary key, or <code>None</code></td></tr>
</table>

<h3>Filtering, ordering, pagination</h3>

```python
stmt = (
    select(User)
    .where(User.is_active == True)
    .order_by(User.created_at.desc())
    .limit(20)
    .offset(40)
)
```

<p>
Note <code>.where(User.email == "bob@mail.com")</code> uses a double <code>==</code> — you are not comparing
values in Python, you are describing a SQL condition. SQLAlchemy turns <code>User.email == "..."</code> into the SQL
<code>WHERE email = '...'</code>.
</p>

<hr/>

<h2 id="ch8">8. Updating and deleting rows</h2>

<h3>Update: load, modify, commit</h3>

```python
async with AsyncSessionLocal() as session:
    user = await session.get(User, 1)
    user.is_active = False      # change the Python object
    await session.commit()       # the UPDATE is sent
```

<p>
You don't write an <code>UPDATE</code> statement — you change the attribute on the loaded object, and the session
detects the change and generates the SQL on commit. This is called <b>change tracking</b>.
</p>

<h3>Delete</h3>

```python
async with AsyncSessionLocal() as session:
    user = await session.get(User, 1)
    await session.delete(user)
    await session.commit()
```

<hr/>

<h2 id="ch9">9. commit, flush, refresh, rollback</h2>

<p>Four session operations that are easy to confuse:</p>

<table>
  <tr><th>Operation</th><th>What it does</th></tr>
  <tr><td><code>await session.commit()</code></td><td>Permanently saves all pending changes to the database, and ends the transaction</td></tr>
  <tr><td><code>await session.flush()</code></td><td>Sends the SQL to the database <b>but doesn't finalize</b> — useful to get a generated <code>id</code> before committing; can still be rolled back</td></tr>
  <tr><td><code>await session.refresh(obj)</code></td><td>Reloads an object's attributes from the database (e.g. to get database-generated values)</td></tr>
  <tr><td><code>await session.rollback()</code></td><td>Discards all pending changes since the last commit — undo</td></tr>
</table>

<p>
<b>Mental model:</b> changes accumulate in the session like a draft. <code>commit</code> publishes the draft;
<code>rollback</code> tears it up. <code>flush</code> sends it to the database to get feedback (like an id) without
committing to it permanently yet.
</p>

<hr/>

<h2 id="ch10">10. Relationships between tables</h2>

<p>
Real data is connected: a user has many sessions, an order belongs to a customer. Two pieces express this: a
<b>ForeignKey</b> column (the actual link stored in the database) and a <b>relationship</b> (the convenient Python
accessor).
</p>

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    posts: Mapped[List["Post"]] = relationship()

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

<table>
  <tr><th>Element</th><th>Role</th></tr>
  <tr><td><code>user_id = mapped_column(ForeignKey("users.id"))</code></td><td>The real column in the <code>posts</code> table; stores which user owns the post</td></tr>
  <tr><td><code>posts: Mapped[List["Post"]] = relationship()</code></td><td>A Python convenience: lets you write <code>user.posts</code> to get the list of a user's posts, without writing SQL</td></tr>
</table>

<p>
<b>Async caveat:</b> under async, accessing a relationship like <code>user.posts</code> may need an extra database
call, which async forbids implicitly. You load them explicitly with <code>selectinload</code>:
</p>

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.posts))
result = await session.scalars(stmt)
users = result.all()   # each user.posts is now loaded and safe to access
```

<hr/>

<h2 id="annexA">Appendix A. Common pitfalls</h2>

<details open>
  <summary>Forgetting <code>+asyncpg</code> in the connection string</summary>

```python
create_async_engine("postgresql://...")           # wrong for async — blocking driver
create_async_engine("postgresql+asyncpg://...")   # correct async driver
```
</details>

<details>
  <summary>Forgetting <code>expire_on_commit=False</code> with async</summary>

<p>Without it, reading an attribute after <code>commit()</code> tries to reload from the database and fails under async. Always set it on the async session factory.</p>
</details>

<details>
  <summary>Expecting the database to be touched before <code>commit()</code></summary>

<p><code>session.add(obj)</code> only stages the object. Nothing is written until <code>await session.commit()</code> (or <code>flush()</code>). A missing commit means the row silently never appears.</p>
</details>

<details>
  <summary>Accessing a relationship under async without eager loading</summary>

```python
user = await session.scalar(select(User).where(User.id == 1))
print(user.posts)   # may raise under async — posts weren't loaded
```

<p>Use <code>.options(selectinload(User.posts))</code> in the query to load them ahead of time.</p>
</details>

<details>
  <summary>Confusing the SQLAlchemy model with the Pydantic schema</summary>

<p>The SQLAlchemy <code>User(Base)</code> describes the database table. The Pydantic <code>UserRead(BaseModel)</code> describes the HTTP response shape. They are separate classes for separate layers, even if their fields overlap.</p>
</details>

<hr/>

<h2 id="annexB">Appendix B. Glossary</h2>

<table>
  <tr><th>Term</th><th>Definition</th></tr>
  <tr><td>ORM</td><td>Object-Relational Mapping: translates automatically between Python objects and database tables</td></tr>
  <tr><td>Engine</td><td>The reusable connection to the database, created once at startup</td></tr>
  <tr><td>Model</td><td>A Python class describing one table (its columns and types)</td></tr>
  <tr><td>Base</td><td>The parent class all models inherit from; collects their metadata</td></tr>
  <tr><td>Session</td><td>A short-lived workspace for one unit of work, ended by commit or rollback</td></tr>
  <tr><td>Mapped[T]</td><td>Declares the Python type of a column in a 2.0-style model</td></tr>
  <tr><td>mapped_column()</td><td>Declares a column's options (primary key, uniqueness, default...)</td></tr>
  <tr><td>Primary key</td><td>The column that uniquely identifies each row (usually <code>id</code>)</td></tr>
  <tr><td>Foreign key</td><td>A column that points to a row in another table</td></tr>
  <tr><td>relationship()</td><td>A Python accessor to navigate a link between tables without writing SQL</td></tr>
  <tr><td>select()</td><td>Builds a read (SELECT) statement in 2.0 style</td></tr>
  <tr><td>commit</td><td>Permanently saves pending changes and ends the transaction</td></tr>
  <tr><td>rollback</td><td>Discards pending changes since the last commit</td></tr>
  <tr><td>flush</td><td>Sends SQL to the database without finalizing; can still be rolled back</td></tr>
</table>

<hr/>

<h2 id="annexC">Appendix C. Synthesis exercises</h2>

<p>Write a model, then answer the questions.</p>

<ol>
  <li>Define a model <code>Product(Base)</code> for a table <code>products</code> with: an integer primary key <code>id</code>; a required <code>name</code> string; an optional <code>description</code> string; a <code>price</code> float; a boolean <code>in_stock</code> defaulting to <code>True</code>.</li>
  <li>Write a statement that reads all products where <code>in_stock</code> is <code>True</code>, ordered by price ascending, limited to 10.</li>
  <li>Write the code to create one new product and save it to the database.</li>
  <li>Which method would you use to fetch a product by its <code>id</code> in a single call: <code>session.scalar</code>, <code>session.get</code>, or <code>session.scalars</code>?</li>
  <li>Why must a query that later accesses a relationship use <code>selectinload</code> under async?</li>
</ol>

<p align="center"><a href="#ch0">Back to top</a></p>