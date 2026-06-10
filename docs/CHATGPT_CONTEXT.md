# CHATGPT_CONTEXT

## 1. Purpose

This file is a short bootstrap context for starting a new ChatGPT conversation about the `soma-arch` home services platform.

It is safe to paste into a new chat. It intentionally contains only current project and operational orientation, not secrets, credentials, private keys, sensitive logs, or full runbook procedures.

Volatile facts must be refreshed from the repository and, before any runtime work, from the server. Treat this file as orientation, not as proof of live state.

## 2. Roles

- Human owner: defines goals, approves production-sensitive work, approves stable releases, Gateway/Caddy changes, and Home publication changes.
- ChatGPT coordinator: helps reason about plans, risks, docs, task briefs, and validation evidence.
- Codex/Gavrik implementation agent: edits repo files, runs local validation, commits, pushes, and reports exact results when requested.
- Server/runtime: source of truth for live behavior after the exact commit has been pulled, built, restarted, and validated.

## 3. Stable Platform Constraints

- Work in small, auditable changes.
- Keep dev and stable services separate.
- Home publishes stable user-facing tools only.
- Gateway/Caddy is routing and is production-sensitive.
- Do not change Gateway/Caddy, Home publication, stable services, production compose, or runtime paths without explicit approval.
- Runtime data, generated jobs, media, model caches, secrets, and credentials must stay out of Git.
- Hardware context: Ubuntu Server 24.04, i5-14600KF, 32GB RAM, RTX 3060 12GB, 480GB SSD. Avoid assumptions that exceed this capacity.

## 4. Current Repository State

- Active branch: `feature/ffmpeg-dev-skeleton`
- Server worktree for this branch: `/srv/soma/worktrees/ffmpeg-dev-skeleton`
- Latest known server HEAD: `4ab65a3 chore(cockpit): add safe local developer commands`
- Current phase: Developer Cockpit
- Mac workspace: `/Users/grigorynokhrin/projects/soma-arch`
- Server canonical repo path historically used for stable workflow: `/home/grigorynokhrin/soma-arch`

Refresh these facts with `git status`, `git log`, and server inspection before runtime work.

## 5. Current Documentation State

Documentation foundation completed:

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

Key ownership:

- `docs/PLATFORM_ARCHITECTURE.md` owns platform identity, roots, and high-level ownership boundaries.
- `docs/NAMING_AND_LAYOUT_POLICY.md` owns platform naming and filesystem layout policy.
- `docs/SERVICES_REGISTRY.md` owns service inventory.
- `docs/runbooks/*.md` own operational procedures.
- `docs/services/*.md` own service design and behavior.
- Home is publication.
- Gateway/Caddy is routing.
- Worktrees are temporary Git checkouts for branches or tasks; they are not architecture.
- `docs/reports/live_server_layout_audit.md` records observed live server layout facts.
- Multiple compose ownership models currently coexist on the server.

## 6. Current Services/Topology Summary

- FFmpeg stable: `/ffmpeg/`, container `soma-ffmpeg`, `127.0.0.1:18083 -> 8000`, compose service `ffmpeg`.
- FFmpeg dev: `/ffmpeg-dev/`, container `soma-ffmpeg-dev`, `127.0.0.1:18082 -> 8000`, compose service `ffmpeg-dev`.
- Whisper stable: `/myservices/whisper/`, container `myservices-whisper`, compose service `whisper`, production compose `/home/grigorynokhrin/myservices/compose.yaml`.
- Whisper dev: `/whisper-dev/`, container `soma-whisper-dev`, `127.0.0.1:18080 -> 8000`.
- Home: `/myservices/`, container `myservices-home`, compose service `home`.
- Gateway/Caddy: container `myservices-caddy`, tracked reference `gateway/myservices/Caddyfile.current`, historical live file `/home/grigorynokhrin/myservices/caddy/Caddyfile`.

Live service state, ports, routes, images, networks, and mounts must be refreshed from the server before runtime work.

## 7. Current Engineering Workflow Rules

- Read the relevant registry, runbook, service design doc, and task constraints first.
- Commit and push before server validation.
- Server validation is valid only after the exact commit is pulled on the server, built, restarted, given readiness time, and runtime-tested.
- Validate direct service routes before Gateway/Caddy or Home publication.
- Gateway/Caddy and Home publication changes require explicit approval.
- Documentation changes should accompany behavior changes.
- For docs-only tasks, local `git diff --check`, `git diff --stat`, and `git status --short` are usually sufficient unless the task says otherwise.

## 8. Current Phase

Current phase: Developer Cockpit.

Developer Cockpit v1 is implemented as safe local commands in the root `Makefile`, with VS Code tasks in `.vscode/tasks.json`.

Useful local cockpit commands:

- `make cockpit`
- `make status`
- `make context`
- `make local-validate`
- `make server-commands`

The documentation foundation is in place. The next work should use the canonical docs and cockpit commands instead of creating competing runbooks or copying command blocks by hand.

## 9. Open Follow-Up Items

- Keep structured release notes and validation reports under consideration.
- Add supersession/archive notes for older flat rollout/status docs when cleanup begins.
- Refresh server live state before any runtime, Caddy, Home, or stable-service action.
- Keep Gateway/Caddy route changes separate from service implementation work unless explicitly approved.
- Use the live server layout audit as a factual baseline before discussing cleanup or migration.

## 10. How To Use This File In A New ChatGPT Chat

Paste this file at the start of a new ChatGPT conversation and say what task you want to perform.

Then ask ChatGPT to refresh repo facts from canonical documents before planning work:

- `docs/ENGINEERING_WORKFLOW.md`
- `docs/SERVICES_REGISTRY.md`
- the relevant `docs/runbooks/*.md`
- the relevant `docs/services/*.md`

For runtime work, provide fresh server command output. Do not rely on this file as live-state evidence.

## 11. Maintenance Policy

Update this file only when high-level project context changes:

- current phase
- active branch or server worktree
- canonical documentation set
- service topology summary
- engineering workflow rules
- major safety boundaries

Keep it concise, paste-safe, and free of secrets. Prefer links to canonical docs over copying runbook procedures.
