import functools
import json
import logging
import os
import re

import google.generativeai as genai
import MeCab
import pandas as pd
from langchain.retrievers.ensemble import EnsembleRetriever
from langchain.schema.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config import settings

LOGGER = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY


@functools.lru_cache(maxsize=1)
def _create_bm25_knowledge_db():
    knowledge_file_path = settings.PYTHON_SERVER_ROOT / "faiss_knowledge" / "manifesto_demo_slides.csv"

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
    bm25_search = BM25Retriever.from_documents(documents, preprocess_func=preprocess)
    return bm25_search


@functools.lru_cache(maxsize=1)
def load_stopwords() -> list[str]:
    """ストップワードを読み込む"""
    stopword_path = settings.PYTHON_SERVER_ROOT / "src" / "stopwords-ja.txt"
    with open(stopword_path) as f:
        stopwords = f.read().split("\n")
    return stopwords


def extract_nouns_verbs(text):
    """名詞動詞形状詞のみ抜く"""
    parser = MeCab.Tagger()
    parsed_text = parser.parse(text)
    lines = parsed_text.split("\n")
    nouns_verbs = []
    for line in lines:
        if "名詞" in line or "動詞" in line or "形状詞" in line:
            parts = line.split("\t")
            word = parts[0]
            if not word.isascii():
                nouns_verbs.append(word)
    return nouns_verbs


def preprocess(text):
    """前処理適用関数"""
    stopwords = load_stopwords()
    token_list = [token for token in extract_nouns_verbs(text) if token not in stopwords]
    return " ".join(token_list)


def get_bm25_knowledge(query, top_k=5):
    """bm25での検索"""
    bm25_retriever = _create_bm25_knowledge_db()
    bm25_retriever.k = top_k
    context_docs = bm25_retriever.get_relevant_documents(query)
    print(f"len={len(context_docs)}")
    top_docs = context_docs[:top_k]
    return [(doc.page_content, doc.metadata) for doc in top_docs]


def get_hybrid_knowledge(query, top_k=5):
    """ハイブリッド検索"""
    bm25_retriever = _create_bm25_knowledge_db()
    bm25_retriever.k = top_k
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector = FAISS.load_local(
        settings.FAISS_KNOWLEDGE_DB_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    faiss_retriever = vector.as_retriever(search_kwargs={"k": top_k})
    ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5])
    context_docs = ensemble_retriever.get_relevant_documents(query)
    print(f"len={len(context_docs)}")
    top_docs = context_docs[:top_k]
    return [(doc.page_content, doc.metadata) for doc in top_docs]


def get_qa(query):
    """回答例を一つ取得する"""
    result = get_multiple_qa(query=query, top_k=1)
    return result[0]


def get_multiple_qa(*, query, top_k=5):
    """回答例を取得する"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector = FAISS.load_local(
        settings.FAISS_QA_DB_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    retriever = vector.as_retriever()

    context_docs = retriever.get_relevant_documents(query)
    print(f"len={len(context_docs)}")

    top_docs = context_docs[:top_k]
    return [doc.page_content for doc in top_docs]


def get_knowledge(query):
    """RAGナレッジを一つ取得する"""
    result = get_multiple_knowledge(query=query, top_k=1)
    return result[0]


def get_multiple_knowledge(*, query, top_k=10):
    """RAGナレッジを取得する"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector = FAISS.load_local(
        settings.FAISS_KNOWLEDGE_DB_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    retriever = vector.as_retriever(search_kwargs={"k": top_k})

    context_docs = retriever.get_relevant_documents(query)
    print(f"len={len(context_docs)}")

    top_docs = context_docs[:top_k]
    for doc in top_docs:
        print(f"metadata={doc.metadata}")
    return [(doc.page_content, doc.metadata) for doc in top_docs]


DEFAULT_FALLBACK_KNOWLEDGE_METADATA = {"row": 1, "image": "slide_1.png"}


async def get_best_knowledge(query, top_k=15):
    """RAGナレッジを取得した上でLLMで評価する"""
    top_docs = get_multiple_knowledge(query=query, top_k=top_k)
    docs = ""
    for idx, (doc, metadata) in enumerate(top_docs, 1):
        print(f"metadata={metadata}")
        print(doc)
        docs += f"[ドキュメント id={idx}]\n{doc}\n\n"

    system_prompt = f"""
以下のドキュメントの中から最も入力に関連のある1から{top_k}までのドキュメントのidを答えてください。
もし関連のあるドキュメントがない場合は0を出力してください。
回答は答えの数字のみでお願いします。理由など他の情報は不要です。

[出力例]
0

[入力]
{query}

{docs}

"""
    LOGGER.debug("Ask the AI to find the best knowledge (top_k=%d, found_docs=%d, query=%s)", top_k, len(top_docs), query)
    model = genai.GenerativeModel("gemini-1.5-pro", generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(system_prompt)
    reply = response.text

    LOGGER.warning("AI response: %s", reply)
    LOGGER.warning("文書数: %s", len(top_docs))
    number_match = re.search(r"[\d]+", reply)
    if not number_match:
        LOGGER.warning("No number found in the AI response.")
        return "該当する知識は存在しません。政策に関係しない話題には回答を差し控えてください。", DEFAULT_FALLBACK_KNOWLEDGE_METADATA
    else:
        number = int(number_match[0])
        LOGGER.info("Picked up the index:%d for %d docs", number, len(top_docs))

    if number == 0 or number > top_k:
        LOGGER.warning("The number is out of range.")
        return "該当する知識は存在しません。政策に関係しない話題には回答を差し控えてください。", DEFAULT_FALLBACK_KNOWLEDGE_METADATA
    elif number > len(top_docs):
        # This should not happen but just in case
        LOGGER.warning(f"Number is out of range: {number} > {len(top_docs)}. This was from this prompt: {system_prompt}.\nThe answer to this prompt was: {reply}")
        return "ドキュメントの中から知識をうまく抽出出来ませんでした。自身がまだ学習中であり、その質問にまだ回答できない旨を回答して下さい", DEFAULT_FALLBACK_KNOWLEDGE_METADATA
    elif number < 0:
        # This should not happen but just in case
        LOGGER.warning(f"Number is out of range: {number} < 0. This was from this prompt: {system_prompt}\nThe answer to this prompt was: {reply}")
        return "ドキュメントの中から知識をうまく抽出出来ませんでした。自身がまだ学習中であり、その質問にまだ回答できない旨を回答して下さい", DEFAULT_FALLBACK_KNOWLEDGE_METADATA
    else:
        rel_doc = top_docs[number - 1]
        LOGGER.debug("Selected document: %s", rel_doc)
        return rel_doc


async def get_best_knowledge_with_score(query):
    """RAGナレッジを一つ、類似度とともに取得する"""
    LOGGER.debug("Get the best knowledge with score. Query=%s", query)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector = FAISS.load_local(
        settings.FAISS_KNOWLEDGE_DB_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    docs_and_scores = await vector.asimilarity_search_with_relevance_scores(query=query, k=1)
    doc, score = docs_and_scores[0]
    doc_in_prompt = f"関連度（-1.0 ~ +1.0）: {score}\n関連情報本文: {doc.page_content}"
    return doc_in_prompt, doc.metadata


async def get_n_best_knowledge(query, top_k=5, top_n=5):
    """RAGナレッジを取得した上でLLMで評価し、最大top_n個を返す"""
    top_docs = get_hybrid_knowledge(query=query, top_k=top_k)
    docs = ""
    for idx, (doc, metadata) in enumerate(top_docs, 1):
        print(f"metadata={metadata}")
        print(doc)
        docs += f"[ドキュメント id={idx}]\n{doc}\n\n"

    system_prompt = f"""
質問と、その質問に対して関連性が高いと判定された{top_k}件のドキュメントを与えるので、その中から関連度の高い{top_n}件のドキュメントのidをjsonで出力して下さい。

* 抽象的な質問の場合は、なるべくその内容が包含されるようなドキュメントを選定して下さい
    * e.g. 政策について質問された場合は、5つの政策全体について記載されたドキュメントを関連度が高いものと判断して下さい
* idは配列に格納し、配列の要素は関連度の高い順に並べてください。
* 該当するドキュメントが存在しない場合は空の配列を出力してください
* 前提として、このシステムはyoutubeライブのコメントの自動返信や、電話での自動応答に利用されます
    * それらのユーザーの質問に返答する際に有用なドキュメントを選定して下さい
* 以下のjson形式で出力してください。リストの各要素はintを徹底してください。

[出力例]
{{
    "results": [7, 3, 6]
}}

[質問]
{query}

{docs}

"""
    LOGGER.debug("Ask the AI to find the best knowledge (top_k=%d, found_docs=%d, query=%s)", top_k, len(top_docs), query)
    model = genai.GenerativeModel("gemini-1.5-pro", generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(system_prompt)
    reply = response.text

    try:
        obj = json.loads(reply)
        results = obj.get("results", [])
        if results and isinstance(results[0], str):
            results = [int(i) for i in results]
        rel_docs = [top_docs[i - 1] for i in results if 0 < i <= top_k]
        if len(rel_docs) == 0:
            return [("ドキュメントの中から知識をうまく抽出出来ませんでした。自身がまだ学習中であり、その質問に回答できない旨を回答して下さい", DEFAULT_FALLBACK_KNOWLEDGE_METADATA)]
        return rel_docs
    except Exception as e:
        LOGGER.warning("Failed to parse the JSON response: %s", reply)
        LOGGER.exception(e)
        return [("ドキュメントの中から知識をうまく抽出出来ませんでした。自身がまだ学習中であり、その質問に回答できない旨を回答して下さい", DEFAULT_FALLBACK_KNOWLEDGE_METADATA)]
