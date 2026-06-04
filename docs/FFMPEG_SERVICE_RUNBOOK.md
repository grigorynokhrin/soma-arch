# FFMPEG_SERVICE_RUNBOOK

This document records the stable `soma-ffmpeg` service promoted from the validated `soma-ffmpeg-dev` baseline.

## Purpose

`ffmpeg` is the stable FFmpeg web tool.

`ffmpeg-dev` remains available for future v2 experiments and should not be used as the stable service once `ffmpeg` is rolled out.

## Source Layout

Source:

    services/ffmpeg/

Compose:

    compose/ffmpeg.compose.yml

Image:

    soma-ffmpeg:local

Container:

    soma-ffmpeg

Service name:

    ffmpeg

Data directory:

    /srv/soma/data/ffmpeg

Route:

    /ffmpeg/

Direct local bind:

    127.0.0.1:18083 -> 8000

The stable service is copied from the validated `ffmpeg-dev` baseline at commit `7cce8d8` and uses separate source, compose, container, image, route, and data paths.

## Current Live State

The stable FFmpeg service has been promoted and validated on the server.

Live stable service:

    route: /ffmpeg/
    service name: ffmpeg
    container: soma-ffmpeg
    image: soma-ffmpeg:local
    direct bind: 127.0.0.1:18083 -> 8000
    data: /srv/soma/data/ffmpeg

Live dev service remains separate:

    route: /ffmpeg-dev/
    container: soma-ffmpeg-dev
    direct bind: 127.0.0.1:18082 -> 8000
    data: /srv/soma/data/ffmpeg-dev

Runtime validation passed:

- `/ffmpeg/healthz` responded `ok`
- `/ffmpeg/job/status.json` responded with service `ffmpeg`
- Caddy route `/ffmpeg/` is active
- Home page button is `FFmpeg -> /ffmpeg/`
- `/ffmpeg-dev/` remains available for dev work

## Dev vs Stable

- `ffmpeg-dev`: experimental service for future v2 changes, route `/ffmpeg-dev`, data `/srv/soma/data/ffmpeg-dev`.
- `ffmpeg`: stable validated tool, route `/ffmpeg`, data `/srv/soma/data/ffmpeg`.

Do not promote experimental `ffmpeg-dev` changes into `ffmpeg` without a separate validation and release step.

Official lifecycle:

1. Develop and test experimental changes in `ffmpeg-dev`.
2. Validate through direct bind and Caddy route.
3. Promote the validated baseline into `ffmpeg`.
4. Keep `ffmpeg` stable while `ffmpeg-dev` remains available for future experiments.

## Build And Run

Prepare the data directory on the server:

    mkdir -p /srv/soma/data/ffmpeg
    sudo chown grigorynokhrin:docker /srv/soma/data/ffmpeg
    chmod 775 /srv/soma/data/ffmpeg

Build only the stable FFmpeg service:

    docker compose -f compose/ffmpeg.compose.yml build ffmpeg

Start only the stable FFmpeg service:

    docker compose -f compose/ffmpeg.compose.yml up -d ffmpeg

Check the container:

    docker ps --filter name=soma-ffmpeg

Do not run `docker compose down` from unrelated compose projects.

## Healthcheck

Direct bind:

    curl -fsS http://127.0.0.1:18083/ffmpeg/healthz

Expected response:

    ok

Index smoke check:

    curl -fsS http://127.0.0.1:18083/ffmpeg/ | grep -E 'action=|href=|FFmpeg'

Expected internal links should be path-based and start with `/ffmpeg/`.

Status endpoint after a job exists:

    curl -fsS http://127.0.0.1:18083/ffmpeg/job/status.json

Expected service field:

    "service": "ffmpeg"

## Caddy Route Reference

Do not modify live Caddy as part of this repo-only service promotion unless a separate task explicitly asks for it.

Active route blocks:

    handle /ffmpeg-dev* {
        reverse_proxy soma-ffmpeg-dev:8000
    }

    handle /ffmpeg* {
        reverse_proxy soma-ffmpeg:8000
    }

Keep `/ffmpeg-dev*` before `/ffmpeg*` in route references so the stable `/ffmpeg*` prefix does not shadow the dev route.

The stable service compose attaches `soma-ffmpeg` to the external Docker network `compose_default` with alias `soma-ffmpeg`, matching the route above.

## Home Entry

The live Home page button points to:

    FFmpeg -> /ffmpeg/

The stable Home entry should not be replaced by `/ffmpeg-dev/`. The Home UI source is not tracked in this repository; Home remains part of the legacy runtime under `/home/grigorynokhrin/myservices`.

## Smoke Test

Use a small local video first.

MP4 remux:

1. Open `http://127.0.0.1:18083/ffmpeg/`.
2. Upload one video in the MP4 remux block.
3. Probe streams.
4. Keep selected audio/subtitle streams.
5. Submit remux.
6. Confirm the job reaches `done` or `done_with_warnings`.
7. Confirm the artifact downloads from `/ffmpeg/download/...`.

Batch conversion:

1. Upload one or more videos in the batch conversion block.
2. Select one profile.
3. Submit conversion.
4. Confirm the job reaches `done` or `done_with_warnings`.
5. Confirm one output artifact per input file.
6. Inspect `/ffmpeg/job/status.json` for warnings and `ffmpeg_commands`.

## Disable Or Roll Back

Stop only the stable FFmpeg compose project:

    docker compose -f compose/ffmpeg.compose.yml down

This stops `soma-ffmpeg` but does not affect `soma-ffmpeg-dev`, Whisper, Caddy, Home, OCR, or legacy production compose.

If the Caddy route was added separately, remove or comment only the `/ffmpeg*` route block and reload Caddy according to that separate Caddy change plan.

Do not remove `/srv/soma/data/ffmpeg` unless a separate cleanup task explicitly asks for it.
