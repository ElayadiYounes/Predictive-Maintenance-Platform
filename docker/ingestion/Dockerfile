FROM python:3.11-slim-bookworm

# 1. System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Work directory
WORKDIR /app

COPY docker/ingestion/requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip && \
    pip install \
    --disable-pip-version-check \
    --no-cache-dir \
    -r /tmp/requirements.txt

# 4. Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=dev \
    HOME=/home/ingestion

# 5. Security (User creation & Ownership transfer)
# Création de l'utilisateur système non-root
RUN useradd --create-home --uid 1002 ingestion && \
    chown -R ingestion:ingestion /app

# Changement d'utilisateur
USER ingestion

# 6. Default command (overridden by compose)
CMD ["python"]
