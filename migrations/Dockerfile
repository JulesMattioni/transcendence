FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

COPY migrations/pyproject.toml migrations/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY migrations/ .

COPY shared/ ./shared/
COPY core/app/ ./core_models/
COPY auth/app/ ./auth_models/
COPY rag/app/ ./rag_models/
COPY org/app/ ./organisations_models/

CMD ["alembic", "upgrade", "head"]
