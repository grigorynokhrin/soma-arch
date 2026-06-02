# CODEX_TASK_TEMPLATE

Use this template when assigning work to Codex.

## Generic task prompt

    Read AGENTS.md, docs/CODEX_HANDOFF.md, docs/PROJECT_PHASE_1_STATUS.md, docs/TARGET_ARCHITECTURE.md, docs/CURRENT_STATE.md, and docs/DECISIONS.md.

    Task:
    <describe the task>

    Constraints:
    - Do not modify /home/grigorynokhrin/myservices legacy runtime files.
    - Do not replace /myservices/whisper.
    - Do not stop, restart, or recreate legacy containers.
    - Do not expose new services on 0.0.0.0.
    - Bind dev services to 127.0.0.1 first.
    - Do not commit secrets, data, model caches, audio, or generated job files.
    - Keep changes small and reviewable.
    - Update docs if behavior changes.

    Expected output:
    - Summary of changes.
    - Files changed.
    - Commands run.
    - Tests performed.
    - Risks.
    - Rollback plan.
    - Whether server runtime commands are required.

## Task type: new service skeleton

    Create a new dev service skeleton for <service-name>.

    Requirements:
    - Source under services/<service-name>/.
    - Compose file under compose/<service-name>.compose.yml.
    - Runtime data under /srv/soma/data/<service-name>/.
    - Bind only to 127.0.0.1.
    - Add /healthz endpoint.
    - Run as non-root where practical.
    - Add docs/<SERVICE_NAME>_BOOTSTRAP.md.
    - Add validation commands.
    - Do not modify legacy production routes.

## Task type: portal UI

    Implement initial soma-portal-ui skeleton.

    Requirements:
    - Source under services/portal-ui/.
    - Compose file under compose/portal-ui.compose.yml.
    - FastAPI or similarly simple web framework is acceptable.
    - Add /healthz.
    - Add /services page.
    - Link to /whisper-dev.
    - Bind only to 127.0.0.1.
    - Add docs/PORTAL_UI_BOOTSTRAP.md.
    - Do not modify legacy routes.

## Task type: healthcheck extension

    Update runtime healthcheck template.

    Requirements:
    - Modify runtime/scripts/healthcheck.sh.
    - Dev services must be optional warnings unless explicitly promoted.
    - Legacy checks must remain hard checks.
    - Update docs/RUNTIME_HEALTHCHECK.md.
    - Provide exact command to copy template to /srv/soma/scripts/healthcheck.sh.
    - Provide test command: cd /srv/soma && make health.

## Task type: Caddy dev route

    Prepare a Caddy dev route for <service-name>.

    Requirements:
    - Do not replace existing legacy routes.
    - Add only a dev route.
    - Validate Caddy config before reload.
    - Prefer reload over restart.
    - Document network assumptions.
    - Update gateway reference files.
    - Add docs/<SERVICE_NAME>_CADDY_ROUTE.md.
    - Include rollback instructions.

## Task type: refactor existing service

    Refactor <service-name>.

    Requirements:
    - Preserve public API unless explicitly asked.
    - Keep changes small.
    - Add tests or smoke-test commands.
    - Update docs if behavior changes.
    - Do not touch unrelated services.

## Runtime validation checklist

For repo-only changes:

    git status --short --branch

For compose changes:

    docker compose -f compose/<service>.compose.yml config

For server runtime changes:

    cd /srv/soma
    make health

For Caddy dev route:

    curl -fsS http://127.0.0.1/<route>/healthz
    curl -fsS http://127.0.0.1/myservices/whisper/healthz

## Done checklist

A Codex task is not done until it reports:

    [ ] What changed
    [ ] Why it changed
    [ ] Files changed
    [ ] Tests/commands run
    [ ] Docs updated
    [ ] Legacy impact
    [ ] Runtime commands required
    [ ] Rollback plan
    [ ] Known limitations
