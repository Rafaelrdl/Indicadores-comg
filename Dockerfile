FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 POETRY_VIRTUALENVS_CREATE=false
RUN apt-get update && apt-get install -y build-essential curl git && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip poetry
COPY pyproject.toml poetry.lock* ./
RUN if [ -f poetry.lock ]; then \
        poetry install --only main --no-root --no-interaction --no-ansi; \
    else \
        poetry export --without-hashes -f requirements.txt --output requirements.txt && \
        pip install --no-cache-dir -r requirements.txt; \
    fi
COPY . .
RUN useradd -m -u 1000 appuser

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app
USER appuser
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
