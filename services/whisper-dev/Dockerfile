FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

WORKDIR /app

ARG APP_UID=1000
ARG APP_GID=990

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/hf_cache
ENV HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
ENV WHISPER_ROOT_PATH=/whisper-dev
ENV WHISPER_OUTPUT_DIR=/app/outputs
ENV WHISPER_JOBS_DIR=/app/data/jobs
ENV WHISPER_CONTEXTS_PATH=/app/contexts.json
ENV WHISPER_RETENTION_MAX_JOBS=5

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     python3 python3-pip python3-venv ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && ln -sf /usr/bin/python3 /usr/local/bin/python \
  && ln -sf /usr/bin/pip3 /usr/local/bin/pip

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install -r requirements.txt

COPY contexts.json .
COPY app.py .
COPY templates ./templates

RUN mkdir -p /app/outputs /app/uploads /app/data/jobs /app/hf_cache \
  && groupadd -g "${APP_GID}" appgroup \
  && useradd -u "${APP_UID}" -g "${APP_GID}" -m -s /usr/sbin/nologin appuser \
  && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
