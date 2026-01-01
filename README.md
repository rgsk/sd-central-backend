fast api

```
run dev server
fastapi dev src/main.py
```

alembic

```
alembic upgrade head
alembic downgrade base
alembic history
alembic upgrade +1
alembic downgrade -1

reset alembic tracking
DROP TABLE alembic_version;
```
