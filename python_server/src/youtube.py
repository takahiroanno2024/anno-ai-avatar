import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import tenacity
from pydantic import BaseModel

from src.config import settings


class YouTubeChatMessage(BaseModel):
    """YouTube チャットメッセージ"""

    video_id: str
    message_id: str
    message_text: str
    author_name: str
    author_image_url: str
    created_at: datetime.datetime


class YouTubeChatMessageCursor(BaseModel):
    """YouTube チャットメッセージカーソル"""

    video_id: str
    message_id: str


class YouTubeClient:
    """YouTube API のクライアント"""

    def __init__(self) -> None:
        self.api_key = settings.YOUTUBE_API_KEY

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        reraise=True,
    )
    async def get_chat_id(self) -> str | None:
        """YouTube ビデオのライブチャットIDを取得する

        see: https://developers.google.com/youtube/v3/docs/videos/list?hl=ja#http-request
        """
        video_id = settings.YT_ID

        if not video_id:
            raise ValueError("YouTube URL is required")

        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "key": self.api_key,
            "id": video_id,
            "part": "liveStreamingDetails",
        }

        async with httpx.AsyncClient() as client_:
            response = await client_.get(url, params=params)
            response.raise_for_status()  # HTTPステータスコードのチェック
            data = response.json()

        live_streaming_details = data.get("items", [{}])[0].get("liveStreamingDetails", {})

        return live_streaming_details.get("activeLiveChatId")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        reraise=True,
    )
    async def get_chat(
        self,
        *,
        chat_id: str,
        pageToken: str | None = None,
    ) -> dict[str, Any]:
        """指定したライブチャットIDに対するチャットメッセージを取得するチャットメッセージを

        Args:
            chat_id (str): チャットID
            pageToken (str | None): ページトークン

        レスポンス例:
        {
          "kind": "youtube#liveChatMessageListResponse",
          "etag": etag,
          "nextPageToken": string,
          "pollingIntervalMillis": unsigned integer,
          "offlineAt": datetime,
          "pageInfo": {
            "totalResults": integer,
            "resultsPerPage": integer
          },
          "items": [
            liveChatMessage Resource
          ]
        }

        see: https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list?hl=ja#http-request
        """
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        params = {
            "key": self.api_key,
            "liveChatId": chat_id,
            "part": "id,snippet,authorDetails",
            "pageToken": pageToken,
        }

        async with httpx.AsyncClient() as client_:
            response = await client_.get(url, params=params)
            response.raise_for_status()  # HTTPステータスコードのチェック
            data = response.json()

        return data

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        reraise=True,
    )
    async def get_chat_messages(
        self,
        *,
        chat_id: str,
        page_token: str | None = None,
    ) -> tuple[list[YouTubeChatMessage], str | None]:
        """指定したライブチャットIDに対するチャットメッセージを取得する

        Args:
            chat_id (str): チャットID
            page_token (str | None): ページトークン

        Returns:
            tuple[list[YouTubeChatMessage], str | None]: チャットメッセージリストとページトークン

        see: https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list?hl=ja#http-request
        """
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        params = {
            "key": self.api_key,
            "liveChatId": chat_id,
            "part": "id,snippet,authorDetails",
            "pageToken": page_token,
        }

        async with httpx.AsyncClient() as client_:
            response = await client_.get(url, params=params)
            response.raise_for_status()  # HTTPステータスコードのチェック
            data = response.json()

        messages = []

        for item in data.get("items", []):
            type_ = item["snippet"]["type"]

            if type_ != "textMessageEvent":
                continue

            message_text = item["snippet"]["textMessageDetails"]["messageText"]

            message = YouTubeChatMessage(
                video_id=settings.YT_ID,
                message_id=item["id"],
                message_text=message_text,
                author_name=item["authorDetails"]["displayName"],
                author_image_url=item["authorDetails"]["profileImageUrl"],
                created_at=datetime.datetime.fromisoformat(item["snippet"]["publishedAt"]).astimezone(ZoneInfo("Asia/Tokyo")),
            )

            messages.append(message)

        return messages, data.get("nextPageToken")


youtube_client = YouTubeClient()
