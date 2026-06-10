# Soma Migration Inventory And Mapping Plan

This document maps the observed server layout to the target architecture defined in `docs/MIGRATION.md`.

It is inventory and planning only. It does not authorize or perform filesystem, runtime, Compose, container, Gateway, Home, route, or DNS changes.

## 1. Current Observed State

The observed server uses three ownership models at the same time:

- legacy runtime ownership under `/home/grigorynokhrin/myservices`
- repo-managed FFmpeg Compose files executed from the current server checkout under `/srv/soma/worktrees/ffmpeg-dev-skeleton`
- server-local runtime content under `/srv/soma`, including Whisper dev Compose, service directories, data, backups, and candidate data

Observed high-level layout:

```text
/home/grigorynokhrin/
  soma-arch/                         main/reference Git checkout
  soma-arch-worktrees/              older worktree root
  myservices/                        legacy runtime contour

/srv/soma/
  backups/
  compose/
  data/
  gateway/
  ops/
  portal-ui/
  scripts/
  services/
  shared/
  worktrees/
```

The target architecture is a unified `/srv/soma` layout with independent `prod/` and `dev/` environments. Current paths must not be treated as target ownership without the mapping and questions below being resolved.

## 2. Current Runtime Inventory

### Runtime Roots

| Current root | Observed role | Ownership confidence |
| --- | --- | --- |
| `/home/grigorynokhrin/myservices` | Legacy runtime for Home, stable Whisper, and Caddy | Observed |
| `/srv/soma` | Soma runtime root containing Compose, data, services, worktrees, backups, and supporting areas | Observed |
| `/srv/soma/worktrees/ffmpeg-dev-skeleton` | Checkout supplying live FFmpeg stable/dev Compose files | Observed |
| `/home/grigorynokhrin/soma-arch` | Main/reference Git checkout | Observed |
| `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` | Detached Whisper worktree | Observed; current purpose unknown |

### Compose Roots

| Compose project | Current config path | Observed ownership |
| --- | --- | --- |
| `myservices` | `/home/grigorynokhrin/myservices/compose.yaml` | Legacy runtime |
| `myservices` | `/home/grigorynokhrin/myservices/compose.override.yaml` | Legacy runtime |
| `compose` | `/srv/soma/compose/whisper-dev.compose.yml` | Server-local Soma runtime |
| `soma-ffmpeg` | `/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg.compose.yml` | Repo-managed checkout |
| `soma-ffmpeg-dev` | `/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg-dev.compose.yml` | Repo-managed checkout |

### Service Roots

| Current path | Observed name | Runtime role |
| --- | --- | --- |
| `/home/grigorynokhrin/myservices/home` | Home | Legacy production source/runtime area |
| `/home/grigorynokhrin/myservices/whisper` | Whisper | Legacy production source/data area; exact internal split requires inventory |
| `/home/grigorynokhrin/myservices/caddy` | Gateway/Caddy | Legacy production configuration area |
| `/srv/soma/services/whisper` | Whisper | Ownership and active use unknown |
| `/srv/soma/services/whisper-dev` | Whisper dev | Ownership and active use unknown |
| `/srv/soma/services/supir` | Supir | Prototype/placeholder ownership unknown |
| `/srv/soma/services/tesseract` | Tesseract | Prototype/placeholder ownership unknown |
| `/srv/soma/portal-ui` | Portal UI | Ownership and active use unknown |
| `/srv/soma/gateway` | Gateway | Ownership and active use unknown |

### Data Roots

| Current path | Associated name | Observed classification |
| --- | --- | --- |
| `/srv/soma/data/ffmpeg` | FFmpeg stable | Stable runtime data |
| `/srv/soma/data/ffmpeg-dev` | FFmpeg dev | Development runtime data |
| `/srv/soma/data/whisper` | Whisper | Intended environment/active ownership unknown |
| `/srv/soma/data/whisper-dev` | Whisper dev | Development runtime data |
| `/srv/soma/data/whisper-prod-candidate` | Whisper production candidate | Candidate lifecycle/retention unknown |
| `/srv/soma/data/supir` | Supir | Prototype/placeholder ownership unknown |
| `/srv/soma/data/tesseract` | Tesseract | Prototype/placeholder ownership unknown |
| `/home/grigorynokhrin/myservices` | Legacy services | Contains `23G`; exact service/data/artifact split requires inventory |

### Container Names

| Running container | Current ownership model |
| --- | --- |
| `myservices-home` | Legacy runtime |
| `myservices-whisper` | Legacy runtime |
| `myservices-caddy` | Legacy runtime |
| `soma-ffmpeg` | Repo-managed FFmpeg stable |
| `soma-ffmpeg-dev` | Repo-managed FFmpeg dev |
| `soma-whisper-dev` | Server-local Whisper dev Compose project |

### Routes

The live server layout audit did not capture route responses or live Gateway configuration. No route is treated as newly observed by this plan.

| Service/component | Observed live route evidence in audit |
| --- | --- |
| Home | Not captured |
| Whisper stable | Not captured |
| Whisper dev | Not captured |
| FFmpeg stable | Not captured |
| FFmpeg dev | Not captured |
| Gateway/Caddy | Running container observed; live route table not captured |

Route mapping requires a separate read-only live Gateway audit before migration execution planning.

## 3. Target Runtime Inventory

The target inventory is defined by `docs/MIGRATION.md`:

```text
/srv/soma/
  prod/
    app/
      home/
      gateway/
      services/
        whisper/
        ffmpeg/
    compose/
    data/
    artifacts/
    logs/
    config/

  dev/
    app/
      home/
      gateway/
      services/
        whisper/
        ffmpeg/
    compose/
    data/
    artifacts/
    logs/
    config/

  shared/
    models/
    cache/

  backups/
```

Target ownership rules:

- `prod/` owns stable application, Compose, data, artifacts, logs, and configuration.
- `dev/` owns development application, Compose, data, artifacts, logs, and configuration.
- `shared/` contains only deliberately shared models and caches.
- `backups/` contains recovery and migration rollback material.
- Source, data, artifacts, logs, and configuration remain separate.

## 4. Source-To-Target Mapping

The target paths below are mapping candidates, not approved moves. `TBD` means ownership or content must be inspected before a final target can be assigned.

| Current Path | Target Path | Notes |
| --- | --- | --- |
| `/home/grigorynokhrin/myservices` | Split across `/srv/soma/prod/app`, `/srv/soma/prod/compose`, `/srv/soma/prod/data`, `/srv/soma/prod/artifacts`, `/srv/soma/prod/logs`, and `/srv/soma/prod/config` | Must inventory contents by responsibility; no whole-directory move is defined. |
| `/home/grigorynokhrin/myservices/home` | `/srv/soma/prod/app/home` | Source/runtime/config boundaries require inspection. |
| `/home/grigorynokhrin/myservices/whisper` | `/srv/soma/prod/app/services/whisper`, `/srv/soma/prod/data/whisper`, `/srv/soma/prod/artifacts/whisper`, `/srv/soma/prod/logs/whisper`, `/srv/soma/prod/config/whisper` | Exact current content split is unknown. |
| `/home/grigorynokhrin/myservices/caddy` | `/srv/soma/prod/app/gateway` and `/srv/soma/prod/config/gateway` | Live configuration ownership and mount details require confirmation. |
| `/home/grigorynokhrin/myservices/compose.yaml` | `/srv/soma/prod/compose/compose.yaml` or service-specific files under `/srv/soma/prod/compose` | Target Compose organization requires a separate decision. |
| `/home/grigorynokhrin/myservices/compose.override.yaml` | `/srv/soma/prod/compose/` | Override purpose must be inspected before mapping. |
| `/srv/soma/services/whisper` | `/srv/soma/prod/app/services/whisper` or TBD | Current ownership and active use unknown. |
| `/srv/soma/services/whisper-dev` | `/srv/soma/dev/app/services/whisper` or TBD | Current ownership and active use unknown. |
| `/srv/soma/services/supir` | TBD | Supir is not part of the target application inventory in `docs/MIGRATION.md`; review required. |
| `/srv/soma/services/tesseract` | TBD | Tesseract is not part of the target application inventory in `docs/MIGRATION.md`; review required. |
| `/srv/soma/data/ffmpeg` | `/srv/soma/prod/data/ffmpeg` | Inspect whether outputs/logs/config are mixed into this data root. |
| `/srv/soma/data/ffmpeg-dev` | `/srv/soma/dev/data/ffmpeg` | Inspect whether outputs/logs/config are mixed into this data root. |
| `/srv/soma/data/whisper` | `/srv/soma/prod/data/whisper` or TBD | Current environment ownership unknown. |
| `/srv/soma/data/whisper-dev` | `/srv/soma/dev/data/whisper` | Inspect whether artifacts/logs/config are mixed into this data root. |
| `/srv/soma/data/whisper-prod-candidate` | TBD | Candidate retention and rollback value must be decided. |
| `/srv/soma/data/supir` | TBD | Ownership and future service status unknown. |
| `/srv/soma/data/tesseract` | TBD | Ownership and future service status unknown. |
| `/srv/soma/compose/whisper-dev.compose.yml` | `/srv/soma/dev/compose/whisper.compose.yml` | Requires comparison with repo source and target path configuration. |
| `/srv/soma/compose/*` | `/srv/soma/prod/compose` or `/srv/soma/dev/compose` | Classify every file by environment before mapping. |
| `/srv/soma/portal-ui` | `/srv/soma/prod/app/home`, `/srv/soma/dev/app/home`, or TBD | Ownership and active use unknown. |
| `/srv/soma/gateway` | `/srv/soma/prod/app/gateway`, `/srv/soma/dev/app/gateway`, or TBD | Ownership and active use unknown. |
| `/srv/soma/shared` | `/srv/soma/shared` | Keep only deliberately shared models/cache; other contents require classification. |
| `/srv/soma/backups` | `/srv/soma/backups` | Keep; inventory retention, ownership, and restore purpose separately. |
| `/srv/soma/ops` | TBD | Target `docs/MIGRATION.md` does not define a separate `ops/` area. |
| `/srv/soma/scripts` | Environment-specific app/compose support or TBD | Script ownership and mutation risk require review. |
| `/srv/soma/worktrees/*` | No runtime target | Operational checkouts are not application/runtime architecture. Lifecycle is planned separately. |

## 5. Migration Candidates

These classifications describe planning status only. They do not recommend or authorize execution.

| Current Area | Classification | Reason |
| --- | --- | --- |
| `/home/grigorynokhrin/myservices` | Review | Must be decomposed by source, Compose, data, artifacts, logs, and config. |
| `/srv/soma/data/ffmpeg` | Move | Has a clear candidate production data target, subject to content inspection. |
| `/srv/soma/data/ffmpeg-dev` | Move | Has a clear candidate development data target, subject to content inspection. |
| `/srv/soma/data/whisper-dev` | Move | Has a clear candidate development data target, subject to content inspection. |
| `/srv/soma/data/whisper` | Review | Environment ownership is not confirmed. |
| `/srv/soma/data/whisper-prod-candidate` | Review | Retention and rollback purpose unresolved. |
| `/srv/soma/data/supir` | Unknown | Target service status unresolved. |
| `/srv/soma/data/tesseract` | Unknown | Target service status unresolved. |
| `/srv/soma/services/whisper` | Review | Active ownership and duplication with other Whisper source are unresolved. |
| `/srv/soma/services/whisper-dev` | Review | Active ownership and duplication with repo source are unresolved. |
| `/srv/soma/services/supir` | Unknown | Target service status unresolved. |
| `/srv/soma/services/tesseract` | Unknown | Target service status unresolved. |
| `/srv/soma/compose` | Merge | Candidate files must be classified into target `prod/compose` or `dev/compose`. |
| `/srv/soma/portal-ui` | Review | Home/portal ownership unresolved. |
| `/srv/soma/gateway` | Review | Gateway ownership and live use unresolved. |
| `/srv/soma/shared` | Keep | Target retains `shared/`, but content must be limited to deliberate sharing. |
| `/srv/soma/backups` | Keep | Target retains backups; retention and restore metadata still require review. |
| `/srv/soma/ops` | Review | No direct target area is defined. |
| `/srv/soma/scripts` | Review | Scripts must be assigned to environment or repository ownership. |
| `/srv/soma/worktrees` | Keep | Operational checkout root remains outside production/development runtime content. |
| `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` | Review | Detached checkout lifecycle and rollback value unresolved. |

## 6. Blocking Questions

All questions below must be answered before migration execution planning.

### Whisper Stable Ownership

- Which source tree is authoritative for stable Whisper?
- Which Compose definition is authoritative?
- Which data directories contain persistent data versus artifacts, logs, cache, and configuration?
- Does `/srv/soma/data/whisper` belong to stable Whisper or another candidate environment?

### Home Ownership

- Is `/home/grigorynokhrin/myservices/home` the authoritative Home source?
- Is `/srv/soma/portal-ui` active, duplicate, prototype, or unused?
- Should production and development Home applications use one source with environment configuration or separate deployed copies?

### Gateway Ownership

- Which live Gateway configuration and Compose definition are authoritative?
- What is the role of `/srv/soma/gateway`?
- How will production and development Gateway configuration remain isolated?
- What routes are currently active and must be preserved?

### Whisper Production Candidate

- Is `/srv/soma/data/whisper-prod-candidate` required for rollback or validation evidence?
- Does it contain unique user data or generated artifacts?
- What retention rule applies?

### Detached Worktree

- Why is `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` detached?
- Does it reference a deployed image, rollback point, or unique unmerged state?
- What evidence is required before its lifecycle can be decided?

### Supir And Tesseract

- Are these active, planned, abandoned, or data-only placeholders?
- Do their service/data directories contain unique source, models, user data, or artifacts?
- Should they be added to the target application inventory or handled separately?

### Compose Ownership

- Should target Compose definitions be generated from the Git control-plane repository or maintained directly under `/srv/soma`?
- Should production and development use one aggregate Compose file each or service-specific Compose files?
- How will deployed Compose revisions be identified and rolled back?

### Shared Storage

- Which models and caches may safely be shared between production and development?
- Which existing directories are mutable and therefore must not be shared?

## 7. Proposed Dev Environment Build Order

This is a future planning sequence only. It does not execute any step.

1. Complete read-only inventories for every current service, data, Compose, Gateway, Home, shared, backup, and candidate directory.
2. Resolve authoritative ownership for Whisper, Home, Gateway, Supir, and Tesseract.
3. Define the exact target dev directory manifest under `/srv/soma/dev` without creating it.
4. Define dev environment variables and path contracts with no service depending on fixed host paths.
5. Define dev Compose ownership and validate rendered configuration offline.
6. Define dev application deployment content for Home, Gateway, Whisper, and FFmpeg.
7. Define dev data, artifact, log, and config separation for each service.
8. Define deliberately shared models/cache and verify that mutable runtime data remains isolated.
9. Define backup and rollback requirements for every source area that would later be copied or transformed.
10. Create a separate approved execution plan with dry runs, validation gates, and rollback steps.
11. Only after approval, assemble the dev environment without changing production.
12. Validate dev services directly before any future Gateway, Home, DNS, or production work.

## 8. Out Of Scope

No migration is performed by this document.

This document performs no:

- runtime changes
- filesystem creation, movement, rename, or deletion
- Compose changes
- container changes
- Gateway/Caddy changes
- Home changes
- route changes
- DNS changes
- service code changes
- worktree removal

Any migration execution requires a separate approved plan, current live audit, backups, validation criteria, and rollback instructions.
