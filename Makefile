# Veridion developer commands. Run `make` or `make help` for the list.
# Requires: uv (Python), Node.js 22+ with npm, and optionally Tesseract for scanned PDFs.

API := apps/api
WEB := apps/web

.DEFAULT_GOAL := help
.PHONY: help setup dev api web seed snapshot test lint typecheck check build eval migrate db-check stack stack-down clean

help: ## List the available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install API and web dependencies
	cd $(API) && uv sync --extra postgres
	cd $(WEB) && npm ci --no-audit --no-fund

dev: ## Run the API (:8000, with an embedded worker) and the web app (:3000) together
	@trap 'kill 0' INT TERM EXIT; \
	(cd $(API) && uv run veridion serve --reload) & \
	(cd $(WEB) && npm run dev) & \
	wait

api: ## Run only the API
	cd $(API) && uv run veridion serve --reload

web: ## Run only the web app
	cd $(WEB) && npm run dev

seed: ## (Re)create the sample workspace (demo@veridion.example / veridion-demo); MODE=rules|hybrid|auto (default auto)
	cd $(API) && uv run veridion seed demo --reset --mode $(or $(MODE),auto)

snapshot: ## Re-record the public /demo from the seeded workspace
	cd $(API) && uv run veridion demo snapshot

test: ## Run the API test suite
	cd $(API) && uv run pytest

lint: ## Lint Python and TypeScript
	cd $(API) && uv run ruff check src tests migrations
	cd $(WEB) && npm run lint

typecheck: ## Type-check the web app
	cd $(WEB) && npm run typecheck

db-check: ## Fail if the models have changes that no migration covers (uses a throwaway database)
	@tmp=$$(mktemp -d) && export DATABASE_URL="sqlite:///$$tmp/check.db" && cd $(API) && \
	uv run veridion db upgrade > /dev/null && uv run veridion db check; status=$$?; rm -rf "$$tmp"; exit $$status

check: lint typecheck test db-check ## Everything CI runs before building

build: ## Production build of the web app
	cd $(WEB) && npm run build

eval: ## Run the evaluation suite (rules only; add MODE=both to include the model)
	cd $(API) && uv run veridion eval run --mode $(or $(MODE),rules) --out ../../docs/evaluation-latest.md

migrate: ## Apply database migrations to DATABASE_URL
	cd $(API) && uv run veridion db upgrade

stack: ## Build and start the production-shaped container stack (needs SECRET_KEY in .env)
	docker compose up --build --detach
	@echo "Web: http://localhost:3000   (seed with: docker compose run --rm api veridion seed demo --mode rules)"

stack-down: ## Stop the container stack (data volumes are kept)
	docker compose down

clean: ## Remove build output and caches (keeps your database and uploaded documents)
	rm -rf $(WEB)/.next $(API)/.pytest_cache $(API)/.ruff_cache
