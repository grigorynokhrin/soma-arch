# RUNTIME_STATUS

This document records runtime status observations during the migration from the legacy `myservices` environment to the target `soma` platform.

## runtime-status-check-v1

Date:

    2026-06-02

Host:

    grlvm

Legacy runtime path:

    /home/grigorynokhrin/myservices

## Purpose

Verify the current state of running containers after creating the empty `/srv/soma` skeleton.

This check is observational only.

It did not intentionally:

- start containers
- stop containers
- restart containers
- modify Compose
- modify Caddy
- modify routes
- modify files in `~/myservices`

## Commands used

    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    cd ~/myservices && docker compose ps

## Running containers

Observed running containers:

    myservices-caddy
    myservices-whisper
    myservices-home

## Docker ps observation

    NAMES                IMAGE                STATUS       PORTS
    myservices-caddy     caddy:2-alpine       Up 3 hours   443/tcp, 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 2019/tcp, 443/udp
    myservices-whisper   myservices-whisper   Up 3 hours   8000/tcp
    myservices-home      myservices-home      Up 3 hours   8000/tcp

## Docker ps -a observation

    NAMES                IMAGE                      STATUS                      PORTS
    image-upscale        myservices-image-upscale   Exited (137) 2 months ago
    myservices-caddy     caddy:2-alpine             Up 3 hours                  443/tcp, 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 2019/tcp, 443/udp
    myservices-whisper   myservices-whisper         Up 3 hours                  8000/tcp
    myservices-home      myservices-home            Up 3 hours                  8000/tcp

## Compose status observation

    NAME                 IMAGE                COMMAND                  SERVICE   CREATED        STATUS       PORTS
    myservices-caddy     caddy:2-alpine       "caddy run --config …"   caddy     2 months ago   Up 3 hours   443/tcp, 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 2019/tcp, 443/udp
    myservices-home      myservices-home      "uvicorn app:app --h…"   home      2 months ago   Up 3 hours   8000/tcp
    myservices-whisper   myservices-whisper   "/opt/nvidia/nvidia_…"   whisper   2 months ago   Up 3 hours   8000/tcp

## Classification update

Based on this check, the current runtime classification is:

### active-running

- `myservices-caddy`
- `myservices-home`
- `myservices-whisper`

### existing-stopped

- `image-upscale`

## Image-upscale note

`image-upscale` exists as a container and uses image:

    myservices-image-upscale

Current observed status:

    Exited (137) 2 months ago

This means it is not part of the currently running contour.

Exit code `137` usually means the container process was killed with SIGKILL. Possible causes can include OOM, manual kill, or hard termination. This document does not determine the root cause.

The creation of `/srv/soma` skeleton did not interact with Docker and is not considered the cause of this stopped state.

## Operational implication

Until further investigation, `image-upscale` should be treated as:

- existing
- potentially reusable
- not currently running
- not part of the live active contour

Do not delete or rebuild it without a separate Git-tracked step.
