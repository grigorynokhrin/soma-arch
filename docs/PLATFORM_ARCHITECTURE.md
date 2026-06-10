# PLATFORM_ARCHITECTURE

This document defines the platform-level architecture identity for `soma`.

It answers what the major names, roots, and ownership boundaries mean. It is not a service registry, runbook, release note, or live runtime report.

Volatile runtime facts must be refreshed from the repository and server before operational work.

## 1. Purpose

The purpose of this document is to define the platform vocabulary and ownership model:

- what `soma` means
- what `soma-arch` means
- what the target runtime roots mean
- what remains legacy
- which repo directories own source, compose, gateway references, runtime templates, and documentation
- how platform concepts relate to Home publication and Gateway/Caddy routing

Use this document for architecture identity. Use `docs/SERVICES_REGISTRY.md` for current inventory, service runbooks for operations, and service design docs for service behavior.

## 2. Quick Platform Map

```text
Soma platform
├── Control plane
│   └── soma-arch repo
│       ├── docs/
│       ├── services/
│       ├── compose/
│       ├── gateway/
│       └── runtime/
├── Target runtime
│   └── /srv/soma
│       ├── data/
│       ├── services/
│       ├── worktrees/
│       ├── backups/
│       └── ops/
└── Legacy runtime
    └── /home/grigorynokhrin/myservices
        ├── home
        ├── whisper
        └── caddy
```

Current ownership snapshot:

| Area | Current ownership |
| --- | --- |
| FFmpeg stable/dev | Repo-managed; running from current feature worktree compose; data under `/srv/soma/data`. |
| Whisper stable | Legacy `myservices` contour. |
| Whisper dev | Mixed/server-local `/srv/soma` compose ownership. |
| Home | Legacy `myservices` contour. |
| Gateway/Caddy | Legacy `myservices` contour with tracked reference config in this repo. |
| Supir/Tesseract | Placeholders/prototypes; not active stable services unless separately promoted. |

## 3. Platform Identity

`soma` is the platform/product identity for the home-server service environment.

It refers to the intended platform as a whole:

- user-facing stable tools
- dev/test services
- Gateway/Caddy routing
- Home/MyServices publication
- runtime data roots
- operational workflow
- documentation and release discipline

`soma` is not a single container, service, route, or directory.

## 4. Control Plane

`soma-arch` is the Git control-plane repository.

It owns:

- documentation
- tracked service source
- tracked Compose definitions
- tracked Gateway/Caddy reference configuration
- runtime templates and helper scripts
- reports and architecture records

Known workspace paths:

| Path | Meaning | State |
| --- | --- | --- |
| `/Users/grigorynokhrin/projects/soma-arch` | Mac editing workspace | Directly observed during local audits. |
| `/home/grigorynokhrin/soma-arch` | Server reference repo path | Documented; requires live server confirmation before runtime work. |

The control plane is not the same thing as the runtime. A committed repository change does not affect live services until the server pulls, builds/restarts where needed, waits for readiness, and validates runtime behavior.

## 5. Target Runtime Roots

`/srv/soma` is the target server runtime root for the `soma` platform.

It is the intended home for repo-managed runtime layout and supporting operational assets. Its exact live contents must be confirmed on the server before runtime work.

Target root meanings:

| Path | Meaning |
| --- | --- |
| `/srv/soma` | Target platform runtime root. |
| `/srv/soma/worktrees` | Target server feature-worktree root. |
| `/srv/soma/worktrees/<branch-or-task>` | Server checkout used to validate a specific branch or task without switching the main server repo. |
| `/srv/soma/data` | Target service data root for repo-managed soma services. |
| `/srv/soma/data/<service>` | Target persistent runtime data for a specific soma service. |

Current known example:

```text
/srv/soma/worktrees/ffmpeg-dev-skeleton
```

This path is documented as the server worktree for branch `feature/ffmpeg-dev-skeleton`; its current live HEAD requires server confirmation.

## 6. Legacy Runtime Contour

`/home/grigorynokhrin/myservices` is the legacy runtime contour.

It remains production-sensitive because it is documented as owning the existing Home/MyServices stack and production compose file.

Documented legacy ownership includes:

| Path / Name | Meaning |
| --- | --- |
| `/home/grigorynokhrin/myservices` | Legacy/stable runtime root. |
| `/home/grigorynokhrin/myservices/compose.yaml` | Production compose file for legacy services. |
| `/home/grigorynokhrin/myservices/home` | Live Home source location documented by runbooks. |
| `/home/grigorynokhrin/myservices/caddy/Caddyfile` | Historical live Caddyfile path documented by Gateway docs. |
| `myservices-home` | Home container in the legacy contour. |
| `myservices-caddy` | Gateway/Caddy container in the legacy contour. |
| `myservices-whisper` | Stable Whisper container in the legacy contour. |

Do not delete, rename, move, or replace this contour without explicit approval, a documented migration plan, and rollback path.

## 7. Repository Directory Ownership

The repository directory model is:

| Path | Owner role |
| --- | --- |
| `docs/` | Documentation system. |
| `services/` | Tracked service source. |
| `compose/` | Tracked Compose definitions. |
| `gateway/` | Tracked Gateway/Caddy reference configuration. |
| `runtime/` | Runtime templates and helper scripts intended for `/srv/soma`. |
| `scripts/` | Repository helper script area. |
| `ops/` | Operations notes/placeholders. |
| `.github/` | GitHub templates/configuration. |

Directory boundaries:

- `docs/` should describe and govern work, not become runtime state.
- `services/` should hold source code, not user uploads, generated artifacts, model caches, or runtime data.
- `compose/` should contain reproducible compose definitions that can be run from the repo root.
- `gateway/` stores reference configuration; it is not proof of live Caddy state.
- `runtime/` stores templates/helpers, not the live `/srv/soma` filesystem itself.

## 8. Documentation Ownership

Canonical documentation responsibilities:

| Document | Responsibility |
| --- | --- |
| `docs/PLATFORM_ARCHITECTURE.md` | Platform identity, roots, and high-level ownership boundaries. |
| `docs/ENGINEERING_WORKFLOW.md` | Engineering process, gates, validation policy, safety rules. |
| `docs/DOCUMENTATION_ARCHITECTURE.md` | Documentation hierarchy, structure, lifecycle, and ownership model. |
| `docs/SERVICES_REGISTRY.md` | Current service/component inventory. |
| `docs/DOCUMENTATION_RECONCILIATION.md` | Documentation ownership audit and classification. |
| `docs/runbooks/*.md` | Operational procedures. |
| `docs/services/*.md` | Service behavior and architecture. |
| `docs/CHATGPT_CONTEXT.md` | Short paste-safe bootstrap context for new ChatGPT conversations. |
| `docs/reports/*.md` | Audit/report outputs. |

## 9. Current State

Current state is mixed:

- `soma-arch` is the Git control-plane repository.
- FFmpeg stable and FFmpeg dev have tracked service source and tracked compose files.
- Whisper dev has tracked service source and compose.
- Stable Whisper remains tied to the legacy `myservices` contour.
- Home source is documented as outside this repo under `/home/grigorynokhrin/myservices/home`.
- Gateway/Caddy has a tracked reference config under `gateway/`, but live Caddy state may differ.
- The platform is transitioning from legacy runtime ownership toward repo-managed soma service ownership.

The latest local filesystem audit could not directly observe `/home/grigorynokhrin`, `/srv`, or Docker because it was run from the Mac workspace. Treat server runtime facts as needing live confirmation.

## 10. Target State

Target architecture direction:

- `soma` is the platform identity.
- `soma-arch` remains the control-plane repository.
- `/srv/soma` becomes the target runtime root.
- `/srv/soma/worktrees` holds server feature worktrees.
- `/srv/soma/data` holds persistent data for repo-managed soma services.
- Stable services have tracked source, tracked compose, runbooks, service design docs, validation evidence, and documented rollback/disable paths.
- Dev services stay isolated from stable services.
- Home publishes stable user-facing tools only.
- Gateway/Caddy routes requests but does not define product publication.

Long-term target details are documented in `docs/TARGET_ARCHITECTURE.md`.

## 11. Legacy State

Legacy state includes:

- `/home/grigorynokhrin/myservices`
- `myservices-*` containers
- production compose outside this repo
- Home source outside this repo
- live Caddyfile outside this repo
- historical flat documentation and status snapshots

Legacy does not mean disposable. It means production-sensitive historical runtime state that must be preserved until an explicit migration replaces it.

## 12. Home And Gateway Boundaries

Home is publication.

- Home decides which stable tools users see.
- Home must not publish dev services as normal user-facing tools.
- Home publication changes require explicit approval and runtime validation.

Gateway/Caddy is routing.

- Gateway decides which request paths can reach which upstreams.
- Gateway route availability does not imply Home publication.
- Gateway/Caddy changes are production-sensitive and require explicit approval.

`docs/services/home.md` owns Home design. `docs/services/gateway.md` owns Gateway design.

## 13. Open Questions

Open platform questions:

1. Should `/home/grigorynokhrin/soma-arch` remain the server reference repo, or should `/srv/soma/worktrees` become the primary operational model?
2. Should all stable services eventually use `/srv/soma/data/<service>`?
3. Should stable Whisper gain tracked `services/whisper` and `compose/whisper.compose.yml` equivalents?
4. Should stable routes standardize under top-level paths or `/myservices/<service>/` paths?
5. Should live Gateway/Caddy config become fully repo-managed?
6. Should Home source be moved or mirrored into this repository?
7. What should the long-term network naming convention be for `compose_default`, `myservices_default`, and any future soma-owned network?

These questions require explicit decisions before restructuring.

## 14. Non-Goals

This document does not:

- perform runtime inspection
- change server state
- define service-specific behavior
- replace service runbooks
- replace `docs/SERVICES_REGISTRY.md`
- replace `docs/TARGET_ARCHITECTURE.md`
- prescribe a migration plan
- recommend cleanup or restructuring by itself

## 15. Related Documents

- `docs/TARGET_ARCHITECTURE.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/CHATGPT_CONTEXT.md`
- `docs/reports/filesystem_architecture_audit.md`
- `docs/runbooks/gateway.md`
- `docs/services/gateway.md`
- `runtime/README.md`
