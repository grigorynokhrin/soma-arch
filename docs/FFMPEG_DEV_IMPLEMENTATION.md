# FFMPEG_DEV_IMPLEMENTATION

This document records the initial `soma-ffmpeg-dev` skeleton.

## Status

Initial repository skeleton:

    services/ffmpeg-dev/
    compose/ffmpeg-dev.compose.yml

This is dev-only. It does not modify Home, Whisper, production Compose, `/srv/soma`, or `/home/grigorynokhrin/myservices`.

## Purpose

`soma-ffmpeg-dev` is a standalone FastAPI web service for FFmpeg workflows.

It is intentionally separate from:

    soma-whisper-dev
    myservices-whisper
    myservices-home

Do not combine FFmpeg with Whisper or Home.

## Resource Policy

`soma-ffmpeg-dev` v1 is intentionally CPU-only. Do not add GPU access to `compose/ffmpeg-dev.compose.yml` in v1.

FFmpeg does not automatically use NVIDIA GPU, CUDA, or NVENC because the host has an RTX 3060. NVIDIA video acceleration requires explicit NVENC/NVDEC hardware paths and compatible codecs; it is not automatic CUDA-core execution.

Current workflow expectations:

- MP4 remux uses stream copy and is mostly I/O/container-bound.
- device profiles target MPEG-2/VOB and MPEG-4 Part 2/Xvid-style AVI.
- those legacy/device encode targets are CPU encode targets in v1.

Future hardware-accelerated profiles should be explicit profile additions. Primary candidates are H.264/H.265 via NVENC. AV1 NVENC is only valid if the actual GPU supports AV1 encode. VP8/VP9 should not be documented as NVENC encode targets; they may be relevant for hardware decode via NVDEC.

## Routes

The app uses:

    FFMPEG_ROOT_PATH=/ffmpeg-dev

FastAPI routes are defined without hardcoding `/ffmpeg-dev`:

    GET  /
    GET  /healthz
    POST /remux/probe
    POST /remux/run
    POST /convert/run
    GET  /job/status.json
    GET  /job/result
    GET  /download/{artifact_name}

Future production route, if promoted later:

    /myservices/ffmpeg

That route is not added in this skeleton.

## Caddy Dev Route

The repo reference Caddyfile includes a dev route:

    handle /ffmpeg-dev* {
        reverse_proxy soma-ffmpeg-dev:8000
    }

The FFmpeg dev compose file persists membership in the external Docker network used by Caddy:

    compose_default

The service keeps its normal project network and also joins that external Caddy/dev network with alias:

    soma-ffmpeg-dev

The `/myservices/` home page button/link is not tracked in this repo. Adding a visible home-page entry for FFmpeg is a separate legacy-home task.

## Runtime Data Layout

Dev runtime data is expected at:

    /srv/soma/data/ffmpeg-dev

Container path:

    /data

Current-job layout:

    /data/current/
      job.json
      status.json
      probe.json
      job.log
      input/
      tmp/
      output/

Only the last job is kept. Starting a new remux probe or conversion run clears `/data/current`.

Exception:

    POST /remux/run

uses the already probed current file and does not clear it again.

## MP4 Remux Mode

The upper UI block handles one-file MP4 remux.

Flow:

1. Upload exactly one video file.
2. Run `ffprobe`.
3. Display video, audio, subtitle, and chapter information.
4. Select audio streams to keep.
5. Select one kept audio stream as default.
6. Select subtitle streams to keep.
7. Set output filename.
8. Set allowlisted metadata fields.
9. Run FFmpeg with stream copy.

Remux command policy:

    keep first video stream
    map selected audio streams
    map selected subtitle streams
    -c copy
    -map_chapters 0
    -map_metadata -1 for old global/container metadata
    allowlisted user-entered -metadata fields only
    -movflags use_metadata_tags
    convert MP4-incompatible text subtitles to mov_text
    reject image subtitles before FFmpeg
    exactly one selected default audio stream when requested

Remux mode does not transcode video or audio. It preserves chapters/parts, wipes old global/container metadata, and writes only user-entered allowlisted global metadata:

    title
    artist
    date
    genre
    language
    description
    publisher

Selected audio/subtitle stream language and title/name tags are restored from probe data as much as MP4 supports. Text subtitles that MP4 cannot copy directly, including SubRip/SRT, ASS/SSA, and WebVTT, are converted to `mov_text`. Image subtitles such as DVD subtitles or PGS fail before FFmpeg because OCR is out of scope for v1. Per-stream metadata editing is not in v1: stream tags are not taken from the user-entered global metadata fields. MP4/player visibility of some global metadata fields is container/player-dependent.

If FFmpeg cannot mux a selected stream into MP4, the job fails and shows a concise stderr excerpt.

Subtitle limitation:

    Image subtitles cannot be converted to MP4 text subtitles without OCR; deselect this subtitle stream.

FFmpeg and FFprobe stdout/stderr are decoded with replacement characters for invalid UTF-8 bytes, so user-facing job errors should show the real FFmpeg failure rather than a Python `UnicodeDecodeError`.

## Profile Conversion Mode

The lower UI block handles one or more input files converted by one fixed profile.

Flow:

1. Upload one or more video files.
2. Select a predefined profile.
3. Convert each input to one output file.
4. Offer one download per output.

Conversion maps:

    first video stream
    all audio streams if present
    compatible subtitle streams only when safe
    chapters with -map_chapters 0
    metadata with -map_metadata 0

FFmpeg commands are generated from structured profile fields. There is no raw command input and no `shell=True`.

These v1 profiles are CPU encode profiles. They do not request NVENC, NVDEC, CUDA, or GPU device access.

Batch profile subtitle policy:

- video/audio profile settings are unchanged
- subtitles are not mapped blindly
- compatible subtitle streams are preserved only when safe for the target container
- text subtitles such as SubRip/SRT, ASS/SSA, WebVTT, and MOV text are burned into video for legacy AVI/VOB profiles
- unsupported image subtitles are dropped with a warning instead of failing the job

This differs from MP4 remux mode, where text subtitles are represented as MP4 `mov_text` subtitle streams when possible.

## Predefined Profiles

Profiles live in:

    services/ffmpeg-dev/profiles.json

Current profiles:

- `cowon-iaudio-d2-plus`
- `lacie-ss-4x3-vob-pal`
- `lacie-ss-16x9-vob-pal`
- `lacie-ss-16x9-avi`

### Cowon iAudio D2+

Output:

    AVI
    MPEG-4 Part 2 / Xvid-style
    320x240
    4:3
    MP3 stereo 128 kbps

### LaCie SS 4:3

Output:

    VOB-like MPEG-PS
    MPEG-2 video
    720x576
    4:3
    PAL 25 fps
    AC3 stereo 192 kbps

### LaCie SS 16:9 PAL

Output:

    VOB-like MPEG-PS
    MPEG-2 video
    720x576
    16:9 anamorphic PAL intent
    PAL 25 fps
    AC3 448 kbps

### LaCie SS 16:9

Output:

    AVI
    MPEG-4 Part 2 / Xvid-style
    1024x576
    16:9 square pixels
    PAL 25 fps
    AC3 448 kbps

## LaCie Bitrate Assumption

The original LaCie requirements did not specify exact video bitrates.

Implementation defaults:

    LaCie VOB profiles: 6000 kbps average, 9000 kbps max
    LaCie AVI profile: 2000 kbps average, 3000 kbps max

These should be adjusted after real device playback tests.

## Known Limitations

- dev-only skeleton; Caddy route is reference-only until the live Caddyfile is updated/reloaded
- one active job only
- only the last job is kept
- no database
- no profile editing or CRUD
- no authentication
- no explicit free-space preflight yet
- image subtitles are rejected in MP4 remux unless OCR support is added later
- VOB output is a VOB-like MPEG-PS file, not a full DVD folder structure
- profile conversion image subtitles are dropped with warning unless OCR support is added later

## Next Iteration TODO

- profile CRUD/editing
- explicit disk free-space check before accepting large jobs
- better stream compatibility warnings before MP4 remux
- device-tested LaCie bitrate tuning
- optional audio codec override for LaCie MP3 alternatives
- legacy-home `/myservices/` button/link task
