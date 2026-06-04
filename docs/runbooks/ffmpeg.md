# FFmpeg Service Runbook

This is the canonical operational runbook for the stable FFmpeg service.

It consolidates evidence from FFmpeg docs, compose files, service source, gateway references, and validation notes. Architecture details should live in future `docs/services/ffmpeg.md`; this runbook stays focused on operations.

## Audit Sources

Audited locations:

- `docs/`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `services/ffmpeg/`
- `services/ffmpeg-dev/`
- `compose/ffmpeg.compose.yml`
- `compose/ffmpeg-dev.compose.yml`
- `gateway/myservices/Caddyfile.current`
- `runtime/`
- `docs/CURRENT_STATE.md`
- `docs/RUNTIME_STATUS.md`

No Markdown lint configuration or package script was found during this task.

## Purpose

`ffmpeg` is the stable user-facing FFmpeg web tool.

It exists to provide browser-based media workflows for:

- MP4 remux with stream selection and allowlisted metadata fields
- legacy/device profile conversion
- status and diagnostics for FFmpeg command execution

Intended users:

- the home-server owner and trusted local users using Home/MyServices

Dev vs stable:

- `ffmpeg-dev` is the experimental service for future v2 work.
- `ffmpeg` is the stable validated tool and the Home-published service.
- Home must not publish `ffmpeg-dev` as the primary user-facing entry.

## Service Topology

Stable service:

| Field | Value |
| --- | --- |
| Route | `/ffmpeg/` |
| Container | `soma-ffmpeg` |
| Image | `soma-ffmpeg:local` |
| Direct bind | `127.0.0.1:18083 -> 8000` |
| Compose file | `compose/ffmpeg.compose.yml` |
| Compose service | `ffmpeg` |
| Data directory | `/srv/soma/data/ffmpeg` |
| Service identity | `ffmpeg` |

Dev service:

| Field | Value |
| --- | --- |
| Route | `/ffmpeg-dev/` |
| Container | `soma-ffmpeg-dev` |
| Image | `soma-ffmpeg-dev:local` |
| Direct bind | `127.0.0.1:18082 -> 8000` |
| Compose file | `compose/ffmpeg-dev.compose.yml` |
| Compose service | `ffmpeg-dev` |
| Data directory | `/srv/soma/data/ffmpeg-dev` |
| Service identity | `ffmpeg-dev` |

Home relationship:

- Home/MyServices publishes stable tools only.
- The live Home entry is documented as `FFmpeg -> /ffmpeg/`.
- Home source is not tracked in this repo; it remains under `/home/grigorynokhrin/myservices/home`.

Gateway/Caddy relationship:

- Tracked route reference: `gateway/myservices/Caddyfile.current`.
- Live Caddyfile is documented as `/home/grigorynokhrin/myservices/caddy/Caddyfile`.
- Live Caddy may differ from the tracked reference; inspect mounts before live edits.

Tracked route order:

    handle /ffmpeg-dev* {
        reverse_proxy soma-ffmpeg-dev:8000
    }

    handle /ffmpeg* {
        reverse_proxy soma-ffmpeg:8000
    }

Keep `/ffmpeg-dev*` before `/ffmpeg*` so the stable prefix does not shadow the dev route.

## Repository Locations

Stable source:

    services/ffmpeg/

Dev source:

    services/ffmpeg-dev/

Stable compose:

    compose/ffmpeg.compose.yml

Dev compose:

    compose/ffmpeg-dev.compose.yml

Profiles:

    services/ffmpeg/profiles.json
    services/ffmpeg-dev/profiles.json

Command generation:

    services/ffmpeg/command_builder.py
    services/ffmpeg-dev/command_builder.py

Selfcheck:

    services/ffmpeg/selfcheck.py
    services/ffmpeg-dev/selfcheck.py

Gateway reference:

    gateway/myservices/Caddyfile.current

## Server Locations

Known stable paths:

    /srv/soma/data/ffmpeg

Known dev paths:

    /srv/soma/data/ffmpeg-dev

Known Caddy/Home runtime paths:

    /home/grigorynokhrin/myservices/caddy/Caddyfile
    /home/grigorynokhrin/myservices/home

TODO:

- Document whether the stable FFmpeg server checkout is `/home/grigorynokhrin/soma-arch`, `/srv/soma/worktrees/...`, or both for routine stable deployment.

## Operational Lifecycle

Use the general workflow in:

    docs/ENGINEERING_WORKFLOW.md

Use the first dev-to-stable playbook in:

    docs/FIRST_RELEASE_PLAYBOOK.md

Current lifecycle:

1. Develop and test experimental changes in `ffmpeg-dev`.
2. Validate direct bind and Caddy behavior for dev.
3. Promote the validated baseline into `ffmpeg`.
4. Keep `ffmpeg` stable while `ffmpeg-dev` remains available for experiments.

Do not copy broad workflow text here. This runbook records FFmpeg-specific operational facts.

## Deployment Expectations

Server validation is valid only after commit/push/pull. Do not validate server runtime from uncommitted Mac-only changes.

Required checks before build/restart:

    git status --short --branch
    git log --oneline -3
    git pull --ff-only
    git log --oneline -3

Stable data directory must exist and be writable before first run:

    /srv/soma/data/ffmpeg

Known first-run permission repair from the first-release playbook:

    sudo mkdir -p /srv/soma/data/ffmpeg
    sudo chown -R 1000:990 /srv/soma/data/ffmpeg
    sudo chmod -R u+rwX,g+rwX /srv/soma/data/ffmpeg

Stable build/restart commands documented in `docs/FFMPEG_SERVICE_RUNBOOK.md`:

    docker compose -f compose/ffmpeg.compose.yml build ffmpeg
    docker compose -f compose/ffmpeg.compose.yml up -d ffmpeg

Use `--no-cache` only when a task or playbook explicitly requires a clean image rebuild.

Do not run `docker compose down` from unrelated compose projects.

## Readiness

Do not curl immediately after restart or `up -d`.

Use a readiness loop against the direct health endpoint:

    for i in $(seq 1 30); do
      if curl -fsS http://127.0.0.1:18083/ffmpeg/healthz; then
        break
      fi
      sleep 2
    done

Immediate testing after restart is unsafe because Caddy can briefly return connection reset or 502 while the upstream process is still starting.

## Basic Health Checks

Direct stable health:

    curl -fsS http://127.0.0.1:18083/ffmpeg/healthz

Expected:

    ok

Caddy stable health:

    curl -fsS http://127.0.0.1/ffmpeg/healthz

Index smoke:

    curl -fsS http://127.0.0.1:18083/ffmpeg/ | grep -E 'action=|href=|FFmpeg'

Status endpoint after a job exists:

    curl -fsS http://127.0.0.1:18083/ffmpeg/job/status.json

Expected service identity:

    "service": "ffmpeg"

Dev health should remain separate:

    curl -fsS http://127.0.0.1:18082/ffmpeg-dev/healthz

## Runtime Validation Scenarios

### Scenario 1: Basic Conversion

Goal:

- Confirm the lower batch conversion workflow produces one output artifact per input file.

Input expectations:

- One or more small video files.
- One selected predefined profile.

Expected outputs:

- Job reaches `done` or `done_with_warnings`.
- One output artifact per input file.
- `/ffmpeg/job/status.json` includes warnings and `ffmpeg_commands` when relevant.

Success criteria:

- Output artifact downloads from `/ffmpeg/download/...`.
- No unrelated services are changed.

Known warnings:

- Unsupported subtitles may be dropped with a warning.

### Scenario 2: Large MP4 Metadata

Goal:

- Confirm MP4 remux and metadata post-processing are safe for multi-GB files.

Input expectations:

- Large MP4 or remuxable media file.
- Optional metadata fields.

Expected outputs:

- FFmpeg remux succeeds.
- ExifTool metadata post-processing uses `-api LargeFileSupport=1`.
- If metadata post-processing fails after FFmpeg succeeds, the MP4 remains downloadable.

Success criteria:

- Job status is `done` or `done_with_warnings`.
- Metadata failure does not delete or hide the artifact.
- Warning explains metadata post-processing failure if it occurs.

Known warnings:

- Metadata display remains player-dependent.
- Large MP4 metadata writes can take extra time because the container may be rewritten.

### Scenario 3: Legacy Conversion

Goal:

- Confirm AVI/VOB legacy profile conversions keep video/audio profile behavior and handle subtitles safely.

Input expectations:

- Video file with or without subtitle streams.
- One of the predefined legacy profiles.

Expected outputs:

- Video/audio codecs match the selected profile.
- Compatible subtitle streams are preserved only when safe.
- Unsupported subtitle streams are dropped with warning.

Success criteria:

- No `subtitles=` burn-in filter is used by default.
- Job finishes rather than failing only because unsupported subtitles exist.

Known warning format:

    Subtitle stream #N codec X was dropped because profile Y does not support subtitle preservation.

### Scenario 4: PAL 16:9

Goal:

- Confirm LaCie SS 16:9 VOB PAL output uses anamorphic PAL geometry without distortion.

Input expectations:

- 16:9 square-pixel source such as `1280x720`.
- Profile `lacie-ss-16x9-vob-pal`.

Expected outputs:

- MPEG-2/VOB-like output.
- `720x576` stored frame.
- `25 fps`.
- SAR `64:45`.
- DAR `16:9`.
- No subtitle stream when unsupported subtitles are dropped.

Success criteria:

- No visible horizontal or vertical distortion.
- No black bars added by the FFmpeg filter chain.
- No subtitle burn-in.
- For 16:9 source, runtime command should include `scale=720:576,setdar=16:9` and should not include `subtitles=`, `pad=`, or `crop=`.

Known warnings:

- Unsupported subtitles are dropped with warning.

### Scenario 5: PAL 4:3

Goal:

- Confirm LaCie SS 4:3 VOB PAL output uses 4:3 PAL display geometry without letterboxing.

Input expectations:

- Widescreen source when validating crop behavior.
- Profile `lacie-ss-4x3-vob-pal`.

Expected outputs:

- MPEG-2/VOB-like output.
- `720x576` stored frame.
- `25 fps`.
- DAR `4:3`.
- Center-crop 16:9 source to 4:3 visible image, then scale to `720x576`.

Success criteria:

- No pad/letterbox/pillarbox.
- No visible geometry distortion.
- No subtitle burn-in.

Known warnings:

- Unsupported subtitles are dropped with warning.

## Diagnostics

### status.json

Purpose:

- Machine-readable job status.
- Debugging source for status, stage, artifacts, warnings, and command records.

Expected fields include:

- `schema_version`
- `service`
- `job_id`
- `mode`
- `status`
- `stage`
- `artifacts`
- `input_files`
- `profile_id`
- `warnings`
- `ffmpeg_commands`

How to use:

- Check whether the running service identifies as `ffmpeg`.
- Check warnings for dropped subtitles or metadata post-processing issues.
- Check `ffmpeg_commands` for actual batch conversion command shape.

### job.log

Purpose:

- Human-readable job log for uploads, warnings, command execution, and diagnostics.

Known behavior:

- Batch conversion writes the generated FFmpeg command into `job.log`.
- FFmpeg/FFprobe stdout/stderr should be decoded with replacement so invalid UTF-8 does not hide the real FFmpeg error.

How to use:

- Inspect actual command execution when runtime behavior differs from expected behavior.
- Compare command shape against the validation scenario requirements.

TODO:

- Document the exact stable server path to `job.log` after the next server validation. The app stores current job data under the configured `/data/current` container path, backed by `/srv/soma/data/ffmpeg`.

## Known Operational Rules

### Large MP4 Metadata

- ExifTool must be called with `-api LargeFileSupport=1`.
- Without that option, ExifTool can fail with `End of processing at large atom (LargeFileSupport not enabled)`.
- Metadata post-processing must not destroy or hide a successful remux.
- If FFmpeg created the output MP4 and ExifTool fails, the artifact remains in `artifacts`, job status becomes `done_with_warnings`, and the warning is shown.
- Year-only dates such as `2002` are normalized to `2002:01:01 00:00:00`.
- Comment-style aliases are skipped because some MP4 readers display UTF-8 comment aliases as mojibake.
- FFmpeg/libavformat Encoder tags such as `Lavf...` are removed from known QuickTime-family locations.

### Subtitle Handling

MP4 remux:

- Video is stream-copied.
- Selected audio streams are stream-copied.
- Text subtitles that MP4 cannot copy directly become `mov_text`.
- Image subtitles such as DVD or PGS are rejected before FFmpeg because OCR is out of scope.
- Selected audio/subtitle stream language and title/name tags are restored from probe data as much as MP4 supports.

Legacy AVI/VOB conversion:

- Do not blindly map every subtitle stream.
- Preserve compatible subtitle streams only when safe for the target container.
- `xsub` may be copied for AVI profiles when safe.
- `dvd_subtitle` may be copied for VOB profiles when safe.
- Unsupported subtitles are dropped with warning.
- Subtitles must not be burned into video automatically.

### PAL Handling

LaCie SS 16:9 VOB PAL:

- Stored frame: `720x576`.
- Frame rate: `25 fps`.
- Display aspect: `16:9`.
- Expected SAR from validation: `64:45`.
- 16:9 square-pixel sources are scaled directly to stored `720x576`.
- No crop, pad, letterbox, or pillarbox for 16:9 source.

LaCie SS 4:3 VOB PAL:

- Stored frame: `720x576`.
- Frame rate: `25 fps`.
- Display aspect: `4:3`.
- 16:9 square-pixel sources are center-cropped to 4:3 visible geometry, then scaled to stored `720x576`.
- No pad, letterbox, or pillarbox.

Root cause of the previous distorted PAL 16:9 output:

- Treating `720x576` as square-pixel display geometry and using fit-with-pad behavior. PAL VOB 16:9 is anamorphic: `720x576` is storage size; DAR/SAR carry display geometry.

## Known Failure Modes

| Symptom | Cause | Resolution |
| --- | --- | --- |
| Server runtime does not show a new field or behavior such as `ffmpeg_commands` | Server built old code or did not pull the commit | Check server branch/status/log, `git pull --ff-only`, rebuild, restart, readiness wait, retest |
| Server checkout says detached HEAD | Worktree/checkouts not on intended branch | Switch or recreate the server worktree on the correct branch before validation |
| False 502 or connection reset after restart | Readiness race | Use healthcheck loop before Caddy/Home validation |
| Upload or job write fails with permission errors | Root-owned `/srv/soma/data/ffmpeg` or dev data dir | Fix ownership/permissions for only the target data directory |
| Caddy route works in tracked file but not live | Edited repo reference but not live mounted Caddyfile | Inspect `myservices-caddy` mounts, edit the real mounted Caddyfile only when approved, validate and reload Caddy |
| Home still points to old route | Home source changed but image not rebuilt or service not restarted | Rebuild/restart Home when approved, wait for readiness, verify rendered HTML |
| Subtitles appear burned into legacy output | Old runtime command path or stale image | Inspect `status.json`, `ffmpeg_commands`, and `job.log`; confirm command has no `subtitles=` filter; rebuild current commit |
| PAL 16:9 output distorted or has black bars | Old pad/fit behavior or stale image | Confirm runtime command uses `scale=720:576,setdar=16:9`; rebuild current commit |
| FFmpeg failure appears as Python `UnicodeDecodeError` | Process log decoding regressed | Decode FFmpeg/FFprobe output with replacement and surface real stderr excerpt |

## Rollback / Disable

Documented disable path for stable FFmpeg:

    docker compose -f compose/ffmpeg.compose.yml down

This stops `soma-ffmpeg` but should not affect `soma-ffmpeg-dev`, Whisper, Caddy, Home, OCR, or legacy production compose.

If the Caddy `/ffmpeg*` route was added separately, remove or comment only that route block and reload Caddy according to the approved Caddy change plan.

Do not remove `/srv/soma/data/ffmpeg` unless a separate cleanup task explicitly asks for it.

TODO:

- No rollback image tag for stable FFmpeg is documented in the audited repo docs.
- Document a stable FFmpeg rollback image/tag strategy before the next stable release.

## Dependencies

Runtime dependencies discovered from service/compose/docs:

- Docker and Docker Compose.
- FFmpeg binary in the service image.
- FFprobe binary in the service image.
- ExifTool via `libimage-exiftool-perl`.
- FastAPI app served by Uvicorn.
- Caddy/gateway for `/ffmpeg/`.
- Home/MyServices for user-facing navigation.
- `/srv/soma/data/ffmpeg` writable by the container user.

Operational dependencies:

- Commit/push/pull discipline from `docs/ENGINEERING_WORKFLOW.md`.
- First-release discipline from `docs/FIRST_RELEASE_PLAYBOOK.md`.
- Service inventory from `docs/SERVICES_REGISTRY.md`.

## Documentation Links

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
- `compose/ffmpeg.compose.yml`
- `compose/ffmpeg-dev.compose.yml`
- `gateway/myservices/Caddyfile.current`

## Known Gaps

- No dedicated `docs/services/ffmpeg.md` service design doc exists yet.
- Stable FFmpeg rollback image/tag strategy is not documented.
- Exact stable server checkout/worktree path for routine FFmpeg deployment is TODO.
- Exact host path for stable `job.log` should be documented after next validation.
- Home live source and rebuild commands are documented only at a high level; Home needs its own runbook.
- Gateway live-edit/reload procedure should move into `docs/runbooks/gateway.md`.
- Structured release notes under `docs/releases/` and validation reports under `docs/validations/` do not exist yet.
