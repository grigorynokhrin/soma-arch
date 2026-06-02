# BASELINES

This document records server baseline snapshots used during the migration from the current `myservices` environment to the target `soma` platform.

Baselines are factual snapshots. They must not modify running services.

## server-baseline-v1 — 2026-06-02 08:20:53

Status: captured

Server path:

    /home/grigorynokhrin/myservices/ops/baselines/server-baseline-v1-20260602-082053

Purpose:

Capture the current working state of the server before structural migration toward `soma`.

This baseline was created after the `soma-arch` reference repository had been initialized and after the core reference documents were committed.

## Included files

The baseline directory contains:

- `meta.txt`
- `host.txt`
- `disk.txt`
- `gpu.txt`
- `docker.txt`
- `compose.yaml`
- `Caddyfile`
- `tree-maxdepth3.txt`
- `inspect-myservices-caddy.json`
- `inspect-myservices-home.json`
- `inspect-myservices-whisper.json`
- `inspect-image-upscale.json`

## Captured areas

This baseline captures:

- host and OS information
- disk layout and usage
- GPU state through `nvidia-smi`
- Docker Engine and Docker Compose state
- running containers
- Docker images
- Docker storage summary
- current top-level project tree
- current Compose config
- current Caddy config
- Docker inspect output for active containers

## Active contour at capture time

The active contour was still the legacy `myservices` environment:

- `myservices-caddy`
- `myservices-home`
- `myservices-whisper`
- `image-upscale`

The active project root was:

    /home/grigorynokhrin/myservices

## Migration relevance

This baseline is the reference point before any of the following actions:

- creating `/srv/soma`
- introducing `soma-gateway`
- introducing `soma-portal-ui`
- creating `soma-whisper-dev`
- changing routes
- moving services
- removing cleanup candidates such as `adguardhome`
- cleaning Docker or containerd data

## Safety note

This baseline step did not intentionally:

- stop containers
- restart containers
- delete files
- move files
- rename services
- modify routes
- modify Compose configuration
- modify Caddy configuration

It is a read-only operational snapshot stored under the existing `myservices/ops/baselines` area.
