.PHONY: help dev reset_db migrate_db seed_db populate_seed verify_seed refresh_db refresh_db_from_staging

DATA_NAME ?=
SEED_TARGETS := seed_db populate_seed verify_seed refresh_db
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
ifeq ($(DB_NAMESPACE),)
	sh ./scripts/clear_postgres.sh
	sh ./scripts/restart_postgres.sh
	# Docker restart needs a moment before DB is ready.
	sleep 1
else
	python scripts/reset_schema.py
endif

migrate_db: ## Run alembic migrations
	python scripts/ensure_schema.py
	alembic upgrade head

refresh_db_from_staging: ## Reset local DB and copy from staging
	$(MAKE) reset_db
	sh ./scripts/copy_remote_db_to_local_db.sh

seed_db: ## Seed db with seed json files
	python seeders/seed.py $(if $(SEED_NAME),--data-name $(SEED_NAME),)

refresh_db: ## Reset, migrate, and seed db
	$(MAKE) reset_db
	$(MAKE) migrate_db
	$(MAKE) seed_db DATA_NAME=$(SEED_NAME)

populate_seed: ## Populate seed json files with reponse from test routes
	python scripts/populate_test_routes.py $(if $(SEED_NAME),--data-name $(SEED_NAME),)

verify_seed: ## Verify that seed json files match with reponse from test routes
	python scripts/verify_test_routes.py $(if $(SEED_NAME),--data-name $(SEED_NAME),) $(if $(LOGICAL_COMPARE),--logical-compare,)
