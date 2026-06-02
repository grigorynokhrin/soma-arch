# Pull Request

## Summary

What changed?

## Why

Why is this change needed?

## Scope

Changed files/directories:

- 

## Legacy / production impact

Does this affect `/home/grigorynokhrin/myservices`?

- [ ] No
- [ ] Yes, explain:

Does this affect `/myservices/whisper`?

- [ ] No
- [ ] Yes, explain:

Does this require stopping, restarting, or recreating legacy containers?

- [ ] No
- [ ] Yes, explain:

## Dev / soma impact

Does this affect `/srv/soma` runtime?

- [ ] No
- [ ] Yes, explain:

Does this add or modify a dev service?

- [ ] No
- [ ] Yes, service name:

## Validation

Commands run:

    <paste commands>

Results:

    <paste results>

## Healthcheck

Was `make health` run on the server?

- [ ] No, reason:
- [ ] Yes

Result:

    <paste result>

## Caddy / routes

Does this change Caddy routes?

- [ ] No
- [ ] Yes

New or changed routes:

    <paste routes>

Legacy route check:

    /myservices/whisper/healthz:

Dev route check:

    <paste result>

## Docs

Docs updated:

- [ ] No docs needed
- [ ] docs updated

Files:

- 

## Rollback

How to roll back this change?

    <rollback steps>

## Risks / known limitations

- 

## Checklist

- [ ] I read `AGENTS.md`
- [ ] I read `docs/PROJECT_PHASE_1_STATUS.md`
- [ ] I did not commit secrets or runtime data
- [ ] I did not commit model caches, audio files, or generated job files
- [ ] I did not change legacy production routes unless explicitly requested
- [ ] I documented runtime commands if required
