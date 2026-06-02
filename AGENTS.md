# AGENTS.md

Project guidance for Codex and other coding agents working in this repository.

## Read first

Before making changes, read:

- docs/PROJECT_PHASE_1_STATUS.md
- docs/CODEX_HANDOFF.md
- docs/TARGET_ARCHITECTURE.md
- docs/CURRENT_STATE.md
- docs/DECISIONS.md
- docs/MIGRATION_PLAN.md
- docs/RUNTIME_HEALTHCHECK.md
- docs/CADDY_WHISPER_DEV_ROUTE.md

These files define the current architecture, safety boundaries, runtime layout, and Phase 1 baseline.

## Project purpose

This repository documents and implements the `soma` home-server architecture.

The project is moving from one legacy runtime toward a safer dev/prod workflow.

Current validated state:

- Legacy/prod runtime lives under `/home/grigorynokhrin/myservices`.
- New dev/runtime root lives under `/srv/soma`.
- Server Git repo lives at `/home/grigorynokhrin/soma-arch`.
- Mac Git repo lives at `/Users/grigorynokhrin/projects/soma-arch`.

## Hardware and capacity limits

Target machine:

- Ubuntu Server 24.04 minimal
- Intel Core i5-14600KF
- 32GB DDR4 RAM
- NVIDIA RTX 3060 12GB VRAM
- SSD 480GB

Always design for this machine.

For GPU/LLM work:

- Treat 12GB VRAM as a hard practical limit.
- Prefer small models, quantization, lower context, lower batch sizes, CPU offload, or service separation.
- Do not propose large models that obviously do not fit unless an upgrade path is documented.
- Avoid filling the 480GB SSD with datasets, model caches, or build artifacts.

## Runtime contours

### Legacy / production-like contour

Path:

    /home/grigorynokhrin/myservices

Current legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Current legacy Whisper route:

    /myservices/whisper

Do not replace this route without explicit human approval and a documented migration plan.

### Dev / soma contour

Path:

    /srv/soma

Current dev container:

    soma-whisper-dev

Current dev route:

    /whisper-dev

Current dev direct local port:

    127.0.0.1:18080 -> 8000

## Repository layout

Important directories:

    compose/                    Docker Compose files for soma/dev services
    docs/                       Architecture, status, migration, and validation docs
    gateway/                    Reference gateway/Caddy configs
    runtime/                    Runtime templates copied to /srv/soma
    services/                   Service source code
    scripts/                    Repository helper scripts

Current dev Whisper source:

    services/whisper-dev/
    compose/whisper-dev.compose.yml

Current runtime healthcheck template:

    runtime/scripts/healthcheck.sh

Current Caddy references:

    gateway/myservices/Caddyfile.current
    gateway/myservices/compose.override.caddy-soma-dev.yaml

## Hard safety rules

Do not make destructive changes.

Never run or recommend destructive commands without explicit approval, a dry-run, and a rollback plan.

Dangerous examples:

    rm -rf
    docker volume rm
    docker system prune -a
    docker compose down -v
    mkfs
    chown -R /home
    chmod -R 777

Do not modify legacy production behavior unless the task explicitly says so.

Specifically:

- Do not replace `/myservices/whisper`.
- Do not stop or recreate `myservices-caddy` unless explicitly requested.
- Do not stop or recreate `myservices-whisper` unless explicitly requested.
- Do not delete legacy data without a manifest and approval.
- Do not expose new services publicly by default.
- Do not bind experimental services to `0.0.0.0` unless explicitly requested.
- Prefer `127.0.0.1:<port>` for dev services.
- Do not commit secrets, tokens, private keys, audio files, datasets, model caches, or generated job data.

## Development conventions

For a new service, use this layout:

    services/<service-name>/
    compose/<service-name>.compose.yml
    docs/<SERVICE_NAME>_*.md

Runtime data should live outside Git:

    /srv/soma/data/<service-name>/

Service containers should usually:

- run as non-root
- use environment-driven paths
- bind only to localhost during dev
- have a health endpoint
- have a minimal smoke-test
- keep generated files owned by `grigorynokhrin:docker` where practical

Preferred runtime UID/GID for current host:

    APP_UID=1000
    APP_GID=990

## Docker Compose rules

Compose files in this repo should be reproducible from the repo root.

Prefer relative build contexts in repo compose files.

Example:

    build:
      context: ../services/<service-name>

Runtime bind mounts may point to `/srv/soma/data/...`.

Avoid changing legacy compose files directly unless the task explicitly asks for a legacy migration step.

## Healthcheck rules

Runtime healthcheck command:

    cd /srv/soma
    make health

Healthcheck design rule:

- legacy/prod checks can be hard failures
- dev checks should be warnings unless the service has been explicitly promoted

Current optional dev check:

    soma-whisper-dev
    http://127.0.0.1:18080/whisper-dev/healthz

## Verification commands

For repo-only docs changes:

    git status --short --branch

For compose changes:

    docker compose -f compose/<file>.yml config

For Whisper dev:

    docker compose -f compose/whisper-dev.compose.yml config
    curl -fsS http://127.0.0.1:18080/whisper-dev/healthz

For runtime/server verification:

    cd /srv/soma
    make health

For Caddy route checks:

    curl -fsS http://127.0.0.1/whisper-dev/healthz
    curl -fsS http://127.0.0.1/myservices/whisper/healthz

For Python syntax:

    python3 -m py_compile <file.py>

## Documentation rules

When behavior changes, update docs in the same PR.

Important docs to consider:

    docs/PROJECT_PHASE_1_STATUS.md
    docs/CURRENT_STATE.md
    docs/DECISIONS.md
    docs/RUNTIME_HEALTHCHECK.md
    docs/CADDY_WHISPER_DEV_ROUTE.md

For new services, add a service-specific doc under `docs/`.

Every significant runtime change should include:

- what changed
- why it changed
- exact paths
- validation commands
- rollback notes
- whether legacy/prod was affected

## Pull request expectations

Every PR should state:

- summary
- changed files
- whether legacy runtime is affected
- whether `/srv/soma` runtime commands are required
- test commands run
- rollback plan
- docs updated

Do not hide uncertainty. If something was not tested, say so.

## Definition of done

A task is done when:

- source/config changes are in Git
- docs are updated
- repo status is clean
- relevant compose config validates
- relevant health endpoints respond
- `make health` remains OK when runtime is affected
- rollback path is documented
- legacy/prod behavior is preserved unless explicitly changed
