# Soma Development Environment Build Plan

This document defines a future implementation plan for the target-layout development environment described in `docs/MIGRATION.md` and mapped in `docs/MIGRATION_PLAN.md`.

It is planning only. It does not authorize or perform filesystem, runtime, Compose, container, Gateway, Home, route, or production changes.

## 1. Goal

Build a new isolated development environment under `/srv/soma/dev` that follows the target architecture while leaving every existing runtime environment untouched.

The environment must:

- separate application content, persistent data, artifacts, logs, and configuration
- deploy FFmpeg dev and Whisper dev without changing their stable counterparts
- support direct localhost validation before any publication or routing work
- be reproducible from tracked source and configuration
- have a documented rollback path for every implementation phase

## 2. Existing Development Assets

The following inventory combines repository documentation with the observed server layout. Routes and port mappings are documented configuration facts and require live confirmation before implementation.

| Asset | Repository source/config | Observed server ownership | Documented runtime identity | Data root |
| --- | --- | --- | --- | --- |
| FFmpeg dev | `services/ffmpeg-dev/`, `compose/ffmpeg-dev.compose.yml` | Compose config from `/srv/soma/worktrees/ffmpeg-dev-skeleton/compose/ffmpeg-dev.compose.yml` | Project `soma-ffmpeg-dev`; container `soma-ffmpeg-dev`; route `/ffmpeg-dev/`; `127.0.0.1:18082 -> 8000` | `/srv/soma/data/ffmpeg-dev` |
| Whisper dev | `services/whisper-dev/`, `compose/whisper-dev.compose.yml` | Compose config at `/srv/soma/compose/whisper-dev.compose.yml` | Project `compose`; container `soma-whisper-dev`; route `/whisper-dev/`; `127.0.0.1:18080 -> 8000` | `/srv/soma/data/whisper-dev` |

Other relevant observed assets:

- `/srv/soma/services/whisper-dev` exists, but its authoritative relationship to repository source is not confirmed.
- `/srv/soma/data/whisper-prod-candidate` exists, but it is not part of the normal development target and its lifecycle is unresolved.
- FFmpeg dev and Whisper dev are currently running containers according to the live server layout audit.
- FFmpeg dev Compose is repo-managed; Whisper dev currently uses a server-local Compose copy. The target environment must resolve this ownership difference.
- Existing routes depend on Gateway/Caddy, but the initial target-layout build must use direct localhost ports and must not change Gateway or Home.

## 3. Target Dev Layout

The development environment will use the target structure from `docs/MIGRATION.md`:

```text
/srv/soma/dev/
  app/
    home/
    gateway/
    services/
      whisper/
      ffmpeg/
  compose/
  data/
    whisper/
    ffmpeg/
  artifacts/
    whisper/
    ffmpeg/
  logs/
    whisper/
    ffmpeg/
  config/
    whisper/
    ffmpeg/
```

Target responsibilities:

| Area | Responsibility |
| --- | --- |
| `app/services/` | Deployed application content derived from tracked service source. |
| `compose/` | Development-only Compose definitions and environment wiring. |
| `data/` | Persistent service state that is not a downloadable artifact. |
| `artifacts/` | Generated transcripts, converted media, and other user-facing results. |
| `logs/` | Service and job diagnostics kept outside application source. |
| `config/` | Environment-specific configuration kept outside application source. |
| `app/home/` | Reserved target location for a separately approved development Home deployment. |
| `app/gateway/` | Reserved target location for a separately approved development Gateway deployment. |

No implementation phase in this plan publishes services through Home or Gateway. Direct localhost access is the validation boundary.

## 4. Build Phases

Each phase requires separate approval before execution. A failed validation gate stops the build and triggers that phase's rollback procedure.

### Phase 0: Preflight And Implementation Manifest

1. Refresh the live, read-only inventory of containers, Compose projects, ports, mounts, permissions, disk usage, and active routes.
2. Record the exact Git commit intended for deployment.
3. Compare tracked Compose files with live development Compose configuration.
4. Define the complete directory, ownership, environment-variable, mount, port, project-name, and container-name manifest.
5. Confirm that every target path is development-only and that no bind mount resolves into production or legacy runtime storage.
6. Define backup and rollback evidence before any directory is created.

### Phase 1: Create Target Directory Structure

1. Create only the approved `/srv/soma/dev` directory manifest.
2. Apply the minimum ownership and permissions required by the service runtime users.
3. Keep source, data, artifacts, logs, and configuration in separate directories.
4. Do not copy existing mutable data during this phase.
5. Verify that no symlink or mount crosses into production or legacy paths.

### Phase 2: Deploy FFmpeg Dev Into Target Layout

1. Deploy the validated FFmpeg dev application content to `/srv/soma/dev/app/services/ffmpeg`.
2. Prepare a development-only Compose definition under `/srv/soma/dev/compose` from tracked configuration.
3. Configure FFmpeg dev data, artifacts, logs, and configuration under their target directories.
4. Assign a unique target Compose project, container name, and localhost port that do not collide with any running service.
5. Start only the new target-layout FFmpeg dev service in the later approved execution task.
6. Leave the existing `soma-ffmpeg-dev` and stable `soma-ffmpeg` services unchanged until the new instance has passed validation.

### Phase 3: Deploy Whisper Dev Into Target Layout

1. Resolve whether repository source or `/srv/soma/services/whisper-dev` is authoritative before deployment.
2. Deploy the approved Whisper dev application content to `/srv/soma/dev/app/services/whisper`.
3. Prepare a development-only Compose definition under `/srv/soma/dev/compose` from tracked configuration.
4. Configure Whisper dev data, artifacts, logs, model/cache access, and configuration under approved target paths.
5. Assign a unique target Compose project, container name, and localhost port that do not collide with any running service.
6. Start only the new target-layout Whisper dev service in the later approved execution task.
7. Leave `soma-whisper-dev` and stable `myservices-whisper` unchanged until validation is complete.

### Phase 4: Validate Direct Service Access

1. Validate container health and readiness through direct localhost endpoints only.
2. Run one representative FFmpeg dev workflow and one representative Whisper dev transcription workflow.
3. Confirm that redirects, forms, status polling, and artifact links remain inside the selected development root path.
4. Confirm that no request reaches stable services, Home, or Gateway.
5. Capture rendered Compose configuration, health output, job status, logs, and artifact evidence.

### Phase 5: Validate Persistence And Data Paths

1. Confirm uploads, persistent state, artifacts, logs, and configuration are written only to their assigned target directories.
2. Confirm source directories remain unchanged during jobs.
3. Confirm service users can write required paths without broad permission changes.
4. Confirm data and artifacts survive a normal service restart.
5. Confirm cleanup and retention affect only the target development environment.
6. Confirm shared model/cache use, if approved, does not allow mutable development state to damage production state.

### Phase 6: Validate Restart And Rebuild Behavior

1. Restart only the new target-layout development services and repeat readiness checks.
2. Rebuild only the new development images from the recorded Git commit.
3. Recreate only the new development containers and verify persistence again.
4. Confirm Compose project isolation and absence of orphan or cross-project effects.
5. Re-run representative FFmpeg and Whisper workflows.
6. Record image identity, Compose configuration, mounts, permissions, logs, and validation results.

### Phase 7: Closeout

1. Produce a validation report with the deployed commit, commands, results, warnings, and unresolved issues.
2. Confirm that all pre-existing stable and development services remain unchanged and healthy.
3. Document the approved operating and rollback procedures for the target-layout dev environment.
4. Do not retire old development services until a separate cleanup plan is approved.
5. Do not publish the new environment through Home or Gateway as part of closeout.

## 5. Validation Requirements

| Phase | Readiness checks | Runtime validation | Rollback requirement |
| --- | --- | --- | --- |
| 0. Preflight | Inventory is current; target names, ports, mounts, UID/GID, and disk capacity are known | Rendered configuration can be reviewed without changing runtime | Stop planning; no runtime rollback should be necessary |
| 1. Directories | Exact manifest exists with expected ownership and no cross-environment links | Write tests use disposable files in target dev paths only | Remove only newly created empty/test content according to an approved manifest |
| 2. FFmpeg dev | New container becomes healthy on its unique direct port | UI, remux/conversion, status, logs, and artifact download pass | Stop/remove only the new project; preserve validation artifacts; leave existing services running |
| 3. Whisper dev | Model/runtime initialization completes and health endpoint responds | UI, upload, transcription, status, output, and retention checks pass | Stop/remove only the new project; preserve diagnostics; leave existing services running |
| 4. Direct access | Both services respond without Gateway or Home | Real jobs complete and all generated URLs remain in the target dev environment | Stop new services; retain evidence; do not alter routes |
| 5. Persistence | Mounts and permissions match the manifest | Restart preserves intended data/artifacts; cleanup remains isolated | Restore target dev data from the phase backup or discard only approved test data |
| 6. Restart/rebuild | Recreated services reach readiness from the recorded commit | Representative jobs pass after restart and rebuild | Restore the prior target dev image/config; never roll back stable services |
| 7. Closeout | Evidence is complete and existing environments remain healthy | Final read-only comparison shows no production or legacy changes | Keep the new dev environment disabled if acceptance criteria are incomplete |

Every runtime phase must capture:

- exact Git commit and rendered Compose configuration
- container image, project, name, ports, mounts, and health state
- direct health endpoint output
- one real service workflow result
- artifact and log locations
- permission and persistence evidence
- confirmation that stable services and legacy paths were not changed

## 6. Risk Analysis

### Data Path Risks

- An incorrect bind mount could write development data into stable or legacy storage.
- Existing data roots may mix persistent state, artifacts, logs, and configuration.
- Shared model/cache paths may be mutable or incompatible across environments.
- UID/GID or ownership mismatches may block writes or encourage unsafe permission changes.
- Large uploads, models, caches, and generated media may exceed available SSD capacity.

Mitigation requires an exact mount manifest, path guards, capacity checks, service-user write tests, and backups before mutable data is introduced.

### Compose Risks

- Whisper dev currently uses the generic project name `compose`, which can obscure ownership.
- Reusing project names can cause cross-project container, network, or orphan handling.
- Running Compose from the wrong directory can select the wrong environment file or project context.
- Relative build contexts may resolve differently after deployment.

The target dev environment requires explicit project names, explicit config paths, reviewed rendered configuration, and service-scoped operations.

### Container Naming Risks

- Existing `soma-ffmpeg-dev` and `soma-whisper-dev` names are already in use.
- Reusing stable or legacy names could replace or attach to the wrong service.
- Network aliases can collide even when container names differ.

Target names and aliases must be unique during parallel validation. Final naming requires a separate cutover decision.

### Route And Port Conflicts

- Existing direct ports `18082` and `18080` are documented as occupied by FFmpeg dev and Whisper dev.
- Reusing `/ffmpeg-dev/` or `/whisper-dev/` through the existing Gateway would require routing changes.
- Incorrect application root paths can produce redirects or asset links into another environment.

Initial validation must use newly assigned localhost ports with no Gateway changes. Root-path behavior must be tested directly.

### Home Publication Risks

- Home publishes user-facing tools and could expose an incomplete development service.
- A dev link could replace or confuse a stable service entry.
- Home deployment may require rebuilding an unrelated production-owned container.

The target-layout dev environment must not be added to Home under this plan.

### Gateway Risks

- Gateway/Caddy is production-sensitive and currently belongs to the legacy runtime contour.
- Route ordering, catch-all handlers, and Docker network membership can affect existing services.
- Tracked reference configuration may differ from live configuration.

No Gateway, Caddy, network, DNS, or route change is allowed during this build. Any future publication requires a separate live audit and explicit approval.

### Resource Contention Risks

- Whisper may use the RTX 3060; actual GPU configuration must be verified before implementation.
- Concurrent Whisper, FFmpeg, or candidate workloads can contend for CPU, VRAM, RAM, disk I/O, and storage.
- Readiness may lag behind container startup while models load.

Heavy validation must be serialized, capacity must be observed, and readiness must be proven before jobs begin.

## 7. Production Protection Rules

The future implementation must obey all of the following:

- Production and all stable services remain running and unchanged.
- Do not modify anything under `/home/grigorynokhrin/myservices`.
- Do not stop, recreate, rename, or reconfigure `myservices-home`, `myservices-whisper`, or `myservices-caddy`.
- Do not stop, recreate, rename, or reconfigure stable `soma-ffmpeg`.
- Do not modify stable data such as `/srv/soma/data/ffmpeg`.
- Do not modify production Compose definitions.
- Do not modify Gateway/Caddy configuration, Docker networking, DNS, or routes.
- Do not modify Home or publish new development links.
- Do not replace `/myservices/whisper/`, `/ffmpeg/`, or any other stable route.
- Do not reuse stable container names, Compose projects, ports, volumes, networks, or aliases.
- Do not use broad Compose lifecycle commands against unrelated projects.
- Do not remove old development services or data during the build.
- Stop immediately if any command would affect a path, container, network, volume, or project outside the approved target dev manifest.

## 8. Exit Criteria

A future production migration may be discussed only after all of the following are true:

- The target `/srv/soma/dev` layout is implemented exactly as an approved manifest.
- FFmpeg dev and Whisper dev run from an identified, reproducible Git revision.
- Development Compose ownership is explicit, deterministic, and independent of operational checkout names.
- Application source is separate from data, artifacts, logs, and configuration.
- No service depends on legacy absolute host paths where environment configuration is practical.
- Direct health checks and representative real workflows pass for both services.
- URLs, status polling, redirects, and downloads remain inside the development environment.
- Data persistence, cleanup, retention, permissions, restart, rebuild, and rollback behavior are validated.
- Resource usage and storage capacity are measured on the target server.
- Validation proves stable services, legacy runtime paths, Home, Gateway, and routes were not changed.
- A complete validation report and operating procedure exist.
- All blocking ownership questions in `docs/MIGRATION_PLAN.md` that affect production are resolved.
- Production mapping, backups, cutover, acceptance, and rollback are defined in a separate approved production migration plan.

Passing these criteria permits discussion only. It does not authorize production migration.
