# Filesystem Architecture Audit

Audit date: 2026-06-10

Workspace used for this audit:

```text
/Users/grigorynokhrin/projects/soma-arch
```

Current branch observed locally:

```text
feature/ffmpeg-dev-skeleton
```

## Scope And Evidence Rules

This is an analysis-only inventory. No cleanup, move, rename, delete, runtime change, or restructuring decision was performed.

This report distinguishes:

- **Facts**: directly observed in this Mac workspace or exact command output from this audit.
- **Observations**: interpretation of facts from repository files and documentation.
- **Assumptions**: likely meaning or purpose that requires confirmation before runtime work.

Important limitation:

- The requested Linux server paths `/home/grigorynokhrin` and `/srv` were not mounted or available from this Mac workspace.
- Docker was not reachable from this Mac workspace.
- Server filesystem, active containers, live bind mounts, and live Docker networks must be refreshed on the server before any runtime work.

## 1. Home Directory Structure

Requested path:

```text
/home/grigorynokhrin
```

Facts:

| Path | Result | Size | Evidence |
| --- | --- | --- | --- |
| `/home/grigorynokhrin` | Not present in this Mac workspace | Not available | `ls -la /home/grigorynokhrin` returned `No such file or directory`. |

Observations:

- Repository documentation describes `/home/grigorynokhrin/myservices` as the legacy/stable runtime root.
- Repository documentation describes `/home/grigorynokhrin/soma-arch` as a server reference repo path.
- These paths are server-side Linux paths, not visible in the current Mac checkout.

Assumptions requiring server confirmation:

- `/home/grigorynokhrin/myservices` contains live production compose, Home source, Caddy file, Whisper runtime data, and backups.
- `/home/grigorynokhrin/soma-arch` is still present as the server reference repository.

## 2. Server Directory Structure

Requested paths:

```text
/srv
/srv/soma
/srv/soma/worktrees
```

Facts:

| Path | Result | Size | Evidence |
| --- | --- | --- | --- |
| `/srv` | Not present in this Mac workspace | Not available | `ls -la /srv` returned `No such file or directory`. |
| `/srv/soma` | Not directly observable | Not available | Parent `/srv` is not present. |
| `/srv/soma/worktrees` | Not directly observable | Not available | Parent `/srv` is not present. |

Observations:

- Repository docs and runtime templates consistently treat `/srv/soma` as the newer soma runtime root.
- `runtime/Makefile` uses `SOMA_RUNTIME_ROOT ?= /srv/soma`.
- `runtime/scripts/healthcheck.sh` checks for `/srv/soma`, `/home/grigorynokhrin/myservices`, and `/home/grigorynokhrin/soma-arch`.
- The current bootstrap context records server worktree `/srv/soma/worktrees/ffmpeg-dev-skeleton`.

Assumptions requiring server confirmation:

- `/srv/soma` exists on the server.
- `/srv/soma/worktrees/ffmpeg-dev-skeleton` is the active server worktree for branch `feature/ffmpeg-dev-skeleton`.
- `/srv/soma/data` contains runtime data directories for dev/stable soma services.

## 3. Repository Inventory

Requested repository:

```text
/home/grigorynokhrin/soma-arch
```

Fact:

- The requested server repository path is not directly observable from this Mac workspace.

Audited local repository path:

```text
/Users/grigorynokhrin/projects/soma-arch
```

### Git Inventory

Facts:

Remote:

```text
origin  git@github.com:grigorynokhrin/soma-arch.git (fetch)
origin  git@github.com:grigorynokhrin/soma-arch.git (push)
```

Branches:

```text
* feature/ffmpeg-dev-skeleton
  feature/whisper-batch-upload-v1
  main
  remotes/origin/HEAD -> origin/main
  remotes/origin/feature/ffmpeg-dev-skeleton
  remotes/origin/feature/whisper-batch-upload-v1
  remotes/origin/main
```

Local worktree list:

```text
/Users/grigorynokhrin/projects/soma-arch  c3ed8ca [feature/ffmpeg-dev-skeleton]
```

### Top-Level Repository Structure

Facts:

| Path | Apparent purpose | Size |
| --- | --- | --- |
| `.` | Repository root | `5.0M` |
| `.git` | Git metadata | `4.2M` |
| `.github` | GitHub templates/config | `4.0K` |
| `compose` | Repo-tracked Docker Compose files | `16K` |
| `docs` | Documentation, runbooks, service designs, reports | `508K` |
| `gateway` | Tracked gateway/Caddy reference files | `12K` |
| `ops` | Operations notes placeholder | `4.0K` |
| `runtime` | Runtime root templates and healthcheck | `16K` |
| `scripts` | Repository helper script area | `4.0K` |
| `services` | Service source trees | `260K` |

### Documentation Directories

Facts:

```text
docs
docs/runbooks
docs/services
docs/reports
```

Core canonical docs observed:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/runbooks/home.md`
- `docs/runbooks/gateway.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/services/home.md`
- `docs/services/gateway.md`
- `docs/CHATGPT_CONTEXT.md`

Observations:

- Documentation is transitioning from older flat docs to canonical `runbooks/`, `services/`, and now `reports/`.
- `docs/DOCUMENTATION_RECONCILIATION.md` classifies older status and rollout docs as reference, legacy, or archive candidates.

### Service Directories

Facts:

```text
services
services/ffmpeg
services/ffmpeg/templates
services/ffmpeg-dev
services/ffmpeg-dev/templates
services/whisper-dev
services/whisper-dev/templates
```

Service files observed:

```text
services/ffmpeg/Dockerfile
services/ffmpeg/app.py
services/ffmpeg/command_builder.py
services/ffmpeg/profiles.json
services/ffmpeg/requirements.txt
services/ffmpeg/selfcheck.py
services/ffmpeg-dev/Dockerfile
services/ffmpeg-dev/app.py
services/ffmpeg-dev/command_builder.py
services/ffmpeg-dev/profiles.json
services/ffmpeg-dev/requirements.txt
services/ffmpeg-dev/selfcheck.py
services/whisper-dev/Dockerfile
services/whisper-dev/app.py
services/whisper-dev/contexts.json
services/whisper-dev/requirements.txt
```

Observations:

- `services/ffmpeg` is the stable FFmpeg source tree.
- `services/ffmpeg-dev` is the experimental/dev FFmpeg source tree.
- `services/whisper-dev` is the Git-tracked Whisper source used for dev and documented dev-derived production releases.
- No tracked `services/home` source was observed.
- No tracked `services/whisper` stable source tree was observed.

### Compose Files

Facts:

```text
compose/README.md
compose/ffmpeg-dev.compose.yml
compose/ffmpeg.compose.yml
compose/whisper-dev.compose.yml
```

Tracked compose facts:

| Compose file | Project/service facts | Runtime data paths | Ports |
| --- | --- | --- | --- |
| `compose/ffmpeg.compose.yml` | project `soma-ffmpeg`, service `ffmpeg`, container `soma-ffmpeg`, image `soma-ffmpeg:local` | `/srv/soma/data/ffmpeg:/data` | `127.0.0.1:18083:8000` |
| `compose/ffmpeg-dev.compose.yml` | project `soma-ffmpeg-dev`, service `ffmpeg-dev`, container `soma-ffmpeg-dev`, image `soma-ffmpeg-dev:local` | `/srv/soma/data/ffmpeg-dev:/data` | `127.0.0.1:18082:8000` |
| `compose/whisper-dev.compose.yml` | service `whisper-dev`, container `soma-whisper-dev`, image `soma-whisper-dev:local` | `/srv/soma/data/whisper-dev/...` | `127.0.0.1:18080:8000` |

Observations:

- FFmpeg stable/dev compose files have explicit Compose project names.
- Whisper dev compose does not show an explicit top-level Compose project name in the audited file.
- FFmpeg stable/dev attach to external network `compose_default` as `caddy_dev`.
- Whisper dev compose requests `gpus: all`.

### Deployment-Related Directories

Facts:

```text
gateway/README.md
gateway/myservices/Caddyfile.current
gateway/myservices/compose.override.caddy-soma-dev.yaml
runtime/.env.example
runtime/Makefile
runtime/README.md
runtime/scripts/healthcheck.sh
ops/README.md
```

Gateway route facts from tracked `gateway/myservices/Caddyfile.current`:

| Route | Tracked behavior |
| --- | --- |
| `/myservices/image-upscale` | redirect to `/myservices/image-upscale/` |
| `/myservices/image-upscale/*` | reverse proxy `image-upscale:7860` |
| `/myservices/whisper*` | reverse proxy `whisper:8000` |
| `/whisper-dev*` | reverse proxy `soma-whisper-dev:8000` |
| `/ffmpeg-dev*` | reverse proxy `soma-ffmpeg-dev:8000` |
| `/ffmpeg*` | reverse proxy `soma-ffmpeg:8000` |
| `/myservices/ocr*` | Caddy placeholder response |
| `/myservices*` | reverse proxy `home:8000` |
| fallback | `Not found` 404 |

Runtime template facts:

- `runtime/Makefile` includes read-only targets `status`, `legacy-status`, `tree`, and `health`.
- `runtime/scripts/healthcheck.sh` checks runtime root, legacy root, reference repo, Docker availability, running containers, legacy compose status, Whisper health, and optional `soma-whisper-dev`.

### Scripts And Tooling

Facts:

```text
scripts/README.md
.github/pull_request_template.md
```

Observations:

- No repository-level test runner, Makefile, or package manager manifest was observed at the root during this audit.
- Service-level Python selfchecks exist for FFmpeg stable/dev.
- Runtime health tooling is represented under `runtime/`, not root `scripts/`.

## 4. Runtime Inventory

Facts from this Mac workspace:

| Command | Result |
| --- | --- |
| `docker ps --format ...` | Failed: Docker API socket not found at `/Users/grigorynokhrin/.docker/run/docker.sock`. |
| `docker compose ls` | Failed: cannot connect to Docker daemon. |

Live runtime inventory is therefore not directly observable from this workspace.

Repo-documented runtime facts:

| Component | Documented container | Documented route | Documented compose/service | Documented data/source paths |
| --- | --- | --- | --- | --- |
| FFmpeg stable | `soma-ffmpeg` | `/ffmpeg/` | `compose/ffmpeg.compose.yml`, service `ffmpeg` | `/srv/soma/data/ffmpeg`, `services/ffmpeg` |
| FFmpeg dev | `soma-ffmpeg-dev` | `/ffmpeg-dev/` | `compose/ffmpeg-dev.compose.yml`, service `ffmpeg-dev` | `/srv/soma/data/ffmpeg-dev`, `services/ffmpeg-dev` |
| Whisper stable | `myservices-whisper` | `/myservices/whisper/` | `/home/grigorynokhrin/myservices/compose.yaml`, service `whisper` | `/home/grigorynokhrin/myservices/whisper`, source documented as `/home/grigorynokhrin/soma-arch/services/whisper-dev` |
| Whisper dev | `soma-whisper-dev` | `/whisper-dev/` | `compose/whisper-dev.compose.yml`, service `whisper-dev` | `/srv/soma/data/whisper-dev`, `services/whisper-dev` |
| Home | `myservices-home` | `/myservices/` | `/home/grigorynokhrin/myservices/compose.yaml`, service `home` | `/home/grigorynokhrin/myservices/home` documented; no tracked source found |
| Gateway/Caddy | `myservices-caddy` | host `:80` routes | `/home/grigorynokhrin/myservices/compose.yaml`, service `caddy` | tracked reference `gateway/myservices/Caddyfile.current`; live historical `/home/grigorynokhrin/myservices/caddy/Caddyfile` |

Bind mounts documented in repo:

| Service | Source | Destination |
| --- | --- | --- |
| FFmpeg stable | `/srv/soma/data/ffmpeg` | `/data` |
| FFmpeg dev | `/srv/soma/data/ffmpeg-dev` | `/data` |
| Whisper dev | `/srv/soma/data/whisper-dev/jobs` | `/app/data/jobs` |
| Whisper dev | `/srv/soma/data/whisper-dev/outputs` | `/app/outputs` |
| Whisper dev | `/srv/soma/data/whisper-dev/hf_cache` | `/app/hf_cache` |
| Whisper stable | `/home/grigorynokhrin/myservices/whisper/outputs` | `/app/outputs` |
| Whisper stable | `/home/grigorynokhrin/myservices/whisper/data` | `/app/data` |
| Whisper stable | `/home/grigorynokhrin/myservices/whisper/hf_cache` | `/app/hf_cache` |
| Gateway/Caddy | `/home/grigorynokhrin/myservices/caddy/Caddyfile` | `/etc/caddy/Caddyfile` |

Assumptions requiring server confirmation:

- The documented containers are currently active.
- The documented bind mounts are still live.
- `compose_default` and `myservices_default` network memberships match tracked docs.
- The live Caddyfile matches or intentionally differs from `gateway/myservices/Caddyfile.current`.

## 5. Worktree Inventory

Facts from local Git:

| Path | Branch | Commit | Status | Relationship to active services |
| --- | --- | --- | --- | --- |
| `/Users/grigorynokhrin/projects/soma-arch` | `feature/ffmpeg-dev-skeleton` | `c3ed8ca` at audit time | Clean before this report was added | Mac editing/control workspace; not a runtime worktree. |

Repo-documented/server-reported context:

| Path | Branch | Purpose | Status | Relationship to active services |
| --- | --- | --- | --- | --- |
| `/srv/soma/worktrees/ffmpeg-dev-skeleton` | `feature/ffmpeg-dev-skeleton` | Server-side worktree for FFmpeg/dev-stable feature branch | Not directly observable from Mac workspace | Expected server validation checkout for current branch. |
| `/home/grigorynokhrin/soma-arch` | Unknown from direct audit | Server reference repo path | Not directly observable from Mac workspace | Documented as historical/canonical repo path for stable workflow. |

Assumptions requiring server confirmation:

- `/srv/soma/worktrees/ffmpeg-dev-skeleton` exists and has HEAD `0714bcb` or a newer pulled commit.
- `/home/grigorynokhrin/soma-arch` exists and remains the reference repo for stable workflows.
- No additional server worktrees exist.

## 6. Naming Audit

### Consistent Patterns

Observations:

- Stable service source directories omit `-dev`: `services/ffmpeg`.
- Dev service source directories use `-dev`: `services/ffmpeg-dev`, `services/whisper-dev`.
- Stable FFmpeg container uses `soma-ffmpeg`.
- Dev containers use `soma-<service>-dev`: `soma-ffmpeg-dev`, `soma-whisper-dev`.
- Compose files use `<service>.compose.yml` and `<service>-dev.compose.yml`.
- Canonical runbooks use `docs/runbooks/<service>.md`.
- Canonical service design docs use `docs/services/<service>.md`.
- Runtime data for soma services follows `/srv/soma/data/<service>`.

### Inconsistent Or Legacy Patterns

Observations:

- Stable Whisper container is legacy-named `myservices-whisper`, while FFmpeg stable is `soma-ffmpeg`.
- Stable Whisper route is `/myservices/whisper/`, while stable FFmpeg route is `/ffmpeg/`.
- Home and Gateway containers use `myservices-*` names because they belong to the legacy runtime contour.
- Production compose for legacy services lives outside the repo at `/home/grigorynokhrin/myservices/compose.yaml`.
- Tracked Gateway config is under the repo, but live historical Caddyfile is documented under `/home/grigorynokhrin/myservices/caddy/Caddyfile`.
- `services/whisper-dev` appears to serve both dev source and stable production-derived source; there is no tracked `services/whisper` directory.
- `compose/whisper-dev.compose.yml` lacks the explicit top-level project name pattern used by FFmpeg stable/dev.
- Older flat docs coexist with canonical `runbooks/` and `services/` docs.

### Ambiguous Names

Observations:

- `myservices` means both a legacy runtime root and the Home/MyServices user-facing portal.
- `gateway/myservices/Caddyfile.current` is a tracked reference, but `current` may be misread as guaranteed live state.
- `compose_default` is the external network name used for Caddy/dev reachability, but the name does not communicate Caddy or soma ownership.
- `feature/ffmpeg-dev-skeleton` now contains stable FFmpeg, docs foundation, and Gateway/Home/Whisper docs, so the branch name is narrower than its current contents.

## 7. Architecture Interpretation

Facts:

- The local Git repository contains source, compose references, docs, runtime templates, and gateway references.
- The live legacy/stable runtime is documented under `/home/grigorynokhrin/myservices`.
- The soma runtime root is documented as `/srv/soma`.
- The current Mac checkout is not itself the runtime.

Observations:

- **Control plane** appears to be the Git repository plus documentation, compose files, and runtime templates.
- **Runtime** appears to be split between legacy `/home/grigorynokhrin/myservices` and newer `/srv/soma` directories.
- **Deployment infrastructure** appears to include Docker Compose files, Caddy reference config, runtime Makefile, and healthcheck scripts.
- **Documentation** is now centered on `docs/SERVICES_REGISTRY.md`, `docs/runbooks/`, and `docs/services/`.
- **Historical/legacy material** includes older flat docs, `/home/grigorynokhrin/myservices`, `myservices-*` containers, and historical Caddy/Home source outside this repo.

Assumptions:

- The platform is mid-transition from legacy `myservices` ownership toward repo-managed soma service ownership.
- FFmpeg is the first stable service with both tracked stable source and tracked stable compose in this repo.
- Whisper stable remains partially legacy because its production compose and container naming are still under `myservices`.

## 8. Architectural Questions, Missing Conventions, And Documentation Needs

No changes are recommended in this report. The following questions and gaps require clarification before restructuring decisions.

Architectural questions:

1. Should `/home/grigorynokhrin/soma-arch` remain the server reference repo, or should server worktrees under `/srv/soma/worktrees` become the primary operational model?
2. Should stable services eventually all use `/srv/soma/data/<service>` runtime data, or should legacy services keep `/home/grigorynokhrin/myservices` indefinitely?
3. Should stable Whisper eventually gain tracked `services/whisper` and `compose/whisper.compose.yml` equivalents, or remain dev-derived from `services/whisper-dev`?
4. Should stable service routes standardize under top-level paths such as `/ffmpeg/`, or under `/myservices/<service>/`, or remain service-specific?
5. Should Gateway/Caddy live config become fully repo-managed, or remain a manually reconciled legacy file?
6. Should Home source be imported into this repo, or intentionally remain in `/home/grigorynokhrin/myservices/home`?
7. What is the intended long-term meaning of `compose_default` versus `myservices_default`?

Missing conventions:

- Clear policy for stable service source directories when legacy production still uses dev-derived source.
- Clear naming rule for stable routes outside `/myservices`.
- Clear rule for when compose files require explicit top-level project names.
- Clear convention for server worktree names and lifecycle.
- Clear convention for live Caddyfile reconciliation against tracked references.
- Clear convention for where structured release notes and validation reports should begin.

Areas needing documentation:

- Current server top-level `/home/grigorynokhrin` directory inventory with sizes.
- Current server top-level `/srv` and `/srv/soma/worktrees` inventory with sizes.
- Current Docker container list, compose projects, networks, and bind mounts.
- Current Home source ownership and exact file that controls service publication.
- Current stable Whisper deployment source, image, and direct host port policy.
- Current Caddy live mount and network membership.
- Worktree lifecycle policy for branch validation and retirement.

## 9. Commands Run During This Audit

Repository/local commands that succeeded:

```text
pwd
git status --short --branch
git remote -v
git branch -a
git worktree list
find . -maxdepth 2 -type d | sort
find docs -maxdepth 2 -type f -print | sort
find services -maxdepth 2 -type f -print | sort
find compose -maxdepth 2 -type f -print | sort
find gateway -maxdepth 3 -type f -print | sort
find runtime -maxdepth 3 -type f -print | sort
find scripts -maxdepth 3 -type f -print | sort
find .github -maxdepth 3 -type f -print | sort
du -sh . .git compose docs gateway ops runtime scripts services .github
sed -n ... selected docs, compose, gateway, and runtime files
```

Commands that failed because server/runtime resources were not available from this workspace:

```text
ls -la /home/grigorynokhrin
ls -la /srv
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
docker compose ls
```

## 10. Server-Side Refresh Commands For A Future Runtime Audit

These commands should be run on the server when a live audit is approved:

```text
du -sh /home/grigorynokhrin/* 2>/dev/null
du -sh /srv/* 2>/dev/null
find /srv/soma -maxdepth 2 -type d -print | sort
find /srv/soma/worktrees -maxdepth 2 -type d -print | sort
cd /home/grigorynokhrin/soma-arch && git status --short --branch
cd /home/grigorynokhrin/soma-arch && git remote -v
cd /home/grigorynokhrin/soma-arch && git branch -a
cd /home/grigorynokhrin/soma-arch && git worktree list
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
docker compose ls
docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker inspect soma-ffmpeg --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker inspect soma-ffmpeg-dev --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker inspect soma-whisper-dev --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker inspect myservices-whisper --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Do not use these commands as cleanup instructions. They are read-only audit commands except for any implicit shell history or command output files an operator may choose to create separately.
