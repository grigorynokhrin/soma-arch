# WHISPER_RETENTION_CLEANUP

This document records the manual retention cleanup performed for the legacy Whisper service.

## Status

Name:

    whisper-retention-cleanup-v1

Status:

    completed

Date:

    2026-06-02

Server:

    grlvm

Legacy runtime root:

    /home/grigorynokhrin/myservices

Legacy Whisper path:

    /home/grigorynokhrin/myservices/whisper

## Purpose

Old Whisper request data was taking unnecessary disk space.

The cleanup goal was to remove old request artifacts while keeping the most recent 5 jobs.

The cleanup covered:

- old job directories under `./whisper/data/jobs`
- old transcript/output files under `./whisper/outputs`

The cleanup did not intentionally modify:

- Whisper source code
- Dockerfile
- requirements.txt
- templates
- Hugging Face cache
- Docker Compose
- Caddy routes
- running containers

## Pre-cleanup facts

Before cleanup, Whisper data inventory showed:

    ./whisper size: 6.6G

Old output files existed in:

    ./whisper/outputs

Old job directories existed in:

    ./whisper/data/jobs

Audio/media files were found inside job directories, including:

    *.m4a
    audio_16k.wav
    chunk_*.wav

## Retention policy applied manually

Policy:

    keep last 5 job directories

The last 5 job directories were selected by directory modification time.

## First cleanup attempt

A first cleanup attempt was made without `sudo`.

Result:

    failed

Reason:

    Permission denied

Observed cause:

    files inside ./whisper/data/jobs were owned by root:root

Example ownership pattern:

    root:root 644 ./whisper/data/jobs/<job_id>/<file>

The service remained healthy after this failed attempt.

## Successful cleanup

A second cleanup was performed with `sudo`.

Manifest:

    /srv/soma/ops/baselines/whisper-retention-cleanup-sudo-20260602-100341.txt

Manifest owner/group after correction:

    grigorynokhrin:docker

Manifest mode:

    -rw-rw-r--

## Deleted data

Deleted old job directories:

    31

Deleted old output files:

    36

The deleted output files matched:

    *.txt
    *.srt
    *.vtt
    *.json

under:

    ./whisper/outputs

## Preserved data

The following 5 job directories were preserved:

    ./whisper/data/jobs/784b99abef30
    ./whisper/data/jobs/64e29faa12a4
    ./whisper/data/jobs/07394a3af229
    ./whisper/data/jobs/cb1572600303
    ./whisper/data/jobs/a41b9d5e712e

Remaining job directory count after cleanup:

    5

Remaining output file count after cleanup:

    0

## Post-cleanup size

After cleanup:

    ./whisper size: 2.1G

Approximate reduction:

    6.6G -> 2.1G

## Post-cleanup healthcheck

After cleanup, the runtime healthcheck passed.

Command:

    cd /srv/soma
    make health

Observed result:

    [OK] whisper health endpoint responded
    ok
    [OK] healthcheck completed without hard failures

## Safety notes

This cleanup intentionally removed old request data from the legacy Whisper runtime.

It did not intentionally remove:

- source code
- service templates
- model cache
- Docker image
- Compose configuration
- Caddy configuration

The running legacy service remained healthy after cleanup.

## Future requirement

The future `soma-whisper-dev` and then production `soma-whisper-api` should implement retention automatically.

Required default behavior:

    keep only the latest 5 jobs

Retention should remove old artifacts together:

- original uploaded audio/video
- normalized audio
- chunk audio files
- transcript files
- subtitle files
- intermediate files
- job logs
- job metadata

Retention should be configurable through environment variables, for example:

    WHISPER_RETENTION_MAX_JOBS=5

Optional future settings:

    WHISPER_RETENTION_MAX_AGE_DAYS
    WHISPER_RETENTION_MAX_TOTAL_SIZE_GB

## Implementation note for future service

Retention should run after a job reaches a terminal state:

- completed
- error
- deleted

The cleanup should never remove a currently running job.

Recommended rule:

    sort job directories by updated_at or directory mtime
    keep the newest N
    delete only terminal jobs older than the newest N

The service should also expose retention state in `/whisper/history`.
