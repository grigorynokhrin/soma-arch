# ENGINEERING_WORKFLOW

This document defines the engineering workflow for developing, validating, releasing, and documenting home services in `soma-arch`.

It is the general process constitution for service work. Specific playbooks, such as `docs/FIRST_RELEASE_PLAYBOOK.md`, should build on this workflow rather than replace it.

## 1. Purpose

The purpose of this workflow is to keep service development safe, reproducible, and auditable across:

- the Mac workspace
- Codex/Gavrik implementation work
- server worktrees
- Docker runtime validation
- stable Home and gateway publication

Critical rule:

Server validation is valid only when the exact changes were committed, pushed, pulled on the server, built, restarted, waited for readiness, and runtime-tested.

## 2. Scope

This workflow applies to services and operational assets in `soma-arch`, including:

- stable services such as Whisper and FFmpeg
- dev services such as `whisper-dev` and `ffmpeg-dev`
- supporting Home/MyServices UI
- Caddy/gateway references
- compose files
- runtime runbooks and validation docs

It does not grant permission to change production-sensitive systems. Gateway, Home, stable services, production compose, and unrelated services still require explicit approval when affected.

## 3. Roles

This is a lightweight engineering workflow, not Scrum.

Human owner / business owner / architect:

- defines business goals and product intent
- sets constraints and safety boundaries
- approves product decisions
- explicitly approves stable releases
- explicitly approves gateway changes
- explicitly approves Home publication
- explicitly approves production-sensitive actions

ChatGPT engineering coordinator:

- helps analyze tasks
- prepares engineering plans
- writes Codex task briefs
- reviews logs, diff summaries, and validation outputs
- can identify risks and inconsistencies
- is not a runtime source of truth without actual logs, status output, or command output

Codex/Gavrik implementation agent:

- changes code and documentation
- runs local validation
- prepares commits and pushes
- updates documentation together with code when behavior changes
- reports validation output and final repository status

Server/runtime environment:

- source of truth for actual service behavior
- must only be validated after pull, build, restart, readiness wait, and runtime validation
- can reveal deployment issues that local checks cannot

## 4. Core Principles

- Work in small, auditable steps.
- Keep dev and stable services separate.
- Home must link only to stable user-facing tools.
- Dev routes are for engineering/testing only.
- Do not treat server rebuild as proof that a patch was applied unless the server pulled the exact commit.
- Commit and push before server validation.
- Validate direct service routes before Caddy/Home publication.
- Use readiness waits after restart.
- Update docs when behavior changes.
- Keep runtime data out of Git.
- Preserve rollback or disable paths for production-sensitive work.

## 5. Environments

Mac workspace:

    /Users/grigorynokhrin/projects/soma-arch

Purpose:

- edit code and docs
- run local selfchecks/tests
- commit and push

Server worktrees:

    /srv/soma/worktrees/...

Purpose:

- pull exact commits
- build images
- restart services
- run direct and Caddy runtime validation

Codex/Gavrik:

- implementation agent operating in the repo workspace
- may run local checks, commit, and push when explicitly requested

Dev environment:

- for experiments and active development
- can change more often than stable
- still requires commit/push/pull before server validation
- should not be linked from Home

Stable environment:

- user-facing tool
- changes only after confirmed dev validation or explicit approval
- Home publishes stable services only

Gateway/Home environment:

- production-sensitive
- must not be changed without explicit approval
- Home changes may require image rebuild
- before changing Caddy, inspect live mounts:

    docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'

## 6. Standard Development Cycle

### DISCOVER

Goal:

- understand the request, constraints, affected services, and risk.

Required actions:

- read the task brief
- identify affected services and files
- list safety constraints
- inspect relevant docs and current state

Required artifacts:

- task brief
- affected services list
- constraints list

Exit criteria:

- scope is clear enough to design or ask targeted questions
- unsafe or ambiguous actions are identified

### DESIGN

Goal:

- decide what should change and why.

Required actions:

- outline behavior or documentation target
- define acceptance criteria
- identify risks
- define rollback expectation when runtime or stable behavior is affected

Required artifacts:

- design note
- acceptance criteria
- risk list
- rollback expectation if applicable

Exit criteria:

- intended behavior is clear
- validation target is known

### PLAN

Goal:

- produce an implementation and validation path.

Required actions:

- list files to add/change
- define local validation commands
- define server validation commands when needed
- identify docs impact

Required artifacts:

- implementation plan
- validation plan
- documentation impact checklist

Exit criteria:

- work can proceed without hidden deployment assumptions

### IMPLEMENT

Goal:

- make the planned code, config, or documentation changes.

Required actions:

- edit only scoped files
- keep changes minimal
- avoid unrelated refactors
- update docs with behavior changes

Required artifacts:

- changed files list
- code/doc diff

Exit criteria:

- diff matches the plan or deviations are explained

### LOCAL VERIFY

Goal:

- prove local syntax, tests, formatting, and diff hygiene.

Required actions:

- run service selfchecks/tests
- run `compileall` for Python services when applicable
- run `git diff --check`
- run `git diff --stat`
- run `git status --short`

Required artifacts:

- selfcheck/tests output
- compileall output if applicable
- `git diff --check` output
- `git diff --stat` output
- `git status --short` output

Exit criteria:

- local checks pass
- status shows only intended changes

### INTEGRATE

Goal:

- make the change available to server validation and team review.

Required actions:

- stage intended files
- commit with a clear message
- push to the intended branch

Required artifacts:

- commit message
- commit hash
- pushed branch

Exit criteria:

- commit exists remotely
- server can pull the exact commit

### SERVER DEPLOY

Goal:

- deploy the exact committed code to server runtime.

Required actions:

- check server Git state
- confirm branch is correct and not detached HEAD
- pull with `git pull --ff-only`
- build image
- restart or `up -d` target service only

Required artifacts:

- server git status
- server branch
- server `git log --oneline -3`
- pull output
- build output
- restart output

Exit criteria:

- server is running the intended commit
- target container is recreated/restarted as intended

### READINESS

Goal:

- wait until the service is actually ready before validating.

Required actions:

- run a healthcheck loop or an intentional sleep plus healthcheck
- check container status if healthcheck fails

Required artifacts:

- readiness command
- readiness result
- container status

Exit criteria:

- service health endpoint responds
- transient restart errors are no longer being mistaken for product failures

### RUNTIME VALIDATE

Goal:

- prove actual server behavior meets acceptance criteria.

Required actions:

- run direct route checks
- run Caddy route checks if gateway is in scope
- execute the validation scenario
- collect status/log artifacts
- use screenshots only when useful for UI or visual media validation

Required artifacts:

- validation command or scenario
- expected result
- actual result
- logs/status artifacts
- screenshots only when useful

Exit criteria:

- runtime behavior matches acceptance criteria
- failures are traced to actual command/log/status evidence

### RECONCILE DOCS

Goal:

- make repository docs match implemented and deployed behavior.

Required actions:

- update runbooks, service docs, release docs, and gateway references as needed
- capture runtime facts learned during rollout
- commit documentation changes if separate

Required artifacts:

- updated docs list
- doc commit hash if separate

Exit criteria:

- docs do not contradict the live or intended state
- operational lessons are not trapped only in chat history

### CLOSE

Goal:

- report the final state clearly.

Required actions:

- summarize what changed
- include validation output
- include commit hash and push result
- state limitations and follow-up items
- report final Git status

Required artifacts:

- final summary
- known limitations
- follow-up backlog items if any

Exit criteria:

- human owner can see what changed, what was validated, and what remains

## 7. Required Artifacts By Stage

| Stage | Required artifacts |
| --- | --- |
| DISCOVER | Task brief, affected services list, constraints list |
| DESIGN | Design note, acceptance criteria, risk list, rollback expectation if applicable |
| PLAN | Implementation plan, validation plan, documentation impact checklist |
| IMPLEMENT | Changed files list, code/doc diff |
| LOCAL VERIFY | Selfcheck/tests output, compileall output if applicable, `git diff --check`, `git diff --stat`, `git status --short` |
| INTEGRATE | Commit message, commit hash, pushed branch |
| SERVER DEPLOY | Server git status, server branch, `git log --oneline -3`, pull output, build output, restart output |
| READINESS | Readiness command, readiness result, container status |
| RUNTIME VALIDATE | Validation scenario/command, expected result, actual result, logs/status artifacts, screenshots when useful |
| RECONCILE DOCS | Updated docs list, doc commit hash if separate |
| CLOSE | Final summary, known limitations, follow-up backlog items |

## 8. Naming Conventions

Service slugs:

- lowercase
- hyphen-separated
- stable service has no `-dev` suffix
- dev service uses `-dev`
- examples: `whisper`, `whisper-dev`, `ffmpeg`, `ffmpeg-dev`

Documentation paths for future structured artifacts:

    docs/workflows/
      YYYY-MM-DD__service__change-slug__brief.md

    docs/decisions/
      ADR-YYYYMMDD-NNN-service-change-slug.md

    docs/releases/
      YYYY-MM-DD__service__vX.Y.Z__release.md

    docs/validations/
      YYYY-MM-DD__service__env__change-slug__validation.md

    docs/runbooks/
      service-name.md

    docs/services/
      service-name.md

Examples:

    docs/workflows/2026-06-04__ffmpeg__pal-subtitles-fix__brief.md
    docs/decisions/ADR-20260604-001-ffmpeg-drop-unsupported-subtitles.md
    docs/releases/2026-06-04__ffmpeg__v1.0.0__stable-release.md
    docs/validations/2026-06-04__ffmpeg__stable__pal-16x9-validation.md
    docs/runbooks/ffmpeg.md
    docs/services/ffmpeg.md

Branch names:

    feature/<service>-<change-slug>
    fix/<service>-<change-slug>
    docs/<change-slug>
    release/<service>-vX.Y.Z

Examples:

    feature/ffmpeg-pal-profiles
    fix/ffmpeg-large-mp4-metadata
    docs/engineering-workflow
    release/ffmpeg-v1.0.0

Commit messages:

    type(scope): summary

Examples:

    docs(workflow): define engineering workflow constitution
    fix(ffmpeg): drop unsupported subtitles in legacy conversion
    docs(ffmpeg): reconcile stable rollout notes
    release(ffmpeg): promote dev baseline to stable

Release IDs:

    <service>-vX.Y.Z-YYYY.MM.DD

Example:

    ffmpeg-v1.0.0-2026.06.04

Validation scenario names:

    <service>-<env>-<change-slug>-<scenario>

Example:

    ffmpeg-stable-pal-16x9-vob-validation

Runtime artifact references:

- include job id if available
- include route
- include service/container
- include input filename only when safe
- include artifact filenames when they are not secrets or private data

## 9. Change Types

| Type | Use when | Runtime tests required | Docs required | Stable promotion allowed | Approval level |
| --- | --- | --- | --- | --- | --- |
| feature | Adds user-visible capability | Yes for service behavior | Yes | Yes after validation | Human approval for stable exposure |
| bugfix | Fixes incorrect behavior | Yes if runtime behavior changes | Yes when behavior or ops changes | Yes after validation | Human approval for stable services |
| refactor | Changes structure without intended behavior change | Local tests; runtime if risk is nontrivial | Usually note if important | Only with validation | Human approval if stable-sensitive |
| docs | Documentation only | No, unless docs claim runtime state | Yes | Not applicable | Normal review |
| infra | Compose, Docker, runtime, gateway, healthcheck | Yes | Yes | Yes after validation | Explicit approval |
| config | Settings, env, defaults, routes | Yes if runtime-visible | Yes | Yes after validation | Explicit approval for stable/gateway/Home |
| release | Promotes or updates stable service | Yes | Yes | Yes | Explicit stable release approval |
| hotfix | Urgent stable fix | Yes, focused | Yes, can reconcile after if urgent | Yes | Explicit urgent approval |
| validation-only | Runs tests/checks without changing behavior | Yes, by definition | Capture result if important | No by itself | Approval if touching runtime |
| reconcile | Aligns repo/docs with live facts | Usually no, unless config changes | Yes | No by itself | Approval if live-sensitive |

## 10. Gates And Approvals

Dev gate:

- dev changes may proceed after local scope is clear
- server validation still requires commit/push/pull

Stable gate:

- stable changes require explicit human approval unless the task is docs-only reconciliation
- stable runtime changes require server deployment and validation

Gateway/Home gate:

- production-sensitive
- must not be changed without explicit approval
- Caddy live mount must be inspected before live edits
- Home changes require rebuild when source is baked into the image

Release gate:

- exact baseline commit known
- validation evidence captured
- docs updated
- rollback or disable notes present
- no merge to `main` unless explicitly requested

## 11. Definition Of Done

Local change DoD:

- diff contains only intended files
- selfcheck/tests passed
- `compileall` passed if applicable
- `git diff --check` clean
- docs updated if needed
- final local status understood

Server dev validation DoD:

- commit pushed
- server pulled correct commit
- server branch/status/log checked
- image rebuilt
- service restarted
- readiness passed
- runtime scenario passed

Stable release DoD:

- dev validation passed
- release doc exists
- stable service rebuilt/restarted
- Home/gateway updated only if explicitly approved
- runtime validation passed
- docs reconciled
- final commit hash recorded

## 12. Safety Rules

- Never treat server rebuild as proof that a patch was applied without commit/push/pull.
- Do not change production compose, Caddy, gateway, Home, stable services, or unrelated services without explicit approval.
- Do not force push.
- Do not merge to `main` without explicit approval.
- Do not store secrets in repo or logs.
- Destructive commands require explicit warning, approval, and rollback plan.
- Always check server git branch, status, and log before server validation.
- Always use readiness wait after restart.
- Root-owned data directories must be fixed before first start.
- Do not expose dev tools through Home.
- Keep runtime data, media inputs, outputs, caches, and model artifacts out of Git.

## 13. Documentation Policy

Behavior changes require documentation updates in the same branch.

Documentation should capture:

- what changed
- why it changed
- affected services
- routes and ports
- data directories
- validation commands and results
- rollback or disable notes when runtime is affected
- known limitations and follow-up items

Docs should be concise and operational. Do not paste huge logs. Summarize logs and include exact commands where useful.

## 14. Runtime Validation Policy

Runtime validation is authoritative only when:

1. Code/docs/config are committed.
2. Commit is pushed.
3. Server pulls the commit with `git pull --ff-only`.
4. Server branch/status/log are checked.
5. Image is rebuilt when needed.
6. Service is restarted or recreated.
7. Readiness wait passes.
8. Runtime scenario passes.

If server behavior looks stale, check:

    git status --short --branch
    git log --oneline -3
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'

For Caddy changes, inspect mounts before editing:

    docker inspect myservices-caddy --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'

## 15. Relationship To FIRST_RELEASE_PLAYBOOK

General workflow:

    docs/ENGINEERING_WORKFLOW.md

Specific first-release playbook:

    docs/FIRST_RELEASE_PLAYBOOK.md

`ENGINEERING_WORKFLOW.md` defines the general process and terminology.

`FIRST_RELEASE_PLAYBOOK.md` defines the specific sequence for promoting a validated dev service into its first stable sibling.

No terminology conflicts were found during creation of this document. If future conflicts appear, reconcile them explicitly in a follow-up docs change rather than silently rewriting one document from the other.

## 16. Templates

### Task Brief Template

```text
Title:

Goal:

Affected services:

Constraints:

Allowed files/actions:

Forbidden files/actions:

Acceptance criteria:

Validation required:

Docs required:
```

### Design Note Template

```text
Context:

Current behavior:

Desired behavior:

Proposed design:

Alternatives considered:

Risks:

Rollback or disable expectation:

Acceptance criteria:
```

### Validation Report Template

```text
Service:
Environment:
Commit:
Route:
Container:

Scenario:
Expected result:
Actual result:

Commands run:

Status/log artifacts:

Result:
Known limitations:
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

Validation evidence:

Routes:

Data directories:

Rollback/disable:

Known limitations:
```

### Closeout Summary Template

```text
Summary:

Files changed:

Validation:

Commit:

Push:

Final status:

Known limitations:

Follow-ups:
```

### Codex Task Template

```text
Task:

Work only inside:

Do not:
- modify live runtime unless explicitly requested
- modify unrelated services
- force push
- merge to main

Allowed files:

Goal:

Required changes:

Validation:

Commit/push:

Expected output:
```

## 17. Open Questions / Future Automation

- Should structured workflow artifacts be required under `docs/workflows/` for every nontrivial change?
- Should release docs move from monolithic files into `docs/releases/`?
- Should validation reports move into `docs/validations/`?
- Should a helper script verify server branch, commit, container, and healthz in one command?
- Should compose services define container healthchecks for readiness loops?
- Should Home publication get its own dedicated playbook?
- Should later stable updates get a `STABLE_RELEASE_PLAYBOOK.md` separate from first release?
