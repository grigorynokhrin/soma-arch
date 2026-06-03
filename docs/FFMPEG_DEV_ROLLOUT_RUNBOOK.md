# FFMPEG_DEV_ROLLOUT_RUNBOOK

This runbook validates `soma-ffmpeg-dev` as a dev-only service on the server.

It must not change Caddy, Home, Whisper, production Compose, or legacy `/home/grigorynokhrin/myservices` behavior. Initial validation uses the direct localhost bind only:

    http://127.0.0.1:18082/ffmpeg-dev/healthz
    http://127.0.0.1:18082/ffmpeg-dev/

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

No Caddy route is expected during this initial rollout.

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

### Compose Project Safety

Do not run `docker compose down` from unrelated compose projects.

Always include the FFmpeg dev compose file when stopping this service:

    docker compose -f compose/ffmpeg-dev.compose.yml down

Do not use `--remove-orphans` during this rollout unless there is a separate, reviewed cleanup plan.
