FROM python:3.12

RUN mkdir python_server
WORKDIR python_server
RUN mkdir -p log/files_to_upload
COPY ./comment_proxy comment_proxy
COPY ./src src
COPY ./faiss_knowledge faiss_knowledge
COPY ./faiss_qa faiss_qa
COPY ./PDF PDF
COPY ./Text Text
COPY ./qa_datasets qa_datasets
COPY ./google-credentials google-credentials
COPY ./alembic alembic
COPY ./alembic.ini alembic.ini
COPY ./.env .env
COPY ./entry.sh entry.sh
RUN apt update \
  && apt-get install -y poppler-utils

RUN pip install poetry \
  && poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock* ./
RUN poetry install

RUN poetry run python -m src.cli.import_docs_csv
RUN poetry run python -m src.cli.save_faiss_knowledge_db
RUN poetry run python -m src.cli.save_faiss_db

CMD ["./entry.sh"]

