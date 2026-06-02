# WHISPER_DEV_SMOKE_TEST

This document records the first functional smoke-test of `soma-whisper-dev`.

## Status

Name:

    soma-whisper-dev-smoke-test-v1

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

## Pre-test state

The dev container was running:

    soma-whisper-dev   Up

The dev health endpoint returned:

    ok

Endpoint:

    http://127.0.0.1:18080/whisper-dev/healthz

The dev data directories existed and were owned by:

    grigorynokhrin:docker

Directories:

    /srv/soma/data/whisper-dev/jobs
    /srv/soma/data/whisper-dev/outputs
    /srv/soma/data/whisper-dev/hf_cache

## Test input

A synthetic WAV file was generated with `ffmpeg` inside the dev container.

Container path:

    /tmp/soma-test.wav

The file was copied to the host with `docker cp`.

Host path:

    /tmp/soma-test.wav

Observed host file:

    /tmp/soma-test.wav

Observed size:

    64078 bytes

Purpose:

    avoid using personal audio for first functional test

## Submit request

The test file was submitted to:

    http://127.0.0.1:18080/whisper-dev/submit

Submitted form values:

    audio_file=soma-test.wav
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

Observed response:

    HTTP/1.1 303 See Other

Redirect location:

    http://127.0.0.1:18080/whisper-dev/jobs/3c52d24a91d6

## Job

Job ID:

    3c52d24a91d6

Job path:

    /srv/soma/data/whisper-dev/jobs/3c52d24a91d6

Observed job directory owner/group:

    grigorynokhrin:docker

## Job status result

Endpoint:

    http://127.0.0.1:18080/whisper-dev/jobs/3c52d24a91d6/status.json

Observed status:

    done

Observed stage:

    done

Observed model:

    tiny

Requested compute:

    int8

Used compute:

    int8

Observed chunks:

    1

Observed result text:

    Okay, let's go.

Observed started_at:

    2026-06-02T12:03:25

Observed finished_at:

    2026-06-02T12:03:29

## GPU/model result

Container logs showed:

    [WHISPER_MODEL] name=tiny requested_compute=int8 actual_compute=int8 device=cuda

This confirms that the test used CUDA inside `soma-whisper-dev`.

## Generated files

Generated job files existed under:

    /srv/soma/data/whisper-dev/jobs/3c52d24a91d6

Observed generated files included:

    soma-test.wav
    audio_16k.wav
    chunk_001.wav
    intermediate.jsonl
    job.json
    job.log
    soma-test_chunk01.txt
    3c52d24a91d6-soma-test.txt
    3c52d24a91d6-soma-test.srt

Observed host ownership for generated files:

    grigorynokhrin:docker

This confirms that the dev container no longer creates runtime data as `root:root`.

## Job log

Observed job lifecycle:

    job created
    source uploaded
    job started
    probing duration
    converting to wav
    chunking
    loading model
    transcribing chunk 1/1
    assembling final txt/srt
    job done

## Artifact endpoints

TXT artifact endpoint:

    http://127.0.0.1:18080/whisper-dev/jobs/3c52d24a91d6/artifacts/3c52d24a91d6-soma-test.txt

Observed TXT response:

    Okay, let's go.

SRT artifact endpoint:

    http://127.0.0.1:18080/whisper-dev/jobs/3c52d24a91d6/artifacts/3c52d24a91d6-soma-test.srt

Observed SRT response:

    1
    00:00:00,000 --> 00:00:02,000
    Okay, let's go.

## Data sizes after smoke-test

Observed sizes:

    /srv/soma/data/whisper-dev/hf_cache   75M
    /srv/soma/data/whisper-dev/jobs       224K
    /srv/soma/data/whisper-dev/outputs    4.0K

The model cache was populated under the dev data root.

## Notes

A `HEAD` request to the result page returned:

    405 Method Not Allowed

This is acceptable because the route supports `GET`.

A direct `GET` to the dev UI endpoint was previously verified to return HTML:

    http://127.0.0.1:18080/whisper-dev/

## Legacy safety check

After the dev smoke-test, the legacy runtime healthcheck passed.

Command:

    cd /srv/soma
    make health

Verified legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Observed legacy Whisper health:

    ok

Final healthcheck result:

    [OK] healthcheck completed without hard failures

## Result

The first functional smoke-test passed.

Validated pipeline:

    upload
    create job
    transcode audio
    split into chunks
    load faster-whisper model
    run CUDA inference
    generate TXT
    generate SRT
    serve status.json
    serve artifacts
    preserve host ownership as grigorynokhrin:docker

## Next step

The next validation should test retention behavior.

Goal:

    prove that WHISPER_RETENTION_MAX_JOBS=5 keeps only the newest 5 terminal jobs

Recommended approach:

    submit 5 additional tiny synthetic jobs
    verify that the oldest job is deleted automatically
    verify all remaining job files are owned by grigorynokhrin:docker
    verify legacy health remains OK
