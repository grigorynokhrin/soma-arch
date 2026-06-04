# Whisper Service Design

This is the canonical service design document for the stable Whisper service.

It describes what Whisper is, why it exists, how transcription workflows are structured, what design decisions shape the implementation, and how the service fits into the rest of the platform. It is not an operations runbook. Operational procedures live in `docs/runbooks/whisper.md`.

## Purpose

Whisper is the stable user-facing speech-to-text service in the Home/MyServices environment.

It exists to let trusted local users upload audio or video files and receive transcription artifacts without manually running FFmpeg, managing model caches, chunking audio, or assembling text/subtitle files. It supports routine transcription workflows for recorded audio, video with embedded audio, and multi-file batches.

Within the home platform, Whisper owns the transcription step:

- Home publishes the stable entry point.
- Gateway/Caddy routes the stable prefix.
- Whisper accepts uploads, prepares audio, runs the transcription model, writes artifacts, and exposes job status.
- FFmpeg can prepare or convert media before transcription, but broader media conversion belongs to the FFmpeg service.

## Scope

The service does:

- audio and video upload for transcription
- speech-to-text processing
- single-file transcription
- batch upload v1 with sequential file processing
- audio normalization to 16 kHz mono WAV before transcription
- chunked transcription with configurable chunk length and overlap
- optional VAD filtering
- optional short transcription context
- TXT generation
- SRT generation for single-file jobs
- combined TXT generation for batch jobs
- job-based status and artifact access
- filesystem retention by newest terminal jobs

The service does not do:

- video conversion as a user-facing workflow
- media remuxing
- media library management
- workflow orchestration across services
- document OCR
- combined SRT generation for batch v1
- arbitrary model/runtime command execution from the UI
- long-term archival of generated media and transcripts

## Users And Use Cases

Intended users are the home-server owner and trusted local users using Home/MyServices.

Typical supported workflows:

- Transcribe one audio file and download TXT/SRT artifacts.
- Transcribe one video file by extracting and normalizing its audio internally.
- Submit multiple files in one batch job and receive one combined TXT artifact.
- Use short context text or a context preset to guide transcription terminology.
- Use chunk settings to process longer media.
- Inspect status and logs when transcription takes longer than expected or fails.

Supported downstream relationship:

- FFmpeg may be used before Whisper to prepare media, but Whisper itself handles the audio extraction/normalization needed for transcription.

TODO:

- Document any stable note-generation or downstream document-processing workflow only after it is implemented or validated.

## Service Topology

Stable service:

| Field | Value |
| --- | --- |
| Route | `/myservices/whisper/` |
| Container | `myservices-whisper` |
| Compose service | `whisper` |
| Compose file | `/home/grigorynokhrin/myservices/compose.yaml` |
| Docker network | `myservices_default` |
| Upstream port | `8000` |
| Home publication | Published as a stable Home/MyServices tool |
| Source path used for current releases | `/home/grigorynokhrin/soma-arch/services/whisper-dev` |

Dev service:

| Field | Value |
| --- | --- |
| Route | `/whisper-dev/` |
| Container | `soma-whisper-dev` |
| Image | `soma-whisper-dev:local` |
| Direct bind | `127.0.0.1:18080 -> 8000` |
| Compose file | `compose/whisper-dev.compose.yml` |
| Compose service | `whisper-dev` |
| Runtime data | `/srv/soma/data/whisper-dev` |
| Home publication | Not published as a stable Home tool |

Home relationship:

- Home route is `/myservices/`.
- Home publishes stable tools only.
- Whisper and FFmpeg are stable Home entries.
- Dev routes must not replace stable Home entries.

Gateway/Caddy relationship:

- Caddy routes `/myservices/whisper*` to `whisper:8000`.
- The tracked reference is `gateway/myservices/Caddyfile.current`.
- The live Caddyfile is documented under `/home/grigorynokhrin/myservices/caddy/Caddyfile`.
- Live Caddy may differ from the tracked reference.

Operational commands for deploy, restart, readiness, and rollback belong in `docs/runbooks/whisper.md`.

## Architecture Overview

Major components:

| Component | Evidence | Responsibility | Inputs | Outputs | Constraints |
| --- | --- | --- | --- | --- | --- |
| Web/UI layer | `services/whisper-dev/app.py`, templates | Render upload form, status page, result page, artifact links | HTTP requests, form fields, upload files | HTML, redirects, text artifacts, JSON status | Root-path driven by `WHISPER_ROOT_PATH`. |
| Upload layer | `submit` route | Accept one or more uploaded files and place them in a job directory | uploaded audio/video files | source files under job storage | Uses safe basename via `Path(filename).name`; no long-term archive guarantee. |
| Job manager | `create_job`, `update_job`, `run_transcription_job` | Create and update job metadata and lifecycle state | selected options, uploaded files | `job.json`, progress fields, status/stage | Filesystem JSON, not a database. |
| Audio preparation layer | `ffprobe_duration`, `transcode_to_pcm16_mono_16k`, `split_wav_with_overlap` | Probe duration, normalize audio, create chunks | source media | `audio_16k.wav`, `chunk_*.wav` | Depends on FFmpeg/FFprobe. |
| Transcription engine | `load_model_cached`, `model.transcribe` | Load faster-whisper model and transcribe chunks | WAV chunks, language, context, beam, VAD options | text segments, SRT timing entries, detected language metadata | Device is `auto`; runtime evidence must confirm actual device. |
| Artifact generator | `segments_to_txt_and_srt`, `merge_srt`, batch assembly | Build user-facing TXT/SRT outputs | chunk transcription results | final TXT, final SRT, batch TXT | Batch v1 does not generate combined SRT. |
| Diagnostics layer | `append_job_log`, `job.json`, status route | Preserve state and execution trace | job lifecycle events | `job.log`, `job.json`, status endpoint | Logs can include filenames and stage details. |
| Retention manager | `cleanup_old_jobs` | Keep only newest terminal jobs | job directories and metadata | deleted old terminal jobs | Does not delete running jobs; max count is environment-driven. |

## Data Flow

Single-file flow:

1. User opens Whisper through Home/MyServices.
2. User uploads one audio or video file and selects transcription options.
3. Service creates a job directory under the configured jobs directory.
4. Source file is copied into the job directory.
5. Background task starts the transcription job.
6. Service probes media duration with FFprobe.
7. Service converts the source to 16 kHz mono PCM WAV with FFmpeg.
8. Service splits the normalized WAV into chunks using chunk length and overlap settings.
9. faster-whisper model is loaded or reused from the in-process model cache.
10. Each chunk is transcribed.
11. Chunk text and `intermediate.jsonl` records are written.
12. Final TXT and SRT artifacts are assembled.
13. `job.json` and `job.log` are updated through the lifecycle.
14. Job reaches `done`, and artifacts become available through the job pages.
15. Retention cleanup runs after terminal state.

Batch flow:

1. User uploads multiple files in one submit.
2. Service creates one batch job.
3. Uploaded files are stored under an `inputs/` subdirectory with indexed filenames.
4. Files are processed sequentially.
5. Each input file gets its own processing directory.
6. Each input is probed, normalized, chunked, and transcribed.
7. Per-file status is recorded in `input_files`.
8. Text sections are assembled into one combined batch TXT.
9. No combined batch SRT is produced in v1.
10. Retention cleanup runs after terminal state.

## Job Model

Jobs are filesystem-backed directories under `WHISPER_JOBS_DIR`.

Each job has:

- a 12-character hex job ID
- `job.json`
- `job.log`
- uploaded source file(s)
- normalized audio
- chunk audio files
- chunk text files
- intermediate per-chunk JSONL
- final artifact files

Core job fields include:

- `job_id`
- `filename`
- `is_batch`
- `files_count`
- `input_files`
- `status`
- `stage`
- `progress_current`
- `progress_total`
- `started_at`
- `finished_at`
- `error`
- `language`
- `model_name`
- `compute_type`
- `used_compute`
- `chunk_min`
- `overlap_sec`
- `beam`
- `vad`
- `keep_tmp`
- `duration_min`
- `chunks_count`
- `result_text`
- `txt_file`
- `srt_file`

Observed lifecycle states:

- `queued`
- `running`
- `done`
- `error`
- `deleted` as a terminal status considered by retention

Observed stages include:

- `uploaded`
- `converting`
- `chunking`
- `transcribing`
- `assembling`
- `done`
- `error`
- batch-specific stages such as `processing file N/M`

Failure behavior:

- If the job fails, status becomes `error`, stage becomes `error`, and `error` is recorded in `job.json`.
- File-level batch failure marks the input file as `error` before raising job failure.
- Retention still runs after terminal error.

Warning behavior:

- The implementation primarily models success and error states.
- TODO: Define explicit non-fatal warning fields if future Whisper behavior needs warnings separate from errors.

## Model Design

Verified facts:

- Backend uses `faster-whisper`.
- Model construction uses `WhisperModel`.
- Device selection is `device="auto"`.
- Compute fallback order is requested compute type, then `int8`, then `float32`.
- Model cache key is `(model_name, requested_compute)`.
- The model cache is in process memory.
- CPU threads are set to half of available CPUs, with a minimum of 2.
- `num_workers=1`.
- Actual compute and device are logged when model loading succeeds.
- Failed model load attempts are logged.
- Dev validation confirmed `tiny` with requested `int8`, used `int8`, and device `cuda`.

Documented UI/runtime defaults:

- model: `medium`
- compute: `float32`
- chunk length: 5 minutes
- overlap: 0 seconds
- beam: 1
- language default in source: `ru`
- language options: `auto`, `ru`, `en`
- VAD optional

Documented normal UI model choices:

- `medium`
- `small`

The UI text documents that `large-v3` was removed from normal mode as too expensive.

TODO:

- Document production GPU behavior for each normal model/compute option after measured validation.
- Document whether production compose explicitly grants GPU access.
- Document practical model cache memory behavior under repeated jobs.

## Retention And Storage Design

Retention is environment-driven:

- stable production: `WHISPER_RETENTION_MAX_JOBS=20`
- dev: `WHISPER_RETENTION_MAX_JOBS=5`

Retention behavior:

- runs after successful job completion
- runs after job error
- sorts job directories by `finished_at`, then `started_at`, then directory mtime fallback
- keeps the newest N job directories
- deletes only terminal jobs with status `done`, `error`, or `deleted`
- does not intentionally delete running jobs

Stable production data lives outside Git:

- `/home/grigorynokhrin/myservices/whisper/outputs`
- `/home/grigorynokhrin/myservices/whisper/data`
- `/home/grigorynokhrin/myservices/whisper/hf_cache`

Dev data lives outside Git:

- `/srv/soma/data/whisper-dev/jobs`
- `/srv/soma/data/whisper-dev/outputs`
- `/srv/soma/data/whisper-dev/hf_cache`

Design intent:

- generated audio, chunks, transcripts, model cache, and job metadata are runtime data
- runtime data must not be committed to Git
- generated files should be writable by runtime user `uid=1000`, `gid=990`
- host ownership should be `grigorynokhrin:docker`

## Diagnostics Design

`job.json`:

- primary structured job state
- used by status pages and status endpoint
- records job options, progress, artifacts, errors, timestamps, and batch input state

`job.log`:

- append-only lifecycle log for the job
- records source upload, probing, conversion, chunking, model loading, chunk transcription, assembly, completion, and errors

`intermediate.jsonl`:

- records per-chunk details
- includes filename, chunk name, time offset, detected language, text, and elapsed seconds

Container logs:

- record model load success/failure lines
- include actual compute and actual device where available

Status endpoint:

- returns the job JSON for `/jobs/<job-id>/status.json`

Artifact endpoint:

- returns job artifacts from `/jobs/<job-id>/artifacts/<filename>`

Diagnostics exist because transcription runtime can fail at several distinct layers: upload, FFprobe, FFmpeg conversion, chunking, model loading, model inference, artifact assembly, or retention cleanup.

## Error And Warning Semantics

Fatal failure:

- no uploaded file
- invalid overlap/chunk relationship
- FFprobe or FFmpeg failure
- no chunks produced after splitting
- model load failure after compute fallback attempts
- transcription failure
- artifact assembly failure

Observed failure state:

- `status: error`
- `stage: error`
- `error` field contains message
- `job.log` records the error

Upload validation:

- no file selected is rejected before creating a useful transcription job
- overlap must be non-negative
- overlap must be smaller than chunk length

Retention/cleanup edge cases:

- retention catches deletion errors and logs `[WHISPER_RETENTION_FAIL]`
- retention skips non-terminal jobs

Non-fatal warnings:

- TODO: no stable warning field is documented for Whisper jobs. Future warning semantics should be added deliberately if partial-success behavior appears.

## Configuration

Stable production configuration documented in release notes:

```text
WHISPER_ROOT_PATH=/myservices/whisper
WHISPER_OUTPUT_DIR=/app/outputs
WHISPER_JOBS_DIR=/app/data/jobs
WHISPER_CONTEXTS_PATH=/app/contexts.json
WHISPER_RETENTION_MAX_JOBS=20
HF_HOME=/app/hf_cache
HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
```

Stable runtime:

- compose file: `/home/grigorynokhrin/myservices/compose.yaml`
- service: `whisper`
- container: `myservices-whisper`
- network: `myservices_default`
- route: `/myservices/whisper/`
- upstream port: `8000`

Dev compose configuration:

```text
WHISPER_ROOT_PATH=/whisper-dev
WHISPER_OUTPUT_DIR=/app/outputs
WHISPER_JOBS_DIR=/app/data/jobs
WHISPER_CONTEXTS_PATH=/app/contexts.json
WHISPER_RETENTION_MAX_JOBS=5
HF_HOME=/app/hf_cache
HUGGINGFACE_HUB_CACHE=/app/hf_cache/hub
```

Dev compose also documents:

- container `soma-whisper-dev`
- image `soma-whisper-dev:local`
- build context `../services/whisper-dev`
- direct bind `127.0.0.1:18080:8000`
- `gpus: all`
- restart policy `unless-stopped`

Other configuration:

- `WHISPER_MAX_CONTEXT_CHARS`, default `1200`
- Dockerfile runtime user from build args `APP_UID=1000`, `APP_GID=990`

TODO:

- Capture exact production compose GPU settings from the live compose file during an approved runtime inspection.
- Capture exact stable direct host port if any.

## Integration Points

Home/MyServices:

- publishes the stable Whisper entry
- must not publish dev services as stable tools
- tracked Home source is not present in this repo

Gateway/Caddy:

- routes `/myservices/whisper*` to `whisper:8000`
- `/whisper-dev*` routes to `soma-whisper-dev:8000`
- route changes are production-sensitive

Docker Compose:

- stable production compose is outside this repo under `/home/grigorynokhrin/myservices/compose.yaml`
- dev compose is tracked under `compose/whisper-dev.compose.yml`

FFmpeg:

- internal dependency for duration probing, audio normalization, and chunk creation
- user-facing FFmpeg conversion/remux workflows belong to the FFmpeg service

Future platform services:

- OCR/document services and broader workflow orchestration are future platform concerns, not current Whisper responsibilities.

## Constraints

Target hardware:

- Ubuntu Server 24.04
- Intel Core i5-14600KF
- 32GB DDR4
- NVIDIA RTX 3060 12GB VRAM
- SSD 480GB

Implications for Whisper:

- Transcription can be GPU-sensitive, but actual device usage must be verified from logs.
- 12GB VRAM is a practical limit.
- Do not parallelize heavy production, dev, and candidate transcription tests.
- SSD space matters because uploaded media, normalized WAV files, chunk files, transcripts, and model caches can grow.
- Model/cache downloads and generated artifacts must remain outside Git.
- Service isolation matters because Whisper, FFmpeg, Home, and Gateway have different runtime risks.

## Security And Safety Considerations

Uploaded media:

- uploaded files are copied into job directories under runtime storage
- filename handling uses basenames to avoid direct path traversal from submitted filenames
- generated artifacts may include private audio-derived text and should remain outside Git

Routes:

- stable route is behind the Home/MyServices and Caddy setup
- dev route is separate and must not replace stable Home publication

Permissions:

- runtime container user is documented as `uid=1000`, `gid=990`
- host writable directories should be `grigorynokhrin:docker`
- root-owned generated files previously caused cleanup/permission problems

Logging:

- job logs and JSON metadata can contain filenames, transcript snippets, context text, and errors
- no secrets should be placed in context text, filenames, logs, or committed docs

Operational safety:

- Caddy and Home changes require explicit approval
- production compose is outside this repo and must not be modified casually
- rollback is an explicit operator action only

## Operational Boundaries

This document does not own operational procedures.

Use `docs/runbooks/whisper.md` for:

- deployment and restart
- readiness checks
- runtime validation
- diagnostics inspection
- known failure modes
- rollback and disable notes
- production safety rules

This design document owns:

- service purpose and scope
- architecture overview
- data flow
- job model
- model/storage/diagnostics design
- design decisions
- future evolution

## Design Decisions

| Decision | Rationale | Consequences |
| --- | --- | --- |
| Keep stable Whisper under `/myservices/whisper/` during transition. | The existing route is a working production contract. | Source can evolve while route and Caddy contract remain stable. |
| Use separate stable and dev services. | Experiments should not happen directly on a working service. | Dev and stable require separate route/data/compose awareness. |
| Keep production compose in legacy runtime for now. | Production ownership remains with the working MyServices contour. | Repo tracks source and docs, but production compose content is not fully visible here. |
| Use environment-driven root paths and storage paths. | Same source can render correctly for dev and production routes. | Route-sensitive changes require prod-root validation. |
| Use job-based filesystem storage. | JSON and files are easy to inspect and back up on a single server. | Retention and cleanup are necessary to control disk use. |
| Process batch uploads sequentially in one job. | Batch v1 stays simple and avoids parallel GPU/VRAM pressure. | One combined TXT is produced; no combined SRT in v1. |
| Normalize audio with FFmpeg before transcription. | faster-whisper receives consistent 16 kHz mono WAV chunks. | FFmpeg/FFprobe are required runtime dependencies. |
| Cache loaded models in process memory. | Repeated jobs can avoid reloading the same model/compute pair. | Process restart clears the cache; GPU/CPU memory use must be monitored. |
| Use compute fallback. | A requested compute type may fail in a given runtime. | Actual compute must be recorded and checked, not assumed. |
| Use retention-limited job storage. | Media and transcript artifacts can consume disk quickly. | Old terminal jobs may disappear after retention threshold. |
| Treat diagnostics as first-class artifacts. | Runtime failures need stage-level evidence. | `job.json`, `job.log`, and `intermediate.jsonl` should be preserved until retention removes the job. |

## Known Gaps

- Exact stable direct host port is not documented.
- Exact production compose contents are not tracked in this repo.
- Exact production GPU compose configuration is not documented.
- Exact production image tag/current build ID should be captured in future release notes.
- Exact production server checkout/worktree path for routine deployment should be documented.
- Stable readiness loop should be formalized in the runbook.
- Stable `docker logs` command and expected log excerpts should be documented in the runbook.
- Maximum practical file size/duration is not documented.
- Production model cache sizing expectations are not documented.
- Stable disable strategy is not documented.
- Structured Whisper release notes under `docs/releases/` are missing.
- Structured Whisper validation reports under `docs/validations/` are missing.
- Explicit non-fatal warning semantics are not currently modeled for Whisper jobs.
- Future service ADRs do not yet exist for model/runtime policy decisions.

## Future Evolution

Likely future improvements:

- structured validation reports for single-file, batch, long-file, and error scenarios
- clearer model/runtime capability matrix
- better measured GPU/VRAM guidance for normal production settings
- richer retention controls such as max age or max total size
- clearer warning semantics for partial-success cases
- tighter optional integration with FFmpeg preparation workflows
- Makefile or scripted validation support
- service ADRs for model policy, retention policy, and future route migration
- future `/whisper` target route only after explicit migration planning
- future Home/Gateway runbooks to reduce scattered routing and publication knowledge

## Related Documents

- `docs/runbooks/whisper.md`
- `docs/services/ffmpeg.md`
- `docs/SERVICES_REGISTRY.md`
- `docs/DOCUMENTATION_RECONCILIATION.md`
- `docs/ENGINEERING_WORKFLOW.md`
- `docs/DOCUMENTATION_ARCHITECTURE.md`
- `docs/FIRST_RELEASE_PLAYBOOK.md`
- `docs/WHISPER_RELEASE_MODEL.md`
- `docs/RELEASES.md`
