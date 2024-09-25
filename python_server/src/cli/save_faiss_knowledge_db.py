import os

import click
import pandas as pd
from langchain.schema.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config import settings
from src.get_faiss_vector import get_bm25_knowledge, get_hybrid_knowledge
from src.logger import setup_logger

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

setup_logger()


@click.command()
def main() -> None:
    """FAISSのベクトルを作成して保存する"""
    _save_faiss_knowledge_db()


def _save_faiss_knowledge_db():
    knowledge_file_path = settings.PYTHON_SERVER_ROOT / "faiss_knowledge" / "manifesto_demo_slides.csv"

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    docs = []
    manifests = pd.read_csv(knowledge_file_path)
    for i, row in enumerate(manifests.to_dict(orient="records")):
        title = row.pop("title")
        text = row.pop("text")
        filename = row.pop("filename")
        metadata = {}
        metadata["row"] = i
        metadata["image"] = filename
        page_content = f"Title: {title}\n {text}"
        docs.append(Document(page_content=page_content, metadata=metadata))

    text_splitter = CharacterTextSplitter(
        separator="\n",  # セパレータ
        chunk_size=300,  # チャンクの文字数
        chunk_overlap=0,  # チャンクオーバーラップの文字数
    )
    documents = text_splitter.split_documents(docs)

    vector = FAISS.from_documents(documents, embeddings)

    vector.save_local(settings.FAISS_KNOWLEDGE_DB_DIR)

    query = "政策の5本柱を教えて"
    print("BM25:")
    result = get_bm25_knowledge(query, top_k=2)
    print(result)
    print(len(result))

    print("Hybrid:")
    result = get_hybrid_knowledge(query, top_k=2)
    print(result)


if __name__ == "__main__":
    main()
