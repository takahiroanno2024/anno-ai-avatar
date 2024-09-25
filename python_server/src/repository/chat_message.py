import datetime

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.databases.models.youtube_chat_messages import YoutubeChatMessageModel
from src.youtube import YouTubeChatMessage


class YoutubeChatMessageRepository:
    """YouTube のライブチャットメッセージのリポジトリ"""

    def __init__(self, session: Session):
        self._session = session

    def save(
        self,
        *,
        messages: list[YouTubeChatMessage],
    ) -> None:
        """保存"""
        values = [
            {
                "video_id": settings.YT_ID,
                "message_id": message.message_id,
                "message_text": message.message_text,
                "author_name": message.author_name,
                "author_image_url": message.author_image_url,
                "created_at": message.created_at,
            }
            for message in messages
        ]

        if not values:
            return None

        stmt = pg.Insert(YoutubeChatMessageModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[YoutubeChatMessageModel.message_id],
            set_={
                "video_id": stmt.excluded.video_id,
                "message_text": stmt.excluded.message_text,
                "author_name": stmt.excluded.author_name,
                "author_image_url": stmt.excluded.author_image_url,
            },
        )
        self._session.execute(stmt)

    def find_one(
        self,
        *,
        video_id: str,
        message_id: str,
    ) -> YouTubeChatMessage | None:
        """1 件取得"""
        stmt = select(YoutubeChatMessageModel).where(
            YoutubeChatMessageModel.video_id == video_id,
            YoutubeChatMessageModel.message_id == message_id,
        )

        result = self._session.execute(stmt).scalars().first()

        if not result:
            return None

        return self._build_entity(result)

    def find_latest_messages(
        self,
        *,
        limit: int = 20,
    ) -> list[YouTubeChatMessage]:
        """最新のメッセージを取得する"""
        stmt = select(YoutubeChatMessageModel).order_by(YoutubeChatMessageModel.created_at.desc()).limit(limit)
        results = self._session.execute(stmt).scalars().all()

        return [self._build_entity(model) for model in results]

    def find_oldest_messages(
        self,
        *,
        limit: int = 20,
    ) -> list[YouTubeChatMessage]:
        """最も古いメッセージを取得する"""
        stmt = select(YoutubeChatMessageModel).order_by(YoutubeChatMessageModel.created_at.asc()).limit(limit)
        results = self._session.execute(stmt).scalars().all()

        return [self._build_entity(model) for model in results]

    def find_messages_after(
        self,
        *,
        datetime_: datetime.datetime,
    ) -> list[YouTubeChatMessage]:
        """指定した時刻以降に作成されたメッセージを作成時刻の昇順で取得する"""
        stmt = select(YoutubeChatMessageModel).where(datetime_ <= YoutubeChatMessageModel.created_at).order_by(YoutubeChatMessageModel.created_at.asc())
        results = self._session.execute(stmt).scalars().all()

        return [self._build_entity(model) for model in results]

    def _build_entity(self, model: YoutubeChatMessageModel) -> YouTubeChatMessage:
        return YouTubeChatMessage(
            video_id=model.video_id,
            message_id=model.message_id,
            message_text=model.message_text,
            author_name=model.author_name,
            author_image_url=model.author_image_url,
            created_at=model.created_at,
        )
