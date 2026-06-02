# REPO_LOCATIONS

This document records where the `soma-arch` reference repository is cloned and how it relates to the current server runtime.

## GitHub remote

Repository:

    git@github.com:grigorynokhrin/soma-arch.git

Purpose:

- source of truth for `soma` architecture
- documentation
- migration plans
- future infrastructure files

## Mac clone

Path:

    /Users/grigorynokhrin/projects/soma-arch

Purpose:

- primary editing location from Mac
- Git operations
- documentation updates
- future infrastructure development

## Server clone

Path:

    /home/grigorynokhrin/soma-arch

Purpose:

- server-side reference copy
- access to migration docs from the server
- future source for scripts, compose files, and ops documents

Important:

This path is not the runtime root of the platform.

## Current legacy runtime

Path:

    /home/grigorynokhrin/myservices

Purpose:

- current working legacy service environment
- contains current running Compose/Caddy/Whisper/Image-upscale setup

Status:

- must not be deleted
- must not be renamed yet
- must not be moved without a Git-tracked migration step

## Future target runtime

Planned path:

    /srv/soma

Purpose:

- future runtime root for the `soma` platform

Status:

- not created as the active runtime yet
- should be introduced by an explicit migration step
