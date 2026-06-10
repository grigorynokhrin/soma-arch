# Soma Target Migration Architecture

## 1. Migration Goal

The current server layout is mixed. The migration goal is a unified Soma platform layout with a clear separation between production and development environments.

The target state provides:

- one platform runtime root
- separate production and development application areas
- separate source, data, artifacts, logs, and configuration
- shared model/cache storage where deliberate
- environment identities that do not expose internal implementation details

## 2. Target Server Layout

```text
/srv/soma/
  prod/
    app/
    compose/
    data/
    artifacts/
    logs/
    config/

  dev/
    app/
    compose/
    data/
    artifacts/
    logs/
    config/

  shared/
    models/
    cache/

  backups/
```

Purpose:

| Area | Purpose |
| --- | --- |
| `prod/` | Production environment for stable user-facing services. |
| `dev/` | Development environment for testing and validation. |
| `prod/app/`, `dev/app/` | Application source/deployment content for each environment. |
| `prod/compose/`, `dev/compose/` | Environment-specific Compose definitions. |
| `prod/data/`, `dev/data/` | Persistent service data. |
| `prod/artifacts/`, `dev/artifacts/` | Generated user-facing outputs and downloadable results. |
| `prod/logs/`, `dev/logs/` | Runtime and service logs. |
| `prod/config/`, `dev/config/` | Environment configuration that is separate from application source. |
| `shared/models/` | Deliberately shared model files when compatible with both environments. |
| `shared/cache/` | Deliberately shared caches when safe and beneficial. |
| `backups/` | Backups required for recovery and migration rollback. |

Production and development must not share mutable data, artifacts, logs, or configuration unless the sharing is explicitly designed and documented.

## 3. Target Application Layout

```text
prod/
  app/
    home/
    gateway/
    services/
      whisper/
      ffmpeg/

dev/
  app/
    home/
    gateway/
    services/
      whisper/
      ffmpeg/
```

Components:

- **Home**: user-facing portal that publishes available stable tools in production and approved development tools in development.
- **Gateway**: routing layer that maps human-readable service paths or names to the correct environment services.
- **Whisper**: speech-to-text service and its transcription workflows.
- **FFmpeg**: media remux and conversion service.

Each environment owns its application deployment independently. Development changes must not alter production application content.

## 4. Data Storage Rules

Required separation:

- source code is separate from runtime data
- source code is separate from generated artifacts
- source code is separate from logs
- source code is separate from runtime configuration

Prohibited:

- user data inside source trees
- logs inside source trees
- generated artifacts inside source trees
- model files inside source trees

Persistent data must live under the environment's `data/` area. Generated results must live under `artifacts/`. Logs must live under `logs/`. Runtime configuration must live under `config/` or be supplied through environment configuration.

## 5. Path Management Rules

- Minimize hardcoded absolute paths.
- Prefer environment variables for service paths.
- Prefer Compose and environment-file configuration for runtime locations.
- Services should not depend on a specific host filesystem location.
- Container paths should remain stable while host paths are configured externally.
- Production and development path values must be independently configurable.

Hardcoded paths are technical debt and should be removed during migration whenever practical.

## 6. User-Facing Environment Model

The desired user-facing environments are:

```text
soma
soma-dev
```

- `soma` represents the stable production environment.
- `soma-dev` represents the development and validation environment.

Users should interact with environments, not with worktree names, branch names, container names, Compose project names, or internal filesystem structures.

## 7. Future Access Model

The long-term goal is to make services reachable through human-readable local network names.

Examples:

```text
http://soma
http://soma-dev
```

An equivalent local DNS or name-resolution mechanism is acceptable if it preserves the same clear production/development distinction.

This section describes a target state only. It does not modify networking, DNS, Gateway, Caddy, routes, or runtime configuration.

## 8. Out Of Scope

This document does not perform:

- file moves
- file deletions
- runtime changes
- Compose changes
- Gateway changes
- DNS changes
- Home changes
- container changes

This document defines only the target architecture.
