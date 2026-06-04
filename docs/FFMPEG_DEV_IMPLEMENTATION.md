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

Users can also clear the current job from the web UI:

    POST /job/clear

The clear action only removes the current FFmpeg dev job directory under `/data/current`.

Exception:

    POST /remux/run

uses the already probed current file and does not clear it again.

## Filename Policy

Output filenames preserve human-readable names where safe, including Unicode, spaces, parentheses, ampersand, comma, and dots inside the base name.

The app neutralizes only dangerous/path characters:

    slash
    backslash
    NUL/control characters
    path traversal markers
    empty names

The final extension is forced to the expected output extension:

    MP4 remux: .mp4
    batch profiles: profile extension

Download link text and `Content-Disposition` filename use the final artifact name.

## UI State

The index page shows the active remux form only when the current job is exactly `status=probed`.

Completed, failed, or conversion jobs can still appear in the current-job summary, but stale probe tables are not shown as an active remux form. If a user selects a new file while a probe result is visible, the UI marks the old probe as stale and asks the user to probe the new file.

Submit messages disable the clicked submit button and show a plain waiting message for probe, remux, and batch conversion. These are not true progress bars.

Warnings such as subtitle drop notices are rendered on the index current-job block and result/status pages.

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
10. Post-process player-compatible MP4 metadata with ExifTool when metadata fields are provided.

Remux command policy:

    keep first video stream
    map selected audio streams
    map selected subtitle streams
    -c copy
    -map_chapters 0
    -map_metadata -1 for old global/container metadata
    allowlisted user-entered basic -metadata fields only
    convert MP4-incompatible text subtitles to mov_text
    reject image subtitles before FFmpeg
    exactly one selected default audio stream when requested

After FFmpeg succeeds, the service runs metadata post-processing on the final MP4 artifact under `/data/current/output` only. No arbitrary ExifTool flags come from the user.

The metadata layer uses `exiftool -overwrite_original` to write best-effort player-compatible QuickTime/iTunes/UserData/Keys metadata aliases for the same user-entered fields. This preserves broad Apple/Finder/IINA/VLC-visible behavior where players support those fields.

ExifTool is always called with `-api LargeFileSupport=1`. Without that option, ExifTool can stop at large MP4 atoms with `End of processing at large atom (LargeFileSupport not enabled)` on multi-GB files.

The same ExifTool pass removes FFmpeg/libavformat Encoder tags such as `Lavf...` from known QuickTime-family locations.

Remux mode does not transcode video or audio. It preserves chapters/parts, wipes old global/container metadata, and writes only user-entered allowlisted global metadata:

    title
    artist
    date
    genre
    description

One UI field may be duplicated into several recognized MP4 tag families so common players have a better chance to display it. Exact display remains player-controlled. Metadata post-processing can take extra time on multi-GB MP4 files because the MP4 container may need to be rewritten.

The `description` field is written to Description and LongDescription-style tags. Comment-style aliases are intentionally skipped because some MP4 readers display UTF-8 comment aliases as mojibake.

Year-only `date` values such as `2002` are normalized to `2002:01:01 00:00:00` before writing `ItemList:ContentCreateDate`, because ExifTool rejects a bare year for that QuickTime date tag.

Publisher and global language are intentionally not supported in v1 because common MP4 players do not reliably persist or display them without custom tags. Audio/subtitle stream language metadata is preserved separately from global metadata.

Selected audio/subtitle stream language and title/name tags are restored from probe data as much as MP4 supports. Text subtitles that MP4 cannot copy directly, including SubRip/SRT, ASS/SSA, and WebVTT, are converted to `mov_text`. Image subtitles such as DVD subtitles or PGS fail before FFmpeg because OCR is out of scope for v1. Per-stream metadata editing is not in v1: stream tags are not taken from the user-entered global metadata fields.

If FFmpeg remux succeeds and metadata post-processing fails, the MP4 artifact is preserved and remains downloadable. The job status becomes `done_with_warnings`, and the metadata error is recorded in `warnings` instead of failing the job.

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

Batch conversion records the exact generated FFmpeg command in `job.json` / `status.json` under `ffmpeg_commands` before the process starts, and also writes it to `job.log`. This is the runtime source of truth for debugging server-side conversion behavior.

These v1 profiles are CPU encode profiles. They do not request NVENC, NVDEC, CUDA, or GPU device access.

Batch profile subtitle policy:

- video/audio profile settings are unchanged
- subtitles are not mapped blindly
- compatible subtitle streams are preserved only when safe for the target container
- subtitles are never burned into the video picture in batch conversion profiles
- subtitles that cannot be preserved in the target container are dropped with a warning instead of failing the job

Drop warning format:

    Subtitle stream #N codec X was dropped because profile Y does not support subtitle preservation.

This differs from MP4 remux mode, where text subtitles are represented as MP4 `mov_text` subtitle streams when possible. The remux mode subtitle behavior is separate from batch conversion.

## Predefined Profiles

Profiles live in:

    services/ffmpeg-dev/profiles.json

Current profiles:

- `cowon-iaudio-d2-plus`
- `lacie-ss-4x3-vob-pal`
- `lacie-ss-16x9-vob-pal`
- `lacie-ss-16x9-avi`

The UI labels include the output container for the legacy conversion profiles so the container choice is visible before conversion:

- `Cowon iAudio D2+ (AVI)`
- `LaCie SS 4:3 VOB PAL`
- `LaCie SS 16:9 VOB PAL`
- `LaCie SS 16:9 (AVI)`

### Cowon iAudio D2+

Output:

    AVI
    MPEG-4 Part 2 / Xvid-style
    320x240
    4:3
    MP3 stereo 128 kbps

Legacy-profile assumption: Cowon iAudio D2+ targets an AVI file because the device profile is MPEG-4 Part 2 / Xvid-style video with MP3 audio.

### LaCie SS 4:3

Output:

    VOB-like MPEG-PS
    MPEG-2 video
    720x576
    4:3
    PAL 25 fps
    AC3 stereo 192 kbps

PAL display policy:

    stored frame: 720x576
    display aspect ratio: 4:3
    square-pixel equivalent: 768x576
    16:9 square-pixel sources are center-cropped to 4:3 visible image, then scaled to 720x576 and signaled as 4:3 PAL
    no pad / no letterbox / no pillarbox

### LaCie SS 16:9 PAL

Output:

    VOB-like MPEG-PS
    MPEG-2 video
    720x576
    16:9 anamorphic PAL intent
    PAL 25 fps
    AC3 448 kbps

PAL display policy:

    stored frame: 720x576
    display aspect ratio: 16:9
    square-pixel equivalent: 1024x576
    16:9 square-pixel sources are scaled directly to stored 720x576 and signaled as 16:9 anamorphic PAL
    no pad / no letterbox / no pillarbox

### LaCie SS 16:9

Output:

    AVI
    MPEG-4 Part 2 / Xvid-style
    1024x576
    16:9 square pixels
    PAL 25 fps
    AC3 448 kbps

Legacy-profile assumption: LaCie SS 16:9 AVI targets an AVI file because this profile is MPEG-4 Part 2 / Xvid-style video at square-pixel 1024x576.

Root cause of the distorted PAL 16:9 VOB output was treating 720x576 as square-pixel geometry and using fit-with-pad behavior. PAL VOB 16:9 is anamorphic: 720x576 is storage size, while display geometry is carried by DAR/SAR signaling.

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
