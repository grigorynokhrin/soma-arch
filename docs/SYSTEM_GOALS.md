# SYSTEM_GOALS

## Purpose

Build a reproducible local service platform named `soma` on a Linux GPU server.

The platform must provide a single entry point for multiple local tools and AI/utility services, including:

- Whisper / ASR
- Tesseract / OCR
- SUPIR / image upscale and enhancement
- future local services

The system must be practical, reproducible, observable, and safe to evolve without breaking existing working services.

## User-facing routes

### `/services`

The route `/services` must open the main service portal.

The portal must:

- show available services
- link to each service
- optionally show current server date and time
- act as the stable user entry point into the platform

### `/<service>`

Routes like the following must open the interface of a concrete service:

- `/whisper`
- `/tesseract`
- `/supir`

Each service page must follow the one-window principle:

- no unnecessary redirects
- no unnecessary page reloads
- no multi-page workflow unless explicitly required
- the user starts and observes the task in the same interface

When a task starts, the interface must show:

- task accepted state
- current processing stage
- progress where available
- elapsed time
- estimated remaining time where possible
- final result or error

### `/<service>/history`

Routes like the following must expose task history:

- `/whisper/history`
- `/tesseract/history`
- `/supir/history`

The history page must allow the user to:

- inspect previous tasks
- export one task
- export multiple selected tasks
- export all selected tasks
- delete one task
- delete multiple selected tasks

Deleting a task must also allow cleanup of server-side artifacts when applicable.

## Task records

Each user task must be recorded with metadata sufficient for history, debugging, cleanup, and performance analysis.

Every task should store:

- task id
- service name
- request timestamp
- start timestamp
- finish timestamp
- status
- stage
- error message if any
- request parameters
- input artifact reference or request content
- output artifact reference
- processing duration

## Input measurement requirements

The platform must measure user input quantititatively.

For text input:

- character count
- word count
- byte size where useful

For audio input:

- file size
- duration
- sample rate where available
- channels where available

For image input:

- file size
- width
- height
- pixel area
- format where available

For PDF/OCR input:

- file size
- page count where available

## Performance tracking

The platform must store enough information to estimate and compare service performance over time.

At minimum, it should record:

- queue time
- validation time where available
- processing time
- postprocessing time where available
- total wall-clock time

This history should later be usable for ETA estimation and performance analysis.

## Reproducibility

The platform must be easy to reproduce on another Linux server.

Minimum reproducibility requirements:

- containerized services
- explicit folder structure
- explicit configuration through env files
- Docker Compose as the single-server orchestration layer
- scripts or Makefile for common operations
- no hidden manual steps
- no secrets committed to Git

## Naming conventions

The system namespace is `soma`.

Names for repositories, containers, folders, services, and routes should be consistent and predictable.

Examples:

- repository: `soma-arch`
- server root: `/srv/soma`
- container namespace: `soma-*`
- service folders: `services/whisper`, `services/tesseract`, `services/supir`
- routes: `/whisper`, `/tesseract`, `/supir`

## Safety principle

Working services must not be used as experimental sandboxes.

Risky changes must be developed in a dev/stage copy first and only then promoted to the working environment.
