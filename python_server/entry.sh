#!/bin/bash

poetry run python -m src.cli.databases.create
poetry run alembic upgrade head
poetry run uvicorn src.web.api:app --host 0.0.0.0 --port 7200
