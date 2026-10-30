# Local development helpers. Requires Hugo Extended (see [module.hugoVersion] in hugo.toml).
# Visual regression additionally requires Docker. Run `make` for the list.

.DEFAULT_GOAL := help
.PHONY: help setup serve build check check-all test coverage preflight live spec-required visual visual-update constitution-ids lint new clean

# Pinned so screenshots are comparable: the container fixes font rendering, which is the
# only way CI and a developer machine agree (spec FR-006). Must match the @playwright/test
# version in package.json.
PLAYWRIGHT_IMAGE := mcr.microsoft.com/playwright:v1.62.1-noble

# Neither linter is installed on this machine, and neither is guaranteed on the runner, so
# both are pinned and run in a container / an ephemeral env (CON-VER-004: run the check where
# it will actually run, and make "where" the same everywhere).
SHELLCHECK_IMAGE := koalaman/shellcheck:v0.10.0
BANDIT_VERSION   := 1.9.2
BANDIT_IMAGE     := python:3.12-slim
SHELL_FILES      := scripts/check-local-gates.sh scripts/preflight.sh \
                    .githooks/commit-msg .githooks/pre-commit .githooks/pre-push
DOCKER_RUN = docker run --rm -v "$(CURDIR):/work" -w /work \
	--user "$(shell id -u):$(shell id -g)" \
	-e HOME=/tmp -e npm_config_cache=/tmp/.npm -e CI \
	$(PLAYWRIGHT_IMAGE)

# --cleanDestinationDir matters: without it Hugo leaves stale files in public/ (a renamed
# stylesheet keeps its predecessor), which makes output assertions report phantom problems.
HUGO_BUILD = hugo --minify --gc --cleanDestinationDir

# The shared constitution lives in another repository. CI only gets THIS one, so the rule IDs
# are vendored (docs/constitution-ids.txt) and refreshed from the mirror on purpose, never read
# live by a gate (CON-VER-004).
MIRROR := $(HOME)/data-dash/.constitution-mirror/CONSTITUTION.md

help: ## Show this help
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Install the git hooks (run once per clone)
	@git config core.hooksPath .githooks
	@chmod +x .githooks/* scripts/*.sh 2>/dev/null || true
	@echo "core.hooksPath = $$(git config core.hooksPath)"
	@echo "pre-commit: secrets, protected branch, spec hygiene   (0.13s)"
	@echo "commit-msg: does the message say why"
	@echo "pre-push:   everything CI runs (make preflight)"
	@echo "Bypass any with --no-verify when you want CI to be the judge."

live: ## Check the DEPLOYED site (what the scheduled Health workflow runs)
	python3 scripts/check-live.py

preflight: ## Everything CI checks, run locally (what pre-push runs)
	scripts/preflight.sh

serve: ## Dev server with drafts at http://localhost:1313
	hugo server -D

build: ## Production build into ./public
	$(HUGO_BUILD)

# The gates are what everything else trusts, and they have shipped five bugs of their own.
# Testing them is not optional ceremony; COVERAGE_FLOOR only ever ratchets up (CON-COV-002).
COVERAGE_FLOOR ?= 95

test: ## Unit-test the gate scripts
	python3 -m coverage run -m pytest
	@python3 -m coverage report --fail-under=$(COVERAGE_FLOOR)

coverage: ## Unit tests with a line-by-line miss report
	python3 -m coverage run -m pytest
	python3 -m coverage report -m

check: test ## Everything fast: unit tests, specs, front matter, strict build, output assertions
	python3 scripts/check-specs.py
	python3 scripts/check-citations.py
	python3 scripts/check-content.py
	$(HUGO_BUILD) --panicOnWarning --printPathWarnings
	python3 scripts/check-output.py public
	python3 scripts/check-shipped-deps.py public

lint: ## Static analysis of the gates' own code: shellcheck + bandit (needs Docker and uv)
	docker run --rm -v "$(CURDIR):/mnt" --user "$(shell id -u):$(shell id -g)" \
	  $(SHELLCHECK_IMAGE) --severity=style $(SHELL_FILES)
	@echo "shellcheck: clean"
	docker run --rm -v "$(CURDIR):/work" -w /work --user "$(shell id -u):$(shell id -g)" \
	  -e HOME=/tmp $(BANDIT_IMAGE) bash -c \
	  'pip install --quiet --no-warn-script-location bandit==$(BANDIT_VERSION) && \
	   python -m bandit -r scripts/ -ll -q'
	@echo "bandit (medium+): clean"

constitution-ids: ## Refresh docs/constitution-ids.txt from the local constitution mirror
	@test -f $(MIRROR) || { \
	  echo "No constitution mirror at $(MIRROR)."; \
	  echo "It is created by the fleet repo's tools/install.sh; nothing else can supply it."; \
	  exit 1; }
	@python3 scripts/refresh-constitution-ids.py
	@echo "Review the diff before committing — this file is what CI checks citations against."

spec-required: ## Check this branch records intent (spec or No-Spec:). BASE=main by default
	python3 scripts/check-specs.py --diff-base $(or $(BASE),main)

check-all: check lint visual ## Every gate, including visual regression (needs Docker)

visual: build ## Visual regression against committed baselines (needs Docker)
	$(DOCKER_RUN) bash -c 'npm ci --no-audit --no-fund >/dev/null && npx playwright test'

visual-update: build ## Re-record baselines after an INTENTIONAL design change
	$(DOCKER_RUN) bash -c 'npm ci --no-audit --no-fund >/dev/null && npx playwright test --update-snapshots'
	@echo
	@echo "Baselines re-recorded. Review the changed PNGs before committing —"
	@echo "they are the record of how the site is supposed to look."

new: ## Scaffold an artwork: make new SLUG=my-painting
	@test -n "$(SLUG)" || { echo "usage: make new SLUG=my-painting"; exit 1; }
	hugo new content/$(SLUG)/index.md
	@echo
	@echo "Next: put the image in content/$(SLUG)/ (named $(SLUG).jpg, or update"
	@echo "the 'resources' src), fill in description/dimensions, set draft: false."

clean: ## Remove build output, test artifacts, and the local image-variant cache
	rm -rf public public-check resources/_gen test-results playwright-report
	hugo --gc >/dev/null 2>&1 || true
