import datetime
import pathlib
import random
from collections.abc import Iterator

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import ORJSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config import settings
from src.databases.engine import session_scope
from src.get_faiss_vector import get_hybrid_knowledge, get_multiple_qa
from src.gpt import DocumentRetrievalType, filter_inappropriate_comments, generate_hallucination_response, generate_response
from src.logger import setup_logger
from src.repository.chat_message import YoutubeChatMessageRepository
from src.repository.chat_message_cursor import YoutubeChatMessageCursorRepository
from src.schema.hallucination import HallucinationRequest, HallucinationResponse
from src.templates import TEMPLATE_MESSAGES, TEMPLATE_QUESTIONS
from src.text_to_speech import TextToSpeech
from src.use_cases.find_youtube_chat_messages import FindYoutubeChatMessagesUseCase
from src.use_cases.save_youtube_chat_message import SaveYoutubeChatMessageUseCase
from src.web.schema.response_model.youtube import YouTubeChatMessageModel, YouTubeChatMessagesResponseModel
from src.youtube import YouTubeChatMessage, youtube_client

setup_logger()


class FilteringRequest(BaseModel):
    """POST /filter のRequestのJSON型"""

    messages: list[str]


class YouTubeCommentPostRequest(BaseModel):
    """POST /youtube/chat_messageのリクエストのJSON型"""

    message_id: str
    message: str
    name: str
    profile: str
    live_id: str


app = FastAPI(
    default_response_class=ORJSONResponse,
)
app.mount("/proxy", StaticFiles(directory="./comment_proxy"), name="comment_proxy")


# 現在の時刻を取得し、1時間ごとのファイル名を生成
current_time = datetime.datetime.now(tz=settings.LOCAL_TZ)

t_fmt = current_time.strftime("%Y%m%d_%H%M%S")
log_filename_json = pathlib.Path(__file__).parent.parent.parent / "log" / f"log_{t_fmt}.json"
log_filename_csv = pathlib.Path(__file__).parent.parent.parent / "log" / f"log_{t_fmt}.csv"


# chat_id をグローバルにキャッシュする

cache = {}


async def get_cached_chat_id():
    """キャッシュされたchatidを返す"""
    if "chat_id" in cache:
        return cache["chat_id"]

    chat_id = await youtube_client.get_chat_id()
    cache["chat_id"] = chat_id

    return chat_id


def get_session(request: Request) -> Iterator[Session]:
    """Get session from Session Local"""
    with session_scope() as session:
        yield session


@app.post("/reply")
async def reply(inputtext: str = Form(...)):
    """GPT に問い合わせた回答結果を取得する"""
    res1, res2 = await generate_response(
        text=inputtext, log_filename_json=log_filename_json, log_filename_csv=log_filename_csv, doc_retrieval_type=DocumentRetrievalType.multi, check_hal=True
    )

    if isinstance(res1, bytes):
        res1 = res1.decode("utf-8")
    if isinstance(res2, bytes):
        res2 = res2.decode("utf-8")

    response = {"response_text": res1, "image_filename": res2}

    return ORJSONResponse(content=response)


@app.post("/filter")
async def filter(request: FilteringRequest):
    """コメントのフィルタリングを行う"""
    try:
        filtered = await filter_inappropriate_comments(request.messages)
        return {"messages": filtered}
    except Exception as e:
        print(e)
        return {"messages": []}


@app.get("/get_chat/")
async def live_chat(request: Request):
    """YouTube ライブチャットを取得する"""
    chat_id = await youtube_client.get_chat_id()
    if not chat_id:
        return ORJSONResponse(content={"error": "No active chat found"}, status_code=404)

    # nextPageTokenをリクエストから取得
    page_token = request.query_params.get("pageToken", None)
    chat_data = await youtube_client.get_chat(chat_id=chat_id, pageToken=page_token)
    return ORJSONResponse(content=chat_data)


@app.post("/youtube/chat_message")
async def post_chat_messages(request: YouTubeCommentPostRequest, session: Session = Depends(get_session)):
    """Youtube ライブチャットをポストする"""
    use_case = SaveYoutubeChatMessageUseCase(youtube_chat_message_repo=YoutubeChatMessageRepository(session=session))
    use_case.save_new_message(
        YouTubeChatMessage(
            video_id=request.live_id,
            message_id=request.message_id,
            message_text=request.message,
            author_name=request.name,
            author_image_url=request.profile,
            created_at=datetime.datetime.now(datetime.UTC),
        )
    )
    return ORJSONResponse(content={})


@app.get("/youtube/chat_message")
async def chat_messages(
    request: Request,
    session: Session = Depends(get_session),
):
    """YouTube ライブチャットを取得する"""
    """わんこめに移行
    chat_id = await get_cached_chat_id()

    if not chat_id:
        # 配信中のライブが見つからない場合
        return ORJSONResponse(content={"error": "No active chat found"}, status_code=404)
    """
    # 事前にDBに保存しておいたチャットメッセージを取得する
    use_case = FindYoutubeChatMessagesUseCase(
        youtube_chat_message_repo=YoutubeChatMessageRepository(session=session),
        youtube_chat_message_cursor_repo=YoutubeChatMessageCursorRepository(session=session),
    )

    messages = use_case.find_messages()

    return YouTubeChatMessagesResponseModel(
        messages=[
            YouTubeChatMessageModel(
                video_id=message.video_id,
                message_id=message.message_id,
                message_text=message.message_text,
                author_name=message.author_name,
                author_image_url=message.author_image_url,
            )
            for message in messages
        ]
    )


@app.api_route("/voice", methods=["POST"], response_class=Response)
async def voice(request: Request):
    """テキストを音声に変換する"""
    # NOTE: クエリパラメータから受け取るのが気持ち悪いが、unity側での修正が必要なので一旦既存実装を踏襲する
    text = request.query_params["text"]

    text_to_speech = TextToSpeech()

    audio = await text_to_speech.text_to_speech_stream(text)

    return Response(content=audio, media_type="audio/wav")


@app.api_route("/voice/v2", methods=["POST"], response_class=Response)
async def voice_v2(request: Request):
    """テキストを音声に変換する"""
    # NOTE: クエリパラメータから受け取るのが気持ち悪いが、unity側での修正が必要なので一旦既存実装を踏襲する
    text = request.query_params["text"]

    text_to_speech = TextToSpeech()

    audio = await text_to_speech.text_to_speech_with_azure_tts(text)

    return Response(content=audio, media_type="audio/wav")


@app.api_route("/voice/azure", methods=["POST"], response_class=Response)
async def voice_azure(request: Request):
    """テキストを音声に変換する"""
    # NOTE: クエリパラメータから受け取るのが気持ち悪いが、unity側での修正が必要なので一旦既存実装を踏襲する
    text = request.query_params["text"]

    text_to_speech = TextToSpeech()

    audio = await text_to_speech.azure_text_to_speech(text)

    return Response(content=audio, media_type="audio/wav")


@app.api_route("/voice/male", methods=["POST"], response_class=Response)
async def voice_male(request: Request):
    """テキストを音声に変換する"""
    # NOTE: クエリパラメータから受け取るのが気持ち悪いが、unity側での修正が必要なので一旦既存実装を踏襲する
    text = request.query_params["text"]

    text_to_speech = TextToSpeech()

    audio = await text_to_speech.azure_text_to_speech(text, voice_name="ja-JP-KeitaNeural")

    return Response(content=audio, media_type="audio/wav")


@app.get("/get_info")
async def get_information(
    query: str = Query(..., description="The query text for which to retrieve related information."), top_k: int = Query(5, description="The number of top results to retrieve.")
):
    """Retrieve and return information related to the provided query text using RAG."""
    try:
        # 与えられた質問文に関連する情報を取得する
        knowledge_items = get_hybrid_knowledge(query=query, top_k=top_k)
        qa_items = get_multiple_qa(query=query, top_k=top_k)
    except Exception as e:
        # エラーハンドリング: RAG情報の取得に失敗した場合
        raise HTTPException(status_code=500, detail=f"Failed to retrieve information: {str(e)}") from e
    # 関連情報をJSON形式で返す
    return {"query": query, "knowledge_items": knowledge_items, "qa_items": qa_items}


@app.post("/hallucination")
async def hallucination(request: HallucinationRequest) -> HallucinationResponse:
    """ハルシネーション判定を実施"""
    res = await generate_hallucination_response(text=request.text, doc_retrieval_type=DocumentRetrievalType.multi)
    return res


@app.get("/template_message")
async def get_template_message():
    """テンプレートメッセージを取得する

    テンプレートメッセージ: youtube上でユーザーのコメントがないときに読み上げるメッセージ
    """
    message = random.choice(TEMPLATE_MESSAGES)  # noqa: S311
    return ORJSONResponse(content={"message": message})


@app.get("/template_question")
async def get_template_question():
    """テンプレート質問を取得する

    テンプレート質問: youtube上でユーザーのコメントがないときに読み上げる質問
    """
    question = random.choice(TEMPLATE_QUESTIONS)  # noqa: S311
    return ORJSONResponse(content={"question": question})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7200)
