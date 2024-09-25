from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from src.databases.engine import Base


class YoutubeChatMessageCursorModel(Base):
    """YouTube のライブメッセージをどこまで読んだかのカーソル

    クライアント毎には管理しないので誰が読み出したかにかかわらずカーソルは進む
    """

    __tablename__ = "youtube_chat_message_cursors"

    __table_args__ = (UniqueConstraint("video_id", "message_id", name="unique_video_message"),)

    id = Column(Integer, primary_key=True, autoincrement=True)

    video_id = Column(String, nullable=False)

    # youtube_chat_messages.message_id
    message_id = Column(String, ForeignKey("youtube_chat_messages.message_id"), nullable=False)
