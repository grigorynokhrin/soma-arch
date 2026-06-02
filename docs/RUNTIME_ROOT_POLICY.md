# RUNTIME_ROOT_POLICY

This document defines the target runtime root policy for the `soma` platform.

It explains how `/srv/soma` should be used, how it differs from the current legacy runtime, and what ownership/permissions model should be used during the first implementation phase.

## Purpose

The target runtime root for the `soma` platform is:

    /srv/soma

This directory will eventually contain the runnable server-side structure of the platform:

- Compose files
- gateway configuration
- portal UI
- backend services
- scripts
- operations artifacts
- persistent runtime data

## Important paths

### GitHub reference repository

Remote:

    git@github.com:grigorynokhrin/soma-arch.git

Mac clone:

    /Users/grigorynokhrin/projects/soma-arch

Server clone:

    /home/grigorynokhrin/soma-arch

Purpose:

- architecture reference
- documentation
- migration plans
- future infrastructure source files

This is not the active runtime root.

### Current legacy runtime

Path:

    /home/grigorynokhrin/myservices

Purpose:

- current working service environment
- contains current Caddy/Home/Whisper/Image-upscale setup

Status:

- must remain untouched until explicit migration steps
- must not be renamed yet
- must not be deleted
- must not be moved without a rollback plan

### Future target runtime

Path:

    /srv/soma

Purpose:

- future active runtime root of the `soma` platform

Status:

- target path
- not yet the active runtime
- must be introduced by an explicit migration step

## Initial ownership model

For the first implementation phase, `/srv/soma` should use a simple operator-owned model.

Recommended initial ownership:

    grigorynokhrin:docker

Reasoning:

- `grigorynokhrin` is the current operator and developer
- the `docker` group is already operationally relevant for running containers
- avoids turning every edit into a `sudo` ritual
- simpler than introducing a dedicated `soma` system user too early
- appropriate for a single-user home server during bootstrap

This is a bootstrap model, not necessarily the final hardening model.

## Future ownership model

After the platform stabilizes, a stricter model may be introduced.

Possible future model:

    owner: soma:soma
    operators: soma-ops group
    deploy: dedicated deploy user

This is intentionally deferred.

Do not introduce this complexity before the runtime layout, deployment process, and service boundaries are stable.

## Permission policy

Recommended initial permissions:

### Directories

    775

Reason:

- owner can read/write/execute
- group can read/write/execute
- others can read/execute
- workable during bootstrap

### Regular non-secret files

    664

Reason:

- owner can read/write
- group can read/write
- others can read
- suitable for non-secret config, docs, scripts before hardening

### Executable scripts

    775

Reason:

- scripts must be executable by operator/group
- scripts should remain editable by operator/group

### Secret files

Examples:

- `.env`
- tokens
- private credentials
- API keys
- deploy secrets

Recommended permissions:

    600

or, when group access is intentionally needed:

    640

Rules:

- real secrets must not be committed to Git
- `.env` must not be world-readable
- `.env.example` may be committed
- production credentials must never be copied into documentation

## Target directory layout

Recommended initial `/srv/soma` layout:

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
        baselines/
        manifests/
        runbooks/
        backups/
      scripts/
      data/
        whisper/
        tesseract/
        supir/
      .env
      .env.example
      Makefile
      README.md

## Directory responsibilities

### `/srv/soma/compose`

Purpose:

- Docker Compose files
- environment-specific Compose overrides
- service orchestration definitions

Examples:

- `compose.yaml`
- `compose.dev.yaml`
- `compose.prod.yaml`

### `/srv/soma/gateway`

Purpose:

- gateway / reverse proxy configuration
- route map
- Caddy snippets if needed

Primary component:

- Caddy

### `/srv/soma/portal-ui`

Purpose:

- user-facing portal code
- `/services`
- service pages
- history pages
- one-window UI implementation

The portal UI should not contain heavy inference logic.

### `/srv/soma/services`

Purpose:

- backend service code
- service Dockerfiles
- service dependencies
- service-specific API implementation

Expected services:

- `whisper`
- `tesseract`
- `supir`

Rules:

- service code belongs here
- real user uploads do not belong here
- large generated outputs do not belong here
- real secrets do not belong here

### `/srv/soma/data`

Purpose:

- persistent runtime data
- job records
- input artifacts
- output artifacts
- exports
- temporary runtime files

Expected layout:

    data/
      whisper/
        jobs/
        history/
        exports/
        tmp/
      tesseract/
        jobs/
        history/
        exports/
        tmp/
      supir/
        jobs/
        history/
        exports/
        tmp/

Reasoning:

- separates code from runtime data
- simplifies backup
- reduces risk of committing data accidentally
- makes cleanup policies clearer
- makes prod/dev separation easier later

### `/srv/soma/shared`

Purpose:

- shared contracts
- schemas
- UI/API contracts
- shared utilities when justified

Rules:

- avoid dumping unrelated code here
- only shared items with clear cross-service value belong here

### `/srv/soma/ops`

Purpose:

- operational artifacts
- baselines
- manifests
- runbooks
- backup metadata
- migration notes

Expected layout:

    ops/
      baselines/
      manifests/
      runbooks/
      backups/

### `/srv/soma/scripts`

Purpose:

- named operational scripts
- health checks
- backup scripts
- deploy scripts
- rollback scripts
- cleanup dry-run scripts

Examples:

- `healthcheck.sh`
- `backup.sh`
- `deploy.sh`
- `rollback.sh`
- `cleanup-dry-run.sh`

## Git policy

The `soma-arch` repository may contain:

- documentation
- Compose templates
- Caddy templates
- Dockerfiles
- service source code when introduced
- scripts
- `.env.example`
- runbooks

The repository must not contain:

- `.env`
- secrets
- tokens
- private keys
- real user uploads
- generated outputs
- large model files unless deliberately managed by a separate model strategy

## Runtime data policy

Runtime data belongs under:

    /srv/soma/data

Not under:

    /srv/soma/services

Reason:

- service code and user data have different lifecycles
- data backup and cleanup rules should be independent from code deployment
- service rebuilds should not affect persistent data

## Migration policy

During migration:

- do not move active services directly
- do not rename `~/myservices` directly
- create `/srv/soma` as an empty skeleton first
- copy/adapt one component at a time
- verify after each step
- keep rollback path
- update Git-tracked docs before or along with operational changes

## First implementation step

The first operational implementation step after this policy should be:

    create-srv-soma-skeleton

This step should:

- create `/srv/soma`
- create the target directory skeleton
- apply initial ownership and permissions
- not copy active services
- not stop containers
- not modify Caddy routes
- not modify Compose
- not delete legacy files

Success criteria:

- `/srv/soma` exists
- target directories exist
- ownership is correct
- permissions are reasonable
- current `~/myservices` services continue running
