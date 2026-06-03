# FFMPEG_DEV_ROLLOUT_RUNBOOK

This runbook validates `soma-ffmpeg-dev` as a dev-only service on the server.

It must not change Home, Whisper, production Compose, or legacy `/home/grigorynokhrin/myservices` behavior. Initial validation can use the direct localhost bind:

    http://127.0.0.1:18082/ffmpeg-dev/healthz
    http://127.0.0.1:18082/ffmpeg-dev/

After Caddy is reloaded with the repo route reference, `/ffmpeg-dev` is also available through Caddy:

    http://127.0.0.1/ffmpeg-dev/healthz
    http://127.0.0.1/ffmpeg-dev/

## Compose Safety

The dev compose file has an explicit project name:

    name: soma-ffmpeg-dev

Expected service and container:

    service: ffmpeg-dev
    container: soma-ffmpeg-dev

These names are intentionally separate from:

    myservices-caddy
    myservices-home
    myservices-whisper
    soma-whisper-dev

The build context is relative to the compose file:

    ../services/ffmpeg-dev

This works from a normal checkout or from a server worktree, as long as commands are run from the worktree repo root.

The service also joins the external Docker network used by Caddy:

    compose_default

The external-network alias is:

    soma-ffmpeg-dev

This lets `myservices-caddy` resolve `soma-ffmpeg-dev:8000` for the `/ffmpeg-dev` route.

## Server Worktree Setup

Do not switch `/home/grigorynokhrin/soma-arch` to a feature branch.

Use a separate worktree path for feature validation:

    mkdir -p /srv/soma/worktrees
    cd /home/grigorynokhrin/soma-arch
    git fetch --all --prune
    git worktree add /srv/soma/worktrees/ffmpeg-dev <ffmpeg-feature-branch>

To update an existing worktree:

    cd /srv/soma/worktrees/ffmpeg-dev
    git fetch --all --prune
    git status --short --branch
    git pull --ff-only

## Data Directory

Create the dev data directory before starting the service:

    mkdir -p /srv/soma/data/ffmpeg-dev
    sudo chown grigorynokhrin:docker /srv/soma/data/ffmpeg-dev
    chmod 775 /srv/soma/data/ffmpeg-dev

The container runs as:

    uid=1000
    gid=990

Verify write permissions before rollout if ownership has drifted.

## Build And Start

Run from the FFmpeg worktree repo root:

    cd /srv/soma/worktrees/ffmpeg-dev
    docker compose -f compose/ffmpeg-dev.compose.yml build ffmpeg-dev
    docker compose -f compose/ffmpeg-dev.compose.yml up -d ffmpeg-dev

Check that only the FFmpeg dev container was started:

    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'

Expected direct bind:

    127.0.0.1:18082->8000/tcp

## Smoke Checks

Check health:

    curl -fsS http://127.0.0.1:18082/ffmpeg-dev/healthz

Expected:

    ok

Check the page renders:

    curl -fsS http://127.0.0.1:18082/ffmpeg-dev/ | head

The response should be HTML for the FFmpeg dev page.

## Caddy Route

The live Caddy route should mirror:

    gateway/myservices/Caddyfile.current

Expected route block:

    handle /ffmpeg-dev* {
        reverse_proxy soma-ffmpeg-dev:8000
    }

This route should be placed near `/whisper-dev*` and before the `/myservices*` catch-all.

After reloading Caddy, check:

    curl -fsS http://127.0.0.1/ffmpeg-dev/healthz
    curl -fsS http://127.0.0.1/ffmpeg-dev/ | head

The `/myservices/` home page button/link is not tracked in this repo. Adding a button there is a separate legacy-home task against the runtime home UI source.

## CPU-Only V1 Policy

`soma-ffmpeg-dev` v1 is intentionally CPU-only.

Do not add GPU access to the compose file for this rollout. FFmpeg does not automatically use NVIDIA GPU, CUDA, or NVENC just because the host has an RTX 3060. NVIDIA video acceleration uses explicit NVENC/NVDEC hardware paths.

Expected v1 workload:

- MP4 remux uses stream copy and is mostly I/O/container-bound.
- profile conversion targets MPEG-2/VOB and MPEG-4 Part 2/Xvid-style AVI.
- these legacy/device profiles are CPU encode targets in v1.

Future GPU work should add explicit hardware-accelerated profiles. Prefer H.264/H.265 via NVENC. Use AV1 NVENC only if the actual GPU supports AV1 encode. Do not describe VP8/VP9 as NVENC encode targets; they may be relevant for NVDEC decode.

## Stop And Cleanup

Stop only this compose project:

    cd /srv/soma/worktrees/ffmpeg-dev
    docker compose -f compose/ffmpeg-dev.compose.yml down

Optional worktree cleanup after validation:

    cd /home/grigorynokhrin/soma-arch
    git worktree remove /srv/soma/worktrees/ffmpeg-dev

Do not remove `/srv/soma/data/ffmpeg-dev` unless a separate cleanup task explicitly asks for it.

## Troubleshooting

### Port 18082 Busy

Find the process or container using the port:

    ss -ltnp | grep 18082
    docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep 18082

Stop only the conflicting FFmpeg dev process/container after confirming it belongs to this test.

### Missing ffmpeg Or ffprobe

Open a shell in the dev container and check binaries:

    docker exec soma-ffmpeg-dev ffmpeg -version
    docker exec soma-ffmpeg-dev ffprobe -version

If missing, rebuild only this service from the worktree:

    docker compose -f compose/ffmpeg-dev.compose.yml build ffmpeg-dev

### Permission Issue On Data Directory

Symptoms may include upload failures, inability to write `job.json`, or output creation errors.

Check:

    ls -ld /srv/soma/data/ffmpeg-dev

Expected ownership should allow uid `1000` and gid `990` to write. Repair only this directory:

    sudo chown grigorynokhrin:docker /srv/soma/data/ffmpeg-dev
    chmod 775 /srv/soma/data/ffmpeg-dev

### root_path Redirect Or Form Issues

The app should generate URLs under:

    /ffmpeg-dev

Check the rendered form actions and links:

    curl -fsS http://127.0.0.1:18082/ffmpeg-dev/ | grep -E 'action=|href='

If paths omit `/ffmpeg-dev`, verify the compose environment contains:

    FFMPEG_ROOT_PATH=/ffmpeg-dev

### Filename Or Stale Probe UX Regression

Human output names should preserve spaces, Unicode, parentheses, ampersands, commas, and safe dots. The extension should still be forced to `.mp4` for remux and to the profile extension for batch conversion.

The index page should show an active remux form only for a current job with `status=probed`. Done, failed, or conversion jobs should show as summaries, not as stale probe/remux forms.

The UI should include:

- Clear current job action
- submit waiting message for probe
- submit waiting message for remux
- submit waiting message for batch conversion
- visible warnings on index/result/status views

These submit indicators are not true progress bars.

### MP4 Remux Subtitle Failure

Text subtitle codecs such as SubRip/SRT, ASS/SSA, and WebVTT should be converted to MP4 `mov_text` when needed. Video and audio must remain stream-copy.

Image subtitles such as PGS or DVD subtitles are not supported in MP4 remux v1 because converting them to text requires OCR. The expected user-facing error is:

    Image subtitles cannot be converted to MP4 text subtitles without OCR; deselect this subtitle stream.

If a remux failure shows a Python `UnicodeDecodeError`, the process-output decoding path has regressed. FFmpeg and FFprobe logs should be decoded with replacement so the real FFmpeg error is visible.

### MP4 Remux Player Metadata

When remux metadata fields are filled, FFmpeg writes basic MP4 metadata during mux and ExifTool post-processes the final MP4 with QuickTime/iTunes/UserData/Keys-compatible tags. Check that the job can enter `writing_metadata` and complete without leaving `*_original` backup artifacts.

Metadata display is player-controlled. Validate at least one common desktop player or Finder/QuickTime path if this behavior is the focus of the rollout. Large MP4 files may spend extra time in metadata post-processing because the container can be rewritten.

The description field should appear through Description/LongDescription-style tags. Comment-style aliases are intentionally skipped because some MP4 readers display UTF-8 comment aliases as mojibake.

Final MP4 artifacts should not show FFmpeg/libavformat Encoder values such as `Lavf...`. Publisher and global language are intentionally not supported in v1. Player Language fields should come from selected audio/subtitle stream language tags.

### Batch Profile Subtitle Handling

Legacy AVI/VOB profile conversions should not fail just because the input has subtitles.

Expected behavior:

- compatible subtitle streams are preserved only when safe for the target container
- text subtitles are burned into video for legacy AVI/VOB profiles
- unsupported image subtitles are dropped with a warning
- video and audio profile codecs remain unchanged

This is intentionally different from MP4 remux, where text subtitles become `mov_text` streams when possible.

### Caddy Route Fails

Check that `soma-ffmpeg-dev` is attached to the external Caddy/dev network:

    docker inspect soma-ffmpeg-dev

Expected network:

    compose_default

Check that `myservices-caddy` is also attached to `compose_default` and can resolve the service name:

    docker inspect myservices-caddy
    docker exec myservices-caddy getent hosts soma-ffmpeg-dev

If DNS resolution fails, verify the compose config still includes the external `caddy_dev` network with alias `soma-ffmpeg-dev`.

### Compose Project Safety

Do not run `docker compose down` from unrelated compose projects.

Always include the FFmpeg dev compose file when stopping this service:

    docker compose -f compose/ffmpeg-dev.compose.yml down

Do not use `--remove-orphans` during this rollout unless there is a separate, reviewed cleanup plan.
