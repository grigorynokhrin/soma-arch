# FIRST_RELEASE_PLAYBOOK

This playbook documents the first stable release of a dev tool.

Use it when a validated dev service is promoted into its first stable, user-facing sibling service. It is generic, with `ffmpeg-dev -> ffmpeg` as the concrete example.

Later releases to an already-existing stable service are out of scope and should use a separate update/release playbook.

## Definition

Dev service:

- experimental or engineering-facing service
- internal/dev route
- not linked from Home/MyServices
- safe place for v2 experiments and runtime validation

Stable/prod service:

- user-facing tool
- linked from Home/MyServices only after stable validation passes
- has its own source path, compose file, route, container, image, port, data directory, and runbook

First release:

- initial creation of a stable sibling from a validated dev baseline
- creates the stable source tree, compose file, data directory, route, Home entry, documentation, and operational baseline

Later release:

- updates an already-existing stable service
- does not create the stable service from scratch
- out of scope for this playbook

## Preconditions

Before first release:

- dev service has passed runtime validation
- docs, syntax checks, and selfcheck/tests pass
- all code that will be tested on the server is committed and pushed
- server checkout or worktree is on the correct branch, not detached HEAD
- server has pulled the latest commit with `git pull --ff-only`
- exact baseline commit is known and recorded
- no merge to `main` unless explicitly requested

## Repository Work

Generic steps:

1. Copy the validated dev service source into a stable service source path.
2. Create a separate stable compose file.
3. Change stable service identity, root path, page title, and status label.
4. Use separate container, image, host port, route, and data directory.
5. Add a stable service runbook.
6. Document the expected Caddy route.
7. Do not edit live Caddy unless the task explicitly asks for live publication.
8. Do not expose the dev service in Home.
9. Expose only the stable service in Home after direct and Caddy validation pass.

FFmpeg example:

    services/ffmpeg-dev/        -> services/ffmpeg/
    compose/ffmpeg-dev.compose.yml -> compose/ffmpeg.compose.yml
    soma-ffmpeg-dev             -> soma-ffmpeg
    soma-ffmpeg-dev:local       -> soma-ffmpeg:local
    /ffmpeg-dev                 -> /ffmpeg
    127.0.0.1:18082             -> 127.0.0.1:18083
    /srv/soma/data/ffmpeg-dev   -> /srv/soma/data/ffmpeg

## Commit And Push Rule

Every change that must be tested on the server must be committed and pushed first.

Required sequence:

1. Local validation.
2. `git add ...`
3. `git commit -m "..."`
4. `git push origin <branch>`
5. Server `git pull --ff-only`
6. Build.
7. `up -d` or restart.
8. Healthcheck readiness loop.
9. Runtime validation.

Never validate server runtime from uncommitted Mac-only changes.

If runtime validation appears to contradict local code, first verify the server commit:

    git status --short --branch
    git log --oneline -3

## Server Deployment

Run from the server checkout or server worktree for the target branch.

Generic commands:

    git status --short --branch
    git pull --ff-only
    git log --oneline -3

Create the stable data directory before the first container start:

    sudo mkdir -p /srv/soma/data/<tool>
    sudo chown -R 1000:990 /srv/soma/data/<tool>
    sudo chmod -R u+rwX,g+rwX /srv/soma/data/<tool>

Build the stable service from the stable compose file:

    docker compose -f compose/<tool>.compose.yml build --no-cache <tool>
    docker compose -f compose/<tool>.compose.yml up -d <tool>

Wait for readiness before curling through Caddy or Home:

    for i in $(seq 1 30); do
      if curl -fsS http://127.0.0.1:<port>/<tool>/healthz; then
        break
      fi
      sleep 2
    done

Direct service checks:

    curl -fsS http://127.0.0.1:<port>/<tool>/healthz
    curl -fsS http://127.0.0.1:<port>/<tool>/ | head

FFmpeg example:

    git status --short --branch
    git pull --ff-only
    git log --oneline -3

    sudo mkdir -p /srv/soma/data/ffmpeg
    sudo chown -R 1000:990 /srv/soma/data/ffmpeg
    sudo chmod -R u+rwX,g+rwX /srv/soma/data/ffmpeg

    docker compose -f compose/ffmpeg.compose.yml build --no-cache ffmpeg
    docker compose -f compose/ffmpeg.compose.yml up -d ffmpeg

    for i in $(seq 1 30); do
      if curl -fsS http://127.0.0.1:18083/ffmpeg/healthz; then
        break
      fi
      sleep 2
    done

    curl -fsS http://127.0.0.1:18083/ffmpeg/healthz
    curl -fsS http://127.0.0.1:18083/ffmpeg/ | head

## Caddy Publication

Do not assume the tracked Caddy reference is the live mounted Caddyfile.

Inspect the running Caddy mounts first:

    docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'

Update the real mounted Caddyfile, not only the tracked reference.

Validate before reload:

    docker exec myservices-caddy caddy validate --config /etc/caddy/Caddyfile

Reload:

    docker exec myservices-caddy caddy reload --config /etc/caddy/Caddyfile

Wait briefly or use a readiness loop before testing through Caddy.

Verify through Caddy:

    curl -fsS http://127.0.0.1/<tool>/healthz
    curl -fsS http://127.0.0.1/<tool>/job/status.json

Tracked gateway config must also be updated and committed.

FFmpeg route example:

    handle /ffmpeg* {
        reverse_proxy soma-ffmpeg:8000
    }

If a dev route also exists, keep the dev route before the stable prefix route:

    handle /ffmpeg-dev* {
        reverse_proxy soma-ffmpeg-dev:8000
    }

    handle /ffmpeg* {
        reverse_proxy soma-ffmpeg:8000
    }

## Home UI Publication

Rules:

- Home must not link to dev routes.
- Home gets a stable link only after stable service direct checks pass.
- Home gets a stable link only after Caddy route checks pass.
- If Home source is baked into an image, rebuild the Home image.
- Restart Home and wait for readiness before checking rendered HTML.

Generic flow:

1. Update Home source to link to `/<tool>/`.
2. Rebuild Home if the source is baked into the image.
3. Restart Home.
4. Wait for Home readiness.
5. Verify rendered HTML contains the stable route.
6. Verify rendered HTML does not expose the dev route as the primary entry.

FFmpeg expected Home entry:

    FFmpeg -> /ffmpeg/

Not:

    FFmpeg dev -> /ffmpeg-dev/

Example verification:

    curl -fsS http://127.0.0.1/myservices/ | grep -i ffmpeg

## Validation Checklist

Before calling the first release complete:

- direct stable healthz is `ok`
- Caddy stable healthz is `ok`
- status endpoint reports stable service identity
- Home links to the stable route
- Home does not link to the dev route as the user-facing entry
- dev service remains available separately
- stable service uses its own data directory
- stable service uses its own container/image/port
- no accidental changes to unrelated services
- tracked Caddy reference matches live route intent
- docs are committed
- final `git status --short` is clean

FFmpeg validation examples:

    curl -fsS http://127.0.0.1:18083/ffmpeg/healthz
    curl -fsS http://127.0.0.1/ffmpeg/healthz
    curl -fsS http://127.0.0.1:18083/ffmpeg/job/status.json
    curl -fsS http://127.0.0.1/myservices/ | grep -i ffmpeg
    curl -fsS http://127.0.0.1:18082/ffmpeg-dev/healthz

## Common Failure Modes

Learned during the FFmpeg first release:

- server checkout was detached HEAD, so `git pull` did not apply branch changes
- server built old code because it had not pulled the latest commit
- missing `ffmpeg_commands` or status fields indicated old runtime code
- `/srv/soma/data/ffmpeg` was root-owned and caused `PermissionError`
- route was added to tracked `gateway/myservices/Caddyfile.current` but not to the live mounted Caddyfile
- `curl` immediately after restart produced false 502 or connection reset results
- Home source was edited but the Home image was not rebuilt, so the running UI did not change

## Deliverables

A first-release PR or branch should include:

- stable service source path
- stable compose file
- stable runbook
- tracked Caddy reference update, if the service is published through Caddy
- Home publication notes, if Home was changed
- validation output
- rollback or disable notes
- final clean Git status
