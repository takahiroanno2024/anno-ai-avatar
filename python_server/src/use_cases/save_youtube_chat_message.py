from src.repository.chat_message import YoutubeChatMessageRepository
from src.youtube import YouTubeChatMessage


class SaveYoutubeChatMessageUseCase:
    """Youtubeのライブチャットを保存するユースケース"""

    def __init__(self, *, youtube_chat_message_repo: YoutubeChatMessageRepository):
        self._youtube_chat_message_repo = youtube_chat_message_repo

    def save_new_message(self, message: YouTubeChatMessage):
        """DBに新しいメッセージを1件保存する"""
        self._youtube_chat_message_repo.save(messages=[message])
