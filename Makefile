.PHONY: help dev reset_db seed_db populate_seed verify_seed refresh_db_from_staging setup_test_db

DATA_NAME ?=
SEED_TARGETS := seed_db populate_seed verify_seed
EXTRA_ARGS := $(filter-out $(SEED_TARGETS),$(MAKECMDGOALS))
SEED_NAME := $(if $(DATA_NAME),$(DATA_NAME),$(firstword $(EXTRA_ARGS)))

ifneq ($(filter $(SEED_TARGETS),$(MAKECMDGOALS)),)
  $(eval $(EXTRA_ARGS):;@:)
endif

help: ## Show available commands
	@awk -F':.*## ' '/^[a-zA-Z0-9_%-]+:.*## /{printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Run FastAPI app in development mode
	fastapi dev src/main.py

run: ## Run FastAPI app in production mode
	fastapi run src/main.py

reset_db: ## Clear and restart Postgres
	sh ./scripts/clear_postgres.sh
	sh ./scripts/restart_postgres.sh

refresh_db_from_staging: ## Reset local DB and copy from staging
	$(MAKE) reset_db
	sh ./scripts/copy_remote_db_to_local_db.sh

seed_db: ## Seed db with seed json files
	python seeders/seed.py $(if $(SEED_NAME),--data-name $(SEED_NAME),)

populate_seed: ## Populate seed json files with reponse from test routes
	python scripts/populate_test_routes.py $(if $(SEED_NAME),--data-name $(SEED_NAME),)

verify_seed: ## Verify that seed json files match with reponse from test routes
	python scripts/verify_test_routes.py $(if $(SEED_NAME),--data-name $(SEED_NAME),)

setup_test_db: ## Reset DB, migrate, and seed with e2e data
	$(MAKE) reset_db && sleep 1 && alembic upgrade head && $(MAKE) seed_db e2e
