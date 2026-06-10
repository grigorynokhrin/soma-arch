# NAMING_AND_LAYOUT_POLICY

This document defines naming and filesystem layout policy for the Soma platform.

It exists to prevent branch names, worktree paths, runtime paths, product names, and legacy names from being mistaken for each other. It does not authorize cleanup, migration, renaming, container changes, route changes, or runtime restructuring.

## 1. Core Principles

- Worktrees are not architecture.
- Worktrees are temporary Git checkouts for branches or tasks.
- Runtime layout, source layout, data layout, artifact layout, and documentation layout are separate concerns.
- Names must describe ownership and purpose.
- Stable and dev names must communicate maturity and risk.
- Legacy names may exist, but they must be explicitly marked as legacy.
- Repository paths and server runtime paths are related, but not identical.
- Tracked reference files are not proof of live runtime state.
- Volatile server facts must be refreshed before runtime work.

## 2. Canonical Vocabulary

| Term | Definition |
| --- | --- |
| Soma | Platform/product identity for the home-server service environment. It is not a single service, container, route, branch, or directory. |
| `soma-arch` | Git control-plane repository containing docs, tracked service source, compose definitions, gateway references, runtime templates, and reports. |
| Control plane | The Git-managed source of intent: repository, docs, compose definitions, service source, reference config, and workflow records. |
| Runtime root | Server filesystem root used by live or target service runtime assets. Current target: `/srv/soma`. |
| Service | A deployable application component with a route, container, source, data, runbook, and service design when mature. |
| Stable service | User-facing service intended for normal use and eligible for Home publication. |
| Dev service | Experimental or validation service. It may be routable but must not be Home-published as a stable tool. |
| Home | User-facing publication portal. Home decides which stable tools users see. |
| Gateway | Caddy routing layer. Gateway decides which request paths reach which upstreams. |
| Data root | Persistent service data location. Target pattern: `/srv/soma/data/<service>`. |
| Artifact root | Output/download/result storage location. Target pattern: `/srv/soma/artifacts/<service>` when separated from data. |
| Worktree | Temporary or task-specific Git checkout, usually under `/srv/soma/worktrees/<branch-or-purpose>` on the server. |
| Legacy contour | Existing production-sensitive runtime area under `/home/grigorynokhrin/myservices` and its `myservices-*` services. |

## 3. Current State

Current facts are drawn from:

- `docs/PLATFORM_ARCHITECTURE.md`
- `docs/reports/filesystem_architecture_audit.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/CHATGPT_CONTEXT.md`

Known layout:

| Path / Name | Current meaning |
| --- | --- |
| `/home/grigorynokhrin/soma-arch` | Main/reference Git checkout on the server, documented but requiring live confirmation before runtime work. |
| `/srv/soma/worktrees/ffmpeg-dev-skeleton` | Current server feature worktree for `feature/ffmpeg-dev-skeleton`, documented but requiring live confirmation before runtime work. |
| `/srv/soma/data` | Target service data root for repo-managed soma services. |
| `/home/grigorynokhrin/myservices` | Legacy runtime contour. |
| `docs/` | Repository documentation system. |
| `services/` | Tracked service source. |
| `compose/` | Tracked Compose definitions. |
| `gateway/` | Tracked Gateway/Caddy reference configuration. |
| `runtime/` | Runtime templates/helpers intended for `/srv/soma`. |

Current known service naming examples:

| Service state | Source | Compose file | Container | Data path | Route |
| --- | --- | --- | --- | --- | --- |
| FFmpeg stable | `services/ffmpeg` | `compose/ffmpeg.compose.yml` | `soma-ffmpeg` | `/srv/soma/data/ffmpeg` | `/ffmpeg/` |
| FFmpeg dev | `services/ffmpeg-dev` | `compose/ffmpeg-dev.compose.yml` | `soma-ffmpeg-dev` | `/srv/soma/data/ffmpeg-dev` | `/ffmpeg-dev/` |
| Whisper dev | `services/whisper-dev` | `compose/whisper-dev.compose.yml` | `soma-whisper-dev` | `/srv/soma/data/whisper-dev` | `/whisper-dev/` |
| Whisper stable | `services/whisper-dev` documented as dev-derived source | production compose outside repo | `myservices-whisper` | `/home/grigorynokhrin/myservices/whisper` | `/myservices/whisper/` |

Uncertain runtime facts must be verified on the server. The latest filesystem audit could not directly inspect `/srv`, `/home/grigorynokhrin`, or Docker from the Mac workspace.

## 4. Target Semantic Tree

Target server runtime model:

```text
/srv/soma/
  runtime/
  data/
    <service>/
  artifacts/
    <service>/
  worktrees/
    <branch-or-purpose>/
  backups/
  logs/
```

Target repository model:

```text
soma-arch/
  docs/
    platform/
    services/
    runbooks/
    reports/
  services/
    <service>/
  compose/
    <service>.compose.yml
  gateway/
  runtime/
  scripts/
```

Policy:

- Repository structure and server runtime structure are related but not identical.
- Repository `services/<service>` is source code.
- Runtime `/srv/soma/data/<service>` is persistent service data.
- Runtime `/srv/soma/artifacts/<service>` is for generated outputs if artifacts are separated from service data.
- Runtime `/srv/soma/worktrees/<branch-or-purpose>` is for Git checkouts, not long-term architecture identity.
- `runtime/` in the repository contains templates/helpers; `/srv/soma/runtime` is a possible target runtime area.

The `docs/platform/` directory is a target semantic grouping, not a required immediate migration. Existing canonical platform docs may remain at the top of `docs/` until an approved documentation cleanup moves them.

## 5. Service Naming Policy

### Source Directories

Stable service source:

```text
services/<service>
```

Dev service source:

```text
services/<service>-dev
```

Examples:

```text
services/ffmpeg
services/ffmpeg-dev
```

Policy:

- Stable source directories omit `-dev`.
- Dev source directories include `-dev`.
- Legacy exceptions must be documented. Current exception: stable Whisper is documented as dev-derived from `services/whisper-dev`.

### Compose Files

Stable compose:

```text
compose/<service>.compose.yml
```

Dev compose:

```text
compose/<service>-dev.compose.yml
```

Examples:

```text
compose/ffmpeg.compose.yml
compose/ffmpeg-dev.compose.yml
```

### Compose Project Names

Preferred project names:

```text
soma-<service>
soma-<service>-dev
```

Examples:

```text
soma-ffmpeg
soma-ffmpeg-dev
```

Compose project names should be explicit for new services to avoid cross-compose orphan and naming ambiguity.

### Container Names

Stable containers:

```text
soma-<service>
```

Dev containers:

```text
soma-<service>-dev
```

Examples:

```text
soma-ffmpeg
soma-ffmpeg-dev
```

Legacy container names:

```text
myservices-home
myservices-caddy
myservices-whisper
```

Legacy names may remain until an approved migration changes them.

### Data Directories

Stable data:

```text
/srv/soma/data/<service>
```

Dev data:

```text
/srv/soma/data/<service>-dev
```

Examples:

```text
/srv/soma/data/ffmpeg
/srv/soma/data/ffmpeg-dev
```

Data directories must not be placed inside service source directories.

### Artifact Directories

If artifacts are separated from general service data, use:

```text
/srv/soma/artifacts/<service>
/srv/soma/artifacts/<service>-dev
```

Existing services may keep artifacts inside their current data layout until a separate migration is approved.

### Routes

Stable routes should be deliberate and documented in the service registry, service runbook, service design doc, and Gateway/Home docs when relevant.

Dev routes should include `-dev`:

```text
/<service>-dev/
```

Examples:

```text
/ffmpeg-dev/
/whisper-dev/
```

Current stable route examples:

```text
/ffmpeg/
/myservices/whisper/
```

Stable route standardization remains an open question. Do not infer a new route convention from one service alone.

## 6. Documentation Naming Policy

Documentation locations:

| Type | Preferred location |
| --- | --- |
| Platform-level docs | top-level `docs/*.md` today; future semantic grouping may be `docs/platform/` |
| Service design docs | `docs/services/<service>.md` |
| Runbooks | `docs/runbooks/<service-or-component>.md` |
| Reports/audits | `docs/reports/<topic>.md` |
| Validation reports | `docs/validations/YYYY-MM-DD__service__env__change-slug__validation.md` |
| Release notes | `docs/releases/YYYY-MM-DD__service__vX.Y.Z__release.md` |
| ADRs | `docs/decisions/ADR-YYYYMMDD-NNN-service-change-slug.md` if introduced |
| Workflow briefs | `docs/workflows/YYYY-MM-DD__service__change-slug__brief.md` |

Current canonical platform docs include:

- `docs/PLATFORM_ARCHITECTURE.md`
- `docs/NAMING_AND_LAYOUT_POLICY.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`

Policy:

- Do not create competing docs for the same ownership area.
- Update the canonical owner first, then reconcile supporting docs.
- Historical docs may remain as references, but must not silently override canonical docs.

## 7. Legacy Naming Policy

Explicit legacy classifications:

| Name | Classification | Policy |
| --- | --- | --- |
| `/home/grigorynokhrin/myservices` | Legacy runtime contour | Production-sensitive; do not move/rename/delete without explicit migration approval. |
| `myservices-*` containers | Legacy container names | May remain until an approved migration replaces them. |
| `/myservices/` route | Home/publication route | User-facing portal route, not a general filesystem root. |
| `feature/ffmpeg-dev-skeleton` | Historical branch name | Must not define future platform layout or architecture identity. |
| `gateway/myservices/Caddyfile.current` | Tracked Gateway reference | Not guaranteed live state unless server inspection confirms it. |
| `myservices` term | Ambiguous legacy/product term | Use only with context: legacy runtime root, container prefix, or Home/MyServices portal. |

Legacy names must be documented as legacy when referenced in new docs.

## 8. Anti-Patterns

Discouraged patterns:

- using a worktree name as architecture identity
- putting runtime meaning into branch names
- mixing product identity, repository identity, and runtime path identity
- assuming tracked Caddyfile equals live Caddyfile
- assuming Home publication equals Gateway routing
- assuming a routable dev service is a stable Home-published service
- using ambiguous names like `current` without explaining current relative to what
- storing runtime data, generated artifacts, uploads, model caches, or logs inside service source directories
- using legacy names for new services without documenting why
- letting branch names outlive their purpose as platform vocabulary

## 9. Migration Stance

This policy does not authorize any rename or migration.

Future cleanup requires:

- separate plan
- explicit approval
- live server audit
- affected path/container/route inventory
- validation plan
- rollback notes
- documentation updates

Production Gateway/Caddy and legacy runtime changes require explicit user approval.

Do not use this policy as permission to modify:

- `/home/grigorynokhrin/myservices`
- `/srv/soma`
- Docker containers
- live Caddy/Gateway files
- production compose
- routes
- service code

## 10. Open Questions

Unresolved naming and layout questions:

1. Should Home source be imported into `soma-arch`?
2. Should stable Whisper get `services/whisper` and `compose/whisper.compose.yml`?
3. Should all stable services eventually move data under `/srv/soma/data`?
4. Should stable service routes standardize under top-level routes or `/myservices/<service>/`?
5. Should live Caddy become repo-managed or remain manually reconciled?
6. Should platform-level docs eventually move under `docs/platform/`, or remain top-level for visibility?
7. Should artifact roots be separated from service data roots for every service?
8. What should replace ambiguous network names such as `compose_default` if a future migration introduces soma-owned networks?

These questions require explicit decisions before restructuring.

## 11. Related Documents

- `docs/PLATFORM_ARCHITECTURE.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/CHATGPT_CONTEXT.md`
- `docs/reports/filesystem_architecture_audit.md`
- `docs/services/home.md`
- `docs/services/gateway.md`
- `runtime/README.md`
