import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.databases.models.youtube_chat_message_cursors import YoutubeChatMessageCursorModel
from src.youtube import YouTubeChatMessageCursor


class YoutubeChatMessageCursorRepository:
    """YouTube のライブメッセージカーソルのリポジトリ

    メッセージをどこまで読み出したかを管理する
    """

    def __init__(self, session: Session):
        self._session = session

    def find_current_cursor(self) -> YouTubeChatMessageCursor | None:
        """現在のカーソルを取得する

        最新のものを1つ取得すればok
        """
        stmt = select(YoutubeChatMessageCursorModel).order_by(YoutubeChatMessageCursorModel.id.desc())

        result = self._session.execute(stmt).scalars().first()

        if not result:
            return None

        return self._build_entity(result)

    def save(self, cursor: YouTubeChatMessageCursor) -> None:
        """カーソルを保存する"""
        stmt = pg.Insert(YoutubeChatMessageCursorModel).values(
            {
                "video_id": cursor.video_id,
                "message_id": cursor.message_id,
            }
        )
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[
                YoutubeChatMessageCursorModel.video_id,
                YoutubeChatMessageCursorModel.message_id,
            ]
        )

        self._session.execute(stmt)

    def _build_entity(self, model: YoutubeChatMessageCursorModel) -> YouTubeChatMessageCursor:
        return YouTubeChatMessageCursor(
            video_id=model.video_id,
            message_id=model.message_id,
        )
