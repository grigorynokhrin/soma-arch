# CODEX_HANDOFF

This document gives Codex enough context to continue work after Phase 1.

## Current phase

Phase 1 is complete.

Final Phase 1 status document:

    docs/PROJECT_PHASE_1_STATUS.md

Latest Phase 1 closing commit:

    b5fb4e0 document project phase 1 status

## What Phase 1 achieved

Phase 1 created a safe baseline for future development.

Completed:

- documented architecture
- `/srv/soma` runtime root
- separated legacy/prod and dev contours
- working `soma-whisper-dev`
- Git-tracked dev Whisper source
- Git-tracked dev Whisper compose
- non-root dev Whisper runtime
- smoke-test
- retention-test
- optional dev healthcheck
- Caddy route for `/whisper-dev`
- Caddy reference files
- final status document

## Current production-like legacy contour

Legacy runtime path:

    /home/grigorynokhrin/myservices

Legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Legacy route:

    /myservices/whisper

Legacy health:

    http://127.0.0.1/myservices/whisper/healthz

Expected response:

    ok

Do not modify this contour unless explicitly instructed.

## Current dev contour

Dev runtime path:

    /srv/soma

Current dev service:

    soma-whisper-dev

Direct dev URL:

    http://127.0.0.1:18080/whisper-dev

Caddy dev URL:

    http://127.0.0.1/whisper-dev
    http://10.0.1.196/whisper-dev

Dev health:

    /whisper-dev/healthz

Expected response:

    ok

## Important repo paths

Dev Whisper source:

    services/whisper-dev/

Dev Whisper compose:

    compose/whisper-dev.compose.yml

Runtime healthcheck template:

    runtime/scripts/healthcheck.sh

Caddy reference files:

    gateway/myservices/Caddyfile.current
    gateway/myservices/compose.override.caddy-soma-dev.yaml

Main status docs:

    docs/PROJECT_PHASE_1_STATUS.md
    docs/CURRENT_STATE.md
    docs/TARGET_ARCHITECTURE.md
    docs/DECISIONS.md
    docs/MIGRATION_PLAN.md

## Current validated Whisper dev behavior

Smoke-test:

    job: 3c52d24a91d6
    model: tiny
    compute: int8
    device: cuda
    status: done

Retention:

    WHISPER_RETENTION_MAX_JOBS=5

Validated behavior:

    only newest 5 terminal jobs remain
    generated files are owned by grigorynokhrin:docker
    legacy health remains OK

## Current Caddy state

Runtime Caddyfile:

    /home/grigorynokhrin/myservices/caddy/Caddyfile

Dev route:

    handle /whisper-dev* {
        reverse_proxy soma-whisper-dev:8000
    }

Legacy route:

    handle /myservices/whisper* {
        reverse_proxy whisper:8000
    }

Caddy has been connected to the dev Docker network:

    compose_default

Persistent override exists at runtime:

    /home/grigorynokhrin/myservices/compose.override.yaml

Reference copy in repo:

    gateway/myservices/compose.override.caddy-soma-dev.yaml

Important caveat:

    Caddy recreation with the override has not yet been tested.

Do not recreate Caddy without a backup and explicit approval.

## Standard runtime check

On the server:

    cd /srv/soma
    make health

Expected final line:

    [OK] healthcheck completed without hard failures

## Recommended Phase 2 directions

Good next tasks:

1. `soma-portal-ui`

   Purpose:

        one UI entrypoint for dev services

2. shared job schema / job-store convention

   Purpose:

        common history model for Whisper, OCR, SupIR, future services

3. Tesseract OCR API

   Purpose:

        CPU-friendly next service for document workflows

4. Controlled Caddy recreation test

   Purpose:

        prove persistent network override survives container recreation

## How Codex should work

Preferred workflow:

    branch -> change -> test -> docs -> PR -> human review -> runtime apply

Avoid direct unreviewed production changes.

For runtime changes, Codex should provide commands but not assume they were executed unless the user reports output.

## First files Codex should inspect for any Phase 2 task

    AGENTS.md
    docs/CODEX_HANDOFF.md
    docs/PROJECT_PHASE_1_STATUS.md
    docs/TARGET_ARCHITECTURE.md
    docs/CURRENT_STATE.md
    docs/DECISIONS.md

## Good first Codex prompt

    Read AGENTS.md, docs/CODEX_HANDOFF.md, and docs/PROJECT_PHASE_1_STATUS.md.

    Summarize the current architecture, the hard safety rules, and the recommended Phase 2 starting points.

    Do not modify files yet.
