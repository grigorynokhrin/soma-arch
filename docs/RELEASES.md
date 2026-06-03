# RELEASES

This document records controlled releases for the `soma` home-server architecture.

## whisper-prod-2026.06.03

Status:

    completed

Date:

    2026-06-03

Service:

    myservices-whisper

Route:

    /myservices/whisper

## Summary

This release promoted the tested `soma-whisper-dev` code path into the legacy/prod Whisper container while preserving the existing production route and Caddy contract.

Production Whisper is now built from:

    /home/grigorynokhrin/soma-arch/services/whisper-dev

Production Compose remains:

    /home/grigorynokhrin/myservices/compose.yaml

Caddy was not changed. The production route remains:

    handle /myservices/whisper* {
        reverse_proxy whisper:8000
    }

Service/container/network names remain:

    service: whisper
    container: myservices-whisper
    network: myservices_default

## Included Commits

Important repo commits included in this release:

    72cf3fb Update whisper dev chunk defaults
    c04becc Parameterize whisper dev UI routes
    8e7b3e6 Make whisper dev URLs path-based

## Production Changes

### Default UX

Whisper defaults changed:

    chunk_min default: 5
    overlap_sec default: 0

The web UI hints were updated to match:

    recommended chunk length: 5 minutes
    recommended overlap: 0 seconds

### Route Handling

Templates no longer hardcode:

    /myservices/whisper

The runtime root is driven by:

    WHISPER_ROOT_PATH

Current route values:

    dev:  /whisper-dev
    prod: /myservices/whisper

Internal app navigation is path-based:

    form action: {{ root_path }}/submit
    redirects:   <root_path>/jobs/<job-id>

Generated HTML should not contain internal absolute URLs such as:

    http://127.0.0.1:18081/...

### Production Environment

Production container environment:

    WHISPER_ROOT_PATH=/myservices/whisper
    WHISPER_OUTPUT_DIR=/app/outputs
    WHISPER_JOBS_DIR=/app/data/jobs
    WHISPER_CONTEXTS_PATH=/app/contexts.json
    WHISPER_RETENTION_MAX_JOBS=20
    HF_HOME=/app/hf_cache
    HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub

### Runtime Volumes

Production bind mounts:

    /home/grigorynokhrin/myservices/whisper/outputs -> /app/outputs
    /home/grigorynokhrin/myservices/whisper/data -> /app/data
    /home/grigorynokhrin/myservices/whisper/hf_cache -> /app/hf_cache

### Permissions

The released image runs as:

    appuser uid=1000 gid=990

Writable production directories were migrated to:

    grigorynokhrin:docker

Group write was enabled where needed. A write test as `uid=1000 gid=990` passed before replacing production.

## Backups And Rollback References

Backups created during release:

    /home/grigorynokhrin/myservices/backups/whisper-permissions-20260603-093428
    /home/grigorynokhrin/myservices/backups/whisper-promote-20260603-093625
    /home/grigorynokhrin/myservices/backups/whisper-release-20260603-093727

Rollback image tag:

    myservices-whisper:rollback-20260603-093727

Rollback must be treated as an explicit operator action. Do not run rollback commands casually.

Rollback reference:

    cd /home/grigorynokhrin/myservices
    docker compose stop whisper
    docker tag myservices-whisper:rollback-20260603-093727 myservices-whisper
    docker compose up -d whisper
    curl -fsS http://127.0.0.1/myservices/whisper/healthz

If permissions caused the problem, restore from the permission backup before restarting the service.

## Validation Evidence

Pre-release production health:

    curl -fsS http://127.0.0.1/myservices/whisper/healthz
    ok

Post-release production health:

    curl -fsS http://127.0.0.1/myservices/whisper/healthz
    ok

Runtime healthcheck:

    cd /srv/soma
    make health

Observed result:

    [OK] healthcheck completed without hard failures

Production index check:

    form action="/myservices/whisper/submit"
    chunk_min value="5"
    overlap output "0 сек"

Production smoke-test through Caddy:

    POST /myservices/whisper/submit -> 303
    Location: /myservices/whisper/jobs/fcaff3d603ea

Final job status:

    job_id: fcaff3d603ea
    status: done
    progress: 1/1

Generated artifacts:

    fcaff3d603ea-prod-smoke.txt
    fcaff3d603ea-prod-smoke.srt

Artifact links used:

    /myservices/whisper/jobs/.../artifacts/...

Dev route remained healthy:

    /whisper-dev

## Notes

This release did not:

- change Caddy
- add batch upload
- replace the `/myservices/whisper` route
- move production data into Git
- change the Docker network contract
