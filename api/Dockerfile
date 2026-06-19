# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app:/app/ml/src \
    APP_HOME=/app

WORKDIR ${APP_HOME}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appgroup \
    && useradd --system --create-home --gid appgroup --home-dir /home/appuser appuser

COPY api/requirements.txt /app/api/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r /app/api/requirements.txt

COPY api /app/api
COPY ml/src /app/ml/src
COPY ml/models /app/ml/models
COPY ml/config /app/ml/config

RUN chmod +x /app/api/scripts/entrypoint.sh \
    && mkdir -p /app/ml/data /app/ml/data/processed \
    && ln -s /app/ml/models /app/models \
    && ln -s /app/ml/config /app/config \
    && ln -s /app/ml/data /app/data \
    && chown -R appuser:appgroup /app /home/appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8000/ || exit 1

<<<<<<< HEAD
ENTRYPOINT ["/app/api/scripts/entrypoint.sh"]

CMD ["gunicorn", "api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
=======
CMD ["gunicorn", "api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
>>>>>>> c5241ef (deploy)
