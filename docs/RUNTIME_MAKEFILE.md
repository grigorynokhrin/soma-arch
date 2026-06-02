# RUNTIME_MAKEFILE

This document records the first runtime Makefile for the `/srv/soma` skeleton.

## Step

Name:

    add-runtime-makefile-v1

Status:

    completed

Date:

    2026-06-02

## Purpose

Introduce the first top-level operational command interface for the future `soma` runtime root.

The Makefile is intentionally read-only at this stage.

It must not:

- start containers
- stop containers
- restart containers
- modify Caddy
- modify Docker Compose
- modify the legacy runtime
- delete files

## Source template

The Git-tracked template is:

    runtime/Makefile

The server runtime copy is:

    /srv/soma/Makefile

## Runtime permissions

Observed server file:

    /srv/soma/Makefile

Observed permissions:

    -rw-rw-r--

Observed owner/group:

    grigorynokhrin:docker

## Available commands

### `make help`

Purpose:

Show available runtime commands.

### `make status`

Purpose:

Show read-only platform status:

- `SOMA_RUNTIME_ROOT`
- `SOMA_LEGACY_ROOT`
- `SOMA_REFERENCE_REPO`
- `/srv/soma` directory status
- `soma-arch` Git status
- current `docker ps`

### `make legacy-status`

Purpose:

Show read-only legacy runtime status:

- legacy root directory
- `docker compose ps` from `/home/grigorynokhrin/myservices`

### `make tree`

Purpose:

Show the `/srv/soma` directory tree up to depth 3.

## Verification output

The Makefile was copied from:

    /home/grigorynokhrin/soma-arch/runtime/Makefile

to:

    /srv/soma/Makefile

The following commands were verified:

    cd /srv/soma
    make help
    make status
    make legacy-status

Observed active containers during verification:

    myservices-caddy
    myservices-whisper
    myservices-home

## Safety confirmation

This step did not intentionally:

- modify `~/myservices`
- stop or restart containers
- modify routes
- modify Compose configuration
- modify Caddy configuration

## Operational implication

From this point, `/srv/soma` has a minimal read-only command interface.

The recommended operator entry point is now:

    cd /srv/soma
    make help
    make status

Future Makefile commands must remain small, explicit, and documented before being used for destructive or state-changing operations.
