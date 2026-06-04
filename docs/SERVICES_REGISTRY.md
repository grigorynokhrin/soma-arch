# SERVICES_REGISTRY

This document is the canonical inventory of `soma-arch` services and supporting runtime components.

It answers what exists, where it is exposed, which containers/routes/ports are known, which repo and runtime paths are involved, and which documentation is present or missing.

## 1. Purpose

The services registry owns the platform service inventory.

It should stay concise and structured. It should not become a runbook, design document, release log, or validation report.

Use this registry to answer:

- what services and components exist
- which environment they belong to
- how they are exposed
- which containers, ports, routes, and compose services they use
- where source and runtime configuration likely live
- what documentation exists
- what documentation is missing
- what must be validated before changes

## 2. Source Of Truth Policy

Canonical ownership:

- This registry owns service inventory.
- Runbooks own operational commands.
- Service design docs own architecture and behavior.
- Release notes own release history.
- Validation docs own validation evidence.
- Gateway/Home docs own routing and publication details when such docs exist.

Avoid copying large command blocks from runbooks. Link to relevant docs or mark TODO when the canonical doc does not exist yet.

If duplication is unavoidable, mark one location as canonical.

## 3. Service Status Taxonomy

- `prototype`: idea or skeleton, not expected to be running.
- `dev`: active development or experimental service.
- `stable`: user-facing service intended for normal use.
- `maintenance`: stable or legacy service receiving fixes but not active feature work.
- `deprecated`: retained only for rollback, migration, or historical reference.

## 4. Environment Taxonomy

- `local-mac`: local repository and validation workspace.
- `server-dev`: server-side dev or experimental runtime.
- `server-stable`: server-side stable user-facing runtime.
- `gateway`: Caddy or routing layer.
- `home`: Home/MyServices portal layer.

## 5. Registry Table

| Service / Component | Type | Status | Environment | User-facing route | Internal port | Container | Compose service | Purpose | Docs | Notes / Gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Whisper | service | stable | server-stable | `/myservices/whisper/` | `8000` documented as container port | `myservices-whisper` | `whisper` | Speech-to-text transcription | `docs/runbooks/whisper.md`, `docs/services/whisper.md`, `docs/WHISPER_RELEASE_MODEL.md`, `docs/RELEASES.md` | Production compose lives outside repo at `/home/grigorynokhrin/myservices/compose.yaml`. |
| Whisper dev | service | dev | server-dev | `/whisper-dev/` | `127.0.0.1:18080 -> 8000` | `soma-whisper-dev` | `whisper-dev` | Dev validation for Whisper source | `docs/WHISPER_DEV_BOOTSTRAP.md`, `docs/WHISPER_DEV_SMOKE_TEST.md`, `docs/WHISPER_DEV_RETENTION_TEST.md` | No dedicated `docs/runbooks/whisper-dev.md`; optional dev healthcheck exists in runtime script. |
| FFmpeg | service | stable | server-stable | `/ffmpeg/` | `127.0.0.1:18083 -> 8000` | `soma-ffmpeg` | `ffmpeg` | Stable user-facing FFmpeg web tool | `docs/runbooks/ffmpeg.md`, `docs/services/ffmpeg.md` | Canonical runbook and service design now exist; legacy flat runbook remains as supporting history. |
| FFmpeg dev | service | dev | server-dev | `/ffmpeg-dev/` | `127.0.0.1:18082 -> 8000` | `soma-ffmpeg-dev` | `ffmpeg-dev` | Experimental FFmpeg development and v2 work | `docs/FFMPEG_DEV_IMPLEMENTATION.md`, `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`, `docs/FFMPEG_DEV_SERVICE_SPEC.md` | Must not be published as Home user-facing entry. |
| Home / MyServices | supporting component | stable | home | `/myservices/` | `8000` documented as container port | `myservices-home` | `home` | Publishes stable tools only | `docs/RUNTIME_STATUS.md`, `docs/CURRENT_STATE.md`, `docs/FFMPEG_SERVICE_RUNBOOK.md` | Tracked Home source is not present in this repo; live source is under `/home/grigorynokhrin/myservices/home`. Dedicated runbook/service doc missing. |
| Caddy / Gateway | supporting component | maintenance | gateway | `/`, `/myservices/*`, `/ffmpeg*`, `/ffmpeg-dev*`, `/whisper-dev*` | host `:80`; upstreams use service port `8000` where documented | `myservices-caddy` | `caddy` | Routes Home and services | `gateway/myservices/Caddyfile.current`, `docs/CADDY_WHISPER_DEV_ROUTE.md`, `docs/FFMPEG_SERVICE_RUNBOOK.md` | Live Caddyfile may differ from tracked reference; inspect mounts before live changes. Dedicated runbook/service doc missing. |
| image-upscale | service | deprecated | server-stable | `/myservices/image-upscale/` tracked route | `7860` upstream in tracked Caddyfile | `image-upscale` | TODO: not tracked in repo compose | Historical image upscaling service | `docs/CURRENT_STATE.md`, `docs/RUNTIME_STATUS.md` | Runtime status documented as exited/stopped in `docs/RUNTIME_STATUS.md`; not in current task's known stable service set. |
| OCR placeholder | placeholder | prototype | gateway | `/myservices/ocr*` | none | none | none | Placeholder route only | `gateway/myservices/Caddyfile.current` | Caddy responds `OCR placeholder`; no service source/container tracked. |

## 6. Per-Service Details

### Whisper

Purpose:

- Stable speech-to-text transcription service.

Status:

- `stable`

Environment:

- `server-stable`

Route(s):

- `/myservices/whisper/`

Container(s):

- `myservices-whisper`

Port(s):

- container port `8000` documented in `docs/RUNTIME_STATUS.md`

Compose service(s):

- `whisper`

Known repo paths:

- `services/whisper-dev/` is the Git-tracked source used for dev-derived production releases.
- Production compose is not tracked in this repo.

Known server paths:

- `/home/grigorynokhrin/myservices/compose.yaml`
- `/home/grigorynokhrin/myservices/whisper`
- `/home/grigorynokhrin/myservices/whisper/outputs`
- `/home/grigorynokhrin/myservices/whisper/data`
- `/home/grigorynokhrin/myservices/whisper/hf_cache`

Related docs:

- `docs/runbooks/whisper.md`
- `docs/services/whisper.md`
- `docs/WHISPER_RELEASE_MODEL.md`
- `docs/RELEASES.md`
- `docs/WHISPER_DEV_BOOTSTRAP.md`
- `docs/WHISPER_DEV_SMOKE_TEST.md`
- `docs/WHISPER_DEV_RETENTION_TEST.md`

Validation expectations:

- Health check: `http://127.0.0.1/myservices/whisper/healthz`
- Real submit/result smoke-test for stable releases.
- Verify dev route remains healthy after stable promotion.

Known gaps / TODOs:

- Create structured per-release files under `docs/releases/` if the project migrates away from monolithic `docs/RELEASES.md`.

### Whisper Dev

Purpose:

- Development validation service for Whisper.

Status:

- `dev`

Environment:

- `server-dev`

Route(s):

- `/whisper-dev/`

Container(s):

- `soma-whisper-dev`

Port(s):

- `127.0.0.1:18080 -> 8000`

Compose service(s):

- `whisper-dev`

Known repo paths:

- `services/whisper-dev/`
- `compose/whisper-dev.compose.yml`

Known server paths:

- `/srv/soma/data/whisper-dev/jobs`
- `/srv/soma/data/whisper-dev/outputs`
- `/srv/soma/data/whisper-dev/hf_cache`

Related docs:

- `docs/WHISPER_DEV_BOOTSTRAP.md`
- `docs/WHISPER_DEV_SMOKE_TEST.md`
- `docs/WHISPER_DEV_RETENTION_TEST.md`
- `docs/PHASE_2_PLAN.md`

Validation expectations:

- Health check: `http://127.0.0.1:18080/whisper-dev/healthz`
- Caddy route check when published: `http://127.0.0.1/whisper-dev/healthz`
- Dev validation still requires commit/push/pull before server testing.

Known gaps / TODOs:

- No dedicated dev runbook under target `docs/runbooks/`.

### FFmpeg

Purpose:

- Stable user-facing FFmpeg web tool for MP4 remux and legacy profile conversion.

Status:

- `stable`

Environment:

- `server-stable`

Route(s):

- `/ffmpeg/`

Container(s):

- `soma-ffmpeg`

Port(s):

- `127.0.0.1:18083 -> 8000`

Compose service(s):

- `ffmpeg`

Known repo paths:

- `services/ffmpeg/`
- `compose/ffmpeg.compose.yml`

Known server paths:

- `/srv/soma/data/ffmpeg`

Related docs:

- `docs/runbooks/ffmpeg.md`
- `docs/services/ffmpeg.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`

Validation expectations:

- Direct health check: `http://127.0.0.1:18083/ffmpeg/healthz`
- Caddy health check: `http://127.0.0.1/ffmpeg/healthz`
- Status check should report service `ffmpeg`.
- Runtime scenarios should validate direct route before Home publication.

Known gaps / TODOs:

- Create structured release note under `docs/releases/`.
- Create structured validation reports under `docs/validations/`.

### FFmpeg Dev

Purpose:

- Experimental FFmpeg development service for v2 work.

Status:

- `dev`

Environment:

- `server-dev`

Route(s):

- `/ffmpeg-dev/`

Container(s):

- `soma-ffmpeg-dev`

Port(s):

- `127.0.0.1:18082 -> 8000`

Compose service(s):

- `ffmpeg-dev`

Known repo paths:

- `services/ffmpeg-dev/`
- `compose/ffmpeg-dev.compose.yml`

Known server paths:

- `/srv/soma/data/ffmpeg-dev`

Related docs:

- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`

Validation expectations:

- Direct health check: `http://127.0.0.1:18082/ffmpeg-dev/healthz`
- Caddy health check: `http://127.0.0.1/ffmpeg-dev/healthz`
- Must remain separate from stable `/ffmpeg/`.

Known gaps / TODOs:

- No dedicated target `docs/runbooks/ffmpeg-dev.md`.
- Dev service must not be listed on Home.

### Home / MyServices

Purpose:

- Home/MyServices portal that publishes stable user-facing tools.

Status:

- `stable`

Environment:

- `home`

Route(s):

- `/myservices/`
- documented LAN URL: `http://10.0.1.196/myservices/`

Container(s):

- `myservices-home`

Port(s):

- container port `8000` documented in `docs/RUNTIME_STATUS.md`

Compose service(s):

- `home`

Known repo paths:

- No tracked Home service source found in this repo.

Known server paths:

- `/home/grigorynokhrin/myservices/home`
- `/home/grigorynokhrin/myservices/compose.yaml`

Related docs:

- `docs/CURRENT_STATE.md`
- `docs/RUNTIME_STATUS.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`

Validation expectations:

- Home must publish stable services only.
- Current expected Home entries include Whisper and FFmpeg.
- Dev routes such as `/ffmpeg-dev/` must not be the user-facing Home entry.
- Home source changes may require image rebuild and readiness wait.

Known gaps / TODOs:

- Create `docs/runbooks/home.md`.
- Create `docs/services/home.md`.
- Track or document Home source ownership more explicitly.

### Caddy / Gateway

Purpose:

- Gateway routing for Home, stable services, and selected dev routes.

Status:

- `maintenance`

Environment:

- `gateway`

Route(s):

- `/myservices/image-upscale`
- `/myservices/image-upscale/*`
- `/myservices/whisper*`
- `/whisper-dev*`
- `/ffmpeg-dev*`
- `/ffmpeg*`
- `/myservices/ocr*`
- `/myservices*`

Container(s):

- `myservices-caddy`

Port(s):

- host `:80`
- upstream service ports are documented in `gateway/myservices/Caddyfile.current`

Compose service(s):

- `caddy`

Known repo paths:

- `gateway/myservices/Caddyfile.current`
- `gateway/myservices/compose.override.caddy-soma-dev.yaml`

Known server paths:

- `/home/grigorynokhrin/myservices/caddy/Caddyfile`
- `/home/grigorynokhrin/myservices/compose.yaml`

Related docs:

- `docs/CADDY_WHISPER_DEV_ROUTE.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/PROJECT_PHASE_1_STATUS.md`

Validation expectations:

- Gateway changes require explicit approval.
- Before changing live Caddy, inspect mounts:

      docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'

- Validate Caddy config before reload.
- Verify service health through Caddy after reload.

Known gaps / TODOs:

- Create `docs/runbooks/gateway.md`.
- Create `docs/services/gateway.md`.
- Live Caddyfile may differ from tracked reference.

## 7. Documentation Coverage Matrix

| Service / Component | Registry entry | Service design doc | Runbook | Release notes | Validation reports | Known rollback notes |
| --- | --- | --- | --- | --- | --- | --- |
| Whisper | Yes | Yes: `docs/services/whisper.md` | Yes: `docs/runbooks/whisper.md` | Yes: `docs/RELEASES.md` | Partial: Whisper dev smoke/retention docs and release evidence | Yes: `docs/runbooks/whisper.md`, `docs/WHISPER_RELEASE_MODEL.md`, `docs/RELEASES.md` |
| Whisper dev | Yes | Partial: `docs/WHISPER_DEV_BOOTSTRAP.md` | Partial: dev bootstrap/smoke docs | N/A | Yes: smoke/retention docs | Partial |
| FFmpeg | Yes | Yes: `docs/services/ffmpeg.md` | Yes: `docs/runbooks/ffmpeg.md` | Partial: rollout docs, no structured release file | Partial: runbook and rollout evidence | Yes: disable notes in `docs/runbooks/ffmpeg.md` |
| FFmpeg dev | Yes | Yes: `docs/FFMPEG_DEV_SERVICE_SPEC.md` | Yes: `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` | N/A | Partial: documented rollout validations | Yes: stop/cleanup in rollout runbook |
| Home / MyServices | Yes | Missing target doc | Missing target runbook | N/A | Partial runtime status docs | TODO |
| Caddy / Gateway | Yes | Missing target doc | Partial: Caddy route docs | N/A | Partial route validation docs | Partial |

Expected missing docs:

- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/runbooks/home.md`
- `docs/runbooks/gateway.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/services/home.md`
- `docs/services/gateway.md`

Do not create those files as part of this registry task.

## 8. Operational Risk Notes

- Home must publish stable services only.
- Dev services must not be listed on Home as user-facing tools.
- Gateway/Caddy changes require explicit approval.
- Home source changes require rebuild when source is baked into the image.
- Server validation requires commit/push/pull first.
- After restart, use a readiness loop before validation.
- Verify server branch, status, and log before deploy.
- Watch for detached HEAD on server.
- Root-owned data directories can break services.
- Tracked gateway config may differ from the live mounted Caddyfile.
- Do not infer live runtime state from the repository alone.

## 9. Gaps And Next Actions

Recommended next documentation tasks:

1. Create `docs/runbooks/gateway.md` from Caddy route docs and tracked gateway config.
2. Create `docs/runbooks/home.md` to document Home source ownership, rebuild, readiness, and publication rules.
3. Create `docs/services/home.md`.
4. Create `docs/services/gateway.md`.
5. Decide whether to split `docs/RELEASES.md` into structured `docs/releases/*.md` files.
6. Decide whether to create structured validation reports under `docs/validations/`.

## 10. Links To Process Docs

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
