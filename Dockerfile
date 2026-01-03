FROM python:3.13-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/0.9.15/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked


FROM python:3.13-slim AS final

WORKDIR /app

COPY --from=builder /app/.venv .venv
COPY src/ src/

RUN mkdir -p src/resources && mkdir -p src/workspace/terraform

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "src.documentation_processing.main"]
