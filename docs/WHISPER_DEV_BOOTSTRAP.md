# WHISPER_DEV_BOOTSTRAP

This document records the first isolated development runtime for Whisper under `/srv/soma`.

## Status

Name:

    soma-whisper-dev-bootstrap-v1

Status:

    running

Date:

    2026-06-02

Server:

    grlvm

## Purpose

Create an isolated dev copy of the legacy Whisper service without modifying or replacing the working legacy service.

The dev service is intended for safe iteration before any migration of the production route.

## Source

Legacy service source path:

    /home/grigorynokhrin/myservices/whisper

Dev service path:

    /srv/soma/services/whisper-dev

Dev data path:

    /srv/soma/data/whisper-dev

## Created runtime layout

Service code:

    /srv/soma/services/whisper-dev/Dockerfile
    /srv/soma/services/whisper-dev/app.py
    /srv/soma/services/whisper-dev/requirements.txt
    /srv/soma/services/whisper-dev/contexts.json
    /srv/soma/services/whisper-dev/templates/

Data directories:

    /srv/soma/data/whisper-dev/jobs
    /srv/soma/data/whisper-dev/outputs
    /srv/soma/data/whisper-dev/hf_cache

Compose file:

    /srv/soma/compose/whisper-dev.compose.yml

## Ownership policy

The dev service and data directories were created with:

    grigorynokhrin:docker

Expected directory mode:

    775

Expected regular file mode:

    664

## Legacy facts

The legacy Whisper service uses:

    ROOT_PATH = /myservices/whisper
    OUTPUT_DIR = /app/outputs
    JOBS_DIR = /app/data/jobs

Legacy Docker base image:

    nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

Legacy application command:

    python -m uvicorn app:app --host 0.0.0.0 --port 8000

Legacy Python dependencies include:

    fastapi==0.115.12
    uvicorn[standard]==0.34.0
    faster-whisper==1.2.1
    ctranslate2==4.6.0

## Dev changes in `app.py`

The dev app was copied from the legacy app and patched minimally.

Changed hardcoded paths to environment-driven configuration:

    WHISPER_ROOT_PATH
    WHISPER_OUTPUT_DIR
    WHISPER_JOBS_DIR
    WHISPER_CONTEXTS_PATH
    WHISPER_MAX_CONTEXT_CHARS
    WHISPER_RETENTION_MAX_JOBS

Default dev route:

    /whisper-dev

Default retention value:

    WHISPER_RETENTION_MAX_JOBS=5

Added function:

    cleanup_old_jobs()

The function keeps only the newest N terminal jobs.

Terminal statuses considered removable:

    done
    error
    deleted

Retention is called after:

    job done
    job error

The legacy app was not modified.

## Dev Dockerfile changes

The dev Dockerfile is based on the legacy Dockerfile but adds runtime ownership controls.

Build args:

    APP_UID=1000
    APP_GID=990

Runtime user:

    appuser

Runtime group:

    appgroup

Container runtime identity verified:

    uid=1000(appuser) gid=990(appgroup)

Environment variables added:

    HF_HOME=/app/hf_cache
    HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
    WHISPER_ROOT_PATH=/whisper-dev
    WHISPER_OUTPUT_DIR=/app/outputs
    WHISPER_JOBS_DIR=/app/data/jobs
    WHISPER_CONTEXTS_PATH=/app/contexts.json
    WHISPER_RETENTION_MAX_JOBS=5

Purpose:

    avoid root-owned files in bind-mounted runtime data

## Compose configuration

Compose file:

    /srv/soma/compose/whisper-dev.compose.yml

Container name:

    soma-whisper-dev

Image name:

    soma-whisper-dev:local

Published port:

    127.0.0.1:18080 -> 8000

GPU:

    gpus: all

Restart policy:

    unless-stopped

Mounted data:

    /srv/soma/data/whisper-dev/jobs:/app/data/jobs
    /srv/soma/data/whisper-dev/outputs:/app/outputs
    /srv/soma/data/whisper-dev/hf_cache:/app/hf_cache

## Build result

The dev image was built successfully.

Image:

    soma-whisper-dev:local

Observed build result:

    Image soma-whisper-dev:local Built

Observed disk usage:

    6.77GB

Observed content size:

    2.46GB

Disk remained healthy after build:

    / usage approximately 20%

## Runtime status

The dev container was started successfully.

Container:

    soma-whisper-dev

Observed status:

    Up

Observed port:

    127.0.0.1:18080->8000/tcp

Uvicorn log:

    Application startup complete.
    Uvicorn running on http://0.0.0.0:8000

## Health checks

Direct dev health endpoint:

    http://127.0.0.1:18080/whisper-dev/healthz

Observed response:

    ok

Direct dev UI endpoint:

    http://127.0.0.1:18080/whisper-dev/

Observed result:

    HTML page returned

Note:

    HEAD returned 405 Method Not Allowed.
    This is acceptable because the route supports GET.

## Ownership test

A write test was performed from inside the dev container.

Container-side files:

    /app/data/jobs/ownership-test.txt
    /app/outputs/ownership-test.txt

Container-side ownership:

    appuser:appgroup

Host-side files:

    /srv/soma/data/whisper-dev/jobs/ownership-test.txt
    /srv/soma/data/whisper-dev/outputs/ownership-test.txt

Host-side ownership:

    grigorynokhrin:docker

Result:

    ownership problem from the legacy service is solved for new dev runtime data

The temporary ownership test files were removed after verification.

## Legacy safety check

After starting `soma-whisper-dev`, the legacy runtime healthcheck passed.

Command:

    cd /srv/soma
    make health

Verified legacy containers remained running:

    myservices-caddy
    myservices-home
    myservices-whisper

Verified legacy Whisper endpoint:

    http://127.0.0.1/myservices/whisper/healthz

Observed result:

    ok

Healthcheck final result:

    [OK] healthcheck completed without hard failures

## Safety boundary

This bootstrap did not intentionally:

- stop legacy containers
- restart legacy containers
- change legacy Docker Compose
- change Caddy routes
- expose `soma-whisper-dev` publicly
- replace `myservices-whisper`
- migrate production traffic

The dev service is currently reachable only on the server loopback interface.

## Current access

From the server:

    curl http://127.0.0.1:18080/whisper-dev/healthz

Browser access through Caddy is not configured yet.

## Next steps

Recommended next step:

    test a small audio transcription through soma-whisper-dev

Validation goals:

- job is created under `/srv/soma/data/whisper-dev/jobs`
- generated files are owned by `grigorynokhrin:docker` on the host
- model cache is populated under `/srv/soma/data/whisper-dev/hf_cache`
- retention keeps at most 5 jobs
- legacy Whisper remains healthy

Do not route public `/whisper` traffic to `soma-whisper-dev` until the dev service is tested with real audio.
