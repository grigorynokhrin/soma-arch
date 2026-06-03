# FFMPEG_DEV_IMPLEMENTATION

This document records the initial `soma-ffmpeg-dev` skeleton.

## Status

Initial repository skeleton:

    services/ffmpeg-dev/
    compose/ffmpeg-dev.compose.yml

This is dev-only. It does not modify Caddy, production Compose, `/srv/soma`, or `/home/grigorynokhrin/myservices`.

## Purpose

`soma-ffmpeg-dev` is a standalone FastAPI web service for FFmpeg workflows.

It is intentionally separate from:

    soma-whisper-dev
    myservices-whisper
    myservices-home

Do not combine FFmpeg with Whisper or Home.

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
    allowlisted -metadata fields only
    exactly one selected default audio stream when requested

Remux mode does not transcode. If FFmpeg cannot mux a selected stream into MP4, the job fails and shows a concise stderr excerpt.

Known limitation:

    MP4 subtitle compatibility depends on the source subtitle codec.

Image-based Blu-ray subtitles such as PGS may fail in MP4. The skeleton fails rather than silently degrading quality.

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
    subtitle streams if possible
    chapters with -map_chapters 0
    metadata with -map_metadata 0

FFmpeg commands are generated from structured profile fields. There is no raw command input and no `shell=True`.

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

- dev-only skeleton; no Caddy route is added
- one active job only
- only the last job is kept
- no database
- no profile editing or CRUD
- no authentication
- no explicit free-space preflight yet
- MP4 subtitle compatibility may fail for image-based subtitles
- VOB output is a VOB-like MPEG-PS file, not a full DVD folder structure
- profile conversion subtitle copy may fail depending on output container compatibility

## Next Iteration TODO

- profile CRUD/editing
- explicit disk free-space check before accepting large jobs
- better stream compatibility warnings before MP4 remux
- device-tested LaCie bitrate tuning
- optional audio codec override for LaCie MP3 alternatives
- route document for `/ffmpeg-dev` only after explicit Caddy approval
