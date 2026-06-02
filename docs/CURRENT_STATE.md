# CURRENT_STATE

## Scope

This document records the current known state before the `soma` restructuring.

The current server environment is still named `myservices`, but the target namespace is `soma`.

## Server

- Hostname: `grlvm`
- OS: Ubuntu 24.04.4 LTS
- Kernel: `6.8.0-101-generic`
- Architecture: x86-64
- Hardware vendor: Gigabyte Technology Co., Ltd.
- Hardware model: B760 GAMING X AX DDR4

## Hardware

Known platform:

- CPU: Intel Core i5-14600KF
- RAM: 32GB DDR4
- GPU: NVIDIA GeForce RTX 3060 12GB VRAM
- SSD: Patriot M.2 P310 480GB

## Disk state

The root filesystem was previously limited to about 98G because the Ubuntu LVM root logical volume had been created at 100G.

This was fixed by expanding the root logical volume.

Current known state:

- root filesystem size: approximately 437G
- used: approximately 78G
- available: approximately 341G
- root filesystem usage: approximately 19%

Root disk space is no longer the immediate bottleneck.

Known storage observation:

- significant storage usage was observed under `/var/lib/containerd`
- `/var/lib/docker` itself was small in the previous inspection

## GPU state

Known GPU stack from baseline:

- NVIDIA driver: 580.126.09
- CUDA reported by `nvidia-smi`: 13.0
- GPU: NVIDIA GeForce RTX 3060
- VRAM: 12288MiB

At the time of baseline, one Python process was using around 3766MiB of VRAM.

## Docker state

Known Docker versions from baseline:

- Docker Engine: 29.3.0
- Docker Compose: v5.1.0
- containerd: v2.2.1
- runc: 1.3.4

## Current running containers

Current active containers observed:

- `myservices-caddy`
- `myservices-home`
- `myservices-whisper`
- `image-upscale`

Current images observed:

- `myservices-image-upscale`
- `myservices-whisper`
- `myservices-home`
- `caddy:2-alpine`

## Current server project root

Current server path:

    /home/grigorynokhrin/myservices

Top-level directories observed:

- `adguardhome`
- `caddy`
- `home`
- `image-upscale`
- `ocr`
- `ops`
- `sandbox`
- `whisper`
- `whisper_streamlit_backup_20260311-160741`

## Current active contour

The current active working contour is:

- `compose.yaml`
- `caddy/`
- `home/`
- `whisper/`
- `image-upscale/`

Reasons:

- active containers are running from this environment
- Caddy uses `caddy/Caddyfile`
- Whisper has bind mounts to:
  - `whisper/hf_cache`
  - `whisper/data`
  - `whisper/outputs`
- image-upscale has bind mounts to:
  - `image-upscale/inputs`
  - `image-upscale/outputs`
  - `image-upscale/models`
  - `image-upscale/hf-cache`

## Current inactive or non-core items

### `sandbox/`

Status:

- experimental / sandbox

Observed size:

- approximately 2.9G

### `whisper_streamlit_backup_20260311-160741/`

Status:

- archive / backup

### `ocr/`

Status:

- future placeholder for OCR service

### `adguardhome/`

Status:

- candidate for removal later

Context:

- it was previously attempted for HTTPS-related setup
- it did not help
- it was not fully removed

### `ops/`

Status:

- emerging operations area
- should become the future place for baselines, manifests, scripts, runbooks, and backups

## Current Whisper state

Whisper is not considered dead.

Known facts:

- container is running
- health endpoint has returned OK
- submit flow has worked through Caddy
- jobs can be created
- job pages/results can be served
- GPU eventually participates in processing

Known issue:

- perceived latency after submit may be worse than before
- the issue should be measured by stages rather than guessed

Known diagnostic artifact:

- one test job failed because a generated test WAV file was zero bytes
- this did not prove Whisper service failure

## Known architecture gaps

- no formal Git repository existed for the server architecture at the start of this effort
- no formal prod/dev separation
- inconsistent naming between `myservices-*`, `image-upscale`, and future `soma-*`
- current UI is not yet unified
- service history and performance tracking are not yet standardized
- cleanup candidates exist but should not be removed before baseline and classification

## Current direction

The system should be gradually migrated from the current `myservices` layout toward the `soma` namespace and architecture.

No destructive changes should be made without:

- baseline
- classification
- Git-tracked plan
- explicit rollback path
