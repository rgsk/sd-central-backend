activate venv

```
source .venv/bin/activate
```

install deps from requirements.txt

```
pip install -r requirements.txt
```

freeze deps in requirements.txt

```
pip freeze > requirements.txt
```

fast api

run dev server

```
fastapi dev src/main.py
```

usually the commands regularly used are written in Makefile, run them like below

```
make dev

# above runs the dev server command ie. fastapi dev src/main.py
```

alembic

```
alembic revision --autogenerate -m "your message"
alembic upgrade head
alembic downgrade base
alembic history
alembic upgrade +1
alembic downgrade -1

reset alembic tracking
DROP TABLE alembic_version;
```
