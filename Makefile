.PHONY: help dev reset_db seed_db populate_seed verify_seed

help: ## Show available commands
	@awk -F':.*## ' '/^[a-zA-Z0-9_%-]+:.*## /{printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Run FastAPI dev server
	fastapi dev src/main.py

reset_db: ## Clear and restart Postgres
	sh ./scripts/clear_postgres.sh
	sh ./scripts/restart_postgres.sh

seed_db: ## Seed db with seed json files
	python seeders/academic_classes_students/seed_academic_classes_students.py

populate_seed: ## Populate seed json files with reponse from test routes
	python scripts/populate_test_routes.py

verify_seed: ## Verify that seed json files match with reponse from test routes
	python scripts/verify_test_routes.py
