# CADDY_WHISPER_DEV_ROUTE

This document records the first Caddy route for `soma-whisper-dev`.

## Status

Name:

    caddy-whisper-dev-route-v1

Status:

    passed

Date:

    2026-06-02

Server:

    grlvm

## Purpose

Expose the isolated dev Whisper service through the existing Caddy gateway without replacing the legacy Whisper route.

This route is for development validation only.

## Existing legacy Caddy setup

Caddy container:

    myservices-caddy

Caddy image:

    caddy:2-alpine

Caddyfile path on host:

    /home/grigorynokhrin/myservices/caddy/Caddyfile

Caddyfile mount in container:

    /home/grigorynokhrin/myservices/caddy/Caddyfile -> /etc/caddy/Caddyfile

Compose service path:

    /home/grigorynokhrin/myservices/compose.yaml

Legacy Caddy network before dev work:

    myservices_default

Legacy Whisper route:

    /myservices/whisper*

Legacy Whisper upstream:

    whisper:8000

Legacy health endpoint:

    http://127.0.0.1/myservices/whisper/healthz

Observed legacy health before route work:

    ok

## Dev Whisper runtime

Dev container:

    soma-whisper-dev

Dev image:

    soma-whisper-dev:local

Dev runtime port:

    127.0.0.1:18080 -> 8000

Dev internal route:

    /whisper-dev

Dev health endpoint:

    http://127.0.0.1:18080/whisper-dev/healthz

Observed dev health before Caddy route:

    ok

Dev Docker network:

    compose_default

Observed dev network address:

    compose_default 172.19.0.2

## Network bridge

Caddy originally could not resolve `soma-whisper-dev` because the containers were on different Docker networks.

Before network bridge:

    myservices-caddy -> myservices_default
    soma-whisper-dev -> compose_default

The following runtime command was used:

    docker network connect compose_default myservices-caddy

After network bridge:

    myservices-caddy -> myservices_default 172.18.0.2
    myservices-caddy -> compose_default 172.19.0.3
    soma-whisper-dev -> compose_default 172.19.0.2

DNS from inside Caddy after network bridge:

    soma-whisper-dev -> 172.19.0.2

HTTP from inside Caddy after network bridge:

    http://soma-whisper-dev:8000/whisper-dev/healthz -> ok

## Important persistence note

The command:

    docker network connect compose_default myservices-caddy

is a runtime change.

It may be lost if `myservices-caddy` is recreated.

A later persistent solution should define the external dev network in Compose.

Until then, after Caddy recreation, re-check:

    docker inspect myservices-caddy --format '{{range $name, $net := .NetworkSettings.Networks}}{{println $name $net.IPAddress}}{{end}}'

Expected networks:

    myservices_default
    compose_default

## Caddyfile change

Backup created before edit:

    /home/grigorynokhrin/myservices/caddy/Caddyfile.bak-20260602-181646

Added route:

    handle /whisper-dev* {
        reverse_proxy soma-whisper-dev:8000
    }

The route was inserted after the legacy Whisper block.

Legacy block remained unchanged:

    handle /myservices/whisper* {
        reverse_proxy whisper:8000
    }

## Caddy validation

Validation command:

    docker exec myservices-caddy caddy validate --config /etc/caddy/Caddyfile

Observed result:

    Valid configuration

Caddy warning observed:

    Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies

This warning existed because of formatting only. It did not block validation.

## Caddy reload

Reload command:

    docker exec myservices-caddy caddy reload --config /etc/caddy/Caddyfile

Observed result:

    reload completed without hard failure

Caddy container was not restarted.

Legacy services were not restarted.

## Server-side route checks

Dev route through Caddy from server:

    curl http://127.0.0.1/whisper-dev/healthz

Observed response:

    ok

Legacy route through Caddy from server:

    curl http://127.0.0.1/myservices/whisper/healthz

Observed response:

    ok

Server-side LAN IP check:

    curl http://10.0.1.196/whisper-dev/healthz

Observed response:

    HTTP/1.1 200 OK
    ok

## Mac-side route checks

Mac IP:

    10.0.1.189

Server IP:

    10.0.1.196

Network checks from Mac:

    ping 10.0.1.196 -> OK
    nc -vz 10.0.1.196 22 -> OK
    nc -vz 10.0.1.196 80 -> OK

Python check from Mac:

    http://10.0.1.196/whisper-dev/healthz

Observed result:

    status 200
    body b'ok'

After allowing the relevant process in LuLu, curl from Mac also worked:

    curl http://10.0.1.196/whisper-dev/healthz

Observed result:

    HTTP/1.1 200 OK
    ok

Observed headers included:

    Server: uvicorn
    Via: 1.1 Caddy

## LuLu note

Initial Mac `curl` requests failed with:

    curl: (7) Failed to connect to 10.0.1.196 port 80
    connect ... failed: Bad file descriptor

This was not a server-side Caddy problem.

Evidence:

    nc could connect to TCP port 80
    Python urllib received status 200 and body b'ok'
    Caddy logs showed successful requests from 10.0.1.189
    curl worked after the LuLu allow rule

Recommended LuLu allow rules for local development:

    /usr/bin/curl -> 10.0.1.196 TCP 80
    Python -> 10.0.1.196 TCP 80
    Terminal or iTerm -> 10.0.1.196 TCP 80
    Browser -> 10.0.1.196 TCP 80

## Runtime health after route

Healthcheck command:

    cd /srv/soma
    make health

Observed required legacy containers:

    myservices-caddy
    myservices-home
    myservices-whisper

Observed legacy Whisper health:

    ok

Observed optional dev health:

    optional dev container running: soma-whisper-dev
    optional dev whisper health endpoint responded
    ok

Observed final summary:

    [OK] healthcheck completed without hard failures

## Safety boundary

This route did not intentionally:

- replace `/myservices/whisper`
- stop legacy containers
- restart legacy containers
- migrate production traffic
- expose a new external port
- change the dev container port
- change Whisper model/runtime behavior

The new route only adds:

    /whisper-dev*

## Current validated URLs

From server:

    http://127.0.0.1/whisper-dev/healthz
    http://127.0.0.1/myservices/whisper/healthz

From Mac / LAN:

    http://10.0.1.196/whisper-dev/healthz
    http://10.0.1.196/myservices/whisper/healthz

## Result

The first Caddy dev route passed validation.

Validated behavior:

    Caddy can resolve soma-whisper-dev
    Caddy can proxy /whisper-dev* to soma-whisper-dev:8000
    dev health works through Caddy
    legacy Whisper health remains OK
    runtime healthcheck remains OK
    Mac LAN access works after local LuLu allow rule

## Next step

Make the network bridge persistent.

Recommended next task:

    update legacy compose/Caddy network configuration so myservices-caddy joins compose_default automatically

Important boundary:

    do not recreate or restart legacy services until a backup and dry-run are reviewed
