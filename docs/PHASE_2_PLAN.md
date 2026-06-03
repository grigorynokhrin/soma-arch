# PHASE_2_PLAN

This document defines the practical Phase 2 direction after the Phase 1 platform baseline.

## Summary

Phase 1 is complete. The current safe baseline is:

- legacy/prod contour remains under `/home/grigorynokhrin/myservices`
- legacy Whisper remains available at `/myservices/whisper`
- dev/soma contour exists under `/srv/soma`
- `soma-whisper-dev` is running and validated
- shared job conventions are documented in `docs/JOB_SCHEMA.md`

Phase 2 is now focused on two small, bounded tracks:

1. fix `soma-whisper-dev` UI defaults
2. design and add a new `soma-ffmpeg-dev` service

## Current Phase 2 Priorities

### 1. soma-whisper-dev defaults fix

The next Whisper task should be a small implementation PR that changes only the dev Whisper UI/default behavior:

- default chunk length: `300` seconds / `5` minutes
- default chunk overlap: `0` seconds

This must apply only to `soma-whisper-dev`.

It must not modify:

- legacy Whisper
- `/myservices/whisper`
- Caddy
- `/home/grigorynokhrin/myservices`

### 2. soma-ffmpeg-dev service

The next new service direction is `soma-ffmpeg-dev`, a local/dev-first web UI and API around FFmpeg for:

- Blu-ray rip cleanup and remuxing
- stream inspection and stream selection
- device preset conversion
- structured manual conversion settings

The service must be CPU-first initially. NVENC/GPU acceleration is later only, after driver/CUDA/NVENC compatibility is verified.

## Not Current Phase 2 Priorities

These are explicitly not current Phase 2 priorities:

- Tesseract OCR
- SupIR
- a big generic portal UI
- production Whisper migration

They can be revisited later, but Phase 2 should stay small and useful.

## Work Order

Recommended order:

1. Create documentation/spec for `soma-ffmpeg-dev`.
2. Implement the small `soma-whisper-dev` defaults PR:
   - UI default chunk length becomes `5` minutes
   - UI default overlap becomes `0` seconds
3. Create a minimal `soma-ffmpeg-dev` skeleton in a separate PR.
4. Add `ffprobe` stream inspection.
5. Add stream selection/remux workflow.
6. Add device preset conversion workflow.
7. Add cleanup and retention behavior.
8. Add optional Caddy dev route `/ffmpeg-dev` later, only with explicit approval.

## Safety Rules

Phase 2 must preserve the Phase 1 safety boundary:

- no legacy modifications unless explicitly requested
- no changes to `/myservices/whisper`
- no Caddy recreation without explicit approval, backup, validation, and rollback notes
- no runtime changes in documentation-only PRs
- no generated media, model caches, datasets, or job data in Git
- large media files must stay under runtime data paths, not the repository
- the 480GB SSD is a hard practical constraint
- dev services should bind locally by default
- experimental services must not be exposed publicly by default

## Milestones And Acceptance Criteria

### Milestone 1: Phase 2 docs

Acceptance criteria:

- `docs/PHASE_2_PLAN.md` exists
- `docs/FFMPEG_DEV_SERVICE_SPEC.md` exists
- no service, compose, gateway, runtime, Caddy, or legacy files are changed
- `git diff --name-only` shows only the intended documentation files

### Milestone 2: Whisper dev defaults

Acceptance criteria:

- only `soma-whisper-dev` source/templates are changed
- default chunk length shown in the web UI is `5` minutes
- default overlap shown in the web UI is `0` seconds
- submit behavior still accepts the same structured form fields
- Python syntax check passes for `services/whisper-dev/app.py`
- `docker compose -f compose/whisper-dev.compose.yml config` passes
- dev health endpoint remains `ok` after runtime deployment
- legacy `/myservices/whisper/healthz` remains `ok`

### Milestone 3: FFmpeg skeleton

Acceptance criteria:

- new service source lives under `services/ffmpeg-dev/`
- compose file lives under `compose/ffmpeg-dev.compose.yml`
- runtime data is designed for `/srv/soma/data/ffmpeg-dev`
- service has `GET /ffmpeg-dev/healthz`
- service runs as non-root where practical
- service binds only to localhost in dev
- no Caddy route is added in the initial skeleton
- no legacy paths are modified
- UI has separate MP4 remux and batch profile-conversion blocks
- profile definitions live in structured JSON, not shell snippets

### Milestone 4: ffprobe inspection

Acceptance criteria:

- service can accept or select an input file according to the approved input model
- service runs `ffprobe` safely without shell command strings
- stream metadata is saved under the job directory
- UI displays video, audio, and subtitle streams
- status follows `docs/JOB_SCHEMA.md` where practical

### Milestone 5: Stream selection/remux

Acceptance criteria:

- user can select audio tracks to keep
- user can select subtitle tracks to keep
- user can choose an output container from an allowlist
- FFmpeg args are generated from validated structured options
- unwanted streams are dropped
- output is downloadable
- active jobs are not deleted by cleanup

### Milestone 6: Device presets

Acceptance criteria:

- service exposes initial reviewed presets
- preset requests define container, codecs, resolution, crop/scale mode, bitrate, fps, and stream policy
- 320x240 legacy-device draft preset exists after exact device requirements are confirmed
- output settings are visible before job submission
- GPU/NVENC remains out of scope unless explicitly promoted later

### Milestone 7: Cleanup and retention

Acceptance criteria:

- temporary files are deleted after terminal state where safe
- large outputs are deleted after download or TTL
- failed jobs keep only approved debug material
- logs/status can have separate retention from large files
- preflight disk checks account for the 480GB SSD constraint
- cleanup behavior is visible in the UI

## Recommended Next Codex Task

Recommended next task is one of:

- implement only the `soma-whisper-dev` UI defaults in a small code PR
- create the `soma-ffmpeg-dev` skeleton in a separate PR after this spec is reviewed

Do not combine Whisper defaults, FFmpeg skeleton, Caddy routing, and runtime deployment in one change.
