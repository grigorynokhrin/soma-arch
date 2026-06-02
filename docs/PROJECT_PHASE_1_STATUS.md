# PROJECT_PHASE_1_STATUS

This document closes Phase 1 of the `soma` home-server architecture work.

## Status

Name:

    soma-phase-1-platform-baseline

Status:

    completed

Date:

    2026-06-02

Server:

    grlvm

Current latest known Git commit before this document:

    1bc0916 add caddy dev route references

## Original goal

Build a safer development and production workflow for the home server.

The main goal was to stop making direct unstructured changes to the working system and move toward:

- documented architecture
- reproducible runtime
- separated dev/prod contours
- safe healthchecks
- Git-tracked service source
- clear migration path for future services

## Hardware boundary

Target machine:

    Ubuntu Server 24.04 minimal
    Gigabyte B760 Gaming X AX DDR4
    Intel Core i5-14600KF
    32GB DDR4
    SSD 480GB
    NVIDIA RTX 3060 12GB VRAM

Important operating constraints:

    limited VRAM
    limited SSD
    avoid unsafe changes to working legacy services
    prefer Docker Compose and reproducible runtime state

## Repositories and runtime roots

Reference Git repo on Mac:

    /Users/grigorynokhrin/projects/soma-arch

Reference Git repo on server:

    /home/grigorynokhrin/soma-arch

New runtime root:

    /srv/soma

Legacy runtime root:

    /home/grigorynokhrin/myservices

## Current production / legacy contour

Legacy stack remains active under:

    /home/grigorynokhrin/myservices

Legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Legacy Whisper route:

    /myservices/whisper

Legacy Whisper health endpoint:

    http://127.0.0.1/myservices/whisper/healthz

Observed result:

    ok

Legacy production behavior was preserved during Phase 1.

## Current dev contour

New dev runtime root:

    /srv/soma

Dev Whisper service:

    soma-whisper-dev

Dev route through direct local port:

    http://127.0.0.1:18080/whisper-dev

Dev route through Caddy:

    http://127.0.0.1/whisper-dev
    http://10.0.1.196/whisper-dev

Dev health endpoint:

    /whisper-dev/healthz

Observed result:

    ok

## Git-tracked dev service source

The dev Whisper service source is tracked in Git:

    services/whisper-dev/

Files:

    services/whisper-dev/Dockerfile
    services/whisper-dev/app.py
    services/whisper-dev/contexts.json
    services/whisper-dev/requirements.txt
    services/whisper-dev/templates/index.html
    services/whisper-dev/templates/job_result.html
    services/whisper-dev/templates/job_status.html
    services/whisper-dev/templates/job_status_old.html

Compose file:

    compose/whisper-dev.compose.yml

The repo compose file uses a relative build context:

    ../services/whisper-dev

Runtime compose file:

    /srv/soma/compose/whisper-dev.compose.yml

Runtime service path:

    /srv/soma/services/whisper-dev

Runtime data path:

    /srv/soma/data/whisper-dev

## Dev Whisper changes

The dev Whisper service was copied from legacy Whisper and patched minimally.

Main changes:

    environment-driven paths
    /whisper-dev root path
    non-root runtime user
    dedicated /srv/soma data paths
    retention max jobs
    isolated Hugging Face cache

Runtime user inside container:

    appuser

Runtime group inside container:

    appgroup

Host ownership for generated files:

    grigorynokhrin:docker

This solved the legacy `root:root` generated-file problem for the dev contour.

## Dev Whisper validation

Smoke-test result:

    passed

Smoke-test job:

    3c52d24a91d6

Model:

    tiny

Compute:

    int8

Device:

    cuda

Generated artifacts:

    txt
    srt
    status.json
    job log
    intermediate jsonl
    chunk wav

Result text:

    Okay, let's go.

## Retention validation

Retention setting:

    WHISPER_RETENTION_MAX_JOBS=5

Retention test result:

    passed

After submitting 5 additional jobs, the original smoke-test job was removed:

    3c52d24a91d6

Remaining job count:

    5

Remaining jobs:

    38153917dac3
    9884775cf449
    7919c7473ee4
    f0b5fa086ade
    fb0f23b326b6

Generated files remained owned by:

    grigorynokhrin:docker

## Runtime healthcheck

Runtime healthcheck script:

    /srv/soma/scripts/healthcheck.sh

Git-tracked template:

    runtime/scripts/healthcheck.sh

Command:

    cd /srv/soma
    make health

Hard checks:

    /srv/soma exists
    /home/grigorynokhrin/myservices exists
    /home/grigorynokhrin/soma-arch exists
    Docker is available
    myservices-caddy is running
    myservices-home is running
    myservices-whisper is running
    legacy Whisper health responds

Optional dev checks:

    soma-whisper-dev container
    http://127.0.0.1:18080/whisper-dev/healthz

Important rule:

    legacy failures are hard failures
    dev failures are warnings unless explicitly promoted

Observed final summary:

    [OK] healthcheck completed without hard failures

## Caddy dev route

Caddyfile path:

    /home/grigorynokhrin/myservices/caddy/Caddyfile

Caddy reference file in Git:

    gateway/myservices/Caddyfile.current

Added dev route:

    handle /whisper-dev* {
        reverse_proxy soma-whisper-dev:8000
    }

Legacy route remains:

    handle /myservices/whisper* {
        reverse_proxy whisper:8000
    }

Caddy config validation result:

    Valid configuration

Caddy reload result:

    completed without hard failure

Caddy container was reloaded, not recreated.

## Caddy network bridge

The Caddy container needs access to the dev Docker network.

Runtime network connection was added:

    docker network connect compose_default myservices-caddy

Observed Caddy networks:

    myservices_default
    compose_default

Persistent compose override was created:

    /home/grigorynokhrin/myservices/compose.override.yaml

Git reference copy:

    gateway/myservices/compose.override.caddy-soma-dev.yaml

Override content:

    services:
      caddy:
        networks:
          default: {}
          soma_dev: {}

    networks:
      soma_dev:
        external: true
        name: compose_default

Important note:

    this compose override has been validated with docker compose config
    it has not yet been tested by recreating myservices-caddy

Do not recreate Caddy without a fresh backup and explicit validation step.

## Mac / LAN access

Server IP:

    10.0.1.196

Mac IP:

    10.0.1.189

Validated LAN URL:

    http://10.0.1.196/whisper-dev/healthz

Observed response after local LuLu allow rule:

    HTTP/1.1 200 OK
    ok

Local Mac issue observed:

    /usr/bin/curl was initially blocked or interfered with by local network filtering

Resolution:

    allow relevant process in LuLu

Recommended LuLu local dev allow rules:

    /usr/bin/curl -> 10.0.1.196 TCP 80
    Python -> 10.0.1.196 TCP 80
    Terminal or iTerm -> 10.0.1.196 TCP 80
    Browser -> 10.0.1.196 TCP 80

## Documentation created during Phase 1

Core architecture docs:

    docs/SYSTEM_GOALS.md
    docs/TARGET_ARCHITECTURE.md
    docs/CURRENT_STATE.md
    docs/DECISIONS.md
    docs/MIGRATION_PLAN.md
    docs/BASELINES.md
    docs/REPO_LOCATIONS.md
    docs/RUNTIME_ROOT_POLICY.md
    docs/SRV_SOMA_SKELETON.md
    docs/RUNTIME_STATUS.md
    docs/RUNTIME_MAKEFILE.md
    docs/RUNTIME_HEALTHCHECK.md
    docs/BOOTSTRAP_STATUS.md

Whisper-specific docs:

    docs/WHISPER_RETENTION_CLEANUP.md
    docs/WHISPER_DEV_BOOTSTRAP.md
    docs/WHISPER_DEV_SMOKE_TEST.md
    docs/WHISPER_DEV_RETENTION_TEST.md

Caddy docs:

    docs/CADDY_WHISPER_DEV_ROUTE.md

Runtime docs:

    runtime/README.md

## Safety rules established

Do not directly replace legacy production routes without a dev validation step.

Do not delete legacy runtime data without:

    dry-run
    backup or manifest
    explicit confirmation

Do not expose new services publicly by default.

Prefer local-only ports first:

    127.0.0.1:<port>

Promote services through stages:

    direct local port
    Caddy dev route
    smoke-test
    healthcheck
    documented migration
    production route

## What is complete

Phase 1 is complete because:

    architecture is documented
    runtime root exists
    dev/prod contours exist
    dev Whisper works independently
    dev Whisper source is in Git
    Caddy can route to dev Whisper
    healthcheck covers legacy and optional dev
    retention policy is tested
    generated-file ownership is fixed in dev
    Mac and server repos are synchronized
    legacy Whisper remains healthy

## What is intentionally not complete

The following items are intentionally left for later phases:

    full portal UI
    job-store service
    shared API convention for all services
    RAG service
    OCR/Tesseract service
    SupIR service migration
    authentication
    queue system
    metrics/observability dashboard
    automated deployment
    Caddy recreation test with persistent network override
    production promotion of /whisper-dev

## Recommended next phase

Phase 2 should focus on product/runtime expansion, not emergency restructuring.

Recommended options:

1. Build `soma-portal-ui`

    Goal:
        one UI entrypoint for dev services

    Initial routes:
        /services
        /whisper
        /whisper/history
        /tesseract
        /tesseract/history
        /supir
        /supir/history

2. Build shared job-store convention

    Goal:
        common job metadata format for Whisper, OCR, SupIR and future services

    Initial implementation:
        filesystem JSON under /srv/soma/data/<service>/jobs

3. Add next service in dev contour

    Candidate:
        Tesseract OCR API

    Reason:
        CPU-friendly, low VRAM risk, useful for document pipelines

4. Improve Caddy persistence

    Goal:
        safely test Caddy recreation with compose.override.yaml

    Boundary:
        only after backup and explicit rollback plan

## Phase 1 conclusion

Phase 1 established a safe development baseline.

The server can now support iterative development without directly experimenting on the working legacy service.

The system is ready for Phase 2 planning.
