from pydantic import BaseModel


class YouTubeChatMessageModel(BaseModel):
    """YouTubeのチャットメッセージ"""

    video_id: str
    message_id: str
    message_text: str
    author_name: str
    author_image_url: str


class YouTubeChatMessagesResponseModel(BaseModel):
    """YouTubeのチャットメッセージのレスポンスモデル"""

    messages: list[YouTubeChatMessageModel]
