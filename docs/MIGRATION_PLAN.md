# MIGRATION_PLAN

This document describes the migration path from the current `myservices` server layout to the target `soma` architecture.

## Goal

Migrate the current working local service environment into a reproducible, Git-tracked, conventionally named `soma` platform without breaking the existing working services.

The migration must be incremental, reversible, and verified after each step.

## Current source state

Current server root:

    /home/grigorynokhrin/myservices

Current active contour:

- `compose.yaml`
- `caddy/`
- `home/`
- `whisper/`
- `image-upscale/`

Current active containers:

- `myservices-caddy`
- `myservices-home`
- `myservices-whisper`
- `image-upscale`

Current non-core or inactive items:

- `sandbox/` — experimental
- `whisper_streamlit_backup_20260311-160741/` — archive / backup
- `ocr/` — future OCR placeholder
- `adguardhome/` — cleanup candidate
- `ops/` — emerging operations area

## Target state

Target platform namespace:

- `soma`

Target future server root:

    /srv/soma

Target major components:

- `soma-gateway`
- `soma-portal-ui`
- `soma-whisper-api`
- `soma-tesseract-api`
- `soma-supir-api`

Target user-facing routes:

- `/services`
- `/whisper`
- `/whisper/history`
- `/tesseract`
- `/tesseract/history`
- `/supir`
- `/supir/history`

## Migration principles

### 1. Do not break the working contour

The current working `myservices` setup must remain available until an equivalent `soma` service is verified.

No direct destructive changes to the active contour are allowed without:

- baseline
- backup where needed
- explicit rollback path
- verification command
- Git-tracked plan

### 2. No direct risky edits to production services

Working services must not be used as experimental sandboxes.

Risky changes must happen in a separate dev copy first.

### 3. Prefer copy-and-verify over rename-and-hope

Do not immediately rename or move active directories.

Preferred pattern:

1. copy or create target structure
2. adapt config
3. run side-by-side where possible
4. verify health
5. switch routing only after success
6. keep rollback path

### 4. One change per step

Each migration step should change one clearly bounded thing.

Examples:

- create `/srv/soma`
- copy Caddy config
- create `soma-gateway`
- create `soma-portal-ui`
- create `soma-whisper-dev`
- verify `soma-whisper-dev`
- switch route
- retire old route

### 5. Verify after every step

Every step must define its own verification.

Examples:

- `docker ps`
- `docker compose ps`
- `curl /healthz`
- browser check
- job submit test
- log check
- disk usage check

### 6. Cleanup is a separate phase

Cleanup candidates must not be removed during structural migration unless the step is explicitly a cleanup step.

Known cleanup candidates:

- `adguardhome/`
- old sandbox artifacts
- obsolete backup folders
- unused images
- unused containerd artifacts

## Proposed phases

## Phase 0 — Reference and baseline

Status: in progress

Purpose:

Create a Git-tracked reference before touching the server layout.

Deliverables:

- `soma-arch` private GitHub repository
- `SYSTEM_GOALS.md`
- `TARGET_ARCHITECTURE.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `MIGRATION_PLAN.md`

Success criteria:

- GitHub repository exists
- docs are filled
- local repo is clean and synced
- current server state is described

## Phase 1 — Server baseline capture

Purpose:

Capture the current server state in a Git-friendly and repeatable way.

Actions:

- capture Docker state
- capture Caddy config
- capture compose config
- capture directory classification
- capture disk/GPU/Docker versions
- store baseline under an ops/baseline area

Success criteria:

- baseline exists
- baseline is timestamped
- baseline does not modify running services

## Phase 2 — Create target `/srv/soma` skeleton

Purpose:

Create the future server root without moving active services.

Target layout:

    /srv/soma/
      compose/
      gateway/
      portal-ui/
      services/
        whisper/
        tesseract/
        supir/
      shared/
      ops/
      scripts/
      .env.example
      Makefile
      README.md

Success criteria:

- `/srv/soma` exists
- skeleton directories exist
- no active service has been moved
- current `myservices` containers still run

## Phase 3 — Introduce `soma-gateway` and route conventions

Purpose:

Prepare gateway routing under the `soma` naming scheme.

Actions:

- create target Caddy config in `/srv/soma/gateway`
- define route map
- avoid breaking current routes
- test gateway config before switching

Success criteria:

- route conventions are documented
- gateway config is valid
- old working routes still work

## Phase 4 — Introduce `soma-portal-ui`

Purpose:

Create the new `/services` portal.

Initial requirements:

- list available services
- link to service pages
- optionally show server time/date
- provide stable entry point

Success criteria:

- `/services` opens
- page loads through gateway
- no existing service is broken

## Phase 5 — Create `soma-whisper-dev`

Purpose:

Create a dev copy of Whisper before touching the working Whisper service.

Rules:

- separate container name
- separate route
- separate job/output data
- model cache may be shared only deliberately
- no destructive changes to current `myservices-whisper`

Possible route:

- `/whisper-dev`

Success criteria:

- dev container starts
- health endpoint works
- small test job works
- logs are readable
- existing `/myservices/whisper` or current route still works

## Phase 6 — Promote Whisper into `soma-whisper-api`

Purpose:

Move from legacy Whisper service to target `soma` naming only after dev copy is verified.

Actions:

- define final route `/whisper`
- define history route `/whisper/history`
- standardize job metadata
- standardize progress/status API
- verify one-window UI assumptions

Success criteria:

- `/whisper` works
- job submit works
- progress/status works
- history model exists
- rollback route exists

## Phase 7 — Add Tesseract/OCR service

Purpose:

Turn the current `ocr/` placeholder into a real `soma-tesseract-api`.

Success criteria:

- `/tesseract` opens
- OCR job can be submitted
- OCR result is saved
- `/tesseract/history` exists or has a defined stub
- job metadata follows the standard model

## Phase 8 — Add SUPIR/image upscale service under `soma`

Purpose:

Bring image upscale service into the `soma` naming and UX model.

Rules:

- respect RTX 3060 12GB VRAM limits
- keep service isolated
- do not break existing `image-upscale` until replacement is verified

Success criteria:

- `/supir` opens
- test image processing works
- input/output artifacts are stored predictably
- `/supir/history` exists or has a defined stub

## Phase 9 — Cleanup legacy artifacts

Purpose:

Remove or archive obsolete non-core items only after replacements are verified.

Candidates:

- `adguardhome/`
- unused sandbox artifacts
- old backups
- unused Docker images
- unused containerd data

Rules:

- cleanup must be explicit
- cleanup must have a dry-run where possible
- cleanup must be reversible where practical
- cleanup must not happen during unrelated migration steps

Success criteria:

- disk usage decreases or clutter is reduced
- active services still work
- cleanup is documented

## Phase 10 — Automation and operations

Purpose:

Make operations repeatable.

Deliverables:

- `Makefile`
- `scripts/healthcheck.sh`
- `scripts/backup.sh`
- `scripts/deploy.sh`
- `scripts/rollback.sh`
- systemd unit where needed
- health checks
- logging conventions

Success criteria:

- common operations are named commands
- service state can be checked quickly
- server reboot behavior is controlled
- backup path is documented

## First implementation step after this plan

Do not start with moving services.

Recommended next step:

`server-baseline-v1`

Actions:

- pull or clone `soma-arch` on the server
- create or update an ops baseline folder
- capture current compose/Caddy/Docker/server state
- do not modify active containers

Expected result:

A timestamped baseline exists and the current working state remains untouched.
