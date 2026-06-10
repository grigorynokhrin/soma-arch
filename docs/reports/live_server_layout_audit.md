# Live Server Layout Audit

Audit date: 2026-06-10

This report documents observed live server layout facts provided for the Soma platform.

It is documentation-only. It does not authorize cleanup, migrations, renames, Gateway/Caddy changes, compose changes, service changes, or runtime restructuring.

## 1. Executive Summary

The live server currently has a mixed ownership model:

- Legacy runtime ownership remains under `/home/grigorynokhrin/myservices`.
- Repo-managed FFmpeg stable/dev services run from compose files inside the `feature/ffmpeg-dev-skeleton` worktree.
- A server-local `/srv/soma` runtime tree exists and contains data roots, service directories, compose/gateway/runtime-style directories, and worktrees.
- Multiple naming eras coexist: `myservices`, `soma`, and `soma-arch`.
- Worktrees are operational Git checkouts, not architecture identity.

The observed state is useful as a factual baseline before any cleanup or migration planning.

## 2. Facts

### Filesystem

Observed `/home/grigorynokhrin` top-level sizes:

| Path | Size | Notes |
| --- | ---: | --- |
| `/home/grigorynokhrin/soma-arch` | `4.1M` | Main/reference Git checkout. |
| `/home/grigorynokhrin/soma-arch-worktrees` | `420K` | Older/separate worktree root. |
| `/home/grigorynokhrin/projects` | `12G` | User projects area. |
| `/home/grigorynokhrin/myservices` | `23G` | Legacy runtime contour. |

Observed `/srv` top-level size:

| Path | Size | Notes |
| --- | ---: | --- |
| `/srv/soma` | `57G` | Soma runtime root. |

Observed `/srv/soma` structure:

```text
/srv/soma/backups
/srv/soma/compose
/srv/soma/data
/srv/soma/gateway
/srv/soma/ops
/srv/soma/portal-ui
/srv/soma/scripts
/srv/soma/services
/srv/soma/shared
/srv/soma/worktrees
```

Observed data roots:

```text
/srv/soma/data/ffmpeg
/srv/soma/data/ffmpeg-dev
/srv/soma/data/whisper
/srv/soma/data/whisper-dev
/srv/soma/data/whisper-prod-candidate
/srv/soma/data/supir
/srv/soma/data/tesseract
```

Observed service directories under `/srv/soma/services`:

```text
/srv/soma/services/whisper
/srv/soma/services/whisper-dev
/srv/soma/services/supir
/srv/soma/services/tesseract
```

### Worktrees

Observed worktrees:

| Path | Branch/state | Notes |
| --- | --- | --- |
| `/home/grigorynokhrin/soma-arch` | `main` | Main/reference checkout. |
| `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` | detached | Older Whisper batch upload worktree. |
| `/srv/soma/worktrees/ffmpeg-dev-skeleton` | `feature/ffmpeg-dev-skeleton` | Current FFmpeg/docs feature worktree. |

### Compose Projects

Observed compose projects:

| Compose project | Config files |
| --- | --- |
| `compose` | `/srv/soma/compose/whisper-dev.compose.yml` |
| `myservices` | `/home/grigorynokhrin/myservices/compose.yaml`; `/home/grigorynokhrin/myservices/compose.override.yaml` |
| `soma-ffmpeg` | `/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg.compose.yml` |
| `soma-ffmpeg-dev` | `/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg-dev.compose.yml` |

### Containers

Observed running containers:

```text
myservices-home
myservices-whisper
myservices-caddy
soma-ffmpeg
soma-ffmpeg-dev
soma-whisper-dev
```

### Runtime Roots

Observed/runtime-relevant roots:

| Root | Role |
| --- | --- |
| `/home/grigorynokhrin/myservices` | Legacy runtime contour for Home, Whisper stable, and Caddy. |
| `/srv/soma` | Soma runtime root with data, worktrees, services, compose, gateway, backups, logs-style structure. |
| `/srv/soma/data` | Data root containing stable/dev/candidate service data directories. |
| `/srv/soma/worktrees` | Worktree root for server feature checkouts. |
| `/home/grigorynokhrin/soma-arch-worktrees` | Older/separate worktree root containing a detached Whisper worktree. |

## 3. Ownership Model Analysis

### Legacy Runtime Ownership

Legacy runtime ownership currently includes:

```text
/home/grigorynokhrin/myservices
myservices-home
myservices-whisper
myservices-caddy
```

Observed implications:

- Home, stable Whisper, and Caddy still run under the legacy `myservices` model.
- The legacy runtime is large enough to matter operationally (`23G` observed).
- Changes here are production-sensitive and should remain explicitly approved.

### Repo-Managed Ownership

Repo-managed ownership currently includes:

```text
ffmpeg
ffmpeg-dev
/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg.compose.yml
/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg-dev.compose.yml
```

Observed implications:

- FFmpeg stable/dev are tied to compose files inside the active feature worktree.
- The running containers `soma-ffmpeg` and `soma-ffmpeg-dev` align with the repo-managed naming policy.
- The worktree path is operational checkout location, not architecture identity.

### Server-Local Ownership

Server-local ownership currently includes:

```text
/srv/soma/compose
/srv/soma/compose/whisper-dev.compose.yml
/srv/soma/data/whisper-prod-candidate
```

Observed implications:

- The `compose` project uses `/srv/soma/compose/whisper-dev.compose.yml`, not a compose file inside the active feature worktree.
- `whisper-prod-candidate` data exists as server-local runtime/candidate state.
- `/srv/soma/services` contains service directories for Whisper, Supir, and Tesseract that are not the same as the current repo `services/` tree observed from the Mac workspace.

## 4. Architecture Observations

- Worktrees are not architecture.
- Repository structure and runtime structure are different concerns.
- The live server currently has multiple compose ownership models.
- The live server currently has multiple naming eras:
  - `myservices`
  - `soma`
  - `soma-arch`
- `/home/grigorynokhrin/myservices` remains a live legacy runtime contour, not merely historical documentation.
- `/srv/soma` is active enough to contain substantial data (`57G`) and multiple service/data directories.
- `/srv/soma/worktrees/ffmpeg-dev-skeleton` is an operational checkout used by live FFmpeg compose projects.
- `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` is detached and should be treated as lifecycle-unclear until reviewed separately.
- `myservices` is overloaded: it names the legacy runtime contour, legacy containers, and the Home/MyServices publication route.
- Gateway/Caddy remains production-sensitive because `myservices-caddy` is running.

## 5. Open Questions

Future Whisper ownership model:

- Should stable Whisper remain under `/home/grigorynokhrin/myservices`, or move toward repo-managed source/compose/data under `/srv/soma`?
- Should stable Whisper gain `services/whisper` and `compose/whisper.compose.yml` in `soma-arch`?

Detached Whisper worktree lifecycle:

- Why is `/home/grigorynokhrin/soma-arch-worktrees/whisper-batch-upload-v1` detached?
- Is it still needed for rollback, audit, or historical validation?
- What policy should govern old worktree retirement?

Portal UI ownership:

- Is `/srv/soma/portal-ui` active, placeholder, or future target state?
- Should Home source eventually move from `/home/grigorynokhrin/myservices/home` into a repo-managed portal source tree?

Supir ownership:

- Are `/srv/soma/services/supir` and `/srv/soma/data/supir` active, prototype, historical, or placeholder?
- Should Supir become a tracked service under `soma-arch/services/`?

Tesseract ownership:

- Are `/srv/soma/services/tesseract` and `/srv/soma/data/tesseract` active, prototype, historical, or placeholder?
- Should Tesseract become a tracked service under `soma-arch/services/`?

Migration path from legacy `myservices` runtime:

- Which services should move first, if any?
- Should Caddy/Gateway move last because it routes all user-facing services?
- Should Home publication move into repo ownership before or after stable Whisper?
- How should data and backup validation be handled before any migration?

Compose ownership:

- Should `/srv/soma/compose` remain a server-local compose owner?
- Should compose files for all repo-managed services live only in `soma-arch/compose` and be executed from checked-out commits?
- Should live compose projects be pinned to stable worktrees, release checkouts, or the main server checkout?

## 6. Non-Goals

This report does not authorize cleanup.

This report does not authorize migrations.

This report does not authorize renames.

This report does not authorize Gateway/Caddy changes.

This report does not authorize:

- moving files
- deleting files
- removing worktrees
- changing compose projects
- recreating containers
- changing routes
- importing server-local services into the repo
- modifying `/home/grigorynokhrin/myservices`
- modifying `/srv/soma`

Any future cleanup or migration requires a separate plan, explicit approval, validation evidence, rollback notes, and a fresh server audit.
