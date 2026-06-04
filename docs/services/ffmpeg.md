# FFmpeg Service Design

This is the canonical service design document for the stable FFmpeg service.

It describes what the service is, why it exists, how it is structured, what architectural decisions shape it, and where it can evolve. It is not an operations runbook. Operational procedures live in `docs/runbooks/ffmpeg.md`.

## Purpose

`ffmpeg` is the stable user-facing FFmpeg web tool for the `soma` home-server platform.

It supports daily media-maintenance tasks that are too specific for a generic upload form but too repetitive to do safely by hand on the command line:

- remuxing a single source file to MP4 while selecting audio/subtitle streams
- writing a small allowlisted set of MP4 metadata fields
- converting one or more files to legacy/device playback profiles
- preserving enough diagnostics to explain exactly what FFmpeg did

The service exists as a separate service because FFmpeg workflows are CPU, disk, file-format, and media-container concerns. They should not be mixed into Whisper, Home, or Gateway. Whisper consumes or produces text from audio; FFmpeg prepares, remuxes, or converts media files. They may be related in a broader media workflow, but they have separate runtime risks and service boundaries.

## Scope

The service does:

- browser-based MP4 remux
- stream inspection through `ffprobe`
- audio stream keep/default selection for remux
- subtitle stream selection for MP4 remux where supported
- structured batch conversion by predefined profiles
- legacy AVI/VOB conversion profiles
- PAL 16:9 and PAL 4:3 handling
- allowlisted MP4 metadata handling
- large MP4 metadata post-processing with ExifTool
- one-current-job status and artifact handling
- diagnostics through `status.json` and `job.log`

The service does not do:

- general video editing
- media library or asset management
- distributed/background transcoding farm behavior
- arbitrary FFmpeg command entry
- automatic subtitle burn-in for batch conversion profiles
- OCR for image subtitles
- GPU/NVENC acceleration in v1
- long-term media archival

## Users And Use Cases

Intended users are the home-server owner and trusted local users using Home/MyServices.

Core use cases:

- Open the stable FFmpeg tool from Home/MyServices and remux a movie into a cleaner MP4.
- Preserve chosen audio tracks and one default audio disposition.
- Preserve or convert MP4-compatible text subtitles in MP4 remux mode.
- Convert media for legacy devices using predefined, validated profile choices.
- Produce PAL 16:9 or PAL 4:3 outputs that display without distortion or added letterbox/pillarbox bars.
- Handle multi-GB MP4 files without losing a successful remux because metadata post-processing failed.
- Inspect `status.json` or `job.log` when a runtime result differs from expectations.

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
| Home publication | Published as `FFmpeg -> /ffmpeg/` |

Development service:

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
| Home publication | Not published on Home |

Home/MyServices publishes stable tools only. The stable FFmpeg entry should point to `/ffmpeg/`; the dev service must not replace it.

Gateway/Caddy routes Home and service prefixes. The tracked route reference is `gateway/myservices/Caddyfile.current`, but the live Caddyfile may differ. Operational Caddy work belongs in the FFmpeg runbook or future gateway runbook.

## Architecture Overview

Major components:

| Component | Evidence | Responsibility | Inputs / Outputs | Constraints |
| --- | --- | --- | --- | --- |
| Web/API layer | `services/ffmpeg/app.py`, templates | FastAPI routes, forms, status/result pages, downloads | Uploads, form fields, HTML, redirects, JSON status | Root-path aware; stable uses `/ffmpeg`, dev uses `/ffmpeg-dev`. |
| Job handling layer | `services/ffmpeg/app.py` | One current job under `/data/current` | `job.json`, `status.json`, `probe.json`, `job.log` | One active job is serialized by a process lock. |
| Upload handling | `remux_probe`, `convert_run` | Store uploaded input files under the current job input directory | Uploaded media to `/data/current/input` | Filenames are sanitized; generated media is outside Git. |
| Command construction | `services/ffmpeg/command_builder.py` | Build structured FFmpeg/ExifTool argument lists | Profiles, probe data, selected options to args arrays | No raw user FFmpeg args; no `shell=True`. |
| Probe/metadata extraction | `ffprobe_json`, `normalize_probe` | Inspect source streams and normalize stream metadata | Media input to stream/chapter/format data | Process output is decoded with replacement to avoid Unicode decode crashes. |
| MP4 metadata post-processing | `build_mp4_player_metadata_command` | Write player-compatible MP4 metadata aliases after remux | Final MP4 plus allowlisted metadata | Uses ExifTool with large-file support and path guard. |
| Artifact handling | `download`, result template | Expose only allowed completed artifacts | Output files to browser downloads | Download path must stay under output directory and match job artifacts. |
| Diagnostics | `public_status`, `append_log` | Preserve machine-readable status and human-readable command log | `status.json`, `job.log` | Actual runtime commands are visible for validation. |

The Docker image installs FFmpeg, ExifTool, and Python dependencies, then runs Uvicorn as a non-root app user.

## Data Flow

MP4 remux flow:

1. User opens `/ffmpeg/` from Home/MyServices or direct route.
2. User uploads exactly one video file in the MP4 remux block.
3. Service clears the current job and stores the upload under `/data/current/input`.
4. Service runs `ffprobe`, normalizes streams, and writes `probe.json`.
5. UI displays video, audio, subtitle, and chapter information.
6. User chooses audio streams, default audio stream, subtitle streams, output filename, and allowlisted metadata.
7. Service builds an FFmpeg remux command from structured options.
8. FFmpeg writes the output under `/data/current/output`.
9. ExifTool post-processes MP4 metadata where applicable.
10. `job.json`, `status.json`, and `job.log` capture status, warnings, artifacts, and diagnostics.
11. User downloads the artifact through `/ffmpeg/download/<artifact>`.

Batch conversion flow:

1. User uploads one or more videos in the batch conversion block.
2. User selects exactly one predefined profile.
3. Service clears the current job and stores all inputs under `/data/current/input`.
4. For each input, service probes media, builds a runtime conversion plan, records the actual FFmpeg command, and runs FFmpeg.
5. One output artifact is created per input file.
6. Unsupported subtitle streams are dropped with warnings unless the profile/container can safely preserve them.
7. Status, warnings, artifacts, and command diagnostics are recorded.

## Job Model

The current implementation uses one current job directory:

    /data/current/
      job.json
      status.json
      probe.json
      job.log
      input/
      tmp/
      output/

Observed statuses and stages include:

- `running`
- `probed`
- `done`
- `done_with_warnings`
- `failed`
- operation-specific stages such as `probing`, `remuxing`, `writing_metadata`, `converting`, and `running N/M`

Job rules:

- Starting a new remux probe clears the previous current job.
- Starting a new batch conversion clears the previous current job.
- Running a remux uses the already probed current input and does not clear it again.
- Successful artifacts are recorded in `artifacts`.
- Download is allowed only for recorded artifacts under the output directory.

Important warning semantics:

- Metadata failure after a successful remux is not a job failure.
- If FFmpeg produced the MP4, the artifact remains available.
- The job should become `done_with_warnings`, with the metadata problem recorded in `warnings`.

## Profile And Conversion Design

Profile definitions live in `services/ffmpeg/profiles.json`.

### MP4 Remux

Intent:

- Clean one source file into an MP4 without video/audio transcoding.

Important behavior:

- Maps the first video stream.
- Maps selected audio streams.
- Maps selected subtitle streams only when MP4-compatible or convertible to `mov_text`.
- Uses `-c copy` globally.
- Preserves chapters with `-map_chapters 0`.
- Wipes old global/container metadata with `-map_metadata -1`.
- Restores selected audio/subtitle stream language/title metadata from probe data.

Expected output:

- MP4 file with selected streams.
- Video/audio remain stream-copy.
- Text subtitles may become `mov_text`.

### Cowon iAudio D2+ AVI

Intent:

- Legacy 320x240 AVI output for Cowon iAudio D2+ style playback.

Expected output shape:

- AVI container
- MPEG-4 Part 2 video with XVID-style fourcc
- 320x240
- display aspect 4:3
- source FPS capped at 30
- MP3 stereo 128 kbps

### LaCie SS 4:3 VOB PAL

Intent:

- PAL VOB-like output for 4:3 legacy display.

Expected output shape:

- VOB container
- MPEG-2 video
- stored frame 720x576
- 25 fps
- display aspect ratio 4:3
- AC3 stereo 192 kbps

Design behavior:

- If the source visible aspect is wider than 4:3, crop sides to 4:3 before scaling.
- Scale to the PAL storage frame `720x576`.
- Signal/display DAR 4:3.
- Do not add padding or black bars by default.

### LaCie SS 16:9 VOB PAL

Intent:

- PAL anamorphic widescreen VOB-like output for 16:9 legacy display.

Expected output shape:

- VOB container
- MPEG-2 video
- stored frame 720x576
- 25 fps
- SAR observed in validation as `64:45`
- DAR 16:9
- AC3 stereo 448 kbps
- no subtitle stream when input subtitles cannot be preserved

Design behavior:

- For 16:9 source, do not crop.
- Scale to the PAL storage frame `720x576`.
- Signal/display DAR 16:9.
- Do not add padding or black bars by default.
- Do not treat `720x576` as square-pixel display geometry.

### LaCie SS 16:9 AVI

Intent:

- Square-pixel 16:9 AVI output for LaCie SS style playback.

Expected output shape:

- AVI container
- MPEG-4 Part 2 video with XVID-style fourcc
- 1024x576
- display aspect 16:9
- 25 fps
- AC3 stereo 448 kbps

## Subtitle Policy

Architectural decision: unsupported subtitles are dropped with warnings instead of being automatically burned into batch conversion output.

Rationale:

- Automatic burn-in changes the picture permanently.
- Burn-in can damage visual integrity, especially when the desired output is a device-compatible video with no added overlays.
- Dropping unsupported subtitles with a visible warning is safer than silently embedding text into the image.

Batch conversion policy:

- Subtitles are not mapped blindly.
- Compatible subtitle streams are preserved only when safe for the target container/profile.
- `xsub` can be preserved for AVI when safe.
- `dvd_subtitle` can be preserved for VOB when safe.
- Text subtitles such as `subrip`, `srt`, `ass`, `ssa`, `webvtt`, and `mov_text` are dropped for legacy AVI/VOB profiles with warnings when unsupported.
- Unsupported image subtitles are also dropped with warnings.

MP4 remux policy differs:

- MP4-compatible `mov_text` subtitles can be copied.
- Text subtitles such as SubRip/SRT, ASS/SSA, and WebVTT can be converted to `mov_text`.
- Image subtitles such as DVD subtitles or PGS are rejected before FFmpeg because OCR is out of scope.

## Metadata Policy

MP4 metadata is treated as useful but secondary to successful media processing.

Metadata design:

- User global metadata is allowlisted to `title`, `artist`, `date`, `genre`, and `description`.
- Old global/container metadata is not preserved in remux mode.
- Selected stream language/title metadata is restored from probe data where MP4 supports it.
- ExifTool writes best-effort QuickTime/iTunes/UserData/Keys-compatible aliases.
- Comment aliases are skipped because some MP4 readers display UTF-8 comment aliases as mojibake.
- FFmpeg/libavformat Encoder tags are removed from known QuickTime-family locations.
- Year-only dates are normalized before QuickTime date writes.
- Publisher and global language are not user-facing v1 fields because common MP4 players do not reliably persist/display them without custom tags.

Large file policy:

- ExifTool is called with `-api LargeFileSupport=1`.
- This avoids large-atom failures on multi-GB MP4 files.
- If ExifTool still fails after FFmpeg succeeds, the artifact is preserved and the job records a warning.

## Diagnostics Design

`status.json` is the machine-readable view of the current job.

It is used by:

- UI status/result views
- runtime validation
- debugging warnings/errors
- confirming service identity and artifacts

Expected contents include:

- schema version
- service
- job id
- mode
- status/stage
- timestamps
- error
- artifacts
- input files
- profile id
- warnings
- `ffmpeg_commands`

`job.log` is the human-readable runtime log.

It records:

- uploads
- probe/FFmpeg/ExifTool command lines
- warnings
- actual generated conversion command strings

The diagnostics exist because command construction can diverge from assumptions during runtime deployment. Recording the exact executed command prevents guessing which FFmpeg path actually ran on the server.

## Error And Warning Semantics

Fatal job failure:

- FFmpeg/FFprobe failure that prevents producing the requested media artifact.
- Unsafe path or unsupported selected MP4 image subtitle.
- Missing input or invalid profile.

Non-fatal warning:

- Media output exists and remains useful, but something secondary did not fully complete.

Metadata warning:

- FFmpeg remux succeeded.
- MP4 artifact exists.
- ExifTool metadata post-processing failed or skipped some field.
- Artifact remains downloadable.
- Job status becomes `done_with_warnings`.

Unsupported subtitle warning:

- Batch conversion profile/container cannot preserve the subtitle stream.
- Stream is dropped.
- Output video must not contain burned subtitles.
- Job can still complete.

## Storage And Runtime Artifacts

Known stable data root:

    /srv/soma/data/ffmpeg

Container data root:

    /data

Current job layout:

    /data/current/
      job.json
      status.json
      probe.json
      job.log
      input/
      tmp/
      output/

Known behavior:

- Only the last/current job is retained by the service model.
- Inputs are uploaded into `input/`.
- Outputs are written into `output/`.
- `job.log`, `job.json`, and `status.json` live under `/data/current`.
- Downloadable artifacts are only those recorded in the current job status.

TODO:

- Document the exact host path used for stable `job.log` after the next runtime validation report.

## Configuration

Stable compose file:

    compose/ffmpeg.compose.yml

Stable environment:

- `FFMPEG_ROOT_PATH=/ffmpeg`
- `FFMPEG_SERVICE_NAME=ffmpeg`
- `FFMPEG_SERVICE_TITLE=FFmpeg`
- `FFMPEG_DATA_DIR=/data`
- `TZ=America/Chicago`

Stable mount:

    /srv/soma/data/ffmpeg:/data

Dev compose file:

    compose/ffmpeg-dev.compose.yml

Dev environment:

- `FFMPEG_ROOT_PATH=/ffmpeg-dev`
- `FFMPEG_DATA_DIR=/data`

Both compose files attach to the external Caddy/dev network `compose_default` with service-specific aliases.

## Integration Points

Home/MyServices:

- Publishes stable FFmpeg as `FFmpeg -> /ffmpeg/`.
- Must not publish `ffmpeg-dev` as the primary user-facing entry.
- Home source is documented as outside this repo under `/home/grigorynokhrin/myservices/home`.

Gateway/Caddy:

- Routes `/ffmpeg*` to `soma-ffmpeg:8000`.
- Routes `/ffmpeg-dev*` to `soma-ffmpeg-dev:8000`.
- Route order matters: `/ffmpeg-dev*` must precede `/ffmpeg*`.
- Live Caddy is production-sensitive and may differ from the tracked reference.

Docker Compose:

- Stable and dev are separate compose projects, services, containers, images, ports, and data directories.

FFmpeg/FFprobe:

- FFprobe inspects streams and chapters.
- FFmpeg performs remux and conversion.
- Commands are built as argument lists, not shell strings.

ExifTool:

- Performs MP4 metadata post-processing.
- Requires LargeFileSupport for large MP4 files.

Future downstream services:

- FFmpeg can prepare media assets for later workflows, including Whisper-related media preparation, but no direct service coupling is documented.

## Constraints

Target machine:

- Ubuntu Server 24.04 minimal
- Intel Core i5-14600KF
- 32GB DDR4 RAM
- NVIDIA RTX 3060 12GB VRAM
- SSD 480GB

Design constraints:

- v1 is CPU-only.
- Do not assume NVIDIA GPU/CUDA/NVENC use unless a future profile explicitly requests it.
- Avoid heavy distributed transcoding assumptions.
- Avoid long-term retention of large media files.
- Keep generated media outside Git.
- Prefer localhost binds for services.
- Keep stable and dev isolated so experiments do not destabilize the Home-published service.

## Security And Safety Considerations

- Uploaded filenames are sanitized before use.
- Output filenames are sanitized and forced to expected extensions.
- Metadata keys are allowlisted.
- User input never becomes raw FFmpeg arguments.
- Subprocess commands are list arguments.
- Download route verifies the artifact name belongs to the current job and resolves under the output directory.
- Metadata post-processing is path-guarded to the output directory.
- Logs should not contain secrets; media filenames and command arguments can appear in `job.log`.
- Gateway/Home changes require explicit approval because they affect user-facing routing.

## Operational Boundaries

This document does not own deploy, restart, readiness, validation, rollback, or failure-mode procedures.

Use `docs/runbooks/ffmpeg.md` for:

- build/restart commands
- health checks
- Caddy validation
- runtime validation scenarios
- diagnostics inspection procedures
- rollback/disable steps
- known operational failure modes

## Design Decisions

| Decision | Rationale | Consequences |
| --- | --- | --- |
| Separate stable `ffmpeg` and experimental `ffmpeg-dev` services. | Stable Home-published usage needs isolation from v2 experiments. | Duplicate source trees/compose files must be reconciled during promotion. |
| Home publishes stable only. | Home is a user-facing portal; dev tools are for engineering validation. | Dev routes remain accessible but should not be the primary Home entry. |
| FFmpeg is separate from Whisper and Home. | Media conversion has different CPU/disk/format risks than transcription or portal UI. | Integration happens through routes/artifacts, not shared process boundaries. |
| Commands are built from structured profiles/options. | Raw command input would be unsafe and hard to validate. | New capabilities need profile/schema changes rather than free-form args. |
| Batch conversion drops unsupported subtitles with warnings. | Automatic burn-in can permanently damage visual output. | Users may lose subtitle streams in legacy outputs, but warnings make it explicit. |
| MP4 remux converts compatible text subtitles to `mov_text`. | MP4 cannot mux all source subtitle codecs directly. | Video/audio remain copy-only while text subtitles may be converted. |
| Metadata failure is non-fatal after successful remux. | The media artifact is more valuable than perfect metadata. | Jobs can complete as `done_with_warnings`. |
| `status.json` and `job.log` are first-class diagnostics. | Runtime command drift was difficult to debug by assumption. | Validation can compare actual executed commands and warnings. |
| PAL VOB profiles use display aspect ratio, not square-pixel assumptions. | PAL storage frame `720x576` is not the displayed shape. | Correct DAR/SAR signaling is part of profile validation. |
| v1 remains CPU-only. | Current profiles are stream-copy, MPEG-2, or MPEG-4 Part 2 targets; GPU paths need explicit design. | NVENC/NVDEC can be added later as explicit profiles. |

## Known Gaps

- Stable rollback image/tag strategy is not documented.
- Exact stable server checkout/worktree path for routine deployment is still TODO in the runbook.
- Exact host path for stable `job.log` should be captured after the next validation.
- Structured FFmpeg release notes under `docs/releases/` are missing.
- Structured FFmpeg validation reports under `docs/validations/` are missing.
- A dedicated Gateway runbook is missing.
- A dedicated Home runbook is missing.
- Dev-to-stable promotion after the first release still needs a later-release playbook.
- The stable and dev source trees are duplicated; the promotion/reconciliation model should stay explicit.

## Future Evolution

Practical future improvements:

- richer runtime validation reports for each profile
- clearer profile catalog and UI guidance
- explicit later-release playbook for stable FFmpeg updates
- Makefile or validation script integration
- structured service ADRs if media policy decisions grow
- hardware-accelerated profiles only when explicitly designed and validated
- clearer warning UX for dropped subtitles and metadata limitations
- eventual service design/runbook separation for Home and Gateway

## Related Documents

- `docs/runbooks/ffmpeg.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
