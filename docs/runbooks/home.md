# Home/MyServices Runbook

This is the canonical operational runbook for the Home/MyServices portal.

It explains how to operate, validate, diagnose, and safely maintain the user-facing Home page. It is not a service design document. Future architecture and behavior rationale belongs in `docs/services/home.md`.

## Audit Sources

Audited locations:

- `docs/`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/CURRENT_STATE.md`
- `docs/RUNTIME_STATUS.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `gateway/myservices/Caddyfile.current`
- `compose/`
- `runtime/`
- repository README files
- `services/`

No tracked Home source was found in this repository. Home source ownership is documented from repository evidence as a legacy runtime concern under `/home/grigorynokhrin/myservices/home`.

## Purpose

Home/MyServices is the user-facing landing page for stable tools on the home server.

It exists to provide a simple, stable entry point for tools that are ready for normal use. The current expected stable entries are:

- Whisper
- FFmpeg

Home is intentionally not an engineering playground. Dev tools such as `whisper-dev` and `ffmpeg-dev` may have their own direct or Caddy routes, but they must not be published as Home user-facing tools.

## Scope

This runbook covers:

- operating Home/MyServices
- validating the landing page
- validating stable service links
- rebuilding and restarting Home when a Home source change is approved
- diagnosing UI, link, route, and proxy failures
- safely updating published stable tools
- avoiding accidental dev tool publication

This runbook does not cover:

- full Home architecture
- Home service design rationale
- FFmpeg internals
- Whisper internals
- Gateway/Caddy internals except where Home-specific routing is involved
- live server edits that have not been explicitly approved

Future architecture content belongs to:

- `docs/services/home.md`

## Service Topology

Stable Home service:

| Field | Value |
| --- | --- |
| Route | `/myservices/` |
| LAN URL | `http://10.0.1.196/myservices/` |
| Container | `myservices-home` |
| Compose service | `home` |
| Container port | `8000` documented in `docs/RUNTIME_STATUS.md` |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Runtime source path | `/home/grigorynokhrin/myservices/home` |
| Tracked source in this repo | Not found |
| Publication policy | Stable tools only |

Gateway relationship:

- `myservices-caddy` exposes host port `80`.
- The tracked reference config is `gateway/myservices/Caddyfile.current`.
- The live Caddyfile is documented as `/home/grigorynokhrin/myservices/caddy/Caddyfile`.
- Live Caddy may differ from the tracked reference. Inspect live mounts before live Gateway work.

Tracked Home route block:

```text
handle /myservices* {
    reverse_proxy home:8000
}
```

Important route ordering:

- More specific `/myservices/...` service routes must appear before the `/myservices*` Home catch-all.
- The tracked Caddyfile currently routes `/myservices/whisper*` before `/myservices*`.
- `/myservices/ocr*` is a placeholder route before `/myservices*`.
- FFmpeg stable uses `/ffmpeg/`, not a `/myservices/ffmpeg/` prefix.

## Publication Policy

Canonical rule:

Home publishes stable tools only.

Current expected stable entries:

- Whisper, route `/myservices/whisper/`
- FFmpeg, route `/ffmpeg/`

Home must not publish:

- `whisper-dev`
- `ffmpeg-dev`
- experimental tools
- prototype services
- temporary validation routes

Validation expectation:

- `/myservices/` renders the Home page.
- Home links point to stable routes.
- No dev route appears as a normal user-facing Home entry.
- The stable FFmpeg entry points to `/ffmpeg/`.
- The stable Whisper entry points to `/myservices/whisper/`.

## Source And Runtime Locations

Known repo paths:

- `docs/runbooks/home.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `gateway/myservices/Caddyfile.current`
- `runtime/scripts/healthcheck.sh`
- `runtime/Makefile`

Known server/runtime paths:

- `/home/grigorynokhrin/myservices`
- `/home/grigorynokhrin/myservices/compose.yaml`
- `/home/grigorynokhrin/myservices/home`
- `/home/grigorynokhrin/myservices/caddy/Caddyfile`

Known current-state observations:

- `myservices-home` is part of the active legacy runtime.
- `home` is the Compose service name observed in `docs/RUNTIME_STATUS.md`.
- The running command observed for Home begins with `uvicorn app:app`.

TODO:

- Confirm whether all Home source files under `/home/grigorynokhrin/myservices/home` are intentionally outside this repository.
- Document the exact Home source file that owns the stable tool list.
- Document whether Home has a dedicated health endpoint.
- Document exact Home log paths if the application writes logs outside container stdout.

## Operational Lifecycle

Use the global workflow in:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/SERVICES_REGISTRY.md`

Home changes are needed when:

- a stable tool is added to Home after direct and Caddy validation passes
- a stable tool is removed or disabled
- a stable route changes
- Home UI text or layout needs an approved update
- stale links must be corrected

Rules:

- Home changes require explicit approval.
- Home must publish stable tools only.
- Do not expose dev tools through Home.
- Commit and push repository documentation or tracked config changes before server validation.
- On the server, pull the exact intended commit before validation.
- Rebuild Home after Home source changes when the source is baked into the image.
- Restart only Home unless a Gateway change is explicitly approved.
- Do not restart unrelated services.

Known operational lesson:

```text
docker compose build home
docker compose up -d home
```

These commands are documented as Home rebuild/restart expectations, but the working directory is the production compose root:

```text
/home/grigorynokhrin/myservices
```

## Deployment And Restart

Before Home deployment or restart, verify the server state:

```text
git status --short --branch
git log --oneline -3
git pull --ff-only
git log --oneline -3
```

For Home source changes in the legacy runtime, use the production compose root:

```text
cd /home/grigorynokhrin/myservices
docker compose build home
docker compose up -d home
```

Rules:

- Restart only `home` for Home-only changes.
- Do not restart Caddy unless a Gateway change is explicitly approved.
- Do not restart Whisper or FFmpeg for a Home-only link change.
- Do not run `docker compose down` from unrelated compose projects.
- Do not use broad destructive cleanup commands as part of Home publication.

TODO:

- Confirm exact command sequence for live Home deployments during the next approved Home change.
- Document whether `--no-cache` is ever needed for Home rebuilds.
- Document whether Home runtime has separate static asset caching to clear.

## Readiness

Do not validate immediately after `docker compose up -d home`.

Readiness evidence should include:

- `myservices-home` is running.
- Caddy can reach `home:8000`.
- `http://127.0.0.1/myservices/` returns the Home page.
- `http://10.0.1.196/myservices/` returns the Home page from the LAN.
- stable service links render.
- dev service links do not render as Home entries.

Container status check:

```text
cd /home/grigorynokhrin/myservices
docker compose ps home
```

HTTP route check:

```text
curl -fsS http://127.0.0.1/myservices/
```

Optional readiness loop:

```text
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1/myservices/ >/tmp/home-page.html; then
    break
  fi
  sleep 2
done
```

TODO:

- Confirm whether Home exposes a dedicated `/healthz` route.
- Add a stricter readiness command after the Home page markup and stable link labels are confirmed from live source.

## Runtime Validation Scenarios

### Scenario 1: Home Page Availability

Goal:

- Confirm the Home page is reachable through Caddy.

Route:

```text
http://127.0.0.1/myservices/
http://10.0.1.196/myservices/
```

Expected result:

- HTTP request succeeds.
- Response is the Home/MyServices landing page.
- No 502 or connection reset occurs after readiness wait.

Evidence to capture:

- command used
- HTTP status or successful `curl -fsS`
- short rendered HTML excerpt showing Home content, without secrets

### Scenario 2: Stable Tool Publication

Goal:

- Confirm Home publishes the expected stable tools.

Expected tools:

- Whisper
- FFmpeg

Suggested checks:

```text
curl -fsS http://127.0.0.1/myservices/ | grep -i whisper
curl -fsS http://127.0.0.1/myservices/ | grep -i ffmpeg
```

Expected result:

- Home includes stable entries for Whisper and FFmpeg.

Evidence to capture:

- rendered link targets or short HTML excerpts showing stable entries

### Scenario 3: FFmpeg Link

Goal:

- Confirm the Home FFmpeg entry points to the stable FFmpeg service.

Expected route:

```text
/ffmpeg/
```

Suggested check:

```text
curl -fsS http://127.0.0.1/myservices/ | grep -E 'href=.*/ffmpeg/?'
```

Follow-up check:

```text
curl -fsS http://127.0.0.1/ffmpeg/healthz
```

Expected result:

- Home links to `/ffmpeg/`.
- The stable FFmpeg route responds.
- Home does not link to `/ffmpeg-dev/` as the user-facing FFmpeg entry.

### Scenario 4: Whisper Link

Goal:

- Confirm the Home Whisper entry points to the stable Whisper service.

Expected route:

```text
/myservices/whisper/
```

Suggested check:

```text
curl -fsS http://127.0.0.1/myservices/ | grep -E 'href=.*/myservices/whisper/?'
```

Follow-up check:

```text
curl -fsS http://127.0.0.1/myservices/whisper/healthz
```

Expected result:

- Home links to `/myservices/whisper/`.
- The stable Whisper route responds with `ok` on its health endpoint.
- Home does not replace stable Whisper with `/whisper-dev/`.

### Scenario 5: No Dev Publication

Goal:

- Confirm dev tools are not published as Home user-facing entries.

Forbidden routes/names:

- `/ffmpeg-dev/`
- `/whisper-dev/`
- `ffmpeg-dev`
- `whisper-dev`

Suggested check:

```text
curl -fsS http://127.0.0.1/myservices/ | grep -E 'ffmpeg-dev|whisper-dev|/ffmpeg-dev|/whisper-dev'
```

Expected result:

- No matches.

If matches appear:

- Treat this as a publication policy violation.
- Revert or correct Home source.
- Rebuild/restart Home after the approved correction.
- Revalidate stable links.

## Diagnostics

Container status:

```text
cd /home/grigorynokhrin/myservices
docker compose ps home
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Home logs:

```text
cd /home/grigorynokhrin/myservices
docker compose logs --tail=100 home
```

Caddy logs relevant to Home:

```text
cd /home/grigorynokhrin/myservices
docker compose logs --tail=100 caddy
```

Route checks:

```text
curl -fsS http://127.0.0.1/myservices/
curl -fsS http://127.0.0.1/ffmpeg/healthz
curl -fsS http://127.0.0.1/myservices/whisper/healthz
```

Source/live mismatch checks:

```text
cd /home/grigorynokhrin/myservices
docker compose config --services
docker compose ps
```

Tracked vs live Caddy distinction:

- Tracked reference: `gateway/myservices/Caddyfile.current`
- Live file documented in repo evidence: `/home/grigorynokhrin/myservices/caddy/Caddyfile`

If a tracked Caddyfile change does not affect live routing, inspect the live Caddy mount before assuming the route was deployed.

TODO:

- Confirm exact Home application log behavior.
- Confirm whether Home has static files or templates that require separate cache checks.
- Confirm whether Home source is mounted into the container or copied into the image.

## Configuration

Discovered configuration:

| Item | Value |
| --- | --- |
| Container | `myservices-home` |
| Compose service | `home` |
| Compose root | `/home/grigorynokhrin/myservices` |
| Compose file | `/home/grigorynokhrin/myservices/compose.yaml` |
| Container port | `8000` |
| Caddy upstream | `home:8000` |
| User-facing route | `/myservices/` |
| LAN URL | `http://10.0.1.196/myservices/` |
| Runtime source path | `/home/grigorynokhrin/myservices/home` |

Unknown/TODO:

- exact Home environment variables
- exact Home image build context
- exact Home source file that defines tool cards/links
- exact host port, if any, beyond Caddy routing
- exact Home health endpoint, if any
- exact static asset behavior

## Integration Points

Gateway/Caddy:

- Routes `/myservices*` to `home:8000`.
- More specific service routes must stay ahead of the Home catch-all.
- Live Gateway changes require explicit approval.

FFmpeg stable:

- Home should link to `/ffmpeg/`.
- Home should not link to `/ffmpeg-dev/` as the stable entry.

Whisper stable:

- Home should link to `/myservices/whisper/`.
- Home should not link to `/whisper-dev/` as the stable entry.

Docker Compose:

- Home is managed by the legacy production compose project under `/home/grigorynokhrin/myservices`.
- Rebuild is required after Home source changes when source is baked into the image.

Future stable services:

- Add only after direct service validation and Caddy route validation.
- Keep dev tools off Home.
- Update registry and runbook docs with publication evidence.

## Operational Risks

- Home must publish stable services only.
- Dev tools must not appear on Home.
- Home source changes require rebuild when source is baked into the image.
- Server validation requires commit/push/pull first for repo changes.
- A stale Home container after source edit can hide changes.
- Gateway/Caddy changes require explicit approval.
- Live Caddyfile may differ from the tracked reference.
- Editing tracked files may not affect live runtime.
- A 502 can occur if Home or Gateway is restarted and validated too early.
- Unrelated services must not be restarted unnecessarily.
- Home source appears to be outside this repo, so repo-only changes may not alter the live page.
- Home publication changes can accidentally point users to experimental services if routes are not checked.

## Known Failure Modes

| Symptom | Likely Cause | Resolution | Evidence To Inspect |
| --- | --- | --- | --- |
| `/myservices/` returns 502 | Home is not ready, Home container is down, or Caddy cannot reach `home:8000` | Wait for readiness, check `docker compose ps home`, inspect Home and Caddy logs, restart only Home if approved | `docker compose ps home`, `docker compose logs home`, `docker compose logs caddy` |
| Home does not show an expected stable service | Home source/config was not updated, image was not rebuilt, or running container is stale | Confirm approved source change, rebuild Home, restart Home, wait for readiness, revalidate rendered HTML | rendered `/myservices/` HTML, Home logs, image/container age |
| Home shows a dev service | Publication policy violation | Correct Home source to stable route or remove dev entry, rebuild/restart Home, validate no dev route appears | rendered HTML grep for dev route/name |
| Home link points to wrong route | Stale source, typo, or old publication entry | Correct link target, rebuild/restart Home, verify service health and rendered href | rendered HTML, route health checks |
| Source changed but UI unchanged | Home image was not rebuilt or container was not restarted | Run approved rebuild/restart, then readiness check | `docker compose build home`, `docker compose up -d home`, rendered HTML |
| Tracked Caddyfile changed but live route unchanged | Live Caddyfile differs from tracked reference or route was not reloaded | Inspect Caddy mount and live Caddyfile; handle as separate approved Gateway task | `docker inspect myservices-caddy`, live Caddyfile path |
| Home route works but service link fails | Target service is down, route is missing, or Caddy cannot resolve upstream | Validate target service directly and through Caddy; inspect Gateway route and service container | service health endpoint, Caddy logs, service logs |

## Rollback / Disable Strategy

Current repository evidence does not define a Home image rollback tag strategy.

Documented safe concepts:

- Revert or correct the Home source/config change.
- Rebuild Home if source is baked into the image.
- Restart only Home.
- Wait for readiness.
- Verify `/myservices/` renders the expected stable links.
- Remove or hide a service link if user access must be disabled.
- Treat Gateway/Caddy route changes as a separate approved task.

TODO:

- Document exact Home backup or rollback image/tag convention after the next approved Home deployment.
- Document whether the live Home source is backed up before edits.

## Dependencies

Discovered dependencies:

- Docker Compose
- `myservices-caddy`
- `myservices-home`
- stable Whisper route `/myservices/whisper/`
- stable FFmpeg route `/ffmpeg/`
- legacy production root `/home/grigorynokhrin/myservices`
- tracked Gateway reference `gateway/myservices/Caddyfile.current`

Assumptions to verify during live work:

- Home app runtime is Python/Uvicorn based on `docs/RUNTIME_STATUS.md`.
- Home source is baked into the image when rebuild is required.
- Home has no separate direct host bind documented in this repo.

## Documentation Links

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/services/home.md`

## Known Gaps

- Exact Home source ownership/tracking status needs a live audit.
- Exact Home source file that defines published service links is not tracked here.
- Exact Home build context is not documented in this repo.
- Exact Home health endpoint is not documented.
- Exact Home readiness command is not documented beyond HTTP route checks.
- Exact Home application log behavior is not documented.
- Exact Home rollback image/tag strategy is not documented.
