# Gateway/Caddy Service Design

This is the canonical service design document for the Gateway/Caddy component.

It describes what Gateway/Caddy is, why centralized routing exists, how services are exposed, how configuration ownership works, and what design decisions shape the routing layer. It is not an operations runbook. Operational procedures live in `docs/runbooks/gateway.md`.

## Purpose

Gateway/Caddy is the routing layer for the home-server platform.

It exists to provide a single HTTP entry point that maps user-facing and development route prefixes to the correct internal service upstreams. Without a centralized gateway, users and operators would need to know individual container ports, direct binds, Docker network details, and dev/stable differences.

Gateway solves an infrastructure-routing problem:

- expose stable and selected dev services through consistent route prefixes
- keep users away from direct container networking details
- allow Home/MyServices to be a portal while Caddy owns proxying
- keep service routing separate from service implementation
- provide explicit route boundaries between stable, dev, historical, and placeholder services

Gateway fits into the platform as the reverse-proxy layer:

- Browser requests enter through Caddy.
- Caddy matches route rules.
- Caddy proxies to the correct upstream service.
- Home decides which stable services are visible to users.
- Individual services handle application workflows after routing.

## Scope

Gateway does:

- route exposure
- reverse proxying
- stable service entry points
- selected dev service entry points
- route isolation by prefix
- placeholder responses where explicitly configured
- fallback handling for unmatched routes

Gateway does not do:

- Home publication decisions
- media processing
- transcription
- application logic
- job execution
- artifact handling
- service health aggregation
- Home UI ownership
- service implementation ownership

Gateway determines route availability. Home determines user visibility. Services determine behavior after a request reaches them.

## Users And Use Cases

Gateway has two main consumers:

- browser users accessing Home and stable tools
- operators/developers validating service routes

Repository-supported use cases:

- User opens Home through `/myservices/`.
- User opens stable Whisper through `/myservices/whisper/`.
- User opens stable FFmpeg through `/ffmpeg/`.
- Developer validates Whisper dev through `/whisper-dev/`.
- Developer validates FFmpeg dev through `/ffmpeg-dev/`.
- Operator checks placeholder or historical routes without treating them as stable Home entries.

Gateway is not a product UI. It enables access, but it does not decide which tools should appear on Home.

## Service Topology

Known Gateway topology:

| Field | Value |
| --- | --- |
| Container | `myservices-caddy` |
| Compose service | `caddy` |
| Image | `caddy:2-alpine` observed in `docs/RUNTIME_STATUS.md` |
| Tracked config | `gateway/myservices/Caddyfile.current` |
| Historical live config | `/home/grigorynokhrin/myservices/caddy/Caddyfile` |
| Container config path | `/etc/caddy/Caddyfile` from prior validation |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Host port | `80` observed in `docs/RUNTIME_STATUS.md` |
| Legacy network | `myservices_default` |
| Dev/Caddy network | `compose_default` |

Home relationship:

- Gateway routes `/myservices*` to `home:8000`.
- Home publication policy and design live in `docs/services/home.md`.

FFmpeg relationship:

- Gateway routes `/ffmpeg*` to `soma-ffmpeg:8000`.
- Gateway routes `/ffmpeg-dev*` to `soma-ffmpeg-dev:8000`.
- `/ffmpeg-dev*` must be ordered before `/ffmpeg*`.

Whisper relationship:

- Gateway routes `/myservices/whisper*` to `whisper:8000`.
- Gateway routes `/whisper-dev*` to `soma-whisper-dev:8000`.

Future services:

- should add stable routes only after direct validation and explicit Gateway approval
- should add Home publication only after route validation and explicit Home approval

Operations for inspection, reload, validation, and rollback belong in `docs/runbooks/gateway.md`.

## Architecture Overview

Major components:

| Component | Evidence | Responsibility | Inputs | Outputs | Constraints |
| --- | --- | --- | --- | --- | --- |
| Routing layer | `gateway/myservices/Caddyfile.current` | Match route prefixes and determine handler blocks | HTTP request path | selected route handler | Route order matters for overlapping prefixes. |
| Reverse proxy layer | `reverse_proxy` directives | Forward matched requests to service upstreams | matched request | upstream request/response | Upstream names must resolve from Caddy's Docker networks. |
| Route configuration layer | tracked Caddyfile and historical live Caddyfile | Record route intent and live routing behavior | Caddyfile blocks | runtime route table | Tracked config may differ from live mounted config. |
| Upstream mapping layer | Caddyfile upstreams, compose aliases | Map logical routes to container DNS names and ports | route prefix | `home:8000`, `soma-ffmpeg:8000`, etc. | Requires correct Docker network membership and aliases. |
| Fallback handling | final `handle` block | Provide response for unmatched routes | unmatched request | `Not found` response | Should remain last. |
| Route segmentation | stable/dev/historical/placeholder prefixes | Separate user-facing, dev, and non-current routes | route categories | predictable route behavior | Dev routes must not imply Home publication. |

Gateway is intentionally infrastructure-only. It should remain small, explicit, and readable so route changes are auditable.

## Routing Model

Gateway uses path-prefix route blocks.

Discovered route classes:

### Stable Routes

Stable routes are intended for normal use:

- `/myservices/`
- `/myservices/whisper/`
- `/ffmpeg/`

Stable routes may be Home-published, but Home publication is still a separate decision.

### Dev Routes

Dev routes support engineering validation:

- `/whisper-dev/`
- `/ffmpeg-dev/`

Dev routes may be routable through Caddy while remaining absent from Home.

### Historical And Placeholder Routes

Historical/placeholder routes are tracked but not part of the current stable Home tool set:

- `/myservices/image-upscale/`
- `/myservices/ocr*`

These routes should not be treated as current stable service publication without separate evidence.

### Fallback Route

The final fallback responds to unmatched requests:

```text
handle {
    respond "Not found" 404
}
```

Route-order rules:

- More specific `/myservices/...` routes must appear before `/myservices*`.
- `/ffmpeg-dev*` must appear before `/ffmpeg*`.
- Fallback must remain last.

## Upstream Model

The Gateway model is:

```text
Gateway route -> upstream service
```

Tracked upstream relationships:

| Gateway route | Upstream | Notes |
| --- | --- | --- |
| `/myservices/image-upscale` | redirect to `/myservices/image-upscale/` | Historical redirect. |
| `/myservices/image-upscale/*` | `image-upscale:7860` | Historical service route. |
| `/myservices/whisper*` | `whisper:8000` | Stable Whisper route in legacy compose network. |
| `/whisper-dev*` | `soma-whisper-dev:8000` | Dev Whisper route; requires dev network reachability. |
| `/ffmpeg-dev*` | `soma-ffmpeg-dev:8000` | Dev FFmpeg route; uses `compose_default` alias. |
| `/ffmpeg*` | `soma-ffmpeg:8000` | Stable FFmpeg route; uses `compose_default` alias. |
| `/myservices/ocr*` | Caddy response | Placeholder, not proxied. |
| `/myservices*` | `home:8000` | Home/MyServices portal route. |

Upstream constraints:

- upstream names must resolve from inside the Caddy container
- upstream ports must match service container ports
- Caddy must share a Docker network with the upstream service
- compose aliases must match tracked route upstream names
- route availability does not imply Home publication

## Publication Vs Routing

Gateway routing is not Home publication.

Architectural rule:

```text
Gateway routing != Home publication
```

Gateway controls accessibility:

- whether a request path can reach an upstream
- whether Caddy can resolve and proxy to the service
- whether route order maps the request to the intended upstream

Home controls visibility:

- which stable services are shown to users
- which route labels appear on the landing page
- whether a tool is presented as ready for normal use

Examples:

- `/ffmpeg-dev/` may be routable but must not be Home-published.
- `/whisper-dev/` may be routable but must not replace stable Whisper on Home.
- `/ffmpeg/` is routable and currently Home-published as stable FFmpeg.
- `/myservices/whisper/` is routable and Home-published as stable Whisper.
- Placeholder routes may exist without becoming visible user tools.

This separation lets engineering validation happen without prematurely exposing experimental services as product entries.

## Configuration Ownership Model

Repository configuration does not automatically equal runtime configuration.

Tracked route reference:

```text
gateway/myservices/Caddyfile.current
```

Historical live route file:

```text
/home/grigorynokhrin/myservices/caddy/Caddyfile
```

Container route file:

```text
/etc/caddy/Caddyfile
```

Prior validation documented this mount:

```text
/home/grigorynokhrin/myservices/caddy/Caddyfile -> /etc/caddy/Caddyfile
```

Why the distinction exists:

- The repository stores reference configuration and desired intent.
- The current live runtime is still under `/home/grigorynokhrin/myservices`.
- The live Caddy container reads the file mounted into `/etc/caddy/Caddyfile`.
- A commit changing the tracked Caddyfile does not by itself change the live mounted file.
- A live edit without a tracked update can make the repository stale.

Design consequence:

- All Gateway changes need both configuration intent and runtime validation.
- The runbook owns the operational inspection and reload procedure.
- This design doc owns the architectural distinction.

## Data Flow

Request flow:

1. User or operator requests a URL on the server.
2. Caddy receives the HTTP request on host port `80`.
3. Caddy evaluates route blocks in order.
4. Matching route either redirects, responds directly, or proxies to an upstream.
5. Upstream service handles application behavior.
6. Gateway returns the upstream response to the browser.

Examples:

```text
/myservices/ -> Caddy -> home:8000 -> Home page
/myservices/whisper/ -> Caddy -> whisper:8000 -> Whisper UI
/ffmpeg/ -> Caddy -> soma-ffmpeg:8000 -> FFmpeg UI
/ffmpeg-dev/ -> Caddy -> soma-ffmpeg-dev:8000 -> FFmpeg dev UI
```

Gateway does not inspect service job state, modify artifacts, run transcription, transcode media, or decide service publication.

## Route Lifecycle

Route introduction:

1. Service exists with an internal upstream and route plan.
2. Direct service validation passes where applicable.
3. Caddy route is proposed in tracked reference config.
4. Live Gateway change is explicitly approved.
5. Live Caddyfile is updated and validated.
6. Caddy reload/restart is performed according to the runbook.
7. Route is validated through Caddy.
8. Home publication is handled separately if the route is stable.

Route validation:

- service-specific route health belongs in service runbooks
- global route/proxy validation belongs in `docs/runbooks/gateway.md`
- Home publication validation belongs in `docs/runbooks/home.md`

Route retirement:

- remove Home publication first if user visibility should end
- remove or alter Gateway route only with explicit Gateway approval
- keep tracked reference and live config in sync
- preserve rollback notes for route-sensitive changes

## Integration Points

Home/MyServices:

- Gateway routes `/myservices*` to `home:8000`.
- More specific `/myservices/...` routes must precede the catch-all.
- Home decides user-visible publication.

FFmpeg stable:

- Gateway routes `/ffmpeg*` to `soma-ffmpeg:8000`.
- FFmpeg stable compose attaches `soma-ffmpeg` to `compose_default` with alias `soma-ffmpeg`.

FFmpeg dev:

- Gateway routes `/ffmpeg-dev*` to `soma-ffmpeg-dev:8000`.
- FFmpeg dev compose attaches `soma-ffmpeg-dev` to `compose_default` with alias `soma-ffmpeg-dev`.

Whisper stable:

- Gateway routes `/myservices/whisper*` to `whisper:8000`.
- Stable Whisper remains under the legacy production compose owner.

Whisper dev:

- Gateway routes `/whisper-dev*` to `soma-whisper-dev:8000`.
- Prior validation documented the need for Caddy to reach the dev Docker network.

Docker Compose:

- Current live production compose is outside this repo at `/home/grigorynokhrin/myservices/compose.yaml`.
- `gateway/myservices/compose.override.caddy-soma-dev.yaml` documents a Caddy network override for `compose_default`.
- FFmpeg stable/dev compose files declare Caddy network aliases.

Runtime filesystem:

- live Caddyfile is documented under `/home/grigorynokhrin/myservices/caddy/Caddyfile`
- tracked reference lives under `gateway/myservices/Caddyfile.current`

Future services:

- should define route prefix, upstream name, port, environment category, Home publication intent, and validation expectations before being exposed

## Configuration

Discovered configuration:

| Item | Value |
| --- | --- |
| Container | `myservices-caddy` |
| Compose service | `caddy` |
| Image | `caddy:2-alpine` |
| Tracked Caddyfile | `gateway/myservices/Caddyfile.current` |
| Historical live Caddyfile | `/home/grigorynokhrin/myservices/caddy/Caddyfile` |
| Container Caddyfile | `/etc/caddy/Caddyfile` |
| Production compose | `/home/grigorynokhrin/myservices/compose.yaml` |
| Host HTTP port | `80` |
| Legacy network | `myservices_default` |
| Dev/Caddy network | `compose_default` |
| Caddy dev-network override | `gateway/myservices/compose.override.caddy-soma-dev.yaml` |

Tracked upstreams:

- `home:8000`
- `whisper:8000`
- `soma-whisper-dev:8000`
- `soma-ffmpeg-dev:8000`
- `soma-ffmpeg:8000`
- `image-upscale:7860`

TODO:

- confirm current live mount inventory
- confirm current live network inventory
- confirm whether the Caddy dev-network override is active live
- document exact current live Caddyfile differences from tracked reference
- document future route metadata format if one is introduced

## Constraints

Verified platform constraints:

- local home-server platform
- Ubuntu Server 24.04 from current-state docs
- Docker-based deployment
- Caddy-based reverse proxy
- active legacy runtime under `/home/grigorynokhrin/myservices`
- target/repo-managed runtime still evolving under `soma`
- local network exposure through host port `80`
- route layer is production-sensitive

Design implications:

- Gateway should stay simple and explicit.
- Route changes should be small and auditable.
- Service-specific behavior should stay out of Gateway.
- Route configuration must respect current legacy/live ownership.
- Dev and stable routes may coexist, but they must remain clearly separated.
- Gateway should not be used to imply Home publication or service maturity.

## Security And Safety Considerations

Safety considerations:

- Gateway/Caddy changes require explicit approval.
- Tracked and live config may differ.
- Live Gateway changes can affect all exposed services.
- A route can accidentally expose a dev or placeholder service.
- Route order can shadow intended routes.
- Wrong upstream names can break services even if containers are healthy.
- Network membership controls which upstream names Caddy can resolve.
- Gateway must not be changed as a side effect of unrelated service work.

Publication safety:

- Gateway route availability does not make a service stable.
- Home publication must remain stable-only.
- Dev routes must not be mistaken for Home-published services.

Configuration safety:

- tracked config should represent intended route state
- live config must be inspected before runtime changes
- live edits should be reconciled back into repo docs/config when approved

## Operational Boundaries

Operational procedures belong to:

- `docs/runbooks/gateway.md`

This design document should not duplicate:

- restart procedures
- reload procedures
- validation procedures
- troubleshooting procedures
- rollback procedures
- live mount inspection sequences

Use the runbook for live Gateway work. Use this design document for understanding Gateway responsibilities and route architecture.

## Design Decisions

| Decision | Rationale | Consequences |
| --- | --- | --- |
| Use a centralized Caddy Gateway. | A single host entry point simplifies browser access and hides direct container ports. | Route changes affect multiple services and must be treated as production-sensitive. |
| Separate routing from Home publication. | Some routes are useful for validation but not ready for normal users. | A service can be routable while absent from Home. |
| Keep Gateway infrastructure-only. | Application logic belongs in services; product navigation belongs in Home. | Gateway remains focused on prefix matching and proxying. |
| Maintain tracked and live config distinction. | Current runtime reads a mounted file outside this repo. | Operators must inspect live mounts before assuming a tracked change is deployed. |
| Allow stable and dev routes to coexist. | Dev validation needs real routing without replacing stable services. | Route classes and Home publication rules must remain clear. |
| Use explicit route prefixes. | Prefix routes are easy to audit and validate. | Route order matters for overlapping prefixes such as `/ffmpeg-dev*` and `/ffmpeg*`. |
| Use Docker DNS upstream names. | Containers can reach services by network aliases. | Caddy must share networks with upstream services. |
| Preserve historical/placeholder routes until separately retired. | Existing routes may be useful for rollback, history, or future work. | Their presence must not be confused with stable Home publication. |

## Known Gaps

- Current live mount inventory has not been re-inspected for this design doc.
- Current live network inventory has not been re-inspected for this design doc.
- It is not documented whether `gateway/myservices/compose.override.caddy-soma-dev.yaml` is active in the live compose project.
- Exact live Caddyfile differences from `gateway/myservices/Caddyfile.current` are not documented.
- Route ownership metadata is not structured outside prose/table docs.
- Future service registration model is not defined.
- Gateway rollback strategy is only documented conceptually.
- Structured Gateway validation reports under `docs/validations/` do not exist yet.
- Target long-term migration from `myservices-caddy` to a future `soma` gateway remains outside this design doc.

## Future Evolution

Potential future improvements:

- add route metadata to the service registry
- create structured validation reports for Gateway changes
- define a formal route ownership table
- document a stable route lifecycle checklist as a playbook
- add ADRs for significant routing model changes
- reconcile live Caddyfile state with tracked reference after approved server inspection
- define a future `soma` gateway migration path
- integrate route health checks into platform health reporting without making Gateway own service internals
- add future stable and dev services using the same stable/dev separation model

Future work should preserve the core boundary: Gateway routes requests; Home publishes stable tools; services own behavior.

## Related Documents

- `docs/runbooks/gateway.md`
- `docs/runbooks/home.md`
- `docs/services/home.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
