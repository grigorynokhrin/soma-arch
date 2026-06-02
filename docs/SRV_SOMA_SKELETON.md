# SRV_SOMA_SKELETON

This document records the creation of the initial `/srv/soma` runtime skeleton.

## Step

Name:

    create-srv-soma-skeleton

Status:

    completed

Date:

    2026-06-02

## Purpose

Create the target runtime root skeleton for the future `soma` platform without modifying the current legacy `myservices` runtime.

## Created path

    /srv/soma

Observed ownership:

    grigorynokhrin:docker

Observed permissions:

    drwxrwxr-x

## Created top-level structure

    /srv/soma/
      compose/
      data/
      gateway/
      ops/
      portal-ui/
      scripts/
      services/
      shared/
      .env.example
      README.md
      Makefile

## Created service directories

    /srv/soma/services/whisper
    /srv/soma/services/tesseract
    /srv/soma/services/supir

## Created data directories

    /srv/soma/data/whisper
    /srv/soma/data/tesseract
    /srv/soma/data/supir

Each service data directory includes:

    jobs/
    history/
    exports/
    tmp/

## Created ops directories

    /srv/soma/ops/baselines
    /srv/soma/ops/manifests
    /srv/soma/ops/runbooks
    /srv/soma/ops/backups

## Safety confirmation

This step did not intentionally:

- copy active services
- modify `~/myservices`
- stop containers
- restart containers
- modify Caddy routes
- modify Docker Compose
- remove legacy files

## Legacy runtime status

Legacy runtime still exists:

    /home/grigorynokhrin/myservices

Observed ownership at verification time:

    grigorynokhrin:docker

## Container status at verification time

Observed running containers:

    myservices-caddy
    myservices-whisper
    myservices-home

Note:

Earlier baseline included `image-upscale` as running. At this verification point it was not listed by `docker ps`. The skeleton creation step did not modify Docker state, so this should be treated as an observation requiring separate confirmation if needed.
