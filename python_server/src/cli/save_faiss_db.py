import csv
import logging
import os
import pathlib

import click
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.cli.loaders.qa_dataset import load_qa_dataset, split_qa_data_train_test
from src.config import settings
from src.logger import setup_logger

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

setup_logger()

LOGGER = logging.getLogger(__name__)


@click.command()
@click.option(
    "--input-csv",
    "-i",
    type=click.Path(exists=True, path_type=pathlib.Path),
    required=True,
    help="Path to the downloaded CSV file from the Google Spreadsheet",
    default=pathlib.Path("qa_datasets", "ブロードリスニング用想定FAQ_ver0.1 - faq.csv"),
)
@click.option("--question-column-name-prefix", "-q", type=str, required=True, help="Prefix of the column name for questions", default="具体の質問")
@click.option("--answer-column-name-prefix", "-a", type=str, required=True, help="Prefix of the column name for answers", default="回答案")
@click.option("--eval-aspect-name-prefix", "-e", type=str, required=True, help="Prefix of the column name for evaluation aspect", default="評価観点")
@click.option("--eval-aspect-slide-number-column-prefix", "-s", type=str, required=True, help="Prefix of the column name for slide number", default="期待するスライドのページ")
@click.option("--embed-answer", "-e", is_flag=True, help="Embed answer in the page content as well as question", default=True)
@click.option("--for-eval", is_flag=True, help="Split the dataset for training", default=False)
@click.option("--random-state", "-r", type=int, help="Random seed", default=42)
@click.option("--test-size", "-t", type=float, help="Test size ratio", default=0.2)
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging", default=False)
def main(
    input_csv: pathlib.Path,
    question_column_name_prefix: str,
    answer_column_name_prefix: str,
    eval_aspect_name_prefix: str,
    eval_aspect_slide_number_column_prefix: str,
    embed_answer: bool,
    for_eval: bool,
    random_state: int,
    test_size: float,
    debug: bool,
) -> None:
    """CSVファイルからQ&Aデータを読み込み、faiss データベースを保存する"""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    dataset = load_qa_dataset(
        input_csv=input_csv,
        question_column_name_prefix=question_column_name_prefix,
        answer_column_name_prefix=answer_column_name_prefix,
        eval_aspect_name_prefix=eval_aspect_name_prefix,
        eval_aspect_slide_number_column_prefix=eval_aspect_slide_number_column_prefix,
    )
    if for_eval:
        train_set, _ = split_qa_data_train_test(dataset, test_size=test_size, random_state=random_state)
    else:
        train_set = dataset
    docs = []
    for qa in train_set:
        LOGGER.info(f"question={qa.question}, answer={qa.answer}, eval_aspect_text={qa.eval_aspect_text}, eval_aspect_slide_number={qa.eval_aspect_slide_number}")
        if embed_answer:
            page_content = f"question: {qa.question}\nanswer: {qa.answer}"
        else:
            page_content = qa.question
        doc = Document(page_content=page_content, metadata={"question": qa.question, "answer": qa.answer})
        docs.append(doc)
    LOGGER.info(f"len(docs)={len(docs)}")
    _save_faiss_db(docs)


def _save_faiss_db(docs: list[Document]):
    LOGGER.info(f"len(docs)={len(docs)}")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)

    vector = FAISS.from_documents(documents, embeddings)

    vector.save_local(settings.FAISS_QA_DB_DIR)

    retriever = vector.as_retriever()

    query = "どうやって有権者の声を聞くの？"
    context_docs = retriever.get_relevant_documents(query)
    print(f"len={len(context_docs)}")

    first = context_docs[0]
    print(f"metadata={first.metadata}")
    print(first.page_content)


def load_broadlistening_qa_csv(file_path, question_column_prefix, answer_column_prefix, embed_answer=False) -> Document:
    """CSVを読みこむ。内部的にGoogle Spreadsheetで管理しているQ&A集からダウンロードしたCSVを想定。"""
    with open(file_path) as f:
        reader = csv.reader(f)
        header = next(reader)
        question_column_indices = [i for i, h in enumerate(header) if h.startswith(question_column_prefix)]
        answer_column_indices = [i for i, h in enumerate(header) if h.startswith(answer_column_prefix)]

        try:
            question_column_index = question_column_indices[0]
        except IndexError as e:
            raise ValueError("question_column is not found") from e
        if len(question_column_indices) > 1:
            LOGGER.warning(f"question_column_indices={question_column_indices}")

        try:
            answer_column_index = answer_column_indices[0]
        except IndexError as e:
            raise ValueError("answer_column is not found") from e
        if len(answer_column_indices) > 1:
            LOGGER.warning(f"answer_column_indices={answer_column_indices}")

        qa_list = []
        for row in reader:
            question = row[question_column_index]
            answer = row[answer_column_index]
            if question and answer:
                qa_list.append((question, answer))

        document = []
        for q, a in qa_list:
            if embed_answer:
                page_content = f"question: {q}\nanswer: {a}"
            else:
                page_content = q
            doc = Document(page_content=page_content, metadata={"question": q, "answer": a})
            document.append(doc)

        return document


if __name__ == "__main__":
    main()
