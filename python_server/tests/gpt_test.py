import asyncio
import datetime
import os
import sys
from zoneinfo import ZoneInfo

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import settings
from src.gpt import filter_inappropriate_comments, generate_response

tz = ZoneInfo("Asia/Tokyo")


async def test_single_question() -> None:
    # このテストはUnitテストというよりはIntegrationテストに近いため、
    # 環境変数INTEGRATION_TESTがtrueのときのみ実行する
    # （例）INTEGRATION_TEST=true pytest tests/gpt_test.py
    if os.environ.get("INTEGRATION_TEST") != "true":
        return

    text = "なぜ国会議員ではなく都知事を目指すの？"
    print(f"Input text: {text}")
    message = await _request_gpt(text)

    print("Response message: ", message)


async def test_multiple_questions() -> None:
    if os.environ.get("INTEGRATION_TEST") != "true":
        return

    texts = [
        "なんで都知事になろうと思ったの？専門性を活かして政府のブレインやったほうがよくない？",
        "経済成長と社会福祉、どちらのほうが大切？",
        "著作物を違法に学習に利用している思われる生成AIは禁止すべきでは？",
        "どういう女性が好み？",
    ]

    tasks = [_request_gpt(text) for text in texts]

    results = await asyncio.gather(*tasks)

    print("\n\n==result==")

    for text, result in zip(texts, results, strict=True):
        print(f"Text: {text}\nResult: {result}\n\n")


async def test_filter_inappropriate_comments() -> None:
    if os.environ.get("INTEGRATION_TEST") != "true":
        return

    texts = [
        "なんで都知事になろうと思ったの？専門性を活かして政府のブレインやったほうがよくない？",
        "経済成長と社会福祉、どちらのほうが大切？",
        "つまんね",
        "著作物を違法に学習に利用している思われる生成AIは禁止すべきでは？",
        "ウェーイ",
        "選挙活動もVTuberの時代か、すげーな",
        "こいつも学歴詐称だろどうせ",
        "握手して！",
        "応援してます。頑張って！",
        "# 経済成長と社会福祉、どちらのほうが大切？",  # コメントアウトの例
        "＃ 著作物を違法に学習に利用している思われる生成AIは禁止すべきでは？",  # コメントアウトの例
        "ハッシュタグ施策 #TOKYOAI について教えて",  # 文中の場合はコメントアウトされない
    ]

    res = await filter_inappropriate_comments(texts)

    expected = [
        "なんで都知事になろうと思ったの？専門性を活かして政府のブレインやったほうがよくない？",
        "経済成長と社会福祉、どちらのほうが大切？",
        "著作物を違法に学習に利用している思われる生成AIは禁止すべきでは？",
        "選挙活動もVTuberの時代か、すげーな",
        "握手して！",
        "応援してます。頑張って！",
    ]
    assert res == expected


async def _request_gpt(text: str) -> str:
    current_time = datetime.datetime.now(tz=tz)
    t_fmt = current_time.strftime("%Y%m%d_%H%M%S")

    log_filename_json = settings.PYTHON_SERVER_ROOT / "log" / f"log_{t_fmt}.json"
    log_filename_csv = settings.PYTHON_SERVER_ROOT / "log" / f"log_{t_fmt}.csv"
    message, _ = await generate_response(text, log_filename_csv, log_filename_json)
    return message
