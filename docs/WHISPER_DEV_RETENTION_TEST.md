# WHISPER_DEV_RETENTION_TEST

This document records the first retention test of `soma-whisper-dev`.

## Status

Name:

    soma-whisper-dev-retention-test-v1

Status:

    passed

Date:

    2026-06-02

Server:

    grlvm

## Runtime under test

Container:

    soma-whisper-dev

Image:

    soma-whisper-dev:local

Compose file:

    /srv/soma/compose/whisper-dev.compose.yml

Service code:

    /srv/soma/services/whisper-dev

Service data:

    /srv/soma/data/whisper-dev

Access:

    http://127.0.0.1:18080/whisper-dev

Retention setting:

    WHISPER_RETENTION_MAX_JOBS=5

## Purpose

Verify that the dev Whisper runtime keeps only the newest 5 terminal jobs.

This test also verifies that retention cleanup does not break:

- dev health
- legacy health
- host ownership of generated files

## Pre-test state

Before the retention test, the dev runtime had one completed smoke-test job:

    3c52d24a91d6

Observed job count before test:

    1

Observed dev health before test:

    ok

Observed legacy health before test:

    [OK] healthcheck completed without hard failures

## Test method

Five additional synthetic WAV jobs were submitted to `soma-whisper-dev`.

Synthetic files were generated inside the dev container using `ffmpeg`, then copied to the host with `docker cp`.

The files were submitted from the host to:

    http://127.0.0.1:18080/whisper-dev/submit

Submitted form values for each job:

    language=auto
    model_name=tiny
    compute_type=int8
    chunk_min=1
    overlap_sec=0
    beam=1
    context_preset=none
    context_text=
    vad=false
    keep_tmp=false

## Submitted jobs

Five new jobs were created.

Job 1:

    38153917dac3

Observed status:

    done

Job 2:

    9884775cf449

Observed status:

    done

Job 3:

    7919c7473ee4

Observed status:

    done

Job 4:

    f0b5fa086ade

Observed status:

    done

Job 5:

    fb0f23b326b6

Observed status:

    done

Each job reached terminal status by attempt 2.

## Retention result

After the fifth new job completed, the runtime contained exactly 5 job directories.

Observed remaining jobs:

    /srv/soma/data/whisper-dev/jobs/38153917dac3
    /srv/soma/data/whisper-dev/jobs/7919c7473ee4
    /srv/soma/data/whisper-dev/jobs/9884775cf449
    /srv/soma/data/whisper-dev/jobs/f0b5fa086ade
    /srv/soma/data/whisper-dev/jobs/fb0f23b326b6

Observed count:

    5

The original smoke-test job was removed:

    3c52d24a91d6

Observed result:

    [OK] old job removed by retention: 3c52d24a91d6

## Ownership result

Generated job files under `/srv/soma/data/whisper-dev/jobs` were owned by:

    grigorynokhrin:docker

Observed file mode sample:

    644

Observed examples:

    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/f0b5fa086ade/f0b5fa086ade-soma-retention-4.txt
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/f0b5fa086ade/intermediate.jsonl
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/f0b5fa086ade/soma-retention-4.wav
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/f0b5fa086ade/audio_16k.wav
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/f0b5fa086ade/f0b5fa086ade-soma-retention-4.srt
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/fb0f23b326b6/fb0f23b326b6-soma-retention-5.txt
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/7919c7473ee4/7919c7473ee4-soma-retention-3.txt
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/9884775cf449/9884775cf449-soma-retention-2.txt
    grigorynokhrin:docker 644 /srv/soma/data/whisper-dev/jobs/38153917dac3/38153917dac3-soma-retention-1.srt

This confirms that retention does not reintroduce the legacy `root:root` runtime-data problem.

## Data sizes after retention test

Observed sizes:

    /srv/soma/data/whisper-dev/hf_cache   75M
    /srv/soma/data/whisper-dev/jobs       1.1M
    /srv/soma/data/whisper-dev/outputs    4.0K

The Hugging Face cache stayed separate from job data.

## Health checks after test

Dev health endpoint:

    http://127.0.0.1:18080/whisper-dev/healthz

Observed response:

    ok

Legacy healthcheck command:

    cd /srv/soma
    make health

Observed legacy Whisper health:

    ok

Observed final healthcheck result:

    [OK] healthcheck completed without hard failures

## Result

The retention test passed.

Validated behavior:

    WHISPER_RETENTION_MAX_JOBS=5 keeps only the newest 5 terminal jobs

Validated safety:

    old completed job was deleted automatically
    newest 5 jobs remained
    generated files remained owned by grigorynokhrin:docker
    dev health remained ok
    legacy health remained ok

## Current validated jobs

After the retention test, the current dev job set is:

    38153917dac3
    9884775cf449
    7919c7473ee4
    f0b5fa086ade
    fb0f23b326b6

## Next step

The next recommended step is to add `soma-whisper-dev` to the runtime healthcheck as an optional dev service.

Goal:

    make /srv/soma/make health report both legacy production health and optional soma dev health

Important boundary:

    do not make dev service failure block legacy health unless explicitly enabled
