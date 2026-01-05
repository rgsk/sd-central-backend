.PHONY: dev reset-db seed-db

dev:
	fastapi dev src/main.py

reset-db:
	sh ./scripts/clear_postgres.sh && sh ./scripts/restart_postgres.sh

seed-db:
	python seeders/academic_classes_students/seed_academic_classes_students.py
