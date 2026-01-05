.PHONY: dev reset_db seed_db populate_seed verify_seed

dev:
	fastapi dev src/main.py

reset_db:
	sh ./scripts/clear_postgres.sh
	sh ./scripts/restart_postgres.sh

seed_db:
	python seeders/academic_classes_students/seed_academic_classes_students.py

populate_seed:
	python scripts/populate_test_routes.py

verify_seed:
	python scripts/verify_test_routes.py
