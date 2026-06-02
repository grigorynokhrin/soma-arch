# BOOTSTRAP_STATUS

This document records the current bootstrap status of the `soma` runtime foundation.

## Status

Name:

    soma-bootstrap-status-v1

Status:

    completed

Date:

    2026-06-02

Server:

    grlvm

## Purpose

The bootstrap phase created a safe and reproducible foundation for the future `soma` runtime.

The goal was not to migrate services yet.

The goal was to establish:

- Git source of truth
- server-side reference clone
- target runtime root
- documented runtime layout
- read-only operator commands
- read-only healthcheck
- verified legacy service status

## Repository state

GitHub repository:

    git@github.com:grigorynokhrin/soma-arch.git

Mac clone:

    /Users/grigorynokhrin/projects/soma-arch

Server clone:

    /home/grigorynokhrin/soma-arch

Server runtime root:

    /srv/soma

Legacy runtime root:

    /home/grigorynokhrin/myservices

## Current runtime files

The target runtime root currently contains the first operational files:

    /srv/soma/README.md
    /srv/soma/.env.example
    /srv/soma/Makefile
    /srv/soma/scripts/healthcheck.sh

## Runtime ownership policy

Runtime root:

    /srv/soma

Expected owner/group:

    grigorynokhrin:docker

Expected directory mode:

    775

Expected regular file mode:

    664

Expected executable script mode:

    775

Verified script ownership:

    /srv/soma/scripts/healthcheck.sh
    grigorynokhrin:docker

## Available operator commands

Run from:

    cd /srv/soma

Available commands:

    make help
    make status
    make legacy-status
    make tree
    make health

## `make health`

The `make health` command runs:

    /srv/soma/scripts/healthcheck.sh

This command is read-only.

It verifies:

- `/srv/soma`
- `/home/grigorynokhrin/myservices`
- `/home/grigorynokhrin/soma-arch`
- Docker availability
- running Docker containers
- required legacy containers
- legacy Compose status
- Whisper health endpoint

## Verified legacy runtime status

The following legacy containers were verified as running:

    myservices-caddy
    myservices-home
    myservices-whisper

The Whisper health endpoint was verified:

    http://127.0.0.1/myservices/whisper/healthz

Observed response:

    ok

Healthcheck final result:

    [OK] healthcheck completed without hard failures

## Known stopped container

The following legacy-related container exists but is not currently running:

    image-upscale

Observed status from previous runtime status check:

    Exited (137) 2 months ago

This is recorded as known state.

No cleanup or restart action has been taken as part of bootstrap.

## Safety boundary

During bootstrap, no active legacy service was intentionally modified.

Bootstrap did not intentionally:

- stop containers
- restart containers
- change Caddy routes
- change Docker Compose definitions
- migrate service data
- delete files
- rename legacy directories
- move legacy runtime files

## Decisions already established

The following decisions are in effect:

- `soma-arch` is the Git source of truth
- `/srv/soma` is the future runtime root
- `/home/grigorynokhrin/myservices` remains the legacy runtime root
- Caddy remains the gateway choice
- Docker Compose remains the runtime mechanism
- Kubernetes is not used for the current phase
- `portal-ui` will become the single UI entry layer
- service backends will be isolated
- filesystem/JSON job storage is acceptable for the first implementation
- no experiments should be run directly against working legacy services

## Current phase result

Bootstrap is complete enough to proceed to the next phase.

The server now has:

- documented target runtime root
- reproducible Git reference
- read-only status commands
- read-only healthcheck
- verified legacy health

## Next phase

The next phase should prepare the first dev service without touching the working legacy service.

Recommended first dev target:

    soma-whisper-dev

Initial goal:

    create an isolated dev copy of Whisper service structure under /srv/soma

Safety rule:

    do not replace or modify myservices-whisper until the dev service is verified separately
