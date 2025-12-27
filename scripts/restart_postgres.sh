#!/bin/bash

sh "scripts/remove_postgres.sh"

docker volume create sd-central-backend-postgres-data

docker run \
	-p 5498:5432 \
	--name sd-central-backend-postgres \
	-e POSTGRES_PASSWORD=postgres \
	-e POSTGRES_USER=postgres \
	-e POSTGRES_DB=postgres \
	-v sd-central-backend-postgres-data:/var/lib/postgresql/data \
	-d pgvector/pgvector:pg16
