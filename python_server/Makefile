up:
	docker compose up -d

down:
	docker compose down

lint:
	poetry run ruff check .

fmt:
	poetry run ruff format .
	# See: https://docs.astral.sh/ruff/formatter/#sorting-imports
	poetry run ruff check . --fix-only --exit-zero

test-single-question:
	INTEGRATION_TEST=true poetry run pytest -s tests/gpt_test.py::test_single_question

test-multiple-questions:
	INTEGRATION_TEST=true poetry run pytest -s tests/gpt_test.py::test_multiple_questions

test-filter-inappropriate-comments:
	INTEGRATION_TEST=true poetry run pytest -s tests/gpt_test.py::test_filter_inappropriate_comments

run:
	poetry run uvicorn src.web.api:app --host 127.0.0.1 --port 7200

run/production:
	poetry run uvicorn src.web.api:app --host 0.0.0.0 --port 7200

streamlit:
	poetry run streamlit run src/streamlit/main.py

setup/resources:
	sh src/cli/build_resources.sh

## db
db/reset: db/drop db/create migration/up

db/create:
	poetry run python -m src.cli.databases.create
db/drop:
	poetry run python -m src.cli.databases.drop

## alembic
migration/autogen:
	poetry run alembic revision --autogenerate
migration/up:
	poetry run alembic upgrade head
migration/down:
	poetry run alembic downgrade -1
migration/merge-heads:
	poetry run alembic merge heads
