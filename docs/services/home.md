# Home/MyServices Service Design

This is the canonical service design document for the Home/MyServices portal.

It describes what Home is, why it exists, how service publication works, how users move from the platform entry point to stable services, and what design decisions shape it. It is not an operations runbook. Operational procedures live in `docs/runbooks/home.md`.

## Purpose

Home/MyServices is the user-facing entry point for the home-server platform.

It exists to give trusted local users one stable place to discover and open tools that are ready for normal use. Without Home, users would need to remember service-specific routes, know which routes are stable, and avoid experimental endpoints manually.

Home solves a product-navigation problem:

- show the tools intended for daily use
- hide development and experiment routes from normal users
- make stable services discoverable
- keep service publication separate from service implementation
- provide a simple landing page for the current platform while the broader `soma` architecture evolves

Home fits into the platform as the portal layer:

- Gateway/Caddy makes routes available.
- Home decides which stable routes are visible to users.
- FFmpeg and Whisper perform the actual media/transcription work.
- Future stable services can be added deliberately after validation.

## Scope

Home does:

- act as the `/myservices/` platform landing page
- publish stable tools for user navigation
- provide service discovery for trusted local users
- link users to stable service routes
- encode the stable-only publication policy in the user-facing UI

Home does not do:

- media processing
- transcription
- routing or reverse proxying
- service execution
- job processing
- service health aggregation, unless a future implementation explicitly adds it
- dev-service validation
- long-running background work

Gateway/Caddy owns route availability. Individual services own their workflows. Home owns user-visible publication.

## Users And Use Cases

Intended users are the home-server owner and trusted local users on the local network.

Current supported user workflows:

- Open `http://10.0.1.196/myservices/`.
- Discover available stable tools.
- Launch FFmpeg from Home to use the stable media tool.
- Launch Whisper from Home to use the stable transcription tool.
- Return to Home from service pages where services provide a Home link.

Expected future workflow:

- Additional stable services may appear on Home after direct service validation, Gateway validation, and explicit publication approval.

Home is not intended as an engineering index of every route in the system. Dev routes may exist and may be reachable directly, but they are not Home-published tools.

## Service Topology

Stable Home service:

| Field | Value |
| --- | --- |
| Route | `/myservices/` |
| LAN URL | `http://10.0.1.196/myservices/` |
| Container | `myservices-home` |
| Compose service | `home` |
| Container port | `8000` documented in `docs/RUNTIME_STATUS.md` |
| Runtime path | `/home/grigorynokhrin/myservices/home` |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Tracked source in this repo | Not found |
| Publication policy | Stable services only |

Gateway/Caddy relationship:

- Caddy routes `/myservices*` to `home:8000`.
- More specific `/myservices/...` routes must appear before the Home catch-all.
- Gateway operations live in `docs/runbooks/gateway.md`.

FFmpeg relationship:

- Stable route: `/ffmpeg/`
- Expected Home entry: `FFmpeg -> /ffmpeg/`
- Dev route `/ffmpeg-dev/` must not replace the stable Home entry.

Whisper relationship:

- Stable route: `/myservices/whisper/`
- Expected Home entry: Whisper stable route
- Dev route `/whisper-dev/` must not replace the stable Home entry.

Operational commands for rebuild, restart, readiness, validation, and troubleshooting belong in `docs/runbooks/home.md`.

## Architecture Overview

The tracked repository does not contain the Home source code, so this design document describes the architecture from observed runtime and documentation evidence.

Major conceptual components:

| Component | Evidence | Responsibility | Inputs | Outputs | Constraints |
| --- | --- | --- | --- | --- | --- |
| Landing page layer | `myservices-home`, route `/myservices/` | Render the user-facing portal page | HTTP request through Caddy | HTML landing page | Source is documented under `/home/grigorynokhrin/myservices/home`, not tracked here. |
| Service catalog layer | Home publication docs and validation checks | Decide which services appear to users | Stable publication choices | Visible service entries | Must publish stable tools only. Exact config file is TODO. |
| Navigation/UI layer | Home validation checks for FFmpeg and Whisper links | Provide links from Home to services | Published service entries | Browser navigation to service routes | Must not expose dev routes as stable tools. |
| Route relationship layer | `gateway/myservices/Caddyfile.current` | Relate Home links to Gateway routes | Route prefixes | Service pages reached through Caddy | Gateway availability is separate from Home visibility. |
| Publication governance | `docs/ENGINEERING_WORKFLOW.md`, `docs/FIRST_RELEASE_PLAYBOOK.md`, runbooks | Gate when a service can appear on Home | Validation evidence, approval | Stable Home entry | Publication changes require explicit approval. |

Observed runtime evidence:

- `myservices-home` runs as the `home` compose service.
- `docs/RUNTIME_STATUS.md` observed its command beginning with `uvicorn app:app`.
- The live Home source path is documented as `/home/grigorynokhrin/myservices/home`.
- Home source changes require rebuild/restart when the source is baked into the image.

TODO:

- Inspect live Home source in an approved server task to confirm the actual framework, template structure, and publication configuration.

## Service Publication Model

Home publication is a deliberate product decision.

A service existing in the repository, running as a container, or being routable through Gateway does not automatically mean it should appear on Home.

Publication gates:

1. The service has a stable route.
2. The service has passed direct validation where applicable.
3. The service has passed Gateway/Caddy validation.
4. The service is intended for normal user-facing use.
5. The human owner explicitly approves Home publication.
6. Home is updated to link to the stable route.
7. Home is rebuilt/restarted when required.
8. Rendered Home output is validated.

Current expected published services:

- FFmpeg
- Whisper

Current expected non-published services:

- `ffmpeg-dev`
- `whisper-dev`
- experimental tools
- prototype services
- placeholder routes

Architectural rule:

```text
Inventory != publication.
Route availability != Home visibility.
```

## Navigation Model

User navigation is intentionally simple:

```text
Home -> stable service -> service workflow
```

Expected behavior:

1. User opens `/myservices/`.
2. Home renders stable service entries.
3. User selects a service entry.
4. Browser navigates to the service route.
5. The selected service operates independently.
6. User may return to Home using a service-provided Home link where available.

Current expected route relationships:

- Home page: `/myservices/`
- FFmpeg stable: `/ffmpeg/`
- Whisper stable: `/myservices/whisper/`

Navigation constraints:

- Dev services must not be primary Home entries.
- Home should link to stable routes, not direct localhost binds.
- Home does not orchestrate service workflows after navigation.
- Each service owns its own job pages, forms, diagnostics, and artifacts.

## Data Flow

Home interaction flow:

1. Browser requests `/myservices/`.
2. Caddy matches the `/myservices*` catch-all after more specific service routes.
3. Caddy proxies the request to `home:8000`.
4. Home renders the landing page.
5. User clicks a published service entry.
6. Browser requests the linked service route.
7. Gateway/Caddy routes that request to the service upstream.
8. The service handles its own workflow independently.

Home does not pass uploaded files, jobs, artifacts, model state, media metadata, or transcription data between services. It only provides navigation.

## Service Registry Relationship

`docs/SERVICES_REGISTRY.md` is inventory.

Home is publication.

The registry records services and supporting components whether they are stable, dev, deprecated, maintenance, or placeholder. Home should show only stable user-facing tools.

Examples:

- FFmpeg is in the registry and is Home-published because it is stable.
- Whisper is in the registry and is Home-published because it is stable.
- FFmpeg dev is in the registry but is not Home-published.
- Whisper dev is in the registry but is not Home-published.
- Gateway is in the registry but is not a user tool shown on Home.
- Placeholder or deprecated routes are not automatically Home entries.

The registry should remain broader than Home. Home should remain narrower than the registry.

## Routing Relationship

Gateway determines route availability.

Home determines user visibility.

These are separate concerns:

- A Gateway route can exist for engineering validation without appearing on Home.
- A Home link can be stale or wrong even if the Gateway route exists.
- A service can be healthy directly but not published on Home.
- Home publication should happen only after route validation.

Tracked Gateway evidence:

```text
handle /myservices* {
    reverse_proxy home:8000
}
```

Important routing consequences:

- `/myservices*` is a catch-all for Home.
- More specific `/myservices/...` routes, such as `/myservices/whisper*`, must remain before the Home catch-all.
- FFmpeg stable uses `/ffmpeg/`, so its Home entry points outside the `/myservices/` prefix.
- Dev routes such as `/ffmpeg-dev/` and `/whisper-dev/` may exist through Gateway but should not appear on Home.

## Configuration

Discovered configuration:

| Item | Value |
| --- | --- |
| Container | `myservices-home` |
| Compose service | `home` |
| Runtime root | `/home/grigorynokhrin/myservices` |
| Runtime source path | `/home/grigorynokhrin/myservices/home` |
| Production compose path | `/home/grigorynokhrin/myservices/compose.yaml` |
| Container port | `8000` documented in `docs/RUNTIME_STATUS.md` |
| Gateway upstream | `home:8000` |
| User-facing route | `/myservices/` |
| LAN URL | `http://10.0.1.196/myservices/` |

Unknown/TODO:

- exact source ownership and whether Home should eventually move into this repo
- exact Home source file that defines service entries
- exact publication configuration format
- exact build context
- exact environment variables
- exact mounted files and volumes
- exact health endpoint, if any
- exact static asset behavior

## Integration Points

Gateway/Caddy:

- Routes `/myservices*` to `home:8000`.
- Owns route availability and proxy behavior.
- Operational source: `docs/runbooks/gateway.md`.

FFmpeg stable:

- Home should publish `FFmpeg -> /ffmpeg/`.
- FFmpeg owns media-processing workflows after navigation.
- Design source: `docs/services/ffmpeg.md`.
- Operational source: `docs/runbooks/ffmpeg.md`.

Whisper stable:

- Home should publish the stable Whisper route `/myservices/whisper/`.
- Whisper owns transcription workflows after navigation.
- Design source: `docs/services/whisper.md`.
- Operational source: `docs/runbooks/whisper.md`.

Docker Compose:

- Home is part of the legacy production compose project under `/home/grigorynokhrin/myservices`.
- Source changes require rebuild/restart when source is baked into the image.

Future stable services:

- Should enter the registry first.
- Should validate direct and Gateway behavior before Home publication.
- Should be linked from Home only after explicit approval.
- Should not replace dev routes with stable entries accidentally.

## Constraints

Platform constraints:

- Ubuntu Server 24.04
- Intel Core i5-14600KF
- 32GB DDR4
- NVIDIA RTX 3060 12GB
- SSD 480GB
- local home-server environment

Home-specific implications:

- Home should stay lightweight and avoid owning heavy service work.
- Home should not consume GPU or significant storage.
- Home should not manage media files, transcripts, model caches, or job artifacts.
- Home should avoid coupling the portal to service internals.
- Home changes can still be production-sensitive because they alter what users see and launch.

## Security And Safety Considerations

Safety rules:

- Home publishes stable services only.
- Dev routes must not appear as normal Home entries.
- Publication changes require explicit approval.
- Home publication and Gateway routing are separate approvals when both change.
- Home source appears to be outside this repo, so live edits can bypass normal repo controls.
- After Home source changes, rebuild/restart is required when source is baked into the image.
- Rendered Home output must be checked after publication changes.

Security considerations:

- Home is a navigation surface for trusted local users.
- It should not expose secrets, tokens, internal paths, generated artifacts, or private media.
- It should not provide arbitrary command execution.
- It should not expose development tools as user-facing production tools.
- It should not imply that placeholder or deprecated routes are supported services.

## Operational Boundaries

Operational procedures belong to:

- `docs/runbooks/home.md`

This design document should not duplicate:

- rebuild commands
- restart commands
- readiness validation
- troubleshooting procedures
- deployment procedures
- rollback procedures

Use the runbook for live work. Use this design document for understanding the role and boundaries of Home.

## Design Decisions

| Decision | Rationale | Consequences |
| --- | --- | --- |
| Home is a dedicated platform entry point. | Users need one stable place to discover tools. | Home becomes the user-facing portal layer instead of each service being discovered manually. |
| Home publishes stable services only. | Dev routes are for engineering validation and can change. | Publication requires deliberate approval; dev tools remain reachable only through direct/dev routes. |
| Publication is decoupled from Gateway routing. | A route can exist for validation without being ready for normal use. | Both route validation and Home publication must be checked separately. |
| Home does not own service logic. | FFmpeg and Whisper have different runtime risks and workflows. | Home stays lightweight; services own jobs, artifacts, diagnostics, and processing. |
| Home remains in the legacy runtime for now. | Current live evidence places Home under `/home/grigorynokhrin/myservices/home`. | Repo docs must mark source details TODO until live source ownership is reconciled. |
| Home changes require rebuild when source is baked into the image. | Runtime evidence and operational lessons show source edits may not affect the running UI until rebuild/restart. | Publication changes need operational validation, not only source edits. |
| Home is narrower than the service registry. | The registry tracks all services and components; users should see only stable tools. | Registry additions do not automatically become Home entries. |

## Known Gaps

- Exact Home source ownership/tracking status needs a live audit.
- Exact Home source file that defines published service links is not tracked here.
- Exact publication configuration format is unknown.
- Exact Home build context is not documented in this repo.
- Exact Home environment variables are not documented.
- Exact mounted files/volumes are not documented.
- Exact Home health endpoint is not documented.
- Exact rollback strategy is not documented.
- It is not yet decided whether Home source should be migrated into this repository.
- Structured validation reports for Home publication changes do not exist yet.

## Future Evolution

Potential future improvements:

- Move or mirror Home source into the repository if that becomes the chosen ownership model.
- Define a structured service-entry metadata format.
- Add service categories if the number of stable tools grows.
- Add optional health indicators only if they can be implemented without making Home a monitoring system.
- Show version or release visibility for stable services if release documentation becomes structured.
- Add validation reports for Home publication changes under `docs/validations/`.
- Create ADRs if Home publication policy or route model changes materially.
- Keep `docs/services/gateway.md` aligned with Home publication boundaries when the route model changes.

Future work should preserve the current boundary: Home is product navigation, not service orchestration.

## Related Documents

- `docs/runbooks/home.md`
- `docs/runbooks/gateway.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
