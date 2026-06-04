# DOCUMENTATION_ARCHITECTURE

This document defines how project documentation should be organized as the `soma-arch` home services platform grows.

It owns documentation structure, responsibility, naming, and lifecycle. It does not replace the engineering workflow or service-specific runbooks.

## 1. Purpose

The purpose of this document is to prevent documentation sprawl by defining:

- documentation hierarchy
- target directory structure
- source-of-truth ownership
- naming conventions
- documentation lifecycle
- minimum docs required by service maturity
- templates for future docs

## 2. Documentation Hierarchy

### Level 1: Constitution

Canonical document:

    docs/ENGINEERING_WORKFLOW.md

Owns:

- global process rules
- roles and gates
- runtime validation policy
- definition of done
- safety rules

### Level 2: Process Playbooks

Current playbook:

    docs/FIRST_RELEASE_PLAYBOOK.md

Future playbooks:

    docs/playbooks/DEV_SERVICE_ITERATION.md
    docs/playbooks/STABLE_RELEASE.md
    docs/playbooks/HOTFIX.md
    docs/playbooks/ROLLBACK.md

Own:

- repeatable operational procedures
- step-by-step release/deploy/rollback flows
- command sequences that apply to a class of work

### Level 3: Service Registry

Target document:

    docs/SERVICES_REGISTRY.md

Owns the single inventory of services:

- service slug
- display name
- route
- port
- container
- image
- compose file
- source path
- runtime data path
- owner/status
- maturity

### Level 4: Service Runbooks

Target files:

    docs/runbooks/ffmpeg.md
    docs/runbooks/whisper.md
    docs/runbooks/home.md
    docs/runbooks/gateway.md

Each runbook should eventually contain:

- purpose
- route
- container
- port
- compose/service name
- repo paths
- live server paths
- deploy commands
- readiness checks
- runtime validation
- logs
- diagnostics
- rollback
- known pitfalls

Runbooks own operational commands. Service design docs may link to runbooks instead of duplicating deploy steps.

### Level 5: Service Design Docs

Target files:

    docs/services/ffmpeg.md
    docs/services/whisper.md
    docs/services/home.md
    docs/services/gateway.md

Each design doc should eventually contain:

- user-facing purpose
- architecture
- data flow
- dev/stable topology
- configuration
- storage/data directories
- API/UI behavior
- operational constraints
- future backlog

Design docs own service behavior and architecture. Runbooks own how to operate the service.

### Level 6: Release Notes

Target pattern:

    docs/releases/YYYY-MM-DD__service__vX.Y.Z__release.md

Own:

- release ID
- release summary
- baseline commit
- included commits
- runtime changes
- validation evidence
- rollback notes

### Level 7: Validation Reports

Target pattern:

    docs/validations/YYYY-MM-DD__service__env__change-slug__validation.md

Own:

- validation scenario
- environment
- commit tested
- commands run
- expected results
- actual results
- logs/status artifacts
- screenshots when useful

### Level 8: ADRs

Target pattern:

    docs/decisions/ADR-YYYYMMDD-NNN-service-change-slug.md

Own:

- significant architecture decisions
- alternatives considered
- consequences
- status

### Level 9: Workflow Briefs / Task Records

Target pattern:

    docs/workflows/YYYY-MM-DD__service__change-slug__brief.md

Own:

- task brief
- affected services
- constraints
- acceptance criteria
- validation plan
- closeout references

## 3. Directory Structure

Target structure:

    docs/
      ENGINEERING_WORKFLOW.md
      DOCUMENTATION_ARCHITECTURE.md
      FIRST_RELEASE_PLAYBOOK.md
      SERVICES_REGISTRY.md

      playbooks/
        DEV_SERVICE_ITERATION.md
        STABLE_RELEASE.md
        HOTFIX.md
        ROLLBACK.md

      runbooks/
        ffmpeg.md
        whisper.md
        home.md
        gateway.md

      services/
        ffmpeg.md
        whisper.md
        home.md
        gateway.md

      releases/
        YYYY-MM-DD__service__vX.Y.Z__release.md

      validations/
        YYYY-MM-DD__service__env__change-slug__validation.md

      decisions/
        ADR-YYYYMMDD-NNN-service-change-slug.md

      workflows/
        YYYY-MM-DD__service__change-slug__brief.md

The current repository still contains legacy flat docs. Migration into the target structure should be incremental and should not obscure existing release or validation history.

## 4. Source Of Truth Rules

Each documentation type has one canonical responsibility:

- `docs/ENGINEERING_WORKFLOW.md` owns global process rules.
- `docs/FIRST_RELEASE_PLAYBOOK.md` owns the first dev-to-stable release process.
- `docs/DOCUMENTATION_ARCHITECTURE.md` owns documentation structure.
- `docs/SERVICES_REGISTRY.md` owns service inventory.
- `docs/runbooks/*.md` own operational commands.
- `docs/services/*.md` own service architecture and behavior.
- `docs/releases/*.md` own release history.
- `docs/validations/*.md` own validation evidence.
- `docs/decisions/*.md` own architectural decisions.
- `docs/workflows/*.md` own task briefs and task records.

Avoid duplication:

- Link to source-of-truth sections instead of copying large command blocks.
- If duplication is unavoidable, mark one location as canonical.
- If two docs conflict, update the canonical owner first, then reconcile references.

## 5. Naming Conventions

Use the conventions from `docs/ENGINEERING_WORKFLOW.md`.

Service slug:

- lowercase
- hyphen-separated
- stable service has no `-dev` suffix
- dev service uses `-dev`
- examples: `ffmpeg`, `whisper`, `home`, `gateway`, `ffmpeg-dev`

Environment slug:

- `dev`
- `stable`
- `gateway`
- `home`
- `prod-candidate` when a temporary production-shaped candidate exists

Change slug:

- short
- lowercase
- hyphen-separated
- describes the behavior or task
- examples: `pal-subtitles-fix`, `large-mp4-metadata`, `stable-rollout`

Release ID:

    <service>-vX.Y.Z-YYYY.MM.DD

Example:

    ffmpeg-v1.0.0-2026.06.04

Validation scenario ID:

    <service>-<env>-<change-slug>-<scenario>

Examples:

    ffmpeg-stable-pal-16x9-vob-validation
    whisper-stable-batch-upload-smoke

ADR number:

    ADR-YYYYMMDD-NNN-service-change-slug

Example:

    ADR-20260604-001-ffmpeg-drop-unsupported-subtitles

## 6. Documentation Lifecycle

New service:

- update `docs/SERVICES_REGISTRY.md`
- create `docs/services/<service>.md`
- create `docs/runbooks/<service>.md`
- create workflow brief if useful

Feature or bugfix:

- update service doc if behavior changes
- update runbook if deploy or operational behavior changes
- create validation report if runtime evidence matters
- create ADR if the architecture decision is significant

First stable release:

- follow `docs/FIRST_RELEASE_PLAYBOOK.md`
- create release note
- update registry
- update Home/gateway docs if affected

Hotfix:

- create or update validation report
- update runbook if a failure mode becomes known
- create release note if stable behavior changed

Reconciliation:

- update docs when live deployment facts differ from tracked docs
- prefer focused reconciliation commits
- do not silently rewrite historical docs unless the task is explicitly archival cleanup

## 7. Minimal Required Docs By Service Maturity

Prototype:

- workflow brief optional
- service design draft optional
- no Home publication

Dev service:

- `SERVICES_REGISTRY` entry required
- service design doc required
- runbook draft required
- validation command required

Stable service:

- `SERVICES_REGISTRY` entry required
- service design doc required
- runbook required
- release note required
- runtime validation evidence required
- Home publication documented if applicable

Maintenance service:

- known pitfalls section required
- rollback section required
- validation scenarios documented

## 8. Initial Documentation Gap Analysis

Planning/gap analysis only. Do not create all of these files in this task.

Likely missing:

- `docs/SERVICES_REGISTRY.md`
- `docs/runbooks/ffmpeg.md`
- `docs/runbooks/whisper.md`
- `docs/runbooks/home.md`
- `docs/runbooks/gateway.md`
- `docs/services/ffmpeg.md`
- `docs/services/whisper.md`
- `docs/services/home.md`
- `docs/services/gateway.md`
- `docs/playbooks/DEV_SERVICE_ITERATION.md`
- `docs/playbooks/STABLE_RELEASE.md`
- `docs/playbooks/HOTFIX.md`
- `docs/playbooks/ROLLBACK.md`

Existing docs that can feed the future structure:

- `docs/FFMPEG_SERVICE_RUNBOOK.md` can feed `docs/runbooks/ffmpeg.md`.
- `docs/WHISPER_RELEASE_MODEL.md` can feed `docs/services/whisper.md` and `docs/runbooks/whisper.md`.
- `docs/CADDY_WHISPER_DEV_ROUTE.md` and `gateway/myservices/Caddyfile.current` can feed `docs/runbooks/gateway.md`.
- `docs/RELEASES.md` can feed future `docs/releases/*.md` entries.

## 9. Relationship To Existing Docs

Primary related docs:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`

Relationship:

- `ENGINEERING_WORKFLOW.md` defines global engineering process.
- `FIRST_RELEASE_PLAYBOOK.md` defines the specific first dev-to-stable release process.
- `DOCUMENTATION_ARCHITECTURE.md` defines the documentation map and ownership model.

No terminology conflicts were found during creation of this document. If future conflicts appear, reconcile them explicitly instead of silently rewriting existing docs.

## 10. Templates

### Service Registry Entry Template

```text
Service:
Display name:
Maturity:
Owner:
Source path:
Compose file:
Container:
Image:
Route:
Direct port:
Runtime data path:
Home published:
Gateway published:
Status:
Last validated:
Runbook:
Service doc:
```

### Service Runbook Template

```text
# <service> Runbook

Purpose:

Routes:

Container/image:

Compose:

Repo paths:

Live server paths:

Build/deploy:

Readiness:

Runtime validation:

Logs/diagnostics:

Rollback/disable:

Known pitfalls:
```

### Service Design Doc Template

```text
# <service> Service Design

User-facing purpose:

Architecture:

Data flow:

Dev/stable topology:

Configuration:

Storage/data directories:

API/UI behavior:

Operational constraints:

Future backlog:
```

### Release Note Template

```text
Release ID:
Service:
Version:
Date:
Baseline commit:

Summary:

Changes:

Runtime changes:

Validation evidence:

Rollback/disable:

Known limitations:
```

### Validation Report Template

```text
Validation ID:
Service:
Environment:
Commit:
Route:
Container:

Scenario:
Expected result:
Actual result:

Commands:

Logs/status artifacts:

Screenshots:

Result:
Follow-ups:
```

### ADR Template

```text
# ADR-YYYYMMDD-NNN-service-change-slug

Status:
Date:
Service:

Context:

Decision:

Alternatives considered:

Consequences:

Validation or follow-up:
```

### Workflow Brief Template

```text
Title:
Service:
Change slug:
Date:

Goal:

Affected services:

Constraints:

Acceptance criteria:

Implementation plan:

Validation plan:

Documentation impact:

Closeout:
```

## 11. Open Questions / Future Work

- Should existing flat docs be migrated into the target directory structure, or should new structure apply only to new docs?
- Should `docs/RELEASES.md` remain as an index after per-release files are introduced?
- Should service registry generation be automated from compose files and runbooks?
- Should validation reports be mandatory for every stable change?
- Should Home and gateway get separate publication playbooks before the next stable service release?
