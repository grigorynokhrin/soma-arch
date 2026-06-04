# Gateway/Caddy Runbook

This is the canonical operational runbook for the Gateway/Caddy component.

It explains how to inspect, validate, diagnose, and safely maintain the routing layer used by Home/MyServices and service routes. It is not a service design document. Gateway architecture and route-design rationale belongs in `docs/services/gateway.md`.

## Audit Sources

Audited locations:

- `docs/`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/runbooks/home.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/CADDY_WHISPER_DEV_ROUTE.md`
- `docs/CURRENT_STATE.md`
- `docs/RUNTIME_STATUS.md`
- `docs/PROJECT_PHASE_1_STATUS.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `gateway/myservices/Caddyfile.current`
- `gateway/myservices/compose.override.caddy-soma-dev.yaml`
- `compose/`
- `runtime/`
- repository README files

No live server commands were run for this runbook. It uses repository evidence and prior validation records.

## Purpose

Gateway/Caddy is the reverse-proxy layer for the current Home/MyServices runtime and selected stable/dev service routes.

It exists to:

- expose the Home/MyServices portal at `/myservices/`
- route stable Whisper at `/myservices/whisper/`
- route stable FFmpeg at `/ffmpeg/`
- route selected dev services such as `/whisper-dev/` and `/ffmpeg-dev/`
- keep route publication separate from service internals
- provide one host port entry point for browser access

Gateway/Caddy is production-sensitive because a bad route, reload, network change, or container restart can affect multiple user-facing services at once.

## Scope

This runbook covers:

- safe Gateway/Caddy inspection
- route validation
- route/proxy diagnostics
- tracked vs live Caddyfile checks
- restart/reload boundaries
- Caddy route health evidence
- avoiding regressions to Home, FFmpeg, and Whisper

This runbook does not cover:

- full Gateway architecture
- service implementation internals
- Home UI internals
- FFmpeg internals
- Whisper internals
- unauthorized live Caddy changes
- production compose rewrites

Future architecture content belongs to:

- `docs/services/gateway.md`

## Gateway Topology

Known topology:

| Field | Value |
| --- | --- |
| Container | `myservices-caddy` |
| Image | `caddy:2-alpine` observed in `docs/RUNTIME_STATUS.md` |
| Compose service | `caddy` |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Tracked Caddyfile reference | `gateway/myservices/Caddyfile.current` |
| Live Caddyfile path from prior validation | `/home/grigorynokhrin/myservices/caddy/Caddyfile` |
| Container Caddyfile path from prior validation | `/etc/caddy/Caddyfile` |
| Host port | `0.0.0.0:80->80/tcp` observed in `docs/RUNTIME_STATUS.md` |
| Additional exposed container ports | `443/tcp`, `2019/tcp`, `443/udp` observed in `docs/RUNTIME_STATUS.md` |
| Legacy Docker network | `myservices_default` |
| Dev/Caddy external network | `compose_default` |

Known config mount from `docs/CADDY_WHISPER_DEV_ROUTE.md`:

```text
/home/grigorynokhrin/myservices/caddy/Caddyfile -> /etc/caddy/Caddyfile
```

Known network facts:

- The original legacy Caddy network was `myservices_default`.
- Dev services use the external network `compose_default` for Caddy reachability.
- `gateway/myservices/compose.override.caddy-soma-dev.yaml` documents a persistent override that attaches `caddy` to `compose_default`.
- `compose/ffmpeg.compose.yml` attaches `soma-ffmpeg` to `compose_default` with alias `soma-ffmpeg`.
- `compose/ffmpeg-dev.compose.yml` attaches `soma-ffmpeg-dev` to `compose_default` with alias `soma-ffmpeg-dev`.
- Prior Whisper dev validation used a manual `docker network connect compose_default myservices-caddy`; the persistence of Caddy membership after recreation must be verified before relying on it.

TODO:

- Confirm the current live Caddy networks after any Caddy recreation.
- Confirm whether the tracked compose override is active in the live production compose project.
- Document exact current live Caddyfile contents after an approved server inspection.

## Route Inventory

This table is based on `gateway/myservices/Caddyfile.current` plus service runbook evidence.

| Route | Expected upstream | Environment | Publication status | Owner service/component | Notes |
| --- | --- | --- | --- | --- | --- |
| `/myservices/image-upscale` | redirect to `/myservices/image-upscale/` | server-stable historical | Not part of current stable tool set | image-upscale | Tracked redirect route; service is documented as stopped/deprecated in registry/runtime notes. |
| `/myservices/image-upscale/*` | `image-upscale:7860` via `handle_path` | server-stable historical | Not part of current stable tool set | image-upscale | Historical route; do not alter without separate task. |
| `/myservices/whisper*` | `whisper:8000` | server-stable | Home-published stable tool | Whisper | Stable production route. |
| `/whisper-dev*` | `soma-whisper-dev:8000` | server-dev | Dev route; not Home-published | Whisper dev | Requires Caddy to resolve dev service network/alias. |
| `/ffmpeg-dev*` | `soma-ffmpeg-dev:8000` | server-dev | Dev route; not Home-published | FFmpeg dev | Must appear before `/ffmpeg*` to avoid prefix shadowing. |
| `/ffmpeg*` | `soma-ffmpeg:8000` | server-stable | Home-published stable tool via Home link | FFmpeg | Stable route; current Home link is expected to point to `/ffmpeg/`. |
| `/myservices/ocr*` | Caddy `respond "OCR placeholder" 200` | placeholder | Not a live stable service | OCR placeholder | Placeholder response only; no tracked service source/container. |
| `/myservices*` | `home:8000` | home | Home portal | Home/MyServices | Catch-all for Home; keep after more specific `/myservices/...` routes. |
| fallback | Caddy `respond "Not found" 404` | gateway | Not published | Gateway | Default unmatched route behavior. |

Route categories:

- Stable user-facing routes: `/myservices/`, `/myservices/whisper/`, `/ffmpeg/`
- Dev routes: `/whisper-dev/`, `/ffmpeg-dev/`
- Home-published services: Whisper and FFmpeg
- Routes that must not be Home-published as stable entries: `/whisper-dev/`, `/ffmpeg-dev/`
- Historical/placeholder routes: `/myservices/image-upscale/`, `/myservices/ocr*`

## Tracked Vs Live Caddyfile

Do not assume the tracked Caddy reference is the live mounted Caddyfile.

Tracked reference:

```text
gateway/myservices/Caddyfile.current
```

Known live path from prior validation:

```text
/home/grigorynokhrin/myservices/caddy/Caddyfile
```

Known container path from prior validation:

```text
/etc/caddy/Caddyfile
```

Changing `gateway/myservices/Caddyfile.current` is not proof of runtime change. Changing the live Caddyfile is production-sensitive and bypasses normal repository-only safety unless it is paired with an approved runtime task.

Before making any runtime Gateway/Caddy change, inspect the live mounts:

```text
docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Reasoning checklist:

1. Identify which host file is mounted into `/etc/caddy/Caddyfile`.
2. Confirm whether the mounted file is the expected live file.
3. Compare tracked and live config only if needed.
4. Do not modify tracked or live config unless the task explicitly asks for it.
5. If live config changes are approved, update the tracked reference too so the repo remains useful.
6. Validate Caddy config before any reload.
7. Reload or restart only when explicitly approved.

## Operational Lifecycle

Use global process guidance from:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/runbooks/home.md`

Normal inspection workflow:

1. Read the current task and confirm whether Gateway/Caddy is actually in scope.
2. Inspect repository route references.
3. Inspect current container status when a runtime task is approved.
4. Inspect live mounts before any live Caddy action.
5. Validate routes with `curl` after readiness.
6. Escalate to Caddy logs only when route checks fail.

Route validation workflow:

1. Check `myservices-caddy` is running.
2. Check Home route.
3. Check stable service routes.
4. Check dev routes only when they are in scope.
5. Confirm Home does not publish dev routes.

Config update workflow, high level only:

1. Get explicit approval for Gateway/Caddy changes.
2. Commit and push tracked config/doc changes.
3. Pull the exact commit on the server.
4. Inspect live mounts.
5. Update the live mounted Caddyfile only when approved.
6. Validate with `caddy validate`.
7. Reload with `caddy reload` only when approved.
8. Wait for readiness.
9. Validate route inventory.
10. Record evidence and rollback/disable notes.

Do not restart or reload Gateway/Caddy as part of unrelated FFmpeg, Whisper, or Home work.

## Safe Inspection Commands

The following commands are read-only inspection commands when run on the server.

Container status:

```text
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
```

Compose status:

```text
cd /home/grigorynokhrin/myservices
docker compose ps caddy
```

Mount inspection:

```text
docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Network inspection:

```text
docker inspect myservices-caddy --format '{{range $name, $net := .NetworkSettings.Networks}}{{println $name $net.IPAddress}}{{end}}'
```

Recent Caddy logs:

```text
cd /home/grigorynokhrin/myservices
docker compose logs --tail=100 caddy
```

Tracked route search:

```text
grep -R "reverse_proxy\|handle " -n gateway docs compose runtime
```

Route checks:

```text
curl -fsS http://127.0.0.1/myservices/
curl -fsS http://127.0.0.1/myservices/whisper/healthz
curl -fsS http://127.0.0.1/ffmpeg/healthz
curl -fsS http://127.0.0.1/whisper-dev/healthz
curl -fsS http://127.0.0.1/ffmpeg-dev/healthz
```

TODO:

- Document exact LAN route checks for every stable service after the next approved Gateway validation pass.

## Deployment / Reload / Restart Policy

Gateway/Caddy changes require explicit human approval.

Rules:

- Do not restart Gateway/Caddy as part of unrelated service deployments.
- Prefer service-specific restarts for FFmpeg, Whisper, or Home.
- Treat Caddy reload/restart as production-sensitive.
- Inspect live mounts before editing.
- Validate config before reload.
- Use readiness validation before route testing after reload/restart.
- Do not recreate `myservices-caddy` without a backup, route inventory, network validation plan, and explicit approval.

Config validation command documented in prior Caddy validation:

```text
docker exec myservices-caddy caddy validate --config /etc/caddy/Caddyfile
```

Reload command documented in prior Caddy validation:

```text
docker exec myservices-caddy caddy reload --config /etc/caddy/Caddyfile
```

Known prior result:

- `caddy validate` returned valid configuration.
- `caddy reload` completed without hard failure.
- Caddy container was reloaded, not restarted.

TODO:

- Confirm the current preferred live reload procedure before the next approved Caddy change.
- Document whether `docker compose exec caddy ...` should replace `docker exec myservices-caddy ...` for consistency.

## Readiness

Do not validate immediately after a Caddy reload or restart.

Readiness evidence should include:

- `myservices-caddy` is running.
- Home route responds.
- stable service health routes respond.
- dev routes respond only if they are expected to be active.
- route checks do not return transient 502 or connection reset results.

Suggested readiness sequence:

```text
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1/myservices/ >/tmp/gateway-home.html; then
    break
  fi
  sleep 2
done
```

Then validate stable routes:

```text
curl -fsS http://127.0.0.1/myservices/whisper/healthz
curl -fsS http://127.0.0.1/ffmpeg/healthz
```

Investigate 502 as possible:

- readiness race
- upstream container down
- wrong upstream name
- Caddy missing required Docker network
- stale live Caddyfile
- route order mismatch

## Runtime Validation Scenarios

### Scenario 1: Gateway Container Running

Goal:

- Confirm the Gateway container is up.

Expected container:

```text
myservices-caddy
```

Evidence to capture:

```text
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
cd /home/grigorynokhrin/myservices
docker compose ps caddy
```

Expected result:

- `myservices-caddy` is running.
- Host port `80` is exposed as documented.

### Scenario 2: Home Route Availability

Goal:

- Confirm Caddy routes Home/MyServices.

Route:

```text
/myservices/
```

Suggested check:

```text
curl -fsS http://127.0.0.1/myservices/
```

Expected result:

- Home page responds.
- No 502 or connection reset after readiness wait.

Evidence to capture:

- command
- success/failure
- short response excerpt if useful

### Scenario 3: FFmpeg Stable Route

Goal:

- Confirm Caddy routes stable FFmpeg.

Route:

```text
/ffmpeg/
```

Suggested check:

```text
curl -fsS http://127.0.0.1/ffmpeg/healthz
```

Expected result:

- FFmpeg stable health responds.
- If service-specific expected body is needed, use `docs/runbooks/ffmpeg.md`.

Evidence to capture:

- command
- response body or status
- Caddy logs if route fails

### Scenario 4: Whisper Stable Route

Goal:

- Confirm Caddy routes stable Whisper.

Route:

```text
/myservices/whisper/
```

Suggested check:

```text
curl -fsS http://127.0.0.1/myservices/whisper/healthz
```

Expected result:

- Whisper stable health responds with `ok` according to Whisper runbook evidence.

Evidence to capture:

- command
- response body
- Caddy logs if route fails

### Scenario 5: Dev Route Exists But Is Not Home-Published

Goal:

- Confirm dev routes work when expected, while Home still publishes stable tools only.

Dev route examples:

```text
/ffmpeg-dev/
/whisper-dev/
```

Suggested checks:

```text
curl -fsS http://127.0.0.1/ffmpeg-dev/healthz
curl -fsS http://127.0.0.1/whisper-dev/healthz
curl -fsS http://127.0.0.1/myservices/ | grep -E 'ffmpeg-dev|whisper-dev|/ffmpeg-dev|/whisper-dev'
```

Expected result:

- Dev health routes respond only when the corresponding dev service is running and routed.
- The Home grep check returns no matches.

Evidence to capture:

- dev route health result
- Home rendered link check

### Scenario 6: No Unintended Route Regression

Goal:

- Compare expected route inventory with actual responses.

Suggested checks:

```text
curl -fsS http://127.0.0.1/myservices/
curl -fsS http://127.0.0.1/myservices/whisper/healthz
curl -fsS http://127.0.0.1/ffmpeg/healthz
curl -fsS http://127.0.0.1/myservices/ocr
```

Expected result:

- Home works.
- stable routes work.
- placeholder routes still behave as documented unless intentionally changed.
- unmatched routes use the fallback behavior from the live Caddyfile.

TODO:

- Capture a current full route validation report after the next approved Gateway runtime task.

## Diagnostics

Use Caddy diagnostics to answer whether a failure is in the Gateway layer or an upstream service.

Start with:

```text
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
cd /home/grigorynokhrin/myservices
docker compose ps
docker compose logs --tail=100 caddy
```

Inspect live mounts:

```text
docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Inspect networks:

```text
docker inspect myservices-caddy --format '{{range $name, $net := .NetworkSettings.Networks}}{{println $name $net.IPAddress}}{{end}}'
```

Check DNS from inside Caddy when upstream resolution is suspicious:

```text
docker exec myservices-caddy getent hosts soma-ffmpeg
docker exec myservices-caddy getent hosts soma-ffmpeg-dev
docker exec myservices-caddy getent hosts soma-whisper-dev
docker exec myservices-caddy getent hosts whisper
docker exec myservices-caddy getent hosts home
```

Route reasoning:

- If direct service bind works but Caddy route fails, suspect Caddy route, network, DNS, or live/tracked config mismatch.
- If Caddy can resolve upstream but route still fails, inspect upstream service logs.
- If Caddy route returns 502 right after reload/restart, suspect readiness race first.
- If tracked config changed but runtime route did not, inspect the live mounted Caddyfile.
- If Home works but service link fails, check the target service route and Home link separately.
- If a dev service appears on Home, treat it as a Home publication policy issue, not necessarily a Gateway issue.

## Configuration

Discovered configuration:

| Item | Value |
| --- | --- |
| Container | `myservices-caddy` |
| Compose service | `caddy` |
| Image | `caddy:2-alpine` |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Tracked Caddyfile | `gateway/myservices/Caddyfile.current` |
| Live Caddyfile | `/home/grigorynokhrin/myservices/caddy/Caddyfile` |
| Container Caddyfile | `/etc/caddy/Caddyfile` |
| Host port | `80` |
| Legacy network | `myservices_default` |
| Dev/Caddy network | `compose_default` |
| Persistent dev network override | `gateway/myservices/compose.override.caddy-soma-dev.yaml` |

Tracked upstream names:

- `home:8000`
- `whisper:8000`
- `soma-whisper-dev:8000`
- `soma-ffmpeg:8000`
- `soma-ffmpeg-dev:8000`
- `image-upscale:7860`

TODO:

- Confirm current live Caddy networks and aliases after the next approved runtime inspection.
- Confirm whether the persistent Caddy compose override is active in the live deployment.
- Document any current live Caddyfile differences from the tracked reference.

## Integration Points

Home/MyServices:

- Caddy routes `/myservices*` to `home:8000`.
- More specific `/myservices/...` routes must appear before the Home catch-all.
- Home publication policy is owned by `docs/runbooks/home.md`.

Whisper stable:

- Caddy routes `/myservices/whisper*` to `whisper:8000`.
- Whisper operations are owned by `docs/runbooks/whisper.md`.

Whisper dev:

- Caddy routes `/whisper-dev*` to `soma-whisper-dev:8000`.
- Route requires Caddy to resolve the dev service network/alias.

FFmpeg stable:

- Caddy routes `/ffmpeg*` to `soma-ffmpeg:8000`.
- FFmpeg operations are owned by `docs/runbooks/ffmpeg.md`.

FFmpeg dev:

- Caddy routes `/ffmpeg-dev*` to `soma-ffmpeg-dev:8000`.
- Route order matters because `/ffmpeg-dev*` must precede `/ffmpeg*`.

Docker Compose:

- Current legacy production compose is outside this repo under `/home/grigorynokhrin/myservices/compose.yaml`.
- Repo compose files define FFmpeg stable/dev services and their Caddy network aliases.
- Caddy network persistence is documented by a tracked compose override, but live application must be verified.

Future stable services:

- Validate direct service route first.
- Add Gateway route only with explicit approval.
- Validate through Caddy.
- Publish on Home only after stable route validation.

## Operational Risks

- Gateway/Caddy is production-sensitive.
- Tracked Caddyfile may not be the live Caddyfile.
- Modifying tracked config alone may not change runtime.
- Modifying live config bypasses normal repo workflow unless paired with a tracked update.
- Restarting Gateway can affect Home, Whisper, FFmpeg, dev routes, placeholders, and historical routes.
- 502 can happen during readiness races.
- Wrong upstream names can break a service even when the container is healthy.
- Missing Docker network membership can make Caddy unable to resolve dev/stable `soma-*` services.
- Home publication and Gateway routing are separate concerns.
- Dev routes must not be published on Home.
- Do not change unrelated services during Gateway work.
- No Gateway changes without explicit approval.

## Known Failure Modes

| Symptom | Likely Cause | Resolution | Evidence To Inspect |
| --- | --- | --- | --- |
| 502 Bad Gateway | Upstream down, wrong upstream name, missing Docker network, or readiness race | Check Caddy logs, upstream container status, DNS from inside Caddy, and retry after readiness wait | `docker compose logs caddy`, route curl, `docker inspect myservices-caddy`, upstream logs |
| Route not updated after tracked config change | Tracked reference is not the live mounted Caddyfile | Inspect mounts, compare tracked/live config, update live only with approval, validate and reload | `docker inspect myservices-caddy`, live Caddyfile path |
| Home works but service route fails | Route-specific upstream, network, or service issue | Validate target service direct route if available, inspect Caddy route block and upstream logs | service health check, Caddy logs, service logs |
| Service works directly but fails through Gateway | Caddy route, DNS, network, or live config mismatch | Inspect Caddy networks, upstream DNS, route order, and live Caddyfile | `getent hosts` inside Caddy, route inventory |
| Dev service appears on Home | Home publication policy violation | Correct Home source/config and rebuild Home; Gateway route may remain valid as dev route | rendered Home HTML, Home runbook checks |
| Temporary connection reset after reload/restart | Readiness race | Wait and rerun readiness sequence before declaring failure | Caddy logs, container status, repeated curl |
| `/ffmpeg-dev/` is handled by `/ffmpeg*` | Route order regression | Keep `/ffmpeg-dev*` before `/ffmpeg*` in Caddyfile | tracked/live Caddyfile route order |
| Caddy cannot resolve `soma-*` upstream | Caddy missing `compose_default` network or alias missing on service | Verify network membership and service compose aliases; apply approved compose/network fix | `docker inspect`, compose config, Caddy DNS check |

## Rollback / Disable Strategy

Current repository evidence does not define a Gateway image rollback tag strategy.

Conservative concepts:

- Prefer service-level rollback or disabling Home link before changing Gateway when that is sufficient.
- For a bad tracked config change, revert the tracked Caddyfile change in Git.
- For a bad live config change, restore the known-good live Caddyfile backup if one was created for the approved task.
- Validate Caddy config before reload.
- Reload/restart only after explicit approval.
- Revalidate Home and stable routes after rollback.

Known prior backup example:

```text
/home/grigorynokhrin/myservices/caddy/Caddyfile.bak-20260602-181646
```

TODO:

- Document the current backup naming convention for future Gateway changes.
- Document exact rollback command sequence after the next approved Caddy change.
- Document whether Caddy image rollback is relevant or unnecessary for config-only route changes.

## Dependencies

Discovered dependencies:

- Docker
- Docker Compose
- Caddy
- `myservices-caddy`
- live production root `/home/grigorynokhrin/myservices`
- live Caddyfile path `/home/grigorynokhrin/myservices/caddy/Caddyfile`
- Home/MyServices service `home:8000`
- Whisper stable service `whisper:8000`
- Whisper dev service `soma-whisper-dev:8000`
- FFmpeg stable service `soma-ffmpeg:8000`
- FFmpeg dev service `soma-ffmpeg-dev:8000`
- Docker networks `myservices_default` and `compose_default`
- tracked repository reference config `gateway/myservices/Caddyfile.current`

## Documentation Links

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/runbooks/home.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/CADDY_WHISPER_DEV_ROUTE.md`
- `docs/services/gateway.md`
- `gateway/myservices/Caddyfile.current`
- `gateway/myservices/compose.override.caddy-soma-dev.yaml`

## Known Gaps

- Current live Caddyfile contents have not been re-inspected for this runbook.
- Current live Caddy mount has not been re-inspected for this runbook.
- Current live Caddy Docker networks have not been re-inspected for this runbook.
- It is not documented whether `gateway/myservices/compose.override.caddy-soma-dev.yaml` is active in the live compose project.
- Exact Gateway readiness loop should be confirmed during the next approved Gateway task.
- Exact current Gateway rollback command sequence is not documented.
- Structured Gateway validation reports under `docs/validations/` do not exist yet.
