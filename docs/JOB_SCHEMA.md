# JOB_SCHEMA

This document defines the Phase 2 shared job schema and job-store convention for soma services.

The goal is to give Whisper, OCR, SupIR, the future portal UI, and later services a common filesystem contract without changing current runtime behavior.

## Scope

This is a documentation-only convention.

It does not modify:

- runtime code
- Docker Compose files
- legacy `/home/grigorynokhrin/myservices`
- `/myservices/whisper`
- Caddy configuration

Phase 2 services should adopt this convention first in the dev contour under `/srv/soma`.

## Shared Job Directory Layout

Runtime service data should live outside Git:

    /srv/soma/data/<service-name>/

Each job-producing service should keep jobs under:

    /srv/soma/data/<service-name>/jobs/<job-id>/

Recommended service layout:

    /srv/soma/data/<service-name>/
      jobs/
        <job-id>/
          status.json
          job.json
          job.log
          artifacts/
          tmp/
      cache/

Current `soma-whisper-dev` compatibility note:

- current Whisper job directories already live under `/srv/soma/data/whisper-dev/jobs/<job-id>/`
- current Whisper artifacts may live directly in the job directory
- current Whisper may use service-specific files such as `intermediate.jsonl`, `audio_16k.wav`, and `chunk_001.wav`
- Phase 2 consumers should support this existing shape while new services move toward the `artifacts/` and `tmp/` subdirectories

Directory rules:

- `jobs/<job-id>/status.json` is the primary machine-readable status file.
- `jobs/<job-id>/job.json` may store the original request, normalized inputs, and service-specific parameters.
- `jobs/<job-id>/job.log` may store human-readable lifecycle logs.
- `jobs/<job-id>/artifacts/` should contain user-facing outputs.
- `jobs/<job-id>/tmp/` should contain intermediate files that may be deleted after completion unless explicitly retained.
- Model caches, OCR language data caches, and large reusable assets should not live inside a job directory.

## Job ID Rules

Job IDs should be:

- unique within a service
- URL-safe
- filesystem-safe
- short enough for readable artifact names
- opaque to callers

Recommended pattern:

    [a-z0-9]{12,32}

Existing `soma-whisper-dev` job IDs such as `3c52d24a91d6` are compatible.

## status.json Fields

`status.json` should be valid UTF-8 JSON.

Required fields:

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | Job schema version, starting with `1`. |
| `service` | string | Service name, such as `whisper-dev`, `tesseract-dev`, or `supir-dev`. |
| `job_id` | string | Job ID and directory name. |
| `status` | string | Stable lifecycle state. |
| `stage` | string | More detailed current processing stage. |
| `created_at` | string | Local or UTC ISO-8601 timestamp when the job was created. |
| `updated_at` | string | ISO-8601 timestamp for the last status update. |
| `artifacts` | array | User-facing output artifacts. Empty until outputs exist. |

Recommended fields:

| Field | Type | Description |
| --- | --- | --- |
| `started_at` | string or null | Timestamp when processing began. |
| `finished_at` | string or null | Timestamp when terminal processing ended. |
| `error` | object or null | Error details for failed jobs. |
| `input` | object | Sanitized input metadata. |
| `params` | object | Service-specific request parameters safe to expose. |
