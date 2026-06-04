# DOCUMENTATION_RECONCILIATION

This is a documentation audit report and ownership map for the current `soma-arch` repository.

It does not replace the engineering workflow, documentation architecture, service registry, service runbooks, or release notes. It records which existing documents are canonical, supporting, historical, legacy, or archive candidates so future work does not create competing sources of truth.

Audit date: 2026-06-04

## Scope

Audited locations:

- `docs/`
- `docs/runbooks/`
- repository README files
- `compose/README.md`
- `gateway/README.md`
- `ops/README.md`
- `runtime/README.md`
- `scripts/README.md`
- `services/README.md`

Documents reviewed:

- 34 files under `docs/`
- 7 README files
- total: 41 documents

No Markdown lint configuration or package script was found during this reconciliation.

## Classification Legend

- `CANONICAL`: current source of truth for a topic.
- `ACTIVE SUPPORTING`: useful current material that supports a canonical doc.
- `REFERENCE`: useful background or snapshot, but not authoritative for current operations.
- `LEGACY`: superseded by newer documentation, but may still contain useful historical details.
- `ARCHIVE CANDIDATE`: likely should move to an archive area after unique facts are migrated or linked.
- `OBSOLETE`: no longer useful. No documents are classified as obsolete in this pass.

## Documentation Inventory

| Path | Classification | Purpose / Last Known Role | Current Relevance / Overlap |
| --- | --- | --- | --- |
| `README.md` | REFERENCE | Repository entry point. | Keep concise; should point to canonical workflow, architecture, registry, and runbooks. |
| `compose/README.md` | REFERENCE | Directory note for compose files. | Useful local orientation; service inventory belongs in `docs/SERVICES_REGISTRY.md`. |
| `gateway/README.md` | REFERENCE | Directory note for gateway references. | Gateway operations now live in `docs/runbooks/gateway.md`. |
| `ops/README.md` | REFERENCE | Directory note for ops material. | Supporting orientation only. |
| `runtime/README.md` | REFERENCE | Runtime root template orientation. | Overlaps with runtime policy and status docs; not operational source of truth. |
| `scripts/README.md` | REFERENCE | Directory note for helper scripts. | Supporting orientation only. |
| `services/README.md` | REFERENCE | Directory note for service source. | Service inventory belongs in `docs/SERVICES_REGISTRY.md`. |
| `docs/ENGINEERING_WORKFLOW.md` | CANONICAL | Engineering constitution and standard delivery cycle. | Source of truth for process, gates, validation policy, and definition of done. |
| `docs/DOCUMENTATION_ARCHITECTURE.md` | CANONICAL | Documentation hierarchy, naming, lifecycle, target structure. | Source of truth for documentation structure and ownership rules. |
| `docs/SERVICES_REGISTRY.md` | CANONICAL | Inventory of services, routes, containers, ports, paths, maturity. | Source of truth for platform inventory; should be updated because `docs/runbooks/ffmpeg.md` now exists. |
| `docs/FIRST_RELEASE_PLAYBOOK.md` | CANONICAL | First dev-to-stable release playbook. | Source of truth for the first promotion workflow; service runbooks should link to it, not duplicate it. |
| `docs/runbooks/ffmpeg.md` | CANONICAL | Stable FFmpeg operational runbook. | Source of truth for FFmpeg operations. Absorbs the operational pieces of older FFmpeg docs. |
| `docs/DECISIONS.md` | CANONICAL | Current ADR-style decision log. | Source of truth for existing architecture decisions until split into `docs/decisions/`. |
| `docs/TARGET_ARCHITECTURE.md` | CANONICAL | Target platform architecture and route conventions. | Source of truth for target architecture; current runtime state belongs in registry/runbooks. |
| `docs/SYSTEM_GOALS.md` | CANONICAL | User-facing system goals and naming conventions. | Source of truth for product/platform goals. |
| `docs/JOB_SCHEMA.md` | CANONICAL | Shared job model and lifecycle expectations. | Source of truth for job schema unless replaced by a versioned schema doc later. |
| `docs/RELEASES.md` | ACTIVE SUPPORTING | Monolithic release log for Whisper releases. | Current release history source until structured `docs/releases/` entries exist. |
| `docs/runbooks/whisper.md` | CANONICAL | Stable Whisper operational runbook. | Source of truth for Whisper operations. |
| `docs/runbooks/home.md` | CANONICAL | Home/MyServices operational runbook. | Source of truth for Home publication, rebuild/restart, validation, and diagnostics. |
| `docs/runbooks/gateway.md` | CANONICAL | Gateway/Caddy operational runbook. | Source of truth for Gateway inspection, route validation, reload boundaries, and diagnostics. |
| `docs/services/home.md` | CANONICAL | Home/MyServices architecture and behavior design. | Source of truth for Home purpose, publication model, navigation model, and boundaries. |
| `docs/services/whisper.md` | CANONICAL | Stable Whisper architecture and behavior design. | Source of truth for Whisper design; operations remain in `docs/runbooks/whisper.md`. |
| `docs/WHISPER_RELEASE_MODEL.md` | ACTIVE SUPPORTING | Whisper dev-derived production release model. | Supports `docs/runbooks/whisper.md` and future `docs/services/whisper.md`. |
| `docs/services/ffmpeg.md` | CANONICAL | Stable FFmpeg architecture and behavior design. | Source of truth for FFmpeg design; operations remain in `docs/runbooks/ffmpeg.md`. |
| `docs/FFMPEG_DEV_IMPLEMENTATION.md` | ACTIVE SUPPORTING | FFmpeg implementation behavior and profile details. | Supports `docs/services/ffmpeg.md`. Operations now belong in `docs/runbooks/ffmpeg.md`. |
| `docs/FFMPEG_DEV_SERVICE_SPEC.md` | ACTIVE SUPPORTING | FFmpeg dev service requirements and model. | Supports `docs/services/ffmpeg.md`; not an operations runbook. |
| `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` | ACTIVE SUPPORTING | Dev-only FFmpeg rollout and troubleshooting. | Still active for `ffmpeg-dev`; stable operations belong in `docs/runbooks/ffmpeg.md`. |
| `docs/FFMPEG_SERVICE_RUNBOOK.md` | LEGACY | First stable FFmpeg service runbook in flat docs layout. | Superseded by `docs/runbooks/ffmpeg.md`; keep until unique facts are confirmed migrated. |
| `docs/CADDY_WHISPER_DEV_ROUTE.md` | ACTIVE SUPPORTING | First Whisper dev Caddy route validation and notes. | Supports `docs/runbooks/gateway.md`; not source of truth for all Caddy routes. |
| `docs/RUNTIME_HEALTHCHECK.md` | ACTIVE SUPPORTING | Runtime healthcheck design and expected behavior. | Supports future gateway/home/platform runbooks; commands may be referenced by service runbooks. |
| `docs/RUNTIME_MAKEFILE.md` | ACTIVE SUPPORTING | Runtime Makefile commands and safety notes. | Supports operational docs; not full platform inventory. |
| `docs/WHISPER_DEV_BOOTSTRAP.md` | ACTIVE SUPPORTING | Whisper dev bootstrap and validation record. | Supports future Whisper runbook/service design doc. |
| `docs/WHISPER_DEV_SMOKE_TEST.md` | REFERENCE | Whisper dev smoke-test report. | Validation evidence; future location should be `docs/validations/`. |
| `docs/WHISPER_DEV_RETENTION_TEST.md` | REFERENCE | Whisper dev retention validation report. | Validation evidence; future location should be `docs/validations/`. |
| `docs/WHISPER_RETENTION_CLEANUP.md` | REFERENCE | Manual Whisper retention cleanup record. | Useful historical cleanup evidence; future retention policy belongs in Whisper runbook/design doc. |
| `docs/PROJECT_PHASE_1_STATUS.md` | REFERENCE | Phase 1 completion snapshot. | Historical project phase closeout; superseded for current inventory by registry/runbooks. |
| `docs/CODEX_HANDOFF.md` | REFERENCE | Earlier Codex handoff and orientation. | Useful onboarding snapshot; current process belongs in `ENGINEERING_WORKFLOW.md`. |
| `docs/CODEX_TASK_TEMPLATE.md` | ACTIVE SUPPORTING | Prompt/task templates for Codex work. | Supports workflow; could eventually move under `docs/workflows/` or link from workflow doc. |
| `docs/CURRENT_STATE.md` | ARCHIVE CANDIDATE | Early current-state snapshot. | Useful historical baseline; current state should be registry plus runbooks. |
| `docs/RUNTIME_STATUS.md` | ARCHIVE CANDIDATE | Runtime status snapshot. | Useful historical evidence; current status should be registry plus service runbooks. |
| `docs/BOOTSTRAP_STATUS.md` | ARCHIVE CANDIDATE | Bootstrap status snapshot. | Historical; unique facts should be linked or migrated before archiving. |
| `docs/SRV_SOMA_SKELETON.md` | ARCHIVE CANDIDATE | `/srv/soma` skeleton creation record. | Historical setup evidence; target runtime layout belongs in architecture/runbooks. |
| `docs/BASELINES.md` | REFERENCE | Baseline capture index. | Useful historical reference; future baselines may belong under `docs/validations/` or `docs/releases/`. |
| `docs/REPO_LOCATIONS.md` | REFERENCE | Repo and runtime path map. | Overlaps with registry and runbooks; keep as path reference until absorbed. |
| `docs/RUNTIME_ROOT_POLICY.md` | REFERENCE | Runtime root ownership and directory policy. | Still useful background; target ownership should be reflected in architecture/runbooks. |
| `docs/MIGRATION_PLAN.md` | REFERENCE | Original migration plan. | Historical plan; active workflow is now governed by workflow/playbook docs. |
| `docs/PHASE_2_PLAN.md` | LEGACY | Early Phase 2 plan for Whisper defaults and FFmpeg dev. | Mostly completed/superseded by FFmpeg and Whisper docs. |

## Canonical Ownership Map

| Topic | Owner Document | Supporting Documents | No Longer Authoritative For This Topic |
| --- | --- | --- | --- |
| Engineering process | `docs/ENGINEERING_WORKFLOW.md` | `docs/CODEX_TASK_TEMPLATE.md`, `docs/FIRST_RELEASE_PLAYBOOK.md` | `docs/CODEX_HANDOFF.md`, phase/status snapshots |
| Documentation structure | `docs/DOCUMENTATION_ARCHITECTURE.md` | this reconciliation report | Ad hoc flat-doc naming in older docs |
| Platform inventory | `docs/SERVICES_REGISTRY.md` | service runbooks, gateway reference config | `docs/CURRENT_STATE.md`, `docs/RUNTIME_STATUS.md`, `docs/PROJECT_PHASE_1_STATUS.md` |
| FFmpeg operations | `docs/runbooks/ffmpeg.md` | `docs/FFMPEG_SERVICE_RUNBOOK.md`, `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`, `docs/FFMPEG_DEV_IMPLEMENTATION.md` | `docs/FFMPEG_SERVICE_RUNBOOK.md` for stable operations |
| FFmpeg behavior/design | `docs/services/ffmpeg.md` | `docs/FFMPEG_DEV_SERVICE_SPEC.md`, `docs/FFMPEG_DEV_IMPLEMENTATION.md`, source selfchecks | `docs/runbooks/ffmpeg.md` should not become design spec |
| FFmpeg dev rollout | `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` | `docs/runbooks/ffmpeg.md` for stable/dev split | Stable FFmpeg runbooks for dev-specific deployment |
| Whisper operations | `docs/runbooks/whisper.md` | `docs/WHISPER_RELEASE_MODEL.md`, `docs/RELEASES.md`, Whisper validation docs | `docs/PROJECT_PHASE_1_STATUS.md`, `docs/CODEX_HANDOFF.md` |
| Whisper behavior/design | `docs/services/whisper.md` | `docs/WHISPER_RELEASE_MODEL.md`, `docs/JOB_SCHEMA.md`, `docs/WHISPER_DEV_BOOTSTRAP.md` | scattered phase/status docs |
| Home operations | `docs/runbooks/home.md` | `docs/SERVICES_REGISTRY.md`, `docs/runbooks/ffmpeg.md`, `docs/FFMPEG_SERVICE_RUNBOOK.md` | `docs/CURRENT_STATE.md` and `docs/RUNTIME_STATUS.md` as current instructions |
| Home behavior/design | `docs/services/home.md` | `docs/runbooks/home.md`, `docs/SERVICES_REGISTRY.md`, `docs/FIRST_RELEASE_PLAYBOOK.md` | service runbooks as Home architecture docs |
| Gateway/Caddy operations | `docs/runbooks/gateway.md` | `gateway/myservices/Caddyfile.current`, `docs/CADDY_WHISPER_DEV_ROUTE.md`, FFmpeg runbook route sections | individual service rollout docs as global Caddy source |
| Target architecture | `docs/TARGET_ARCHITECTURE.md` | `docs/SYSTEM_GOALS.md`, `docs/DECISIONS.md` | migration/status snapshots |
| Runtime healthcheck behavior | `docs/RUNTIME_HEALTHCHECK.md` until platform runbook exists | `runtime/README.md`, `docs/RUNTIME_MAKEFILE.md` | service-specific release reports |
| Release history | `docs/RELEASES.md` until structured release files exist | service runbooks and validation docs | phase status docs |
| Job schema | `docs/JOB_SCHEMA.md` | service implementations and runbooks | individual service-specific status examples |

## FFmpeg Reconciliation

FFmpeg docs reviewed:

- `docs/runbooks/ffmpeg.md`
- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`

Already absorbed into `docs/runbooks/ffmpeg.md`:

- stable route `/ffmpeg/`
- dev route `/ffmpeg-dev/`
- port split `18083` stable and `18082` dev
- data directory split
- Caddy route ordering
- Home publication rule
- direct and Caddy health checks
- readiness loop
- status/job log diagnostics
- runtime validation scenarios
- large MP4 metadata operational rules
- subtitle handling policy
- PAL handling policy
- rollback/disable notes

Unique information remaining outside the canonical runbook:

- `docs/FFMPEG_DEV_SERVICE_SPEC.md` contains product requirements, API sketches, job/status models, and safety constraints that support `docs/services/ffmpeg.md`.
- `docs/FFMPEG_DEV_IMPLEMENTATION.md` contains implementation details, profile specifics, and limitations that support `docs/services/ffmpeg.md`.
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` remains active for experimental `ffmpeg-dev` rollout, especially server worktree and direct-bind validation.
- `docs/FFMPEG_SERVICE_RUNBOOK.md` contains the first flat-layout stable runbook and can become legacy once all unique facts are confirmed in `docs/runbooks/ffmpeg.md`.

Classification:

- Stable FFmpeg operations: `docs/runbooks/ffmpeg.md` is canonical.
- FFmpeg dev operations: `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` remains active supporting.
- FFmpeg design/behavior: `docs/services/ffmpeg.md` is canonical.
- `docs/FFMPEG_SERVICE_RUNBOOK.md` is legacy.

Reconciliation note:

- `docs/SERVICES_REGISTRY.md` has been updated to recognize `docs/runbooks/ffmpeg.md` and `docs/services/ffmpeg.md`.

## Whisper Reconciliation

Whisper docs reviewed:

- `docs/WHISPER_RELEASE_MODEL.md`
- `docs/RELEASES.md`
- `docs/WHISPER_DEV_BOOTSTRAP.md`
- `docs/WHISPER_DEV_SMOKE_TEST.md`
- `docs/WHISPER_DEV_RETENTION_TEST.md`
- `docs/WHISPER_RETENTION_CLEANUP.md`
- `docs/PROJECT_PHASE_1_STATUS.md`
- `docs/CADDY_WHISPER_DEV_ROUTE.md`

Current state:

- `docs/runbooks/whisper.md` is the canonical operational source.
- `docs/services/whisper.md` is the canonical design source.
- `docs/WHISPER_RELEASE_MODEL.md` remains the strongest supporting source for the dev-derived production release model.
- `docs/RELEASES.md` owns release history and validation evidence for production promotions.
- Dev bootstrap/smoke/retention docs are useful validation evidence, not current source of truth.

`docs/runbooks/whisper.md` absorbs:

- dev/prod route model
- production compose ownership split
- environment variables
- runtime volume paths
- permission requirements
- health checks
- submit/result smoke-test procedure
- retention behavior
- rollback image/backup conventions
- Caddy contract for `/myservices/whisper*`
- safety warnings about GPU contention and legacy route preservation

Recommended classification:

- `docs/runbooks/whisper.md`: canonical.
- `docs/services/whisper.md`: canonical.
- `docs/WHISPER_RELEASE_MODEL.md`: active supporting.
- `docs/RELEASES.md`: active supporting release history.
- Whisper dev validation docs: reference.
- Phase/status docs: reference or archive candidates after unique facts are migrated.

## Home And Gateway Reconciliation

Home:

- No tracked Home source was identified in this repository.
- The current expected Home UX is documented as `FFmpeg -> /ffmpeg/`.
- `docs/runbooks/home.md` is now the canonical Home operational source.
- `docs/services/home.md` is now the canonical Home behavior/design source.

Gateway/Caddy:

- Tracked Caddy reference config exists at `gateway/myservices/Caddyfile.current`.
- The route reference includes `/myservices/whisper*`, `/whisper-dev*`, `/ffmpeg-dev*`, `/ffmpeg*`, `/myservices/ocr*`, and `/myservices*`.
- `docs/CADDY_WHISPER_DEV_ROUTE.md` is a valuable route-change validation report, not a global Caddy runbook.
- `docs/runbooks/gateway.md` is now the canonical Gateway/Caddy operational source.
- Gateway behavior/design still needs future owner `docs/services/gateway.md`.

`docs/runbooks/gateway.md` absorbs:

- live Caddyfile path and mount-check procedure
- tracked vs live config distinction
- route order rules
- Docker network/alias requirements
- validation and reload procedure
- service-specific route contracts by link, not copied in full

## Documentation Duplication Analysis

| Duplication | Locations | Recommended Owner | Recommendation |
| --- | --- | --- | --- |
| FFmpeg stable deployment commands | `docs/runbooks/ffmpeg.md`, `docs/FFMPEG_SERVICE_RUNBOOK.md`, `docs/FIRST_RELEASE_PLAYBOOK.md` | `docs/runbooks/ffmpeg.md` for FFmpeg-specific commands; `docs/FIRST_RELEASE_PLAYBOOK.md` for generic first-release flow | Keep canonical runbook; mark flat runbook legacy; cross-link playbook. |
| FFmpeg dev deployment commands | `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`, `docs/runbooks/ffmpeg.md` | `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` | Keep dev runbook; stable runbook should only summarize dev/stable separation. |
| FFmpeg route/topology facts | `docs/runbooks/ffmpeg.md`, `docs/FFMPEG_SERVICE_RUNBOOK.md`, `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`, `docs/SERVICES_REGISTRY.md`, `gateway/myservices/Caddyfile.current` | `docs/SERVICES_REGISTRY.md` for inventory; `docs/runbooks/ffmpeg.md` for operations; `gateway/...` for reference config | Keep concise copies only where operationally necessary; update stale registry gap text. |
| FFmpeg behavior and profile policy | `docs/FFMPEG_DEV_IMPLEMENTATION.md`, `docs/FFMPEG_DEV_SERVICE_SPEC.md`, `docs/runbooks/ffmpeg.md` | future `docs/services/ffmpeg.md` | Merge behavior into service design doc later; keep runbook focused on operations. |
| Whisper release/promotion flow | `docs/WHISPER_RELEASE_MODEL.md`, `docs/RELEASES.md`, `docs/PROJECT_PHASE_1_STATUS.md` | future `docs/runbooks/whisper.md`; `docs/RELEASES.md` for release history | Create Whisper runbook before adding more Whisper operational docs. |
| Runtime topology and paths | `docs/SERVICES_REGISTRY.md`, `docs/CURRENT_STATE.md`, `docs/RUNTIME_STATUS.md`, `docs/REPO_LOCATIONS.md`, `docs/PROJECT_PHASE_1_STATUS.md` | `docs/SERVICES_REGISTRY.md` | Keep registry current; archive old snapshots after unique facts are migrated. |
| Gateway route procedure | `docs/CADDY_WHISPER_DEV_ROUTE.md`, `docs/runbooks/ffmpeg.md`, `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`, `gateway/myservices/Caddyfile.current` | `docs/runbooks/gateway.md` | Keep service runbooks focused on service-specific checks and link to Gateway runbook for global Caddy operations. |
| Validation evidence | `docs/WHISPER_DEV_SMOKE_TEST.md`, `docs/WHISPER_DEV_RETENTION_TEST.md`, `docs/RELEASES.md`, `docs/runbooks/ffmpeg.md` | future `docs/validations/` for detailed evidence; runbooks for scenario checklist only | Reference existing evidence; move future reports to structured validations. |
| Historical phase status | `docs/PROJECT_PHASE_1_STATUS.md`, `docs/BOOTSTRAP_STATUS.md`, `docs/SRV_SOMA_SKELETON.md`, `docs/PHASE_2_PLAN.md` | no current owner; historical archive | Archive after the registry/runbooks cover current facts. |

## Proposed Documentation State

Canonical:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/runbooks/home.md`
- `docs/runbooks/gateway.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/services/home.md`
- `docs/DECISIONS.md`
- `docs/TARGET_ARCHITECTURE.md`
- `docs/SYSTEM_GOALS.md`
- `docs/JOB_SCHEMA.md`

Active supporting:

- `docs/RELEASES.md`
- `docs/WHISPER_RELEASE_MODEL.md`
- `docs/FFMPEG_DEV_IMPLEMENTATION.md`
- `docs/FFMPEG_DEV_SERVICE_SPEC.md`
- `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md`
- `docs/CADDY_WHISPER_DEV_ROUTE.md`
- `docs/RUNTIME_HEALTHCHECK.md`
- `docs/RUNTIME_MAKEFILE.md`
- `docs/WHISPER_DEV_BOOTSTRAP.md`
- `docs/CODEX_TASK_TEMPLATE.md`

Reference:

- README files
- `docs/BASELINES.md`
- `docs/CODEX_HANDOFF.md`
- `docs/MIGRATION_PLAN.md`
- `docs/PROJECT_PHASE_1_STATUS.md`
- `docs/REPO_LOCATIONS.md`
- `docs/RUNTIME_ROOT_POLICY.md`
- `docs/WHISPER_DEV_SMOKE_TEST.md`
- `docs/WHISPER_DEV_RETENTION_TEST.md`
- `docs/WHISPER_RETENTION_CLEANUP.md`

Legacy:

- `docs/FFMPEG_SERVICE_RUNBOOK.md`
- `docs/PHASE_2_PLAN.md`

Archive candidates:

- `docs/BOOTSTRAP_STATUS.md`
- `docs/CURRENT_STATE.md`
- `docs/RUNTIME_STATUS.md`
- `docs/SRV_SOMA_SKELETON.md`

Obsolete:

- none identified

## Reconciliation Actions

Priority 1, before creating more docs:

1. Add short supersession notes to `docs/FFMPEG_SERVICE_RUNBOOK.md` and `docs/PHASE_2_PLAN.md` instead of leaving them as silently competing docs.
2. Decide whether `docs/FFMPEG_DEV_ROLLOUT_RUNBOOK.md` remains in the flat docs directory or later moves to target runbook/playbook structure.

Priority 2, do soon:

1. Create `docs/services/gateway.md` for Gateway behavior/design ownership.

Priority 3, can wait:

1. Create `docs/archive/` only after deciding archive naming conventions.
2. Move historical phase/status snapshots into archive with redirects or supersession notes.
3. Split `docs/RELEASES.md` into structured `docs/releases/*.md` files.
4. Move future validation reports into `docs/validations/`.
5. Split `docs/DECISIONS.md` into individual ADR files under `docs/decisions/` if decision volume grows.

## Recommendation For Next Phase

Options evaluated:

- Option A: Create Whisper runbook.
- Option B: Create FFmpeg service design doc.
- Option C: Perform archive/deprecation cleanup.

Recommended next step: create `docs/services/gateway.md`.

Reason:

- FFmpeg now has a canonical operational runbook.
- Whisper now has a canonical operational runbook.
- Gateway now has a canonical operational runbook.
- Home now has canonical operational and service design documents.
- Gateway still lacks a service design document.
- Archive/deprecation cleanup should wait until Whisper/Home/Gateway canonical owners exist, otherwise useful facts may be buried before they are absorbed.

Create the Gateway service design doc so routing architecture has a canonical home separate from operations.
