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
| `metrics` | object | Duration, page count, chunk count, device, model, or other useful metrics. |
| `warnings` | array | Non-fatal warnings. |
| `links` | object | Relative URLs useful to the portal UI. |

Artifact objects should use:

| Field | Type | Description |
| --- | --- | --- |
| `name` | string | Human-readable artifact label. |
| `path` | string | Path relative to the job directory. |
| `kind` | string | Artifact kind, such as `txt`, `srt`, `pdf`, `json`, `image`, or `zip`. |
| `mime_type` | string | MIME type when known. |
| `size_bytes` | number or null | File size when known. |

Error objects should use:

| Field | Type | Description |
| --- | --- | --- |
| `code` | string | Stable service-specific error code. |
| `message` | string | Human-readable summary. |
| `detail` | string or null | Optional detail safe for local dev display. |

Example:

```json
{
  "schema_version": "1",
  "service": "whisper-dev",
  "job_id": "3c52d24a91d6",
  "status": "done",
  "stage": "done",
  "created_at": "2026-06-02T12:03:25",
  "started_at": "2026-06-02T12:03:25",
  "updated_at": "2026-06-02T12:03:29",
  "finished_at": "2026-06-02T12:03:29",
  "input": {
    "filename": "soma-test.wav"
  },
  "params": {
    "model_name": "tiny",
    "compute_type": "int8"
  },
  "metrics": {
    "chunks": 1,
    "device": "cuda"
  },
  "artifacts": [
    {
      "name": "Transcript text",
      "path": "3c52d24a91d6-soma-test.txt",
      "kind": "txt",
      "mime_type": "text/plain",
      "size_bytes": null
    },
    {
      "name": "Subtitles",
      "path": "3c52d24a91d6-soma-test.srt",
      "kind": "srt",
      "mime_type": "application/x-subrip",
      "size_bytes": null
    }
  ],
  "warnings": [],
  "error": null
}
```

## Artifact Naming Conventions

Artifacts should be named predictably and should avoid spaces.

Recommended pattern:

    <job-id>-<safe-input-stem>.<extension>

Examples:

    3c52d24a91d6-soma-test.txt
    3c52d24a91d6-soma-test.srt
    38153917dac3-soma-retention-1.srt

For multi-file outputs, include a short role:

    <job-id>-<safe-input-stem>-ocr.txt
    <job-id>-<safe-input-stem>-layout.json
    <job-id>-<safe-input-stem>-page-001.png
    <job-id>-<safe-input-stem>-supir.png

Naming rules:

- use lowercase where practical
- use hyphens instead of spaces
- preserve meaningful file extensions
- include the job ID in user-facing artifact names
- avoid secrets, private paths, and raw user-provided names that have not been sanitized

Intermediate files should use simple service-specific names and should not be listed as user-facing artifacts unless they are intentionally exposed.

## Lifecycle States

`status` should be one of:

| State | Meaning | Terminal |
| --- | --- | --- |
| `queued` | Job accepted but not started. | no |
| `running` | Job is actively processing. | no |
| `done` | Job completed successfully. | yes |
| `failed` | Job ended with an error. | yes |
| `canceled` | Job was canceled by user or service policy. | yes |

`stage` may be service-specific and more detailed.

Examples:

- `created`
- `uploaded`
- `probing`
- `converting`
- `chunking`
- `transcribing`
- `ocr`
- `upscaling`
- `assembling`
- `cleanup`
- `done`
- `failed`

Portal UI and shared history code should depend on `status` for stable behavior and display `stage` as optional detail.

## Ownership And Runtime Rules

Services should run as non-root where practical.

Current preferred host identity:

    APP_UID=1000
    APP_GID=990

Generated runtime files should remain readable and manageable by:

    grigorynokhrin:docker

Rules:

- runtime data lives under `/srv/soma/data/<service-name>/`
- generated jobs, artifacts, logs, and temporary files must not be committed to Git
- services should use environment-driven paths
- dev services should bind to localhost unless explicitly promoted
- job data should not be written into legacy `/home/grigorynokhrin/myservices`
- caches should be service-scoped and outside individual jobs
- large model caches and datasets should respect the 480GB SSD limit

## Retention Expectations

Every job-producing service should define a retention policy before it is treated as a stable dev service.

Recommended default:

    <SERVICE>_RETENTION_MAX_JOBS=5

Retention should apply to terminal jobs:

- `done`
- `failed`
- `canceled`

Retention rules:

- keep the newest terminal jobs first
- do not delete active `queued` or `running` jobs
- preserve ownership rules after cleanup
- keep cache retention separate from job retention
- document whether retention is count-based, age-based, or both

Current `soma-whisper-dev` compatibility note:

- `WHISPER_RETENTION_MAX_JOBS=5` has been validated
- only the newest 5 terminal jobs remain
- generated files remain owned by `grigorynokhrin:docker`
- dev and legacy health remained OK after retention cleanup

## Compatibility With soma-whisper-dev

The current `soma-whisper-dev` runtime is already compatible with the core convention:

- jobs live under `/srv/soma/data/whisper-dev/jobs/<job-id>/`
- each job exposes status through `/whisper-dev/jobs/<job-id>/status.json`
- terminal state `done` is already used
- stage `done` is already used
- artifacts include TXT and SRT files
- job logs and intermediate files are retained per job
- generated files are owned by `grigorynokhrin:docker`
- retention has been validated with `WHISPER_RETENTION_MAX_JOBS=5`

Existing Whisper-specific files should remain valid:

    soma-test.wav
    audio_16k.wav
    chunk_001.wav
    intermediate.jsonl
    job.json
    job.log
    <job-id>-<safe-input-stem>.txt
    <job-id>-<safe-input-stem>.srt

Portal UI and shared job readers should therefore support two artifact locations:

1. artifacts listed in `status.json`
2. current Whisper artifacts found directly in the job directory

This allows Phase 2 to add shared consumers without breaking the validated Phase 1 Whisper service.

## Future Services

### OCR / Tesseract

Recommended service name:

    tesseract-dev

Recommended data root:

    /srv/soma/data/tesseract-dev

Likely artifacts:

- extracted text: `<job-id>-<safe-input-stem>-ocr.txt`
- searchable PDF: `<job-id>-<safe-input-stem>-ocr.pdf`
- page metadata: `<job-id>-<safe-input-stem>-pages.json`
- optional page images: `<job-id>-<safe-input-stem>-page-001.png`

Useful metrics:

- page count
- OCR language
- duration
- input MIME type

### SupIR

Recommended service name:

    supir-dev

Recommended data root:

    /srv/soma/data/supir-dev

Likely artifacts:

- enhanced image: `<job-id>-<safe-input-stem>-supir.png`
- comparison image: `<job-id>-<safe-input-stem>-compare.jpg`
- generation metadata: `<job-id>-<safe-input-stem>-metadata.json`

Useful metrics:

- input dimensions
- output dimensions
- model or preset
- device
- duration
- VRAM-sensitive settings

SupIR work must respect the RTX 3060 12GB VRAM boundary. Prefer small models, conservative tiling, lower batch sizes, and documented fallback behavior.

### Portal UI

The portal UI should treat the filesystem job store as a read-only source at first.

Initial portal behavior:

- list known services
- list recent jobs per service
- read `status.json`
- display stable `status`
- display service-specific `stage`
- link user-facing artifacts
- tolerate missing optional fields
- tolerate current Whisper artifacts in the job directory

Recommended portal routes:

    /services
    /whisper
    /whisper/history
    /tesseract
    /tesseract/history
    /supir
    /supir/history

The portal should not delete jobs, rewrite status files, or manage retention until that behavior is explicitly designed and reviewed.

## Versioning

This document defines schema version:

    1

Future incompatible changes should either:

- increment `schema_version`
- document a compatibility reader
- preserve support for existing `soma-whisper-dev` job records until a migration is approved

## Validation For This Document

This document is documentation-only.

Expected PR validation:

    git diff -- docs/JOB_SCHEMA.md
    git status --short

Expected result:

- only `docs/JOB_SCHEMA.md` is added
- no runtime code changes
- no compose changes
- no Caddy changes
- no legacy `/home/grigorynokhrin/myservices` changes
