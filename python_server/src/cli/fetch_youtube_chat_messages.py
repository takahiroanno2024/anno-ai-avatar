import asyncio

import click

from src.cli.wrap.sync import sync
from src.databases.engine import session_scope
from src.logger import setup_logger
from src.repository.chat_message import YoutubeChatMessageRepository
from src.youtube import YouTubeClient

setup_logger()


@click.command()
@sync
async def main() -> None:
    """YouTube のコメントをひたすら取得してDBに保存する"""
    await _comment_fetcher()


async def _fetch_and_store_comments(
    *,
    client: YouTubeClient,
    chat_id: str,
    page_token: str | None = None,
) -> str | None:
    messages, next_token = await client.get_chat_messages(
        chat_id=chat_id,
        page_token=page_token,
    )

    for message in messages:
        print(f"save message: {message.message_id}, {message.message_text}")

    with session_scope() as session:
        repo = YoutubeChatMessageRepository(session=session)
        repo.save(messages=messages)

    return next_token


async def _comment_fetcher() -> None:
    interval = 60

    client = YouTubeClient()

    chat_id = await client.get_chat_id()

    assert chat_id is not None

    next_token = None

    while True:
        next_token = await _fetch_and_store_comments(
            client=client,
            chat_id=chat_id,
            page_token=next_token,
        )
        print("waiting...")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    main()
