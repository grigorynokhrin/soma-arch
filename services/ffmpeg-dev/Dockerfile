FROM python:3.12-slim-bookworm

WORKDIR /app

ARG APP_UID=1000
ARG APP_GID=990

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV FFMPEG_ROOT_PATH=/ffmpeg-dev
ENV FFMPEG_DATA_DIR=/data

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg ca-certificates libimage-exiftool-perl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install -r requirements.txt

COPY app.py .
COPY command_builder.py .
COPY profiles.json .
COPY templates ./templates

RUN mkdir -p /data \
  && groupadd -g "${APP_GID}" appgroup \
  && useradd -u "${APP_UID}" -g "${APP_GID}" -m -s /usr/sbin/nologin appuser \
  && chown -R appuser:appgroup /app /data

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
