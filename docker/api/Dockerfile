FROM python:3.11-slim-bookworm

#1-dependencies systeme
RUN apt-get update && apt-get install -y --no-install-recommends \
   curl \
   ca-certificates \
   && rm -rf /var/lib/apt/lists/*

#1-repertoire de travail
WORKDIR /app

#2-copie le fichier requirements.txt dans l'image
COPY docker/api/requirements.txt /tmp/requirements.txt

#3-installer requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install \
    --disable-pip-version-check \
    --no-cache-dir \
    -r /tmp/requirements.txt

#4-creation utilisateur
RUN useradd --create-home --uid 1003 apiuser


COPY --chown=apiuser:apiuser api/ /app/api/

RUN chown -R apiuser:apiuser /app

ENV PYTHONUNBUFFERED=1 \
   APP_ENV=dev \
   PYTHONPATH=/app \
   HOME=/home/apiuser

USER apiuser

EXPOSE 8000


HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=30s \
    --retries=3 \
CMD curl --fail http://localhost:8000/health || exit 1



CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]