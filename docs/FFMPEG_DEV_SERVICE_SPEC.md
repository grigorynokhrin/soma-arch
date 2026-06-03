# FFMPEG_DEV_SERVICE_SPEC

This document specifies the proposed `soma-ffmpeg-dev` service for Phase 2.

## Purpose And Scope

`soma-ffmpeg-dev` is a local/dev-first web UI and API service around FFmpeg.

It should help with:

- inspecting media files with `ffprobe`
- cleaning Blu-ray rips by selecting streams and remuxing
- converting media for old or limited playback devices
- applying manual structured conversion settings safely

The service is designed for the real `soma` server:

- Ubuntu Server 24.04 minimal
- Intel Core i5-14600KF
- 32GB DDR4 RAM
- NVIDIA RTX 3060 12GB VRAM
- 480GB SSD

The first version is CPU-only. Do not add GPU access to Compose in v1.

FFmpeg does not automatically use NVIDIA GPU, CUDA, or NVENC just because the host has an RTX 3060. NVIDIA acceleration requires explicit NVENC/NVDEC hardware paths; it is not automatic CUDA-core execution.

V1 workload expectations:

- MP4 remux uses stream copy and is mostly I/O/container-bound.
- device profiles target MPEG-2/VOB and MPEG-4 Part 2/Xvid-style AVI.
- those legacy/device profile encodes are CPU encode targets in v1.

Future hardware-accelerated profiles should be explicit additions. Primary encode targets are H.264/H.265 via NVENC. AV1 NVENC is valid only if the actual GPU supports AV1 encode. VP8/VP9 should not be described as NVENC encode targets; they may be relevant for hardware decode via NVDEC.

## Non-Goals

The first version must not:

- expose the service as production/public
- modify legacy `/home/grigorynokhrin/myservices`
- modify legacy `/myservices/whisper`
- change Caddy in the initial skeleton
- recreate `myservices-caddy`
- provide a raw unrestricted FFmpeg shell command UI
- execute user-provided command fragments
- become a permanent media archive
- store large input/output media forever
- use GPU acceleration or NVENC by default
- add GPU access to Compose in v1

## User Stories

### Blu-ray rip cleanup/remux

As a user with a Blu-ray rip, I want to inspect all streams, keep only the audio and subtitle tracks I care about, choose an output container, and create a cleaned output file.

Expected flow:

1. User uploads or selects a video file.
2. Service runs `ffprobe`.
3. UI displays video, audio, subtitle, and attachment streams.
4. User chooses audio tracks to keep.
5. User chooses subtitle tracks to keep.
6. User chooses output container/settings.
7. Service drops unwanted streams and remuxes/copies selected streams when possible.
8. UI offers the output for download.
9. Temporary files and large outputs are cleaned after download or retention timeout.

### Device preset conversion

As a user with an old or limited playback device, I want to choose a preset that converts a movie to settings the device can actually play.

Example target:

- 320x240 / 240p
- crop/scale behavior that avoids black bars when needed
- bitrate, codec, fps, audio codec, and container compatible with the device

Expected flow:

1. User uploads or selects a video file.
2. User chooses a device preset.
3. UI shows the preset settings before submission.
4. Service applies structured preset settings.
5. Service creates a downloadable output.
6. Temporary files and large outputs are cleaned after download or retention timeout.

### Manual structured conversion

As a user, I want to manually configure common FFmpeg settings without typing raw command-line arguments.

Manual settings should include:

- output container
- video codec
- audio codec
- bitrate
- fps
- resolution
- crop/scale mode
- audio tracks to keep
- subtitle tracks to keep
- subtitle behavior: copy, burn-in later, drop, keep selected
- metadata handling
- output filename stem

Manual settings must be validated and converted into an FFmpeg args array by service code. The service must not be a raw shell command runner.

## Web UI Requirements

The web UI should support:

- one page with two independent workflow blocks and two independent submit buttons
- an upper MP4 remux block for exactly one file
- a lower batch conversion block for one or more files and one predefined profile
- upload file and/or select file from an approved server-side input folder
- probe streams before conversion
- display a stream table
- show video, audio, subtitle, attachment, and unknown streams distinctly
- select audio tracks to keep
- select subtitle tracks to keep
- select output container
- choose preset mode or manual mode
- show estimated disk impact where possible
- show warnings when output may be large
- show job progress/status
- show current lifecycle stage
- link to `status.json` for debugging
- download completed output
- expose cleanup behavior to the user

The UI should not include a raw FFmpeg command text box.

## API Endpoint Draft

Base route:

    /ffmpeg-dev

Initial endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/ffmpeg-dev/healthz` | Return `ok` when service is alive. |
| `POST` | `/ffmpeg-dev/jobs` | Create a probe/remux/convert job from structured request data. |
| `GET` | `/ffmpeg-dev/jobs/{job_id}` | Render job page or return job summary. |
| `GET` | `/ffmpeg-dev/jobs/{job_id}/status.json` | Return machine-readable job status. |
| `GET` | `/ffmpeg-dev/jobs/{job_id}/probe` | Return normalized probe metadata. |
| `GET` | `/ffmpeg-dev/jobs/{job_id}/download/{artifact}` | Download a completed artifact. |
| `POST` | `/ffmpeg-dev/jobs/{job_id}/cleanup` | Request cleanup for terminal job files. |

Optional future endpoint:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/ffmpeg-dev/presets` | Return available preset definitions. |

## Runtime Data Layout

Runtime data should live outside Git:

    /srv/soma/data/ffmpeg-dev/
      jobs/
        <job-id>/
          status.json
          job.json
          job.log
          input/
          output/
          tmp/
          probe.json
      cache/

Rules:

- `input/` holds uploaded or staged source files for the job.
- `output/` holds downloadable user-facing artifacts.
- `tmp/` holds intermediate FFmpeg files that may be deleted after terminal state.
- `probe.json` stores normalized stream metadata from `ffprobe`.
- large media files must not be committed to Git.
- active running jobs must not be deleted by retention.

## status.json Model

`status.json` should align with `docs/JOB_SCHEMA.md`.

Required fields:

- `schema_version`
- `service`
- `job_id`
- `status`
- `stage`
- `created_at`
- `updated_at`
- `artifacts`

Recommended fields:

- `started_at`
- `finished_at`
- `error`
- `input`
- `params`
- `metrics`
- `warnings`
- `links`

Recommended stable statuses:

- `queued`
- `running`
- `done`
- `failed`
- `canceled`

Recommended FFmpeg-specific stages:

- `created`
- `uploaded`
- `probing`
- `ready_for_settings`
- `queued`
- `remuxing`
- `converting`
- `postprocessing`
- `cleanup`
- `done`
- `failed`

## ffprobe Stream Metadata Model

The service should normalize `ffprobe` output into a stable model that the UI can render.

Recommended fields per stream:

- `index`
- `codec_type`
- `codec_name`
- `language`
- `title`
- `duration`
- `bitrate`
- `channels`
- `width`
- `height`
- `disposition`

`disposition` should preserve useful FFmpeg flags such as:

- `default`
- `forced`
- `hearing_impaired`
- `visual_impaired`
- `comment`
- `karaoke`

Missing metadata should be represented as `null` or an empty object, not guessed.

## Safe FFmpeg Command Generation

FFmpeg commands must be generated from structured, validated request objects.

Required model:

- structured request object
- allowlisted codecs
- allowlisted containers
- allowlisted filters
- allowlisted stream selection policies
- generated args array
- subprocess invocation with `shell=False`
- no raw command input
- no user-provided command fragments

Example command generation shape:

```json
{
  "mode": "remux",
  "input_artifact": "input/movie.mkv",
  "output_container": "mkv",
  "audio_streams": [1, 3],
  "subtitle_streams": [5],
  "video": {
    "codec": "copy"
  },
  "audio": {
    "codec": "copy"
  },
  "subtitles": {
    "behavior": "copy_selected"
  },
  "metadata": {
    "behavior": "manual_global_only"
  },
  "output_stem": "movie-clean"
}
```

The service code should turn this into an args list like:

```text
["ffmpeg", "-y", "-i", "...", "-map", "0:0", "-map", "0:1", "..."]
```

The UI may show a read-only preview of generated settings later, but not an editable raw command.

MP4 remux metadata policy:

- preserve selected video/audio/subtitle streams with stream copy
- preserve chapters/parts with `-map_chapters 0`
- do not copy old global/container metadata from source media
- do not merge old global/container metadata with new metadata
- write only manually entered allowlisted global metadata fields
- use `-movflags use_metadata_tags` for MP4 remux output
- restore selected audio/subtitle stream language and title/name tags from probe data as much as MP4 supports
- do not rewrite stream metadata from user global fields
- keep default audio disposition controlled by the UI

The fixed global metadata allowlist is:

- `title`
- `artist`
- `date`
- `genre`
- `language`
- `description`
- `publisher`

Chapters are not considered user metadata for this policy and must remain preserved. MP4/player visibility of some global metadata fields is container/player-dependent. Per-stream metadata editing is not in v1.

MP4 remux subtitle policy:

- video is stream-copied
- selected audio streams are stream-copied
- selected audio default disposition remains controlled by the UI
- MP4-compatible text subtitle streams can be copied
- MP4-incompatible text subtitle streams are converted to `mov_text`
- at minimum, `subrip`, `ass`, `ssa`, and `webvtt` inputs should become `mov_text` when needed
- selected subtitle language and title/name tags should be restored from probe data as much as MP4 supports
- image subtitles such as `dvd_subtitle` and `hdmv_pgs_subtitle` should fail before FFmpeg with a clear OCR-related message
- selected subtitles must not be silently dropped

FFmpeg and FFprobe log decoding should not crash on invalid UTF-8. Capture process output as bytes and decode with replacement, or otherwise configure decoding with `errors="replace"`, so failed jobs display the FFmpeg error rather than a Python `UnicodeDecodeError`.

## Allowlists

Initial container allowlist:

- `mkv`
- `mp4`
- `mov`
- `avi`

Initial video codec allowlist:

- `copy`
- `libx264`
- `libx265`
- `mpeg4`

Initial audio codec allowlist:

- `copy`
- `aac`
- `ac3`
- `mp3`

Initial subtitle behavior allowlist:

- `drop`
- `copy_selected`
- `keep_selected`
- `burn_in_later`

Initial crop/scale modes:

- `none`
- `fit_with_letterbox`
- `crop_to_fill`
- `stretch_exact`

`stretch_exact` should be available only with a clear warning because it distorts aspect ratio.

## Preset Model

Preset definitions should be structured data, not shell snippets.

Recommended fields:

- `name`
- `description`
- `container`
- `video_codec`
- `audio_codec`
- `resolution`
- `crop_scale_mode`
- `video_bitrate`
- `audio_bitrate`
- `fps`
- `stream_policy`
- `subtitle_policy`
- `metadata_policy`

Example:

```json
{
  "name": "mp4-h264-aac-compatible",
  "description": "Conservative MP4 output for broad playback compatibility.",
  "container": "mp4",
  "video_codec": "libx264",
  "audio_codec": "aac",
  "resolution": null,
  "crop_scale_mode": "none",
  "video_bitrate": null,
  "audio_bitrate": "160k",
  "fps": null,
  "stream_policy": "first_video_selected_audio",
  "subtitle_policy": "drop",
  "metadata_policy": "copy_safe"
}
```

## Example Presets

### remux-copy-selected-streams

Purpose:

- clean Blu-ray rips without re-encoding when streams are compatible

Settings:

- container: `mkv`
- video codec: `copy`
- audio codec: `copy`
- subtitles: `copy_selected`
- resolution: unchanged
- fps: unchanged
- stream policy: selected video/audio/subtitle streams only

### mp4-h264-aac-compatible

Purpose:

- create a broadly playable MP4

Settings:

- container: `mp4`
- video codec: `libx264`
- audio codec: `aac`
- subtitles: `drop` initially
- resolution: unchanged unless manually set
- fps: source fps unless manually set
- stream policy: first video plus selected or first audio

### 320x240-legacy-device-draft

Purpose:

- draft preset for an old or limited 320x240 device

Settings to confirm before implementation:

- container: unknown
- video codec: unknown
- audio codec: unknown
- resolution: `320x240`
- crop/scale mode: likely `crop_to_fill` or `fit_with_letterbox`
- video bitrate: unknown
- audio bitrate: unknown
- fps: unknown
- stream policy: first video plus one selected audio track
- subtitles: likely `drop` or future burn-in

Do not finalize this preset until the exact device constraints are known.

## Cleanup And Retention Rules

Cleanup must be part of the service design from the start.

Rules:

- delete `tmp/` after terminal state when no longer needed
- delete large output files after successful download or TTL
- do not delete active `queued` or `running` jobs
- keep logs/status separately from large files
- failed jobs may keep small logs/status for debugging
- failed jobs should not keep large temp files by default
- retention should be count-based, age-based, or both
- cleanup should preserve ownership expectations for `/srv/soma/data/ffmpeg-dev`

Possible defaults:

- keep newest terminal job metadata records
- delete large outputs after successful download or a short TTL
- keep failed logs/status for a short debugging window
- delete failed input/tmp media immediately unless the user explicitly opts to keep them

## Disk-Space Risk Handling

The 480GB SSD is a hard practical constraint. Blu-ray rips and converted outputs can be large enough to fill the disk quickly.

The service should:

- check free disk space before accepting large jobs
- provide a max upload/input size config
- reject jobs when free space is insufficient
- warn about large expected outputs
- avoid duplicate copies when possible
- stream uploads to disk instead of memory
- clean temporary files aggressively
- keep caches separate from job data
- expose current job size and output size when known

Recommended config variables:

- `FFMPEG_DATA_DIR=/srv/soma/data/ffmpeg-dev`
- `FFMPEG_MAX_INPUT_BYTES`
- `FFMPEG_MIN_FREE_BYTES`
- `FFMPEG_OUTPUT_TTL_SECONDS`
- `FFMPEG_RETENTION_MAX_JOBS`

## Security Constraints

The service must be local/dev-first and safe for a home server.

Required constraints:

- prevent path traversal
- normalize filenames safely
- never trust user-provided paths directly
- restrict server-side file selection to approved directories only
- do not expose the host filesystem broadly
- no arbitrary command execution
- no `shell=True`
- no raw command text box
- use allowlisted codecs, containers, filters, and presets
- run as non-root where practical
- bind only to localhost during dev
- avoid secrets in logs
- avoid writing to legacy paths
- keep generated files out of Git

## Initial Implementation Notes

Suggested repository layout:

    services/ffmpeg-dev/
    compose/ffmpeg-dev.compose.yml
    docs/FFMPEG_DEV_SERVICE_SPEC.md

Suggested runtime data root:

    /srv/soma/data/ffmpeg-dev

Suggested route:

    /ffmpeg-dev

The initial skeleton should not edit Caddy. A Caddy dev route for `/ffmpeg-dev` can be added later only with explicit approval and rollback notes.

Initial skeleton document:

    docs/FFMPEG_DEV_IMPLEMENTATION.md

## Open Questions

- Should input files be uploaded through the browser, selected from a server-side folder, or both?
- What should be the maximum input file size?
- Preferred output containers: `mkv`, `mp4`, `mov`, `avi`, other?
- Preferred video codecs: `copy`, `h264`, `h265`, `mpeg4`, other?
- Preferred audio codecs: `copy`, `aac`, `ac3`, `mp3`, other?
- Common subtitle formats: `srt`, `ass`, `pgs`, `vobsub`, embedded text?
- Should image-based Blu-ray subtitles be kept, dropped, or converted later?
- Which exact devices/presets are needed first?
- For 320x240 legacy device: required container, codecs, bitrate, fps, audio format?
- Should output be deleted immediately after successful download or after a short TTL?
- Should failed jobs keep input files for debugging or delete them immediately?
- Is authentication needed later?
