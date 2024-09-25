from sqlalchemy import Column, DateTime, Integer, String, func

from src.databases.engine import Base
from src.databases.models.utils import default_func


class YoutubeChatMessageModel(Base):
    """YouTube のライブメッセージ"""

    __tablename__ = "youtube_chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    video_id = Column(String, nullable=False)
    # liveChatMessages.id
    message_id = Column(String, nullable=False, unique=True)
    # snippet.textMessageDetails.messageText
    message_text = Column(String, nullable=False)
    # authorDetails.displayName
    author_name = Column(String, nullable=False)
    # authorDetails.profileImageUrl
    author_image_url = Column(String, nullable=False)

    created_at = Column(  # type: ignore[assignment]
        DateTime(timezone=True),
        default=default_func.local_now,
        server_default=func.now(),
        nullable=False,
    )
