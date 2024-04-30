echo Run API server
alembic upgrade head
# uvicorn naples.main:api --reload --workers 4 --host
poetry run uvicorn --workers 4 --host 0.0.0.0 --port 8000 naples.main:api
