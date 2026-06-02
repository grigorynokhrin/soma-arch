# TARGET_ARCHITECTURE

## Platform name

The platform name and namespace is `soma`.

The first architecture/infrastructure repository is:

- `soma-arch`

## High-level architecture

`soma` is a single-server service platform.

The target architecture consists of the following layers:

1. Gateway / reverse proxy
2. Portal UI
3. Backend API services
4. Job storage / history / artifacts
5. Ops / reproducibility layer

## Components

### `soma-gateway`

Role:

- receive HTTP traffic
- route user-facing pages
- route API requests
- provide one stable entry point into the platform

Preferred technology:

- Caddy

Reason:

- already used in the current environment
- simple configuration
- enough for a single-server platform

### `soma-portal-ui`

Role:

- render `/services`
- render service pages such as `/whisper`, `/tesseract`, `/supir`
- render history pages such as `/whisper/history`
- provide consistent one-window UX
- communicate with backend APIs

The UI should not contain heavy inference logic.

### `soma-whisper-api`

Role:

- ASR / transcription backend
- receive audio tasks
- validate and measure audio input
- run transcription
- store job metadata
- store outputs
- expose task status and result APIs

### `soma-tesseract-api`

Role:

- OCR backend
- receive image/PDF tasks
- validate and measure input
- run OCR
- store job metadata
- store outputs
- expose task status and result APIs

### `soma-supir-api`

Role:

- image enhancement / upscale backend
- receive image tasks
- validate and measure image input
- run GPU-heavy processing
- store job metadata
- store outputs
- expose task status and result APIs

### `soma-job-store`

This can initially be a filesystem-based storage convention rather than a separate service.

Role:

- store job metadata
- store request parameters
- store event logs
- store input artifacts
- store output artifacts
- store export bundles
- support deletion and cleanup

Initial implementation preference:

- filesystem job directories
- JSON metadata
- plain logs

Possible future implementation:

- SQLite
- PostgreSQL
- separate job-store service

## Route conventions

### User-facing routes

- `/services`
- `/whisper`
- `/whisper/history`
- `/tesseract`
- `/tesseract/history`
- `/supir`
- `/supir/history`

### API route conventions

- `/api/whisper/jobs`
- `/api/whisper/jobs/{job_id}`
- `/api/whisper/jobs/{job_id}/result`
- `/api/whisper/history`
- `/api/tesseract/jobs`
- `/api/tesseract/jobs/{job_id}`
- `/api/supir/jobs`
- `/api/supir/jobs/{job_id}`

## Standard job lifecycle

Every service should follow a common job lifecycle where possible.

Standard states:

- `queued`
- `validating`
- `measuring`
- `running`
- `postprocessing`
- `completed`
- `error`
- `deleted`

The UI must visualize the current stage and elapsed time after the user starts a task.

## Target server folder layout

Long-term target layout:

    /srv/soma/
      compose/
        compose.yaml
        compose.override.yaml
      gateway/
        Caddyfile
      portal-ui/
        Dockerfile
        app/
      services/
        whisper/
          api/
          Dockerfile
          requirements.txt
          data/
            jobs/
            history/
            exports/
            tmp/
          models/
          cache/
        tesseract/
          api/
          Dockerfile
          requirements.txt
          data/
            jobs/
            history/
            exports/
            tmp/
        supir/
          api/
          Dockerfile
          requirements.txt
          data/
            jobs/
            history/
            exports/
            tmp/
          models/
          cache/
      shared/
        schemas/
        ui-contracts/
        utils/
      ops/
        scripts/
        backups/
        manifests/
        baselines/
        runbooks/
      .env
      .env.example
      Makefile
      README.md

## Container naming conventions

Target container names:

- `soma-gateway`
- `soma-portal-ui`
- `soma-whisper-api`
- `soma-tesseract-api`
- `soma-supir-api`

Target Compose service names:

- `gateway`
- `portal-ui`
- `whisper-api`
- `tesseract-api`
- `supir-api`

## Dev/prod separation

Working services must have a protected baseline.

Target principle:

- `*-prod` is the working service
- `*-dev` is the experimental copy
- prod and dev must not share mutable job/output directories
- model caches may be shared only deliberately

No risky changes should be applied directly to the working service.
