# soma runtime root

This directory is the future runtime root for the `soma` platform.

Path:

    /srv/soma

## Current status

This directory is only a skeleton at the moment.

It is not yet the active runtime for services.

The current legacy runtime is still:

    /home/grigorynokhrin/myservices

Do not delete, rename, or move the legacy runtime without an explicit migration step.

## Reference repository

The architecture and migration reference repository is:

    /home/grigorynokhrin/soma-arch

GitHub remote:

    git@github.com:grigorynokhrin/soma-arch.git

Important documents:

    docs/SYSTEM_GOALS.md
    docs/TARGET_ARCHITECTURE.md
    docs/CURRENT_STATE.md
    docs/DECISIONS.md
    docs/MIGRATION_PLAN.md
    docs/RUNTIME_ROOT_POLICY.md
    docs/SRV_SOMA_SKELETON.md
    docs/RUNTIME_STATUS.md

## Directory map

    /srv/soma/compose       Docker Compose files
    /srv/soma/gateway       Caddy / gateway configuration
    /srv/soma/portal-ui     user-facing portal UI
    /srv/soma/services      backend service code
    /srv/soma/data          persistent runtime data
    /srv/soma/shared        shared schemas/contracts/utilities
    /srv/soma/ops           operational artifacts
    /srv/soma/scripts       operational scripts

## Safety rules

- Do not use working services as experimental sandboxes.
- Do not store secrets in Git.
- Do not store user uploads or generated outputs in service code directories.
- Do not move legacy services without a rollback path.
- Verify after every operational change.
EOF

chmod 664 /srv/soma/README.md

echo '=== README ==='
sed -n '1,120p' /srv/soma/README.md

echo
echo '=== permissions ==='
ls -l /srv/soma/README.md
=== README ===
# soma runtime root

This directory is the future runtime root for the `soma` platform.

Path:

    /srv/soma

## Current status

This directory is only a skeleton at the moment.

It is not yet the active runtime for services.

The current legacy runtime is still:

    /home/grigorynokhrin/myservices

Do not delete, rename, or move the legacy runtime without an explicit migration step.

## Reference repository

The architecture and migration reference repository is:

    /home/grigorynokhrin/soma-arch

GitHub remote:

    git@github.com:grigorynokhrin/soma-arch.git

Important documents:

    docs/SYSTEM_GOALS.md
    docs/TARGET_ARCHITECTURE.md
    docs/CURRENT_STATE.md
    docs/DECISIONS.md
    docs/MIGRATION_PLAN.md
    docs/RUNTIME_ROOT_POLICY.md
    docs/SRV_SOMA_SKELETON.md
    docs/RUNTIME_STATUS.md

## Directory map

    /srv/soma/compose       Docker Compose files
    /srv/soma/gateway       Caddy / gateway configuration
    /srv/soma/portal-ui     user-facing portal UI
    /srv/soma/services      backend service code
    /srv/soma/data          persistent runtime data
    /srv/soma/shared        shared schemas/contracts/utilities
    /srv/soma/ops           operational artifacts
    /srv/soma/scripts       operational scripts

## Safety rules

- Do not use working services as experimental sandboxes.
- Do not store secrets in Git.
- Do not store user uploads or generated outputs in service code directories.
- Do not move legacy services without a rollback path.
- Verify after every operational change.

=== permissions ===
-rw-rw-r-- 1 grigorynokhrin docker 1534 Jun  2 09:02 /srv/soma/README.md
