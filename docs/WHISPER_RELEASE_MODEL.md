# WHISPER_RELEASE_MODEL

This document describes the Whisper dev-to-production release model after release `whisper-prod-2026.06.03`.

## Summary

Whisper now uses one source codebase and Dockerfile with different runtime configuration for dev and production.

Source codebase:

    /home/grigorynokhrin/soma-arch/services/whisper-dev

Mac reference repo:

    /Users/grigorynokhrin/projects/soma-arch

Production Compose remains in the legacy runtime:

    /home/grigorynokhrin/myservices/compose.yaml

Production route remains:

    /myservices/whisper

Caddy was not changed for this release.

## Source And Runtime Split

The Git-tracked source lives in `soma-arch`.

Runtime state lives outside Git:

    dev data:  /srv/soma/data/whisper-dev
    prod data: /home/grigorynokhrin/myservices/whisper

Production still uses the legacy Compose owner and route contract:

    compose file: /home/grigorynokhrin/myservices/compose.yaml
    service:      whisper
    container:    myservices-whisper
    network:      myservices_default

This split is intentional during the transition. Source is promoted from the repo; production process ownership remains with `myservices`.

## Environment-Driven Route Model

The app keeps FastAPI `root_path` support:

    ROOT_PATH = os.getenv("WHISPER_ROOT_PATH", "/whisper-dev")
    app = FastAPI(root_path=ROOT_PATH)

The UI uses the configured root path for links, form actions, polling, and redirects.

Current route values:

    dev:  WHISPER_ROOT_PATH=/whisper-dev
    prod: WHISPER_ROOT_PATH=/myservices/whisper

Internal URLs should be path-based, not absolute:

    good: /myservices/whisper/jobs/<job-id>
    bad:  http://127.0.0.1:<port>/myservices/whisper/jobs/<job-id>

Templates must not hardcode:

    /myservices/whisper

The same source should render correctly for both:

    /whisper-dev
    /myservices/whisper

## Production Environment

Production Whisper environment:

    WHISPER_ROOT_PATH=/myservices/whisper
    WHISPER_OUTPUT_DIR=/app/outputs
    WHISPER_JOBS_DIR=/app/data/jobs
    WHISPER_CONTEXTS_PATH=/app/contexts.json
    WHISPER_RETENTION_MAX_JOBS=20
    HF_HOME=/app/hf_cache
    HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub

Production volumes:

    /home/grigorynokhrin/myservices/whisper/outputs:/app/outputs
    /home/grigorynokhrin/myservices/whisper/data:/app/data
    /home/grigorynokhrin/myservices/whisper/hf_cache:/app/hf_cache

Runtime user:

    uid=1000
    gid=990

Expected host ownership:

    grigorynokhrin:docker

## Promotion Checklist

Before promotion:

- confirm the repo source commit intended for release
- confirm dev health is OK
- confirm production health is OK before touching production
- confirm Caddy route contract is unchanged
- confirm production writable directories are owned by `grigorynokhrin:docker`
- confirm `uid=1000 gid=990` can write to production output/data/cache paths
- create a rollback image tag
- create runtime backups for config, service source reference, and permissions

Build/promote using the production Compose owner:

    cd /home/grigorynokhrin/myservices
    docker compose build whisper
    docker compose up -d whisper

Do not change Caddy unless the route contract changes.

## Smoke-Test Checklist

Health checks:

    curl -fsS http://127.0.0.1/myservices/whisper/healthz
    cd /srv/soma
    make health

Index checks:

    form action="/myservices/whisper/submit"
    chunk_min value="5"
    overlap output "0 сек"

Submit a small controlled audio sample through the production route:

    POST /myservices/whisper/submit

Expected submit behavior:

    HTTP 303
    Location: /myservices/whisper/jobs/<job-id>

Expected final job behavior:

    status: done
    progress: 1/1 for a one-chunk smoke sample
    TXT artifact exists
    SRT artifact exists
    artifact links use /myservices/whisper/jobs/.../artifacts/...

Also confirm the dev route remains healthy:

    curl -fsS http://127.0.0.1/whisper-dev/healthz

## Rollback Checklist

Rollback is an explicit recovery action only.

Known rollback image for release `whisper-prod-2026.06.03`:

    myservices-whisper:rollback-20260603-093727

Rollback reference:

    cd /home/grigorynokhrin/myservices
    docker compose stop whisper
    docker tag myservices-whisper:rollback-20260603-093727 myservices-whisper
    docker compose up -d whisper
    curl -fsS http://127.0.0.1/myservices/whisper/healthz

If the problem is file ownership, restore permissions from:

    /home/grigorynokhrin/myservices/backups/whisper-permissions-20260603-093428

If the problem is release content, inspect:

    /home/grigorynokhrin/myservices/backups/whisper-promote-20260603-093625
    /home/grigorynokhrin/myservices/backups/whisper-release-20260603-093727

After rollback, re-run:

    cd /srv/soma
    make health

## Warnings

Do not use this casually:

    docker compose --remove-orphans

It can remove containers that are still part of the current mixed legacy/dev operating model.

Do not modify Caddy unless the route contract changes. Current production contract:

    handle /myservices/whisper* {
        reverse_proxy whisper:8000
    }

Do not parallelize heavy production, dev, and candidate Whisper tests on the RTX 3060 12GB. The GPU has limited VRAM, and concurrent model loads can create misleading failures.

Before replacing production, always verify write permissions for:

    uid=1000
    gid=990

Target writable paths:

    /home/grigorynokhrin/myservices/whisper/outputs
    /home/grigorynokhrin/myservices/whisper/data
    /home/grigorynokhrin/myservices/whisper/hf_cache

Do not store generated audio, transcripts, model caches, or job data in Git.

Do not claim a production promotion is complete until both health and a real submit/result smoke-test have passed.
