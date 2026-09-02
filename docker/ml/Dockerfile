FROM python:3.11-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY docker/ml/requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip && \
    pip install \
    --disable-pip-version-check \
    --no-cache-dir \
    -r /tmp/requirements.txt

COPY jobs /app/jobs

RUN useradd --create-home --uid 1004 mluser && \
    chown -R mluser:mluser /app

ENV PYTHONUNBUFFERED=1 \
    APP_ENV=dev \
    PYTHONPATH=/app \
    HOME=/home/mluser

USER mluser

CMD ["python"]