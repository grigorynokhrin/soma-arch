# Whisper Service Runbook

This is the canonical operational runbook for the stable Whisper service.

It explains how to operate, validate, diagnose, and safely maintain Whisper. It is not a service design document. Architecture and feature design should live in future `docs/services/whisper.md`.

## Purpose

Whisper is the stable user-facing speech-to-text service in the Home/MyServices environment.

It supports the daily task of uploading audio or video files and receiving transcription artifacts. Current production behavior supports both single-file transcription and batch upload v1, where multiple submitted files are processed sequentially inside one job and produce a combined TXT artifact.

Whisper exists as a stable Home/MyServices tool because transcription is a regular user-facing workflow. It should remain separate from FFmpeg and Home:

- FFmpeg prepares/remuxes/converts media files.
- Whisper transcribes audio extracted from uploaded audio/video files.
- Home publishes the stable service entry.
- Gateway/Caddy routes the stable prefix to the service.

## Scope

This runbook covers:

- operational lifecycle
- deployment/restart expectations
- readiness checks
- runtime validation
- logs and diagnostics
- storage, permissions, and retention checks
- known failure modes
- rollback/disable notes documented in existing release material

This runbook does not cover:

- full service architecture
- model-selection rationale beyond documented operational facts
- future feature design
- FFmpeg conversion workflows
- Home or Gateway implementation details except as integration boundaries

TODO:

- Create `docs/services/whisper.md` for service architecture, backend behavior, and future feature design.

## Service Topology

Stable service:

| Field | Value |
| --- | --- |
| Route | `/myservices/whisper/` |
| Container | `myservices-whisper` |
| Compose service | `whisper` |
| Compose file | `/home/grigorynokhrin/myservices/compose.yaml` |
| Docker network | `myservices_default` |
| Upstream port | `8000` inside the container/Caddy upstream |
| Home publication | Published as a stable Home/MyServices tool |
| Source path used for current releases | `/home/grigorynokhrin/soma-arch/services/whisper-dev` |

Stable direct host port:

- TODO: no stable direct host bind is documented in the repo. Stable validation is documented through Caddy at `http://127.0.0.1/myservices/whisper/healthz`.

Dev service:

| Field | Value |
| --- | --- |
| Route | `/whisper-dev/` |
| Container | `soma-whisper-dev` |
| Image | `soma-whisper-dev:local` |
| Direct bind | `127.0.0.1:18080 -> 8000` |
| Compose file | `compose/whisper-dev.compose.yml` |
| Compose service | `whisper-dev` |
| Runtime data | `/srv/soma/data/whisper-dev` |
| Home publication | Not published as a stable Home tool |

Home/MyServices:

- route: `/myservices/`
- stable Home entries include Whisper and FFmpeg
- Home must publish stable tools only
- dev routes must not replace stable Home entries
- tracked Home source is not present in this repo
- live Home source is documented under `/home/grigorynokhrin/myservices/home`

Gateway/Caddy:

- tracked reference: `gateway/myservices/Caddyfile.current`
- live Caddyfile: `/home/grigorynokhrin/myservices/caddy/Caddyfile`
- stable route contract:

```text
handle /myservices/whisper* {
    reverse_proxy whisper:8000
}
```

Do not modify Caddy unless the route contract changes and the task explicitly asks for it.

## Source And Runtime Locations

Known repo paths:

- `services/whisper-dev/`
- `compose/whisper-dev.compose.yml`
- `gateway/myservices/Caddyfile.current`
- `runtime/scripts/healthcheck.sh`
- `runtime/Makefile`

Known stable runtime paths:

- `/home/grigorynokhrin/myservices`
- `/home/grigorynokhrin/myservices/compose.yaml`
- `/home/grigorynokhrin/myservices/whisper`
- `/home/grigorynokhrin/myservices/whisper/outputs`
- `/home/grigorynokhrin/myservices/whisper/data`
- `/home/grigorynokhrin/myservices/whisper/hf_cache`

Known production bind mounts:

```text
/home/grigorynokhrin/myservices/whisper/outputs -> /app/outputs
/home/grigorynokhrin/myservices/whisper/data -> /app/data
/home/grigorynokhrin/myservices/whisper/hf_cache -> /app/hf_cache
```

Known production container paths:

- `/app/outputs`
- `/app/data/jobs`
- `/app/contexts.json`
- `/app/hf_cache`
- `/app/hf_cache/hub`

Known dev runtime paths:

- `/srv/soma/data/whisper-dev/jobs`
- `/srv/soma/data/whisper-dev/outputs`
- `/srv/soma/data/whisper-dev/hf_cache`

Known job files:

- `job.json`
- `job.log`
- `intermediate.jsonl`
- normalized WAV files
- chunk WAV files
- chunk TXT files
- final TXT
- final SRT for single-file jobs
- combined TXT for batch jobs

## Operational Lifecycle

Use the global workflow in:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/SERVICES_REGISTRY.md`

Current lifecycle:

1. Develop and validate changes in `soma-whisper-dev`.
2. Use prod-candidate validation when route-sensitive behavior must render as `/myservices/whisper`.
3. Confirm dev health and stable health before touching production.
4. Promote from the Git-tracked dev-derived source into the legacy production compose owner.
5. Rebuild/restart only the `whisper` service.
6. Validate health and a real submit/result workflow through the production route.
7. Verify the dev route remains healthy after stable promotion.

Server validation rule:

- Commit and push local changes before server validation.
- On the server, verify branch/status/log and use `git pull --ff-only`.
- Do not validate server runtime from uncommitted Mac-only changes.

Home/Gateway rule:

- Home and Gateway changes require explicit approval.
- Caddy was not changed for the documented Whisper production releases.
- Do not replace `/myservices/whisper` without explicit approval and a migration plan.

## Deployment And Restart

Before production deployment:

```text
git status --short --branch
git log --oneline -3
git pull --ff-only
git log --oneline -3
```

Pre-flight checks:

- confirm the intended source commit
- confirm production health is OK before touching production
- confirm dev health is OK
- confirm Caddy route contract is unchanged
- confirm production writable directories are owned by `grigorynokhrin:docker`
- confirm uid `1000` and gid `990` can write to production data/output/cache paths
- create/update rollback references before replacing production

Documented production build/restart commands:

```text
cd /home/grigorynokhrin/myservices
docker compose build whisper
docker compose up -d whisper
```

Rules:

- Restart only the Whisper service unless a task explicitly says otherwise.
- Do not restart or recreate Caddy casually.
- Do not run broad compose commands such as `docker compose --remove-orphans` casually.
- Do not run `docker compose down` from unrelated compose projects.
- Do not modify Home/Gateway during a Whisper-only maintenance task.

TODO:

- Document whether routine stable deployment should use `/home/grigorynokhrin/soma-arch` directly or a server worktree.

## Readiness

Do not assume the service is ready immediately after `docker compose up -d whisper`.

Readiness evidence should include:

- container is running
- health endpoint responds `ok`
- UI route returns HTML
- job submit redirects correctly

Stable health endpoint:

```text
curl -fsS http://127.0.0.1/myservices/whisper/healthz
```

Expected:

```text
ok
```

Runtime healthcheck:

```text
cd /srv/soma
make health
```

Expected final result:

```text
[OK] healthcheck completed without hard failures
```

Dev health endpoint:

```text
curl -fsS http://127.0.0.1/whisper-dev/healthz
```

TODO:

- Add a documented readiness loop for stable Whisper after restart.

## Runtime Validation Scenarios

### Scenario 1: UI Availability

Goal:

- Confirm the stable Whisper UI is reachable through the production route.

Route:

```text
http://127.0.0.1/myservices/whisper/
```

Expected result:

- HTML page renders.
- Form action is path-based and points to `/myservices/whisper/submit`.
- Default chunk length is 5 minutes.
- Default overlap is 0 seconds.

Evidence to capture:

- route tested
- status code
- form action
- default values
- timestamp and commit under test

### Scenario 2: Basic Audio Transcription

Goal:

- Confirm a small controlled audio file can be transcribed through the production route.

Documented submit path:

```text
POST /myservices/whisper/submit
```

Expected submit behavior:

- HTTP 303
- `Location: /myservices/whisper/jobs/<job-id>`

Expected final job behavior:

- `status: done`
- `progress_current` reaches `progress_total`
- one TXT artifact exists
- one SRT artifact exists for single-file mode
- artifact links use `/myservices/whisper/jobs/.../artifacts/...`

Evidence to capture:

- job ID
- final `status.json`
- `job.log` excerpt
- TXT/SRT artifact names
- health before and after

### Scenario 3: Batch Upload Transcription

Goal:

- Confirm batch upload v1 remains healthy in production.

Expected behavior:

- multiple files may be selected in one submit
- one submit creates one job
- files are processed sequentially
- `is_batch: true`
- `files_count` matches submitted files
- all `input_files` reach `done`
- one combined TXT artifact exists
- no combined SRT is generated in batch v1
- combined TXT has one header per input file

Documented production smoke-test:

- job `26b034ed3272`
- status `done`
- progress `2/2`
- combined TXT artifact `26b034ed3272-batch.txt`

Evidence to capture:

- submitted file count
- job ID
- final `status.json`
- combined TXT artifact name
- input file statuses
- health before and after

### Scenario 4: Error Handling For Invalid Input

Goal:

- Confirm user-facing and diagnostic behavior when the submitted input cannot produce chunks/transcription.

Documented evidence:

- a zero-byte generated test WAV caused a failed job in earlier diagnostics and did not prove service failure.

Expected behavior:

- job reaches an error status rather than silently succeeding
- `job.json` records `status`, `stage`, and `error`
- `job.log` records the failing step
- service health remains OK

Evidence to capture:

- invalid input type/size
- job ID
- final `job.json`
- `job.log` excerpt
- health after failure

### Scenario 5: Longer Audio Transcription

Goal:

- Confirm chunking and progress behavior for longer media.

Expected behavior:

- service transcodes input to 16 kHz mono WAV
- chunks are created according to `chunk_min` and `overlap_sec`
- `progress_current` advances per chunk
- final TXT/SRT artifacts are assembled

Warnings/limits:

- Do not parallelize heavy production, dev, and candidate Whisper tests on the RTX 3060 12GB.
- Model/GPU behavior should be verified from logs, not assumed.

Evidence to capture:

- input duration
- chunk settings
- chunk count
- used compute type
- device/model log line if visible
- final artifacts

## Diagnostics

Container logs:

- inspect `myservices-whisper` logs for model loading, runtime errors, and application startup
- documented model log format includes `[WHISPER_MODEL]`
- documented model failure log format includes `[WHISPER_MODEL_FAIL]`

TODO:

- Add exact stable `docker logs` command after confirming the production logging convention.

Job directory diagnostics:

- `job.json`: primary job metadata/status
- `job.log`: job lifecycle log
- `intermediate.jsonl`: per-chunk transcription metadata
- chunk TXT files: per-chunk text
- final TXT/SRT artifacts: user-facing outputs

Common job log stages:

- job created
- source uploaded
- job started
- probing duration
- converting to wav
- chunking
- loading model
- transcribing chunk N/M
- assembling final TXT/SRT
- job done
- job error

Status endpoint:

```text
/myservices/whisper/jobs/<job-id>/status.json
```

Artifact endpoints:

```text
/myservices/whisper/jobs/<job-id>/artifacts/<filename>
```

Runtime healthcheck:

```text
cd /srv/soma
make health
```

## Model And Runtime Notes

Repository-supported facts:

- Python backend uses `faster-whisper`.
- Docker base image is `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`.
- Dependencies include `fastapi`, `uvicorn`, `faster-whisper`, and `ctranslate2`.
- FFmpeg/FFprobe are used for duration probing, conversion to WAV, and chunking.
- Model loading uses `WhisperModel(..., device="auto")`.
- Compute fallback order is requested compute type, then `int8`, then `float32`.
- Model cache key is model name plus requested compute type.
- The app logs actual compute and device when a model loads.
- Dev validation showed `tiny` with requested `int8`, used `int8`, device `cuda`.
- Normal UI defaults are documented as `medium` and `float32`.
- UI choices include `medium` and `small`; `large-v3` is documented as removed from normal mode.
- Language choices are `auto`, `ru`, and `en`.
- Default chunk length is 5 minutes.
- Default overlap is 0 seconds.
- Default beam is 1.
- VAD is optional.

Supported upload extensions from the UI:

```text
.m4a, .mp3, .wav, .flac, .ogg, .mp4, .mkv, .mov, .avi, .webm
```

TODO:

- Document production model cache size expectations.
- Document production GPU memory behavior for `medium` and `float32`.
- Document maximum practical file size/duration after measured validation.

## Storage And Artifacts

Production environment:

```text
WHISPER_OUTPUT_DIR=/app/outputs
WHISPER_JOBS_DIR=/app/data/jobs
WHISPER_CONTEXTS_PATH=/app/contexts.json
WHISPER_RETENTION_MAX_JOBS=20
HF_HOME=/app/hf_cache
HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
```

Production host paths:

```text
/home/grigorynokhrin/myservices/whisper/outputs
/home/grigorynokhrin/myservices/whisper/data
/home/grigorynokhrin/myservices/whisper/hf_cache
```

Expected ownership:

```text
grigorynokhrin:docker
```

Runtime user:

```text
uid=1000
gid=990
```

Retention:

- production retention max is documented as 20 jobs
- dev retention max is documented as 5 jobs
- retention runs after terminal job states
- terminal statuses considered by code are `done`, `error`, and `deleted`
- cleanup must not remove running jobs

Single-file artifacts:

- final TXT
- final SRT
- chunk TXT files
- normalized WAV
- chunk WAV files
- `intermediate.jsonl`
- `job.json`
- `job.log`

Batch artifacts:

- one combined TXT artifact
- no combined SRT in batch v1
- per-input status in `input_files`

## Configuration

Stable production compose:

```text
/home/grigorynokhrin/myservices/compose.yaml
```

Stable compose service/container:

```text
service: whisper
container: myservices-whisper
network: myservices_default
```

Stable route environment:

```text
WHISPER_ROOT_PATH=/myservices/whisper
```

Dev compose:

```text
compose/whisper-dev.compose.yml
```

Dev environment:

```text
WHISPER_ROOT_PATH=/whisper-dev
WHISPER_OUTPUT_DIR=/app/outputs
WHISPER_JOBS_DIR=/app/data/jobs
WHISPER_CONTEXTS_PATH=/app/contexts.json
WHISPER_RETENTION_MAX_JOBS=5
HF_HOME=/app/hf_cache
HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
```

Dev compose also declares:

- `127.0.0.1:18080:8000`
- `gpus: all`
- `restart: unless-stopped`

## Integration Points

Home/MyServices:

- stable user-facing entry
- route `/myservices/`
- should publish stable tools only
- currently includes Whisper and FFmpeg

Gateway/Caddy:

- routes `/myservices/whisper*` to `whisper:8000`
- tracked reference lives at `gateway/myservices/Caddyfile.current`
- live Caddyfile lives under `/home/grigorynokhrin/myservices/caddy/Caddyfile`
- Gateway changes require explicit approval

Docker Compose:

- production compose is owned by the legacy runtime under `/home/grigorynokhrin/myservices`
- dev compose is tracked under `compose/whisper-dev.compose.yml`

FFmpeg:

- Whisper uses FFmpeg internally to convert uploaded audio/video to 16 kHz mono WAV and split chunks.
- Broader FFmpeg media conversion workflows belong to FFmpeg docs, not this runbook.

## Operational Risks

- Server validation requires commit/push/pull first.
- Detached HEAD or stale branch state can invalidate runtime testing.
- Readiness race after restart can produce misleading failures.
- Home publishes stable tools only.
- Gateway/Caddy changes require explicit approval.
- Home changes may require rebuild.
- Root-owned data directories can break runtime writes.
- SSD space matters because uploaded media, normalized WAV, chunks, outputs, and model caches can be large.
- GPU/VRAM behavior must be verified from logs and runtime evidence, not assumed.
- Heavy production/dev/candidate tests should not run in parallel on the RTX 3060 12GB.
- Do not store generated audio, transcripts, model caches, or job data in Git.
- Do not replace `/myservices/whisper` without explicit approval and a migration plan.

## Known Failure Modes

### Service Unavailable

Symptom:

- `/myservices/whisper/healthz` does not return `ok`
- Home link or job pages fail

Likely causes:

- `myservices-whisper` stopped
- Caddy route/upstream issue
- production compose state changed

Inspect:

- container status for `myservices-whisper`
- production compose status under `/home/grigorynokhrin/myservices`
- Caddy route reference and live Caddyfile
- container logs

Resolution:

- restart only `whisper` if service is stopped and the task permits restart
- do not restart Caddy unless explicitly approved

### Model Load Failure

Symptom:

- job fails during model loading
- logs contain `[WHISPER_MODEL_FAIL]`

Likely causes:

- unsupported compute type for runtime
- GPU/CUDA/runtime issue
- model cache/download issue
- insufficient GPU memory

Inspect:

- container logs
- `job.log`
- `job.json`
- Hugging Face cache path
- current GPU usage

Resolution:

- verify compute fallback behavior
- retry with a documented smaller/cheaper model or compute setting only as an explicit validation step
- avoid parallel heavy tests

### Transcription Failure

Symptom:

- job reaches `error`
- TXT/SRT artifacts are missing
- status page shows an error

Likely causes:

- invalid input
- FFmpeg conversion failure
- no chunks produced after splitting
- model inference failure

Inspect:

- `job.json`
- `job.log`
- source file size
- `intermediate.jsonl`
- chunk files

Resolution:

- validate input file is non-empty and readable
- check FFmpeg conversion/chunking stages
- preserve evidence before cleanup

### Upload Or Storage Permission Failure

Symptom:

- upload fails
- job directory cannot be written
- artifacts are missing
- generated files are root-owned or unwritable

Likely causes:

- host directory ownership drift
- bind mount permission mismatch
- runtime user cannot write as uid `1000`, gid `990`

Inspect:

- `/home/grigorynokhrin/myservices/whisper/outputs`
- `/home/grigorynokhrin/myservices/whisper/data`
- `/home/grigorynokhrin/myservices/whisper/hf_cache`
- file ownership under job directories

Resolution:

- restore expected ownership to `grigorynokhrin:docker`
- verify uid `1000`, gid `990` can write before replacing production

### Timeout Or Large File Handling

Symptom:

- long-running job appears stalled
- large file consumes unexpected disk
- chunking/transcription takes longer than expected

Likely causes:

- long input duration
- expensive model/compute choice
- chunk settings
- GPU contention
- SSD pressure

Inspect:

- `job.log`
- `progress_current` and `progress_total`
- disk usage under Whisper data/output/cache directories
- GPU utilization

Resolution:

- capture stage-level evidence before interrupting
- avoid parallel heavy tests
- use measured validation instead of guessing latency

### Route Or Proxy Mismatch

Symptom:

- generated links point to the wrong prefix
- redirect location is wrong
- UI renders absolute localhost URLs unexpectedly

Likely causes:

- incorrect `WHISPER_ROOT_PATH`
- stale template route hardcode
- proxy/root path mismatch

Inspect:

- rendered form action
- redirect location after submit
- artifact links
- production environment

Expected stable values:

- form action starts with `/myservices/whisper/submit`
- submit redirects to `/myservices/whisper/jobs/<job-id>`
- artifact links use `/myservices/whisper/jobs/.../artifacts/...`

## Rollback / Disable Strategy

Rollback is an explicit operator action only.

Known rollback images:

```text
myservices-whisper:rollback-20260603-093727
myservices-whisper:rollback-20260603-133700
```

Documented rollback reference:

```text
cd /home/grigorynokhrin/myservices
docker compose stop whisper
docker tag myservices-whisper:rollback-20260603-133700 myservices-whisper
docker compose up -d --no-build whisper
curl -fsS http://127.0.0.1/myservices/whisper/healthz
```

Permission rollback/reference backups:

```text
/home/grigorynokhrin/myservices/backups/whisper-permissions-20260603-093428
/home/grigorynokhrin/myservices/backups/whisper-promote-20260603-093625
/home/grigorynokhrin/myservices/backups/whisper-release-20260603-093727
/home/grigorynokhrin/myservices/backups/whisper-batch-v1-20260603-133700
```

Disable strategy:

- TODO: no stable disable playbook is documented.
- If disabling user access is required, Home link and Caddy route changes must be handled as separate approved Gateway/Home tasks.
- Do not remove production data directories as part of a disable action unless an explicit cleanup task says so.

## Dependencies

Documented dependencies:

- Docker
- Docker Compose
- Caddy/Gateway
- Home/MyServices
- Python
- FastAPI
- Uvicorn
- FFmpeg/FFprobe
- `faster-whisper`
- `ctranslate2`
- Hugging Face model cache
- NVIDIA CUDA runtime base image
- GPU access for dev compose via `gpus: all`; production GPU configuration is TODO unless confirmed from production compose

TODO:

- Capture exact production Docker image tag after next production validation.
- Capture exact production GPU compose configuration from `/home/grigorynokhrin/myservices/compose.yaml` during an approved server inspection.

## Documentation Links

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/WHISPER_RELEASE_MODEL.md`
- `docs/RELEASES.md`
- future `docs/services/whisper.md` TODO

## Known Gaps

- Exact stable direct host port is not documented.
- Exact production compose contents are not tracked in this repo.
- Exact stable production GPU compose configuration is not documented.
- Exact production image tag/current build ID should be captured in future release notes.
- Exact production server checkout/worktree path for routine deployment should be documented.
- Stable readiness loop should be formalized.
- Stable `docker logs` command and expected log excerpts should be documented.
- Maximum practical file size/duration is not documented.
- Production model cache sizing expectations are not documented.
- Stable disable strategy is not documented.
- `docs/services/whisper.md` is missing.
- Structured Whisper release notes under `docs/releases/` are missing.
- Structured Whisper validation reports under `docs/validations/` are missing.
