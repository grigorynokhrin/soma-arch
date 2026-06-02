# RUNTIME_HEALTHCHECK

This document records the first read-only runtime healthcheck for the `/srv/soma` skeleton.

## Step

Name:

    add-runtime-healthcheck-v1

Status:

    completed

Date:

    2026-06-02

## Purpose

Introduce the first read-only healthcheck script for the future `soma` runtime root.

The healthcheck validates the current bootstrap environment without modifying services.

It checks:

- `/srv/soma` runtime root
- legacy `~/myservices` root
- server-side `~/soma-arch` reference repository
- Docker availability
- currently running containers
- required legacy containers
- legacy Compose status
- Whisper health endpoint

## Source template

Git-tracked template:

    runtime/scripts/healthcheck.sh

Server runtime copy:

    /srv/soma/scripts/healthcheck.sh

## Runtime permissions

Observed server file:

    /srv/soma/scripts/healthcheck.sh

Observed permissions:

    -rwxrwxr-x

Observed owner/group after correction:

    grigorynokhrin:docker

## Healthcheck command

Run from anywhere:

    /srv/soma/scripts/healthcheck.sh

Recommended operator flow:

    cd /srv/soma
    /srv/soma/scripts/healthcheck.sh

## Verification result

The script was executed successfully on server `grlvm`.

Final summary:

    [OK] healthcheck completed without hard failures

## Required legacy containers verified

The following containers were verified as running:

    myservices-caddy
    myservices-home
    myservices-whisper

## Whisper health endpoint

Endpoint checked:

    http://127.0.0.1/myservices/whisper/healthz

Observed result:

    [OK] whisper health endpoint responded
    ok

## Safety confirmation

This healthcheck is read-only.

It does not intentionally:

- start containers
- stop containers
- restart containers
- modify Caddy
- modify Docker Compose
- modify routes
- modify files in `~/myservices`
- delete files
- write runtime data

## Known limitations

This healthcheck currently validates the legacy running contour only.

It does not yet validate:

- `soma-gateway`
- `soma-portal-ui`
- `soma-whisper-api`
- `soma-tesseract-api`
- `soma-supir-api`

Those components do not exist as active runtime services yet.

## Next expected improvement

After this document, the next safe improvement is to add a `make health` target to `/srv/soma/Makefile` that calls:

    /srv/soma/scripts/healthcheck.sh

That change should first be made in the Git-tracked template:

    runtime/Makefile

and then synced to:

    /srv/soma/Makefile

## Optional dev services

As of commit:

    0583758 add optional whisper dev healthcheck

The runtime healthcheck includes an optional dev-service section.

Runtime script:

    /srv/soma/scripts/healthcheck.sh

Repo template:

    runtime/scripts/healthcheck.sh

Section name:

    optional soma dev services

Currently checked optional dev container:

    soma-whisper-dev

Currently checked optional dev endpoint:

    http://127.0.0.1:18080/whisper-dev/healthz

## Healthcheck behavior

Required legacy checks remain hard checks.

Required legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Required legacy health endpoint:

    http://127.0.0.1/myservices/whisper/healthz

If a required legacy container is missing, the healthcheck records a hard failure.

If the optional dev container is missing, the healthcheck records a warning only:

    [WARN] optional dev container not running: soma-whisper-dev

If the optional dev endpoint does not respond, the healthcheck records a warning only:

    [WARN] optional dev whisper health endpoint did not respond successfully

The optional dev section must not make legacy health fail.

## Verified output

With `soma-whisper-dev` running, the healthcheck showed:

    === optional soma dev services ===
    [OK] optional dev container running: soma-whisper-dev
    [OK] optional dev whisper health endpoint responded
    ok

The final summary remained successful:

    === summary ===
    [OK] healthcheck completed without hard failures

## Design rule

Dev services may be added to healthcheck output for visibility.

Dev services must not become required production dependencies until explicitly promoted.

Promotion requires a separate documented migration step.
