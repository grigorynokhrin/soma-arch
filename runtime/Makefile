.PHONY: help status legacy-status tree

SOMA_RUNTIME_ROOT ?= /srv/soma
SOMA_LEGACY_ROOT ?= /home/grigorynokhrin/myservices
SOMA_REFERENCE_REPO ?= /home/grigorynokhrin/soma-arch

help:
	@echo "soma runtime commands"
	@echo
	@echo "Read-only commands:"
	@echo "  make status         Show soma paths and Docker status"
	@echo "  make legacy-status Show legacy myservices Compose status"
	@echo "  make tree           Show /srv/soma directory tree"

status:
	@echo "=== soma paths ==="
	@echo "SOMA_RUNTIME_ROOT=$(SOMA_RUNTIME_ROOT)"
	@echo "SOMA_LEGACY_ROOT=$(SOMA_LEGACY_ROOT)"
	@echo "SOMA_REFERENCE_REPO=$(SOMA_REFERENCE_REPO)"
	@echo
	@echo "=== runtime root ==="
	@ls -ld "$(SOMA_RUNTIME_ROOT)"
	@echo
	@echo "=== reference repo ==="
	@cd "$(SOMA_REFERENCE_REPO)" && git status --short --branch
	@echo
	@echo "=== docker ps ==="
	@docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

legacy-status:
	@echo "=== legacy root ==="
	@ls -ld "$(SOMA_LEGACY_ROOT)"
	@echo
	@echo "=== legacy compose ps ==="
	@cd "$(SOMA_LEGACY_ROOT)" && docker compose ps

tree:
	@echo "=== /srv/soma tree ==="
	@find "$(SOMA_RUNTIME_ROOT)" -maxdepth 3 -type d | sort
