import datetime

from src.repository.chat_message import YoutubeChatMessageRepository
from src.repository.chat_message_cursor import YoutubeChatMessageCursorRepository
from src.youtube import YouTubeChatMessage, YouTubeChatMessageCursor


class FindYoutubeChatMessagesUseCase:
    """YouTube のライブチャットメッセージを取得するユースケース"""

    def __init__(
        self,
        *,
        youtube_chat_message_repo: YoutubeChatMessageRepository,
        youtube_chat_message_cursor_repo: YoutubeChatMessageCursorRepository,
    ):
        self._youtube_chat_message_repo = youtube_chat_message_repo
        self._youtube_chat_message_cursor_repo = youtube_chat_message_cursor_repo

    def find_messages(self) -> list[YouTubeChatMessage]:
        """DB からライブメッセージを取得する

        何度も同じものを読み出さないようにカーソルを使用してどこまで読んだかを管理する
        読みだしたらカーソルを進める

        本来はカーソルを client に返したほうが良いが、現状はサーバー側で管理する

        カーソルが取得できない時(初回を想定)は古いメッセージから返すようにする
        """
        cursor = self._youtube_chat_message_cursor_repo.find_current_cursor()

        if not cursor:
            messages = self._youtube_chat_message_repo.find_oldest_messages()
            self._save_cursor(messages)
            return messages

        message_on_cursor = self._youtube_chat_message_repo.find_one(
            video_id=cursor.video_id,
            message_id=cursor.message_id,
        )

        if message_on_cursor:
            print("message_on_cursor", message_on_cursor.message_text)

        if not message_on_cursor:
            # 想定外だが、カーソルが指すメッセージが存在しない時
            messages = self._youtube_chat_message_repo.find_oldest_messages()
            self._save_cursor(messages)
            return messages

        messages = self._youtube_chat_message_repo.find_messages_after(
            datetime_=message_on_cursor.created_at + datetime.timedelta(seconds=1),
        )

        self._save_cursor(messages)
        return messages

    def _save_cursor(self, messages: list[YouTubeChatMessage]) -> None:
        """カーソルを保存する"""
        if not messages:
            return

        latest_message = sorted(messages, key=lambda x: x.created_at)[-1]

        self._youtube_chat_message_cursor_repo.save(
            YouTubeChatMessageCursor(
                video_id=latest_message.video_id,
                message_id=latest_message.message_id,
            )
        )
