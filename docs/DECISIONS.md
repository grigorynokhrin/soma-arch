# DECISIONS

This document records architectural decisions for the `soma` platform.

## ADR-0001 — Use GitHub private repository as source of truth

Status: accepted

Decision:

Use a private GitHub repository named `soma-arch` as the reference architecture and infrastructure repository.

Reasons:

- external source of truth independent of the server
- version history for architecture and infrastructure
- rollback and auditability
- natural base for future CI/CD

## ADR-0002 — Use SSH for GitHub access

Status: accepted

Decision:

Use SSH remote access for GitHub operations.

Repository remote:

    git@github.com:grigorynokhrin/soma-arch.git

Reasons:

- GitHub does not accept password authentication for Git operations over HTTPS
- SSH avoids repeated Personal Access Token handling
- works well with private repositories
- suitable for long-term developer workflow

## ADR-0003 — Use `soma` as system namespace

Status: accepted

Decision:

Use `soma` as the platform namespace.

Examples:

- repository: `soma-arch`
- future server root: `/srv/soma`
- containers: `soma-gateway`, `soma-portal-ui`, `soma-whisper-api`
- services: `whisper`, `tesseract`, `supir`

Reasons:

- short stable namespace
- consistent naming
- avoids continuing the old inconsistent `myservices` naming as the target

## ADR-0004 — Use Caddy as gateway

Status: accepted

Decision:

Use Caddy as the gateway / reverse proxy for the single-server platform.

Reasons:

- already used in the current environment
- simpler than nginx for this scale
- enough for current routing needs
- avoids premature introduction of heavier routing stacks

## ADR-0005 — Use one portal UI

Status: proposed

Decision:

Use a single `soma-portal-ui` layer for user-facing pages instead of each backend service owning an unrelated UI.

Reasons:

- consistent user experience
- shared one-window interaction model
- easier implementation of progress, timers, history, and service navigation
- avoids UI drift between services

## ADR-0006 — Keep backend services isolated

Status: accepted

Decision:

Keep Whisper, Tesseract/OCR, and SUPIR as separate backend services.

Reasons:

- different dependencies
- different resource profiles
- different model/runtime requirements
- lower risk of breaking unrelated services
- easier dev/prod separation

## ADR-0007 — Start with Docker Compose, not Kubernetes

Status: accepted

Decision:

Use Docker Compose as the orchestration layer for the single Linux server.

Reasons:

- matches the current environment
- simple and reproducible
- enough for one physical server
- avoids premature Kubernetes complexity

## ADR-0008 — Start with filesystem/JSON job storage

Status: proposed

Decision:

Start with filesystem-based job directories and JSON metadata for task history.

Reasons:

- simple to inspect
- easy to back up
- portable across Linux servers
- good enough before the system needs advanced search or analytics

Future option:

- SQLite or PostgreSQL if query complexity grows

## ADR-0009 — Do not experiment directly on working services

Status: accepted

Decision:

Working services must not be used as the experimental environment.

Reasons:

- previous work created uncertainty about whether Whisper was broken
- risky changes must happen in a dev/stage copy
- prod data and dev data should be separated
- rollback should be explicit

## ADR-0010 — Do not delete cleanup candidates before baseline

Status: accepted

Decision:

Do not remove directories such as `adguardhome`, `sandbox`, or backups until baseline and classification are complete.

Reasons:

- avoid accidental data loss
- keep the current working state recoverable
- cleanup should be planned and Git-tracked

## ADR-0011 — Prefer small verified steps

Status: accepted

Decision:

Changes to the platform should be made in small steps with verification after each step.

Reasons:

- reduces risk
- makes failures easier to locate
- prevents uncontrolled changes to working services
- matches the current operating model of diagnosis before modification
