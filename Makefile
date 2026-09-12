# Local development helpers. Requires Hugo Extended (see [module.hugoVersion] in hugo.toml).
# Visual regression additionally requires Docker. Run `make` for the list.

.DEFAULT_GOAL := help
.PHONY: help setup serve build check check-all preflight live spec-required visual visual-update new clean

# Pinned so screenshots are comparable: the container fixes font rendering, which is the
# only way CI and a developer machine agree (spec FR-006). Must match the @playwright/test
# version in package.json.
PLAYWRIGHT_IMAGE := mcr.microsoft.com/playwright:v1.62.1-noble
DOCKER_RUN = docker run --rm -v "$(CURDIR):/work" -w /work \
	--user "$(shell id -u):$(shell id -g)" \
	-e HOME=/tmp -e npm_config_cache=/tmp/.npm -e CI \
	$(PLAYWRIGHT_IMAGE)

# --cleanDestinationDir matters: without it Hugo leaves stale files in public/ (a renamed
# stylesheet keeps its predecessor), which makes output assertions report phantom problems.
HUGO_BUILD = hugo --minify --gc --cleanDestinationDir

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

check: ## Fast gates: specs, front matter, strict build, output assertions
	python3 scripts/check-specs.py
	python3 scripts/check-content.py
	$(HUGO_BUILD) --panicOnWarning --printPathWarnings
	python3 scripts/check-output.py public

spec-required: ## Check this branch records intent (spec or No-Spec:). BASE=main by default
	python3 scripts/check-specs.py --diff-base $(or $(BASE),main)

check-all: check visual ## Every gate, including visual regression (needs Docker)

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
