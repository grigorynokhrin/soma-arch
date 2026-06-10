.PHONY: \
	help \
	cockpit \
	status \
	context \
	git-check \
	docs-list \
	audit-list \
	local-validate-ffmpeg \
	local-validate-compose \
	local-validate \
	server-commands

PYTHONPYCACHEPREFIX ?= /private/tmp/soma-arch-pycache

help: cockpit

cockpit:
	@echo "soma-arch Developer Cockpit v1"
	@echo
	@echo "Safety:"
	@echo "  All v1 targets are local/read-only except local validation commands."
	@echo "  No target builds, starts, stops, restarts, or removes Docker containers."
	@echo "  No target changes Gateway/Caddy, production compose, server files, or runtime data."
	@echo "  Server commands are printed only; they are not executed."
	@echo
	@echo "Local orientation:"
	@echo "  make status                  Show local repo status and worktrees"
	@echo "  make context                 Print docs/CHATGPT_CONTEXT.md"
	@echo "  make docs-list               List key canonical docs"
	@echo "  make audit-list              List docs/reports/*.md"
	@echo
	@echo "Local validation:"
	@echo "  make git-check               Run git diff/status checks"
	@echo "  make local-validate-ffmpeg   Run FFmpeg selfchecks and compile checks"
	@echo "  make local-validate-compose  Run docker compose config checks when Docker is available"
	@echo "  make local-validate          Run FFmpeg, compose, and git checks"
	@echo
	@echo "Server audit helpers:"
	@echo "  make server-commands         Print read-only server audit/status commands"

status:
	@echo "=== pwd ==="
	@pwd
	@echo
	@echo "=== git status ==="
	@git status --short --branch
	@echo
	@echo "=== git log ==="
	@git log --oneline -3
	@echo
	@echo "=== git worktrees ==="
	@git worktree list

context:
	@sed -n '1,240p' docs/CHATGPT_CONTEXT.md

git-check:
	@git diff --check
	@git diff --stat
	@git status --short

docs-list:
	@for doc in \
		docs/CHATGPT_CONTEXT.md \
		docs/PLATFORM_ARCHITECTURE.md \
		docs/NAMING_AND_LAYOUT_POLICY.md \
		docs/SERVICES_REGISTRY.md \
		docs/DOCUMENTATION_ARCHITECTURE.md \
		docs/ENGINEERING_WORKFLOW.md; do \
		if [ -f "$$doc" ]; then \
			echo "$$doc"; \
		else \
			echo "missing: $$doc"; \
		fi; \
	done

audit-list:
	@if [ -d docs/reports ]; then \
		find docs/reports -maxdepth 1 -type f -name '*.md' -print | sort; \
	else \
		echo "No docs/reports directory found."; \
	fi

local-validate-ffmpeg:
	@if [ -f services/ffmpeg/selfcheck.py ]; then \
		echo "=== services/ffmpeg/selfcheck.py ==="; \
		python3 services/ffmpeg/selfcheck.py; \
	else \
		echo "skip: services/ffmpeg/selfcheck.py not found"; \
	fi
	@if [ -f services/ffmpeg-dev/selfcheck.py ]; then \
		echo "=== services/ffmpeg-dev/selfcheck.py ==="; \
		python3 services/ffmpeg-dev/selfcheck.py; \
	else \
		echo "skip: services/ffmpeg-dev/selfcheck.py not found"; \
	fi
	@if [ -d services/ffmpeg ]; then \
		echo "=== compile services/ffmpeg ==="; \
		PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall services/ffmpeg; \
	else \
		echo "skip: services/ffmpeg not found"; \
	fi
	@if [ -d services/ffmpeg-dev ]; then \
		echo "=== compile services/ffmpeg-dev ==="; \
		PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall services/ffmpeg-dev; \
	else \
		echo "skip: services/ffmpeg-dev not found"; \
	fi

local-validate-compose:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "[WARN] docker command not found; skipping compose config checks."; \
	else \
		for file in \
			compose/ffmpeg.compose.yml \
			compose/ffmpeg-dev.compose.yml \
			compose/whisper-dev.compose.yml; do \
			if [ -f "$$file" ]; then \
				echo "=== docker compose -f $$file config ==="; \
				if ! docker compose -f "$$file" config >/dev/null; then \
					echo "[WARN] compose config check failed for $$file; continuing."; \
				fi; \
			else \
				echo "skip: $$file not found"; \
			fi; \
		done; \
	fi

local-validate: local-validate-ffmpeg local-validate-compose git-check

server-commands:
	@echo "Read-only server audit/status commands to run manually on the server:"
	@echo
	@echo "cd /home/grigorynokhrin/soma-arch && git worktree list"
	@echo "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'"
	@echo "docker compose ls"
	@echo "du -sh /home/grigorynokhrin/* 2>/dev/null"
	@echo "du -sh /srv/* 2>/dev/null"
	@echo "find /srv/soma -maxdepth 2 -type d -print | sort"
	@echo "find /srv/soma/worktrees -maxdepth 2 -type d -print | sort"
	@echo "cd /srv/soma && make status"
	@echo "cd /srv/soma && make health"
