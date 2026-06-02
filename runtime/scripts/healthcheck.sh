#!/usr/bin/env bash
set -u

SOMA_RUNTIME_ROOT="${SOMA_RUNTIME_ROOT:-/srv/soma}"
SOMA_LEGACY_ROOT="${SOMA_LEGACY_ROOT:-/home/grigorynokhrin/myservices}"
SOMA_REFERENCE_REPO="${SOMA_REFERENCE_REPO:-/home/grigorynokhrin/soma-arch}"

FAILED=0

section() {
  echo
  echo "=== $1 ==="
}

ok() {
  echo "[OK] $1"
}

warn() {
  echo "[WARN] $1"
}

fail() {
  echo "[FAIL] $1"
  FAILED=1
}

section "soma paths"

if [ -d "$SOMA_RUNTIME_ROOT" ]; then
  ok "runtime root exists: $SOMA_RUNTIME_ROOT"
else
  fail "runtime root missing: $SOMA_RUNTIME_ROOT"
fi

if [ -d "$SOMA_LEGACY_ROOT" ]; then
  ok "legacy root exists: $SOMA_LEGACY_ROOT"
else
  fail "legacy root missing: $SOMA_LEGACY_ROOT"
fi

if [ -d "$SOMA_REFERENCE_REPO/.git" ]; then
  ok "reference repo exists: $SOMA_REFERENCE_REPO"
else
  fail "reference repo missing or not a git repo: $SOMA_REFERENCE_REPO"
fi

section "reference repo status"

if [ -d "$SOMA_REFERENCE_REPO/.git" ]; then
  cd "$SOMA_REFERENCE_REPO" || exit 1
  git status --short --branch
else
  warn "skipping git status"
fi

section "docker availability"

if command -v docker >/dev/null 2>&1; then
  ok "docker command exists"
  docker version --format 'Docker client={{.Client.Version}} server={{.Server.Version}}' 2>/dev/null || warn "docker version check failed"
else
  fail "docker command not found"
fi

section "running containers"

docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' || fail "docker ps failed"

section "required legacy containers"

for name in myservices-caddy myservices-home myservices-whisper; do
  if docker ps --format '{{.Names}}' | grep -qx "$name"; then
    ok "container running: $name"
  else
    fail "container not running: $name"
  fi
done

section "legacy compose status"

if [ -d "$SOMA_LEGACY_ROOT" ]; then
  cd "$SOMA_LEGACY_ROOT" || exit 1
  docker compose ps || fail "docker compose ps failed"
else
  warn "skipping compose status"
fi

section "whisper health endpoint"

if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 5 http://127.0.0.1/myservices/whisper/healthz >/tmp/soma-whisper-healthcheck.out 2>/tmp/soma-whisper-healthcheck.err; then
    ok "whisper health endpoint responded"
    cat /tmp/soma-whisper-healthcheck.out
  else
    warn "whisper health endpoint did not respond successfully"
    cat /tmp/soma-whisper-healthcheck.err 2>/dev/null || true
  fi
else
  warn "curl not found; skipping HTTP health check"
fi

section "summary"

if [ "$FAILED" -eq 0 ]; then
  ok "healthcheck completed without hard failures"
  exit 0
else
  fail "healthcheck completed with failures"
  exit 1
fi
